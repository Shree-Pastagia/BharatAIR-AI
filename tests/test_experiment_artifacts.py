import json

import numpy as np
import pandas as pd
import pytest

from bharatair.experiments import artifacts


def test_atomic_json_csv_and_candidate_commit_are_verified(tmp_path):
    from bharatair.experiments.artifacts import atomic_csv, atomic_json, commit_candidate, verify_completed_candidate

    directory = tmp_path / "candidate"
    directory.mkdir()
    atomic_json(directory / "config.json", {"seed": 9})
    atomic_csv(directory / "pred.csv", pd.DataFrame({"actual": [1.0], "predicted": [2.0]}))
    marker = commit_candidate(directory, provenance={"run_id": "r1", "candidate_id": "c1"},
                              artifact_paths=[directory / "config.json", directory / "pred.csv"])
    assert marker["status"] == "complete"
    assert verify_completed_candidate(directory) == marker
    (directory / "pred.csv").write_text("corrupt", encoding="utf-8")
    with pytest.raises(ValueError, match="failed verification"):
        verify_completed_candidate(directory)


def test_provenance_and_resume_manifest_require_exact_fingerprints():
    with pytest.raises(ValueError, match="configuration_fingerprint"):
        artifacts.validate_candidate_provenance(
            {"run_id": "r1", "candidate_id": "c1", "configuration_fingerprint": "bad",
             "data_fingerprint": "d", "split_fingerprint": "s", "preprocessing_fingerprint": "p"},
            {"run_id": "r1", "candidate_id": "c1", "configuration_fingerprint": "good",
             "data_fingerprint": "d", "split_fingerprint": "s", "preprocessing_fingerprint": "p"},
        )
    with pytest.raises(ValueError, match="data_fingerprint"):
        artifacts.validate_manifest(
            {"run_id": "r1", "config_fingerprint": "c", "data_fingerprint": "old", "split_fingerprint": "s",
             "preprocessing_fingerprint": "p", "runtime": {"device": "cuda", "torch_version": "2", "cuda_version": "12"}},
            {"run_id": "r1", "config_fingerprint": "c", "data_fingerprint": "new", "split_fingerprint": "s",
             "preprocessing_fingerprint": "p", "runtime": {"device": "cuda", "torch_version": "2", "cuda_version": "12"}},
        )


def test_validation_only_synthetic_smoke_never_reads_or_assembles_test_targets(tmp_path, monkeypatch, caplog):
    from bharatair.experiments import run
    from bharatair.experiments.config import ExperimentConfig

    caplog.set_level("INFO")
    rows = 1100
    times = pd.date_range("2020-01-01", periods=rows, freq="h")
    values = 30 + 10 * np.sin(np.arange(rows) / 24) + np.arange(rows) * 0.002
    source = pd.DataFrame({"timestamp_ist": times, "value": values})
    dataset = tmp_path / "synthetic.parquet"
    source.to_parquet(dataset, index=False)
    monkeypatch.setattr(run, "CANONICAL", dataset)

    original_read = pd.read_parquet
    def guarded_read(path, *args, **kwargs):
        columns = kwargs.get("columns")
        if columns and "value" in columns:
            assert kwargs.get("filters") == [("timestamp_ist", "<", pd.Timestamp(times[int(np.floor(.85 * rows))]))]
        return original_read(path, *args, **kwargs)
    monkeypatch.setattr(pd, "read_parquet", guarded_read)

    original_eligible = run.eligible_issue_indices
    def validation_splits_only(series, *args, **kwargs):
        assert kwargs.get("splits") == ("train", "validation")
        return original_eligible(series, *args, **kwargs)
    monkeypatch.setattr(run, "eligible_issue_indices", validation_splits_only)

    monkeypatch.chdir(tmp_path)
    # PROJECT_ROOT is fixed from the package location, so redirect only run artifact root.
    monkeypatch.setattr(run, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(run, "CANONICAL", tmp_path / "data" / "processed" / "synthetic.parquet")
    run.CANONICAL.parent.mkdir(parents=True)
    source.to_parquet(run.CANONICAL, index=False)
    cfg = ExperimentConfig(input_lengths=(24,), horizons=(1,), bootstrap_replicates=2)
    result = run.run_experiment(cfg, run_id="synthetic_validation_smoke", device="cpu")
    run_dir = tmp_path / "runs" / "synthetic_validation_smoke"
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert result["status"] == "validation_complete_test_not_evaluated"
    assert manifest["test_values_loaded"] is False
    assert not (run_dir / "predictions" / "test_selected_predictions.csv").exists()
    assert not (run_dir / "metrics" / "test_selected_metrics.csv").exists()
    assert len(list((run_dir / "candidates").glob("*/attempt_*/complete.json"))) == 8
    telemetry_path = run_dir / "metrics" / "candidate_device_telemetry.json"
    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    assert len(telemetry) == 8
    assert all(value["status"] == "not_applicable" for value in telemetry.values())
    assert manifest["candidate_device_telemetry_sha256"] == run.file_sha256(telemetry_path)
    assert "Test evaluation was not performed" in caplog.text
