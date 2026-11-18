"""Run isolated, validation-only Phase 3 experiments; test scoring is separate."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import platform
import random
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import torch

from bharatair.config import PROJECT_ROOT
from bharatair.evaluation.metrics import score
from bharatair.experiments.artifacts import (
    atomic_bytes, atomic_csv, atomic_json, candidate_identity,
    commit_candidate, file_sha256, fingerprint, validate_candidate_provenance,
    validate_manifest, validate_run_id, verify_completed_candidate,
)
from bharatair.experiments.config import ExperimentConfig
from bharatair.features.windows import (
    assemble_features, common_issue_indices, eligible_issue_indices,
    feature_names, prepare_series,
)
from bharatair.models.baselines import persistence, seasonal_naive
from bharatair.models.classical import CLASSICAL_CONFIGS, classical_importance, make_classical_model, predict_classical
from bharatair.models.neural import NEURAL_CONFIGS, fit_neural, predict_neural

LOG = logging.getLogger(__name__)
CANONICAL = PROJECT_ROOT / "data" / "processed" / "delhi_site_1422_pm25.parquet"


def _versions() -> dict[str, str]:
    result = {}
    for package in ("numpy", "pandas", "pyarrow", "scikit-learn", "xgboost", "torch", "matplotlib", "joblib"):
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = "not-installed"
    return result


def _runtime(device: str, seed: int) -> dict[str, Any]:
    cuda = torch.version.cuda
    gpu = torch.cuda.get_device_name(0) if device == "cuda" else None
    return {
        "python_executable": sys.executable, "python": sys.version,
        "platform": platform.platform(), "processor": platform.processor(),
        "torch_version": torch.__version__, "torch_build": torch.__config__.show(),
        "cuda_version": cuda, "device": device, "gpu_name": gpu,
        "gpu_capability": list(torch.cuda.get_device_capability(0)) if device == "cuda" else None,
        "torch_threads": torch.get_num_threads(), "seed": seed,
        "deterministic_algorithms": True, "library_versions": _versions(),
    }


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)
    torch.set_num_threads(min(4, os.cpu_count() or 1))


def _mase_scale(series) -> float:
    idx = np.flatnonzero(series.observed)
    idx = idx[series.calendar[idx] < series.boundaries.validation_start]
    adjacent = np.diff(idx) == 1
    diff = np.abs(series.values[idx[1:]][adjacent] - series.values[idx[:-1]][adjacent])
    return float(diff.mean()) if len(diff) and diff.mean() > 0 else 1.0


def _predictions(series, issue_idx, horizon, prediction, model, family, input_hours):
    target_idx = issue_idx + horizon
    return pd.DataFrame({
        "model": model, "family": family, "input_hours": input_hours,
        "horizon_hours": horizon, "issue_timestamp": series.calendar[issue_idx],
        "target_timestamp": series.calendar[target_idx], "actual": series.values[target_idx],
        "predicted": prediction,
    })


def _device(requested: str) -> str:
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError(f"CUDA was explicitly requested, but {sys.executable} has no CUDA-enabled PyTorch or available CUDA device (torch={torch.__version__}, torch.version.cuda={torch.version.cuda}).")
    if requested == "cuda":
        # Fail before work if deterministic kernels are unavailable on the selected GPU.
        torch.cuda.get_device_name(0)
    return requested


def _not_applicable_cuda_memory_telemetry(candidate_id: str, reason: str) -> dict[str, Any]:
    return {
        "status": "not_applicable", "telemetry_collected": False,
        "candidate_id": candidate_id, "reason": reason,
        "device_name": None, "device_index": None,
        "peak_memory_allocated_bytes": None, "peak_memory_allocated_mib": None,
        "peak_memory_reserved_bytes": None, "peak_memory_reserved_mib": None,
        "measurement_scope": "CUDA candidate fit and validation prediction execution",
        "measurement_started_at_utc": None, "measurement_completed_at_utc": None,
        "measurement_duration_seconds": None,
    }


def _begin_candidate_cuda_memory_measurement(candidate_id: str, candidate_device: str) -> dict[str, Any] | None:
    """Reset isolated CUDA peak counters immediately before one neural candidate."""
    requested = torch.device(candidate_device)
    if requested.type != "cuda":
        return None
    index = requested.index if requested.index is not None else torch.cuda.current_device()
    device = torch.device("cuda", index)
    try:
        device_name = torch.cuda.get_device_name(device)
        # Drain previous work and release allocator cache so reserved peaks do not
        # inherit a prior candidate's caching-allocator high-water mark.
        torch.cuda.synchronize(device)
        torch.cuda.empty_cache()
        torch.cuda.synchronize(device)
        torch.cuda.reset_peak_memory_stats(device)
        started_at = datetime.now(timezone.utc).isoformat()
        started_perf = time.perf_counter()
    except Exception as exc:
        LOG.exception("CUDA memory telemetry setup failed for candidate %s", candidate_id)
        raise RuntimeError(f"CUDA memory telemetry setup failed for candidate {candidate_id}: {exc}") from exc
    return {
        "candidate_id": candidate_id, "device": device,
        "device_name": device_name, "device_index": int(index),
        "measurement_started_at_utc": started_at, "started_perf": started_perf,
        "measurement_scope": "candidate fit_neural() including epoch validation and predict_neural(); excludes feature assembly and artifact serialization",
        "synchronized_before_reset": True, "peak_stats_reset": True,
    }


def _finish_candidate_cuda_memory_measurement(measurement: dict[str, Any] | None,
                                              candidate_id: str) -> dict[str, Any]:
    """Synchronize and collect finite per-candidate allocator peaks, or fail."""
    if measurement is None:
        return _not_applicable_cuda_memory_telemetry(candidate_id, "candidate executed on CPU")
    try:
        if measurement["candidate_id"] != candidate_id:
            raise ValueError("measurement candidate identity changed")
        device = measurement["device"]
        torch.cuda.synchronize(device)
        allocated = torch.cuda.max_memory_allocated(device)
        reserved = torch.cuda.max_memory_reserved(device)
        completed_at = datetime.now(timezone.utc).isoformat()
        duration = time.perf_counter() - measurement["started_perf"]
        if (not math.isfinite(float(allocated)) or not math.isfinite(float(reserved))
                or allocated < 0 or reserved < 0 or not math.isfinite(duration) or duration < 0):
            raise ValueError("CUDA peak counters or measurement duration were invalid")
    except Exception as exc:
        LOG.exception("CUDA memory telemetry collection failed for candidate %s", candidate_id)
        raise RuntimeError(f"CUDA memory telemetry collection failed for candidate {candidate_id}: {exc}") from exc
    return {
        "status": "success", "telemetry_collected": True,
        "candidate_id": candidate_id, "reason": None,
        "device_name": measurement["device_name"], "device_index": measurement["device_index"],
        "peak_memory_allocated_bytes": int(allocated),
        "peak_memory_allocated_mib": float(allocated) / (1024 ** 2),
        "peak_memory_reserved_bytes": int(reserved),
        "peak_memory_reserved_mib": float(reserved) / (1024 ** 2),
        "measurement_scope": measurement["measurement_scope"],
        "measurement_started_at_utc": measurement["measurement_started_at_utc"],
        "measurement_completed_at_utc": completed_at,
        "measurement_duration_seconds": float(duration),
        "synchronized_before_reset": measurement["synchronized_before_reset"],
        "synchronized_before_readback": True,
        "peak_stats_reset": measurement["peak_stats_reset"],
    }


def _validation_source() -> tuple[pd.DataFrame, pd.DatetimeIndex, pd.Timestamp, str]:
    """Read all timestamps for fixed quantile cuts, but values only before test_start."""
    timestamps = pd.read_parquet(CANONICAL, columns=["timestamp_ist"])["timestamp_ist"]
    if timestamps.dt.tz is not None:
        raise ValueError("Expected naive IST timestamps")
    if timestamps.duplicated().any():
        raise ValueError("Duplicate timestamps must be reviewed before feature construction")
    ordered_times = pd.DatetimeIndex(timestamps.drop_duplicates().sort_values())
    validation_start = ordered_times[int(np.floor(0.70 * len(ordered_times)))]
    test_start = ordered_times[int(np.floor(0.85 * len(ordered_times)))]
    # Parquet predicate pushdown ensures test PM2.5 values are never materialized.
    observed = pd.read_parquet(CANONICAL, columns=["timestamp_ist", "value"],
                               filters=[("timestamp_ist", "<", test_start)])
    observed = observed.sort_values("timestamp_ist", kind="mergesort")
    digest = hashlib.sha256(pd.util.hash_pandas_object(observed[["timestamp_ist", "value"]], index=False).values.tobytes()).hexdigest()
    return observed, ordered_times, pd.Timestamp(test_start), digest


def _validation_data_fingerprint(digest: str, timestamps: pd.DatetimeIndex) -> str:
    return fingerprint({"pretest_observations_sha256": digest, "timestamp_count": len(timestamps),
                        "station_id": "site_1422", "parameter": "PM2.5"})


def _candidate_provenance(run_id: str, model: str, family: str, input_hours: int | None,
                          horizon: int, seed: int, model_config: dict[str, Any],
                          provenance: dict[str, str]) -> dict[str, str]:
    identity = {"model": model, "family": family, "input_hours": input_hours,
                "horizon_hours": horizon, "seed": seed, "model_configuration": model_config}
    return {"run_id": run_id, "candidate_id": candidate_identity(run_id, model, input_hours, horizon),
            **provenance, "run_configuration_fingerprint": provenance["configuration_fingerprint"],
            "configuration_fingerprint": fingerprint({"run_configuration_fingerprint": provenance["configuration_fingerprint"], **identity})}


def _write_candidate(run_dir: Path, run_id: str, model: str, family: str, input_hours: int | None,
                     horizon: int, seed: int, model_config: dict[str, Any], provenance: dict[str, str],
                     metrics: dict[str, Any], pred_frame: pd.DataFrame, checkpoint_writer=None) -> dict[str, Any]:
    cid = candidate_identity(run_id, model, input_hours, horizon)
    candidate_root = run_dir / "candidates" / cid
    candidate_root.mkdir(parents=True, exist_ok=True)
    if any(candidate_root.glob("attempt_*/complete.json")):
        raise RuntimeError(f"Refusing to overwrite committed candidate: {cid}")
    attempts = [int(p.name.split("_")[-1]) for p in candidate_root.glob("attempt_*") if p.name.split("_")[-1].isdigit()]
    directory = candidate_root / f"attempt_{max(attempts, default=0) + 1:03d}"
    directory.mkdir(exist_ok=False)
    checkpoint = directory / ("baseline.json" if family == "baseline" else ("model.joblib" if family == "traditional_ml" else "model.pt"))
    if checkpoint_writer:
        atomic_bytes(checkpoint, checkpoint_writer)
    else:
        atomic_json(checkpoint, {"definition": model, **provenance})
    # Verify checkpoint readability and embedded identity before any complete marker exists.
    if family == "traditional_ml":
        restored = joblib.load(checkpoint)
        if not callable(getattr(restored, "predict", None)):
            raise RuntimeError(f"Serialized estimator is not loadable: {cid}")
    elif family == "deep_learning":
        payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
        validate_candidate_provenance(payload, provenance)
        from bharatair.models.neural import build_neural_model
        restored = build_neural_model(model, int(input_hours))
        restored.load_state_dict(payload["state_dict"])
    else:
        json.loads(checkpoint.read_text(encoding="utf-8"))
    record = {
        "run_id": run_id, "candidate_id": cid, "model": model, "family": family,
        "input_hours": input_hours, "horizon_hours": horizon, "seed": seed,
        "model_configuration": model_config, "checkpoint": str(checkpoint.relative_to(PROJECT_ROOT)),
        "checkpoint_sha256": file_sha256(checkpoint), **metrics,
    }
    pred_frame = pred_frame.copy()
    pred_frame.insert(0, "candidate_id", cid)
    pred_frame.insert(0, "run_id", run_id)
    pred_frame["seed"] = seed
    pred_frame["model_configuration_json"] = json.dumps(model_config, sort_keys=True, default=str)
    pred_frame["checkpoint"] = record["checkpoint"]
    cfg = {**record, **provenance}
    atomic_json(directory / "candidate.json", cfg)
    atomic_json(directory / "validation_metrics.json", record)
    atomic_csv(directory / "validation_predictions.csv", pred_frame, date_format="%Y-%m-%dT%H:%M:%S")
    json.loads((directory / "candidate.json").read_text(encoding="utf-8"))
    json.loads((directory / "validation_metrics.json").read_text(encoding="utf-8"))
    if len(pd.read_csv(directory / "validation_predictions.csv")) != len(pred_frame):
        raise RuntimeError(f"Validation prediction row count verification failed: {cid}")
    artifact_paths = [checkpoint, directory / "candidate.json", directory / "validation_metrics.json", directory / "validation_predictions.csv"]
    return commit_candidate(directory, provenance={"run_id": run_id, "candidate_id": cid, **provenance}, artifact_paths=artifact_paths)


def _load_completed(run_dir: Path, expected_common: dict[str, str]) -> tuple[list[dict[str, Any]], list[pd.DataFrame]]:
    metrics, predictions = [], []
    for marker_path in sorted((run_dir / "candidates").glob("*/attempt_*/complete.json")):
        directory = marker_path.parent
        marker = verify_completed_candidate(directory)
        candidate = json.loads((directory / "candidate.json").read_text(encoding="utf-8"))
        for key, value in expected_common.items():
            if candidate.get(key) != value or marker.get(key) != value:
                raise ValueError(f"Resume refused: candidate {directory.name} mismatches {key}")
        recomputed = _candidate_provenance(candidate["run_id"], candidate["model"], candidate["family"],
            candidate["input_hours"], candidate["horizon_hours"], candidate["seed"],
            candidate["model_configuration"], {"configuration_fingerprint": candidate["run_configuration_fingerprint"],
                "data_fingerprint": candidate["data_fingerprint"], "split_fingerprint": candidate["split_fingerprint"],
                "preprocessing_fingerprint": candidate["preprocessing_fingerprint"]})
        validate_candidate_provenance(candidate, recomputed)
        validate_candidate_provenance(marker, recomputed)
        metric_record = json.loads((directory / "validation_metrics.json").read_text(encoding="utf-8"))
        telemetry = metric_record.get("cuda_memory_telemetry")
        expected_status = "success" if candidate.get("family") == "deep_learning" and str(candidate.get("model_configuration", {}).get("device", "cpu")).startswith("cuda") else "not_applicable"
        if (not isinstance(telemetry, dict) or telemetry.get("candidate_id") != candidate.get("candidate_id")
                or telemetry.get("status") != expected_status):
            raise ValueError(f"Resume refused: candidate {directory.name} has missing or incompatible CUDA memory telemetry")
        if expected_status == "success":
            for key in ("peak_memory_allocated_bytes", "peak_memory_allocated_mib",
                        "peak_memory_reserved_bytes", "peak_memory_reserved_mib"):
                value = telemetry.get(key)
                if not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0:
                    raise ValueError(f"Resume refused: candidate {directory.name} has invalid {key}")
        metrics.append(metric_record)
        predictions.append(pd.read_csv(directory / "validation_predictions.csv", parse_dates=["issue_timestamp", "target_timestamp"]))
    return metrics, predictions


def run_experiment(config: ExperimentConfig | None = None, *, run_id: str | None = None,
                   device: str = "cpu", resume: bool = False) -> dict[str, Any]:
    """Run/recover validation candidates only. This function never builds test windows."""
    config = config or ExperimentConfig()
    device = _device(device)
    _seed_everything(config.seed)
    run_id = validate_run_id(run_id or datetime.now().strftime("phase3_%Y%m%d_%H%M%S"))
    run_dir = PROJECT_ROOT / "runs" / run_id
    if run_dir.exists() and not resume:
        raise FileExistsError(f"Run already exists; choose a new --run-id or use --resume: {run_dir}")
    if not run_dir.exists():
        run_dir.mkdir(parents=True, exist_ok=False)
    for name in ("candidates", "metrics", "predictions", "configs", "logs"):
        (run_dir / name).mkdir(exist_ok=True)

    # Test timestamps establish the approved chronological cut; Parquet values at
    # and after test_start are not loaded on this validation-only path.
    frame, all_timestamps, test_start, observed_digest = _validation_source()
    series = prepare_series(frame, split_timestamps=all_timestamps, data_end=all_timestamps[-1])
    split = series.boundaries.as_dict()
    split_fp = fingerprint(split)
    data_fp = _validation_data_fingerprint(observed_digest, all_timestamps)
    preprocess = {
        "timezone": "naive IST retained", "missing_policy": "no imputation; reject any gap in input-to-target window",
        "scaling": "TrainOnlyScaler for neural models only; classical estimator-native config",
        "feature_rule": "observed PM2.5 lags plus deterministic issue-time calendar features",
        "cohort": config.common_comparison_cohort,
    }
    preprocess_fp = fingerprint(preprocess)
    config_fp = fingerprint({"experiment_config": config.as_dict(), "device": device, "protocol": "phase3-v3-cuda-memory-telemetry"})
    manifest_payload = {
        "schema_version": 2, "run_id": run_id, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "validation_in_progress", "config": config.as_dict(), "config_fingerprint": config_fp,
        "data_fingerprint": data_fp, "validation_observations_sha256": observed_digest,
        "test_values_loaded": False, "dataset_path": str(CANONICAL.relative_to(PROJECT_ROOT)),
        "split_boundaries": split, "split_fingerprint": split_fp,
        "preprocessing": preprocess, "preprocessing_fingerprint": preprocess_fp,
        "station_id": "site_1422", "station": "Dwarka-Sector 8, Delhi - DPCC", "network": "cpcb_caaqm",
        "parameter": "PM2.5", "unit": "µg/m³", "runtime": _runtime(device, config.seed),
        "tree_result_reuse": "legacy artifacts not reused; rerun in isolated run unless exact equivalence is later proven",
        "stale_checkpoint_exclusion": "legacy models/gru_L168_H1.pt excluded; only run-scoped, provenance-verified checkpoints are eligible",
        "cuda_memory_telemetry_policy": "candidate-isolated peaks; synchronize, empty unused allocator cache, reset peak stats immediately before neural candidate, synchronize before readback",
    }
    manifest_path = run_dir / "manifest.json"
    if resume:
        if not manifest_path.is_file():
            raise ValueError("Resume refused: run directory has no manifest")
        validate_manifest(json.loads(manifest_path.read_text(encoding="utf-8")), manifest_payload)
        # Preserve creation time and status history on resume.
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing.get("status") == "validation_complete_test_not_evaluated":
            raise ValueError("Resume refused: validation run is already complete")
        manifest_payload["created_at_utc"] = existing["created_at_utc"]
    atomic_json(manifest_path, manifest_payload)

    indices: dict[int, dict[int, dict[str, np.ndarray]]] = {length: {} for length in config.input_lengths}
    for length in config.input_lengths:
        for horizon in config.horizons:
            result, _ = eligible_issue_indices(series, length, horizon,
                long_gap_threshold=config.long_gap_threshold_hours, splits=("train", "validation"))
            indices[length][horizon] = result
    # Common cohort is validation only: no test split lookup, timestamps, counts, or target reads.
    common_val = {h: common_issue_indices({l: indices[l][h] for l in config.input_lengths}, "validation") for h in config.horizons}
    mase = _mase_scale(series)
    atomic_json(run_dir / "configs" / "validation_protocol.json", {
        "config": config.as_dict(), "split_boundaries": split, "preprocessing": preprocess,
        "mase_scale_train_adjacent_hour_mae": mase,
        "common_validation_issue_counts": {str(h): int(len(v)) for h, v in common_val.items()},
    })

    base_prov = {"configuration_fingerprint": config_fp, "data_fingerprint": data_fp,
                 "split_fingerprint": split_fp, "preprocessing_fingerprint": preprocess_fp}
    expected_prov = {"run_id": run_id, "run_configuration_fingerprint": config_fp,
                     "data_fingerprint": data_fp, "split_fingerprint": split_fp,
                     "preprocessing_fingerprint": preprocess_fp}
    records, _ = _load_completed(run_dir, expected_prov) if resume else ([], [])
    completed_ids = {r["candidate_id"] for r in records}
    total = len(config.horizons) * (2 + len(config.input_lengths) * 6)
    done = len(records)

    # Baselines are candidates too, with their equation documented as the checkpoint.
    for horizon in config.horizons:
        issue = common_val[horizon]
        feats = assemble_features(series, issue, max(config.input_lengths), horizon)
        for name, pred in (("persistence", persistence(series, issue)), ("seasonal_naive", seasonal_naive(series, issue, horizon))):
            cid = candidate_identity(run_id, name, None, horizon)
            if cid in completed_ids:
                continue
            metrics = score(feats["y"], pred, mase_scale=mase)
            metrics["cuda_memory_telemetry"] = _not_applicable_cuda_memory_telemetry(
                cid, "baseline candidate uses CPU execution")
            frame_pred = _predictions(series, issue, horizon, pred, name, "baseline", None)
            prov = _candidate_provenance(run_id, name, "baseline", None, horizon, config.seed, {"definition": name}, base_prov)
            _write_candidate(run_dir, run_id, name, "baseline", None, horizon, config.seed,
                             {"definition": name}, prov, metrics, frame_pred)
            done += 1
            LOG.info("Validation candidate %d/%d complete: %s H=%d MAE=%.4f", done, total, name, horizon, metrics["mae"])

    importances: dict[str, Any] = {}
    for horizon in config.horizons:
        validation_idx = common_val[horizon]
        for length in config.input_lengths:
            train_idx = indices[length][horizon]["train"]
            if not len(train_idx) or not len(validation_idx):
                raise RuntimeError(f"No eligible train/validation windows for L={length}, H={horizon}")
            train = assemble_features(series, train_idx, length, horizon)
            val = assemble_features(series, validation_idx, length, horizon)
            for model_name in ("linear_regression", "random_forest", "xgboost", "lstm", "gru", "tcn"):
                cid = candidate_identity(run_id, model_name, length, horizon)
                if cid in completed_ids:
                    continue
                seed = config.seed + 100_000 + length * 100 + horizon if model_name in NEURAL_CONFIGS else config.seed + length * 100 + horizon
                model_conf = NEURAL_CONFIGS[model_name] if model_name in NEURAL_CONFIGS else CLASSICAL_CONFIGS[model_name]
                candidate_cfg = {"input_hours": length, "horizon_hours": horizon, "seed": seed, "model": model_conf,
                                 "device": device if model_name in NEURAL_CONFIGS else "cpu",
                                 "neural_protocol": "same seed policy, epochs/patience/batch/lr and train-only scaling across LSTM/GRU/TCN" if model_name in NEURAL_CONFIGS else None}
                prov = _candidate_provenance(run_id, model_name,
                    "deep_learning" if model_name in NEURAL_CONFIGS else "traditional_ml", length, horizon, seed, candidate_cfg, base_prov)
                start = time.perf_counter()
                if model_name in NEURAL_CONFIGS:
                    cuda_measurement = _begin_candidate_cuda_memory_measurement(cid, device)
                    fit = fit_neural(model_name, train["sequences"], train["calendar"], train["y"],
                        val["sequences"], val["calendar"], val["y"], seed=seed, input_length=length, device=device)
                    prediction = predict_neural(fit.model, fit.scaler, val["sequences"], val["calendar"], device=device)
                    cuda_telemetry = _finish_candidate_cuda_memory_measurement(cuda_measurement, cid)
                    checkpoint_payload = {
                        "state_dict": {k: v.detach().cpu() for k, v in fit.model.state_dict().items()},
                        "architecture": model_name, "input_hours": length, "horizon_hours": horizon,
                        "seed": seed, "scaler": fit.scaler.state(), "hyperparameters": model_conf,
                        "best_epoch": fit.best_epoch, "training_loss_history": fit.train_loss_history,
                        "validation_loss_history": fit.validation_loss_history, "run_id": run_id,
                        **prov,
                        "candidate_id": cid,
                    }
                    writer = lambda path, obj=checkpoint_payload: torch.save(obj, path)
                    family = "deep_learning"
                    training_seconds = fit.training_seconds
                else:
                    estimator = make_classical_model(model_name, seed)
                    estimator.fit(train["tabular"], train["y"])
                    prediction = predict_classical(estimator, val["tabular"])
                    writer = lambda path, obj=estimator: joblib.dump(obj, path, compress=3)
                    family = "traditional_ml"
                    training_seconds = time.perf_counter() - start
                    cuda_telemetry = _not_applicable_cuda_memory_telemetry(cid, "traditional candidate uses CPU execution")
                    imp = classical_importance(estimator, model_name, feature_names(length))
                    importances[cid] = imp
                metrics = score(val["y"], prediction, mase_scale=mase)
                metrics.update({"training_seconds": training_seconds, "validation_prediction_seconds": time.perf_counter() - start,
                                "n": int(len(validation_idx)), "cuda_memory_telemetry": cuda_telemetry})
                pred_frame = _predictions(series, validation_idx, horizon, prediction, model_name, family, length)
                _write_candidate(run_dir, run_id, model_name, family, length, horizon, seed,
                                 candidate_cfg, prov, metrics, pred_frame, writer)
                if family == "deep_learning":
                    # Do not keep the prior candidate's parameters allocated while
                    # the next candidate's independent peak window begins.
                    del fit
                done += 1
                LOG.info("Validation candidate %d/%d complete: %s L=%d H=%d MAE=%.4f", done, total, model_name, length, horizon, metrics["mae"])

    records, prediction_frames = _load_completed(run_dir, expected_prov)
    metric_df = pd.DataFrame(records)
    atomic_csv(run_dir / "metrics" / "validation_model_metrics.csv", metric_df)
    if importances:
        atomic_json(run_dir / "metrics" / "traditional_feature_importance.json", importances)
    selection = {"selected_using": "validation MAE only", "test_accessed": False, "horizons": {}}
    for horizon in config.horizons:
        subset = metric_df[metric_df.horizon_hours == horizon]
        winners = {}
        for family in ("baseline", "traditional_ml", "deep_learning"):
            part = subset[subset.family == family]
            winners[family] = part.sort_values("mae").iloc[0].to_dict()
        overall = min(winners.values(), key=lambda row: row["mae"])
        selection["horizons"][str(horizon)] = {
            "best_baseline": winners["baseline"], "best_traditional_ml": winners["traditional_ml"],
            "best_deep_learning": winners["deep_learning"], "validation_selected_overall": overall,
        }
    atomic_json(run_dir / "metrics" / "validation_model_selection.json", selection)
    if prediction_frames:
        atomic_csv(run_dir / "predictions" / "validation_all_candidates.csv", pd.concat(prediction_frames, ignore_index=True), date_format="%Y-%m-%dT%H:%M:%S")
    telemetry_summary = {row["candidate_id"]: row["cuda_memory_telemetry"] for row in records}
    telemetry_summary_path = run_dir / "metrics" / "candidate_device_telemetry.json"
    atomic_json(telemetry_summary_path, telemetry_summary)
    manifest_payload["status"] = "validation_complete_test_not_evaluated"
    manifest_payload["validation_candidate_count"] = int(len(metric_df))
    manifest_payload["validation_completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest_payload["validation_selection_sha256"] = file_sha256(run_dir / "metrics" / "validation_model_selection.json")
    manifest_payload["candidate_device_telemetry_sha256"] = file_sha256(telemetry_summary_path)
    atomic_json(manifest_path, manifest_payload)
    LOG.info("Validation complete: %d candidates. Test evaluation was not performed.", len(metric_df))
    return {"run_id": run_id, "run_dir": str(run_dir), "status": manifest_payload["status"], "candidates": len(metric_df), "selection": selection}


def evaluate_test(run_id: str) -> dict[str, Any]:
    """Explicit post-validation test evaluation. Called only by --evaluate-test."""
    run_id = validate_run_id(run_id)
    run_dir = PROJECT_ROOT / "runs" / run_id
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "validation_complete_test_not_evaluated":
        raise ValueError("Test evaluation requires a completed validation-only run")
    selection_path = run_dir / "metrics" / "validation_model_selection.json"
    if file_sha256(selection_path) != manifest.get("validation_selection_sha256"):
        raise ValueError("Validation selection changed after completion; test evaluation refused")
    validation_frame, timestamps, _, observed_digest = _validation_source()
    if _validation_data_fingerprint(observed_digest, timestamps) != manifest.get("data_fingerprint"):
        raise ValueError("Source validation observations changed since model selection; test evaluation refused")
    frame = pd.read_parquet(CANONICAL)
    series = prepare_series(frame)
    config_values = {key: value for key, value in manifest["config"].items() if key in ExperimentConfig.__dataclass_fields__}
    config_values["input_lengths"] = tuple(config_values["input_lengths"])
    config_values["horizons"] = tuple(config_values["horizons"])
    config = ExperimentConfig(**config_values)
    indices: dict[int, dict[int, dict[str, np.ndarray]]] = {l: {} for l in config.input_lengths}
    for length in config.input_lengths:
        for horizon in config.horizons:
            indices[length][horizon], _ = eligible_issue_indices(series, length, horizon, long_gap_threshold=config.long_gap_threshold_hours)
    common_test = {h: common_issue_indices({l: indices[l][h] for l in config.input_lengths}, "test") for h in config.horizons}
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    predictions_path = run_dir / "predictions" / "test_selected_predictions.csv"
    metrics_path = run_dir / "metrics" / "test_selected_metrics.csv"
    if predictions_path.exists() or metrics_path.exists():
        raise FileExistsError("Test evaluation artifacts already exist; refusing to overwrite")
    all_preds = []
    for h in config.horizons:
        issue_idx = common_test[h]
        chosen = selection["horizons"][str(h)]["validation_selected_overall"]
        model, family, length = chosen["model"], chosen["family"], chosen.get("input_hours")
        if family == "baseline":
            prediction = persistence(series, issue_idx) if model == "persistence" else seasonal_naive(series, issue_idx, h)
        else:
            cid = candidate_identity(run_id, model, int(length), h)
            candidate_root = run_dir / "candidates" / cid
            completed = sorted(candidate_root.glob("attempt_*/complete.json"))
            if len(completed) != 1:
                raise ValueError(f"Expected exactly one committed checkpoint for {cid}")
            candidate_dir = completed[0].parent
            marker = verify_completed_candidate(candidate_dir)
            expected = {k: marker[k] for k in ("run_id", "candidate_id", "configuration_fingerprint", "data_fingerprint", "split_fingerprint", "preprocessing_fingerprint")}
            candidate = json.loads((candidate_dir / "candidate.json").read_text(encoding="utf-8"))
            validate_candidate_provenance(candidate, expected)
            features = assemble_features(series, issue_idx, int(length), h)
            checkpoint = candidate_dir / ("model.joblib" if family == "traditional_ml" else "model.pt")
            if family == "traditional_ml":
                estimator = joblib.load(checkpoint)
                prediction = predict_classical(estimator, features["tabular"])
            else:
                payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
                validate_candidate_provenance(payload, expected)
                from bharatair.models.neural import build_neural_model, predict_neural
                from bharatair.features.scaling import TrainOnlyScaler
                network = build_neural_model(model, int(length))
                network.load_state_dict(payload["state_dict"])
                network.eval()
                scaler = TrainOnlyScaler()
                scaler.input_mean_, scaler.input_scale_ = payload["scaler"]["input_mean"], payload["scaler"]["input_scale"]
                scaler.target_mean_, scaler.target_scale_ = payload["scaler"]["target_mean"], payload["scaler"]["target_scale"]
                prediction = predict_neural(network, scaler, features["sequences"], features["calendar"], device="cpu")
        out = _predictions(series, issue_idx, h, prediction, model, family, length)
        all_preds.append(out)
    predictions = pd.concat(all_preds, ignore_index=True)
    predictions["residual"] = predictions["predicted"] - predictions["actual"]
    metric_rows = []
    mase = _mase_scale(series)
    for (model, family, length, horizon), part in predictions.groupby(["model", "family", "input_hours", "horizon_hours"]):
        metric_rows.append({"model": model, "family": family, "input_hours": length, "horizon_hours": int(horizon), **score(part.actual.to_numpy(), part.predicted.to_numpy(), mase_scale=mase)})
    atomic_csv(run_dir / "predictions" / "test_selected_predictions.csv", predictions, date_format="%Y-%m-%dT%H:%M:%S")
    atomic_csv(run_dir / "metrics" / "test_selected_metrics.csv", pd.DataFrame(metric_rows))
    manifest["status"] = "test_evaluated_explicit_opt_in"
    manifest["test_evaluated_at_utc"] = datetime.now(timezone.utc).isoformat()
    atomic_json(manifest_path, manifest)
    return {"run_id": run_id, "status": manifest["status"], "metrics": metric_rows}

