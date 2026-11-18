"""Isolated Phase 5 multi-station validation runner and safety primitives.

The validation entry point has no test-evaluation path. Test scoring is intentionally
not implemented here; it will require a separately reviewed command.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import torch

from bharatair.config import PROJECT_ROOT
from bharatair.experiments.artifacts import (
    atomic_bytes, atomic_csv, atomic_json, commit_candidate, file_sha256,
    fingerprint, validate_manifest, verify_completed_candidate,
)
from bharatair.features.windows import calendar_features, common_issue_indices

REPORTS = PROJECT_ROOT / "reports"
RAW_DIR = PROJECT_ROOT / "data" / "phase4_audit" / "raw_cpcb_pm25" / "yearly"
COHORT_PATH = REPORTS / "PHASE5_STATION_COHORT.csv"
FEASIBILITY_PATH = REPORTS / "PHASE5_STATION_FEASIBILITY.csv"
PREFLIGHT_PATH = REPORTS / "PHASE5_PREFLIGHT.json"
MODELS = ("linear_regression", "random_forest", "xgboost", "lstm", "gru", "tcn")
LOOKBACKS = (24, 48, 168)
HORIZONS = (1, 6, 12, 24)
MIN_TRAIN = 5_000
MIN_VALIDATION = 1_000
MIN_POOLED_TRAIN = 20_000
MIN_POOLED_VALIDATION = 2_500


class TestDataAccessError(RuntimeError):
    """Raised when validation-mode source data crosses the frozen test boundary."""


@dataclass(frozen=True)
class Phase5Context:
    run_id: str
    experiment: str
    cohort: str
    config: dict[str, Any]
    config_fp: str
    data_fp: str
    split_fp: str
    preprocess_fp: str
    output_dir: Path


def runtime_metadata(device: str, seed: int) -> dict[str, Any]:
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError(f"CUDA requested but unavailable in {sys.executable}; torch={torch.__version__}, CUDA build={torch.version.cuda}")
    index = torch.cuda.current_device() if device == "cuda" else None
    return {
        "python_executable": sys.executable, "python": sys.version,
        "platform": platform.platform(), "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda, "device": device,
        "gpu_name": torch.cuda.get_device_name(index) if index is not None else None,
        "gpu_index": index, "seed": seed,
    }


def atomic_write_candidate(directory: Path, *, provenance: dict[str, str],
                           checkpoint_writer, metrics: dict[str, Any],
                           predictions: pd.DataFrame) -> dict[str, Any]:
    """Write candidate artifacts into a new attempt and commit only after read-back."""
    directory.mkdir(parents=True, exist_ok=True)
    if list(directory.glob("attempt_*/complete.json")):
        raise FileExistsError("Refusing to overwrite an already committed Phase 5 candidate")
    attempts = [int(p.name.split("_")[-1]) for p in directory.glob("attempt_*") if p.name.split("_")[-1].isdigit()]
    attempt = directory / f"attempt_{max(attempts, default=0) + 1:03d}"
    attempt.mkdir(exist_ok=False)
    checkpoint = attempt / "checkpoint.bin"
    atomic_bytes(checkpoint, checkpoint_writer)
    atomic_json(attempt / "metrics.json", metrics)
    atomic_csv(attempt / "validation_predictions.csv", predictions, date_format="%Y-%m-%dT%H:%M:%S")
    if not checkpoint.is_file() or not checkpoint.stat().st_size:
        raise RuntimeError("Checkpoint write verification failed")
    reread_metrics = json.loads((attempt / "metrics.json").read_text(encoding="utf-8"))
    reread_predictions = pd.read_csv(attempt / "validation_predictions.csv")
    if len(reread_predictions) != int(reread_metrics.get("n", -1)):
        raise RuntimeError("Prediction row count does not match metric sample count")
    paths = [checkpoint, attempt / "metrics.json", attempt / "validation_predictions.csv"]
    return commit_candidate(attempt, provenance=provenance, artifact_paths=paths)


def verify_candidate_resume(attempt_dir: Path, expected: dict[str, str]) -> dict[str, Any]:
    marker = verify_completed_candidate(attempt_dir)
    if marker is None:
        raise ValueError("Resume refused: candidate lacks a committed completion marker")
    for key, value in expected.items():
        if marker.get(key) != value:
            raise ValueError(f"Resume refused: candidate provenance mismatch for {key}")
    return marker


def _read_filtered(path: Path, station_cutoffs: dict[str, pd.Timestamp]) -> pd.DataFrame:
    """Read only pre-test rows using station-specific frozen test boundaries."""
    if not station_cutoffs:
        raise ValueError("Frozen station test cutoffs are required before source access")
    normalized={str(sid):pd.Timestamp(value) for sid,value in station_cutoffs.items()}
    if any(value.tzinfo is not None for value in normalized.values()):
        raise ValueError("Expected frozen naive IST cutoffs")
    # DNF predicate pushdown keeps later-validating cities while ensuring every
    # station's PM2.5 values at/after its own test start are excluded at read time.
    filters=[[ ("station_id","=",sid), ("collected_at","<",cutoff)]
             for sid,cutoff in normalized.items()]
    table=pq.read_table(path,columns=["station_id","collected_at","value"],filters=filters)
    frame=table.to_pandas()
    if not frame.empty:
        limits=frame.station_id.map(normalized)
        if limits.isna().any() or (frame.collected_at.to_numpy() >= limits.to_numpy()).any():
            raise TestDataAccessError("Parquet reader returned a row at/after that station's test lock")
    return frame


def load_validation_panel(raw_dir: Path, station_ids: Iterable[str],
                          test_cutoffs: dict[str, pd.Timestamp],
                          station_to_city: dict[str,str] | None = None) -> pd.DataFrame:
    """Load only CPCB rows before each station's frozen city test boundary."""
    allowed=set(station_ids)
    if station_to_city is None:
        if len(test_cutoffs)!=1:
            raise ValueError("station_to_city is required for multi-city source loading")
        station_to_city={sid:next(iter(test_cutoffs)) for sid in allowed}
    station_cutoffs={sid:pd.Timestamp(test_cutoffs[station_to_city[sid]]) for sid in allowed}
    pieces=[]
    for path in sorted(raw_dir.glob("*.parquet")):
        schema=pq.read_schema(path)
        if not {"station_id","collected_at","value"}.issubset(set(schema.names)):
            continue
        frame=_read_filtered(path,station_cutoffs)
        if not frame.empty: pieces.append(frame)
    if not pieces: return pd.DataFrame(columns=["station_id","collected_at","value"])
    result=pd.concat(pieces,ignore_index=True)
    limits=result.station_id.map(station_cutoffs)
    if limits.isna().any() or (result.collected_at.to_numpy() >= limits.to_numpy()).any():
        raise TestDataAccessError("Validation panel includes test-period values")
    if result.duplicated(["station_id","collected_at"]).any():
        raise ValueError("Duplicate station timestamps must be resolved from source evidence before modeling")
    return result.sort_values(["station_id","collected_at"],kind="mergesort").reset_index(drop=True)


def exact_common_issue_times(issue_times: dict[int, dict[str, pd.DatetimeIndex]],
                             split: str = "validation") -> pd.DatetimeIndex:
    """Exact timestamp intersection; counts alone are never treated as equivalence."""
    arrays = [pd.DatetimeIndex(issue_times[length][split]) for length in LOOKBACKS]
    common = arrays[0]
    for other in arrays[1:]:
        common = common.intersection(other, sort=False)
    return common.sort_values()


def make_candidate_manifest(cohort: pd.DataFrame, feasibility: pd.DataFrame) -> pd.DataFrame:
    """Expand the full 17,280 grid and annotate, never drop, ineligible definitions."""
    rows: list[dict[str, Any]] = []
    for exp in ("A", "B", "C"):
        cohort_names = (("primary_seven_city_a_b", "primary"), ("pune_tier_b_sensitivity", "pune"))
        for cohort_key, label in cohort_names:
            group = cohort[cohort.cohort.eq(cohort_key)]
            if exp == "B":
                units = [(city, g) for city, g in group.groupby("city", sort=True)]
                variants = ("global", "station_aware")
            else:
                units = [(str(row.station_id), group[group.station_id.eq(row.station_id)]) for row in group.itertuples()]
                variants = ("station_specific",) if exp == "A" else ("leave_one_station_out",)
            for unit_id, unit in units:
                for lookback in LOOKBACKS:
                    for horizon in HORIZONS:
                        for model in MODELS:
                            for variant in variants:
                                if exp == "B":
                                    matched = feasibility[(feasibility.cohort == cohort_key)&(feasibility.city == unit_id)&
                                                          (feasibility.lookback_hours == lookback)&(feasibility.horizon_hours == horizon)]
                                    train_n = int(matched.pooled_train_windows.iloc[0])
                                    val_n = int(matched.pooled_validation_common_168_windows.iloc[0])
                                    train_floor, val_floor = MIN_POOLED_TRAIN, MIN_POOLED_VALIDATION
                                else:
                                    sid = unit_id
                                    f = feasibility[(feasibility.station_id == sid)&(feasibility.lookback_hours == lookback)&
                                                    (feasibility.horizon_hours == horizon)].iloc[0]
                                    if exp == "A":
                                        train_n = int(f.train_eligible_windows)
                                        train_floor, val_floor = MIN_TRAIN, MIN_VALIDATION
                                    else:
                                        train_n = int(f.loso_peer_train_windows)
                                        train_floor, val_floor = MIN_POOLED_TRAIN, MIN_VALIDATION
                                    val_n = int(f.common_168h_cohort_validation)
                                reasons=[]
                                if train_n == 0: reasons.append("zero_training_windows_structurally_untrainable")
                                elif train_n < train_floor: reasons.append("below_training_floor")
                                if val_n < val_floor: reasons.append("below_validation_floor")
                                rows.append({"experiment":exp,"cohort":label,"unit_id":unit_id,"candidate_id":f"{exp}-{label}-{unit_id}-L{lookback}-H{horizon}-{model}-{variant}",
                                    "station_id":unit_id if exp != "B" else "","model":model,"lookback_hours":lookback,"horizon_hours":horizon,
                                    "normalization_variant":variant,"planned":True,"train_windows":train_n,"validation_common_windows":val_n,
                                    "test_values_accessed":False,"execution_status":"not_executed",
                                    "model_selection_eligible":not reasons,"structurally_untrainable":train_n==0,
                                    "ineligibility_reasons":";".join(reasons)})
    result=pd.DataFrame(rows)
    if len(result)!=17280:
        raise RuntimeError(f"Full candidate manifest expected 17,280 rows; found {len(result)}")
    return result


def build_context(run_id: str, experiment: str, cohort: str, config: dict[str, Any],
                  data_fp: str, split_fp: str, preprocess_fp: str) -> Phase5Context:
    if not run_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for ch in run_id):
        raise ValueError("Unsafe Phase 5 run ID")
    if experiment not in {"A", "B", "C"} or cohort not in {"primary", "pune"}:
        raise ValueError("Unknown Phase 5 experiment or cohort")
    config_fp=fingerprint(config)
    return Phase5Context(run_id,experiment,cohort,config,config_fp,data_fp,split_fp,preprocess_fp,
                         PROJECT_ROOT/"runs"/run_id)


def validation_only_plan(output_dir: Path, manifest: pd.DataFrame, *,
                         test_cutoffs: dict[str, str], runtime: dict[str, Any]) -> None:
    """Persist planned candidate definitions without executing any fit."""
    if output_dir.exists():
        raise FileExistsError(f"Refusing to reuse existing Phase 5 run path: {output_dir}")
    output_dir.mkdir(parents=True)
    (output_dir/"candidates").mkdir()
    atomic_csv(output_dir/"candidate_manifest.csv", manifest)
    payload={"run_id":output_dir.name,"status":"planned_not_executed","validation_only":True,
             "test_values_loaded":False,"test_windows_materialized":False,"test_predictions_created":False,
             "test_metrics_created":False,"test_cutoffs_timestamp_only":test_cutoffs,"runtime":runtime,
             "planned_candidate_count":int(len(manifest)),"executed_fit_count":0,
             "selection_eligible_planned_count":int(manifest.model_selection_eligible.sum()),
             "structurally_untrainable_count":int(manifest.structurally_untrainable.sum())}
    atomic_json(output_dir/"manifest.json",payload)


def main() -> None:
    import argparse
    import logging
    parser=argparse.ArgumentParser(description="BharatAir Phase 5 validation-only runner")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--experiment", choices=("A","B","C"), required=True)
    parser.add_argument("--cohort", choices=("primary","pune"), required=True)
    parser.add_argument("--device", choices=("cuda","cpu"), default="cuda")
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan-only", action="store_true", help="write definitions only; execute no fits")
    mode.add_argument("--execute", action="store_true", help="run validation candidates; test evaluation remains unavailable")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--evaluate-test", action="store_true", help="reserved; test evaluation is not implemented")
    args=parser.parse_args()
    if args.evaluate_test:
        raise SystemExit("Test evaluation is not implemented in the Phase 5 runner; validation-only lock remains closed")
    cohort=pd.read_csv(COHORT_PATH,keep_default_na=False)
    feasibility=pd.read_csv(FEASIBILITY_PATH)
    label="primary_seven_city_a_b" if args.cohort=="primary" else "pune_tier_b_sensitivity"
    selected=cohort[cohort.cohort.eq(label)].copy()
    cutoffs={r.city:pd.Timestamp(r.city_split_test_start_ist) for r in selected.drop_duplicates("city").itertuples()}
    runtime=runtime_metadata(args.device,42)
    candidates=make_candidate_manifest(cohort,feasibility)
    candidates=candidates[(candidates.experiment==args.experiment)&(candidates.cohort==args.cohort)]
    out=PROJECT_ROOT/"runs"/args.run_id
    if args.plan_only:
        validation_only_plan(out,candidates,test_cutoffs={k:v.isoformat() for k,v in cutoffs.items()},runtime=runtime)
        print(json.dumps({"run_id":args.run_id,"status":"planned_not_executed","candidates":len(candidates)},indent=2))
        return
    if args.device!="cuda" and args.experiment=="A":
        raise SystemExit("Experiment A neural candidates must run on explicitly selected CUDA; CPU fallback is forbidden")
    station_to_city=dict(zip(selected.station_id.astype(str),selected.city.astype(str)))
    panel=load_validation_panel(RAW_DIR,selected.station_id.astype(str).tolist(),cutoffs,station_to_city)
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
    from bharatair.phase5.engine import execute_validation
    result=execute_validation(run_id=args.run_id,experiment=args.experiment,cohort_name=args.cohort,panel=panel,
                              station_meta=cohort,feasibility=feasibility,device=args.device,resume=args.resume)
    print(json.dumps({"run_id":args.run_id,"status":result["status"],"planned":result["planned_candidate_count"],
        "completed":result["completed_candidate_count"],"failed":result["failed_candidate_count"],
        "ineligible":result["skipped_ineligible_candidate_count"],"run_dir":str(out)},indent=2))

@dataclass
class StationAwareScaler:
    """Train-only station scaling with a training-global fallback for unseen sites."""
    global_stats: tuple[float,float,float,float]
    station_stats: dict[str, tuple[float,float,float,float]]

    @classmethod
    def fit(cls, sequences: np.ndarray, targets: np.ndarray, station_ids: Iterable[str]) -> "StationAwareScaler":
        ids=np.asarray(list(station_ids),dtype=str)
        if len(ids)!=len(sequences) or len(ids)!=len(targets) or not len(ids):
            raise ValueError("Training arrays and station identities must have equal nonzero length")
        def stats(x,y):
            xs=float(x.mean()); xd=float(x.std()) or 1.0
            ys=float(y.mean()); yd=float(y.std()) or 1.0
            return xs,xd,ys,yd
        global_stats=stats(sequences,targets)
        by={str(sid):stats(sequences[ids==sid],targets[ids==sid]) for sid in np.unique(ids)}
        return cls(global_stats,by)

    def transform_x(self, sequences: np.ndarray, station_ids: Iterable[str]) -> np.ndarray:
        ids=np.asarray(list(station_ids),dtype=str)
        if len(ids)!=len(sequences): raise ValueError("Station ID count mismatch")
        out=np.empty_like(sequences,dtype=np.float32)
        for i,sid in enumerate(ids):
            mean,scale,_,_=self.station_stats.get(sid,self.global_stats)
            out[i]=(sequences[i]-mean)/scale
        return out

    def transform_y(self, values: np.ndarray, station_ids: Iterable[str]) -> np.ndarray:
        ids=np.asarray(list(station_ids),dtype=str)
        if len(ids)!=len(values): raise ValueError("Station ID count mismatch")
        out=np.empty_like(values,dtype=np.float32)
        for i,sid in enumerate(ids):
            _,_,mean,scale=self.station_stats.get(sid,self.global_stats)
            out[i]=(values[i]-mean)/scale
        return out

    def inverse_y(self, values: np.ndarray, station_ids: Iterable[str]) -> np.ndarray:
        ids=np.asarray(list(station_ids),dtype=str)
        return np.asarray([v*self.station_stats.get(sid,self.global_stats)[3]+self.station_stats.get(sid,self.global_stats)[2]
                           for v,sid in zip(values,ids)],dtype=np.float64)

    def state(self) -> dict[str,Any]:
        return {"global":list(self.global_stats),"stations":{str(k):[float(x) for x in v] for k,v in sorted(self.station_stats.items(),key=lambda item:str(item[0]))}}


def fit_station_vocabulary(training_station_ids: Iterable[str]) -> dict[str,int]:
    """Create categorical codes from training stations only; 0 is unknown."""
    return {sid:i+1 for i,sid in enumerate(sorted(set(map(str,training_station_ids))))}


def encode_station_ids(station_ids: Iterable[str], vocabulary: dict[str,int]) -> np.ndarray:
    return np.asarray([vocabulary.get(str(sid),0) for sid in station_ids],dtype=np.int64)


def assert_unseen_station_fold(training_station_ids: Iterable[str], heldout_station_id: str) -> None:
    if heldout_station_id in set(map(str,training_station_ids)):
        raise ValueError("Unseen-station leakage: held-out station appears in training examples")


def begin_cuda_telemetry(candidate_id: str, device: str) -> dict[str,Any] | None:
    if not device.startswith("cuda"): return None
    if not torch.cuda.is_available(): raise RuntimeError("CUDA telemetry requested but CUDA is unavailable")
    dev=torch.device(device)
    torch.cuda.synchronize(dev)
    torch.cuda.empty_cache()
    torch.cuda.synchronize(dev)
    torch.cuda.reset_peak_memory_stats(dev)
    return {"candidate_id":candidate_id,"device":dev,"device_name":torch.cuda.get_device_name(dev),
            "device_index":dev.index if dev.index is not None else torch.cuda.current_device(),"started":time.perf_counter()}


def finish_cuda_telemetry(state: dict[str,Any] | None, candidate_id: str) -> dict[str,Any]:
    if state is None:
        return {"status":"not_applicable","candidate_id":candidate_id,"allocated_bytes":None,"reserved_bytes":None}
    if state["candidate_id"]!=candidate_id: raise ValueError("CUDA telemetry candidate identity mismatch")
    dev=state["device"]
    torch.cuda.synchronize(dev)
    allocated=int(torch.cuda.max_memory_allocated(dev)); reserved=int(torch.cuda.max_memory_reserved(dev))
    if allocated<0 or reserved<0 or not math.isfinite(float(allocated+reserved)):
        raise RuntimeError("CUDA telemetry failed; refusing zero fallback")
    return {"status":"success","candidate_id":candidate_id,"device_name":state["device_name"],
            "device_index":state["device_index"],"allocated_bytes":allocated,"allocated_mib":allocated/2**20,
            "reserved_bytes":reserved,"reserved_mib":reserved/2**20,"duration_seconds":time.perf_counter()-state["started"],
            "scope":"candidate fit and validation prediction; excludes data loading and artifact serialization"}


if __name__ == "__main__":
    main()

