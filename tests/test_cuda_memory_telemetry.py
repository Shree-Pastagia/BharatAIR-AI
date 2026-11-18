import json
import math

import pandas as pd
import pytest
import torch

from bharatair.experiments import artifacts, run


def _mock_cuda(monkeypatch, *, allocated=100, reserved=900):
    calls = []
    monkeypatch.setattr(torch.cuda, "get_device_name", lambda device: "Mock CUDA GPU")
    monkeypatch.setattr(torch.cuda, "synchronize", lambda device: calls.append(("synchronize", str(device))))
    monkeypatch.setattr(torch.cuda, "empty_cache", lambda: calls.append(("empty_cache", None)))
    monkeypatch.setattr(torch.cuda, "reset_peak_memory_stats", lambda device: calls.append(("reset", str(device))))
    monkeypatch.setattr(torch.cuda, "max_memory_allocated", lambda device: allocated)
    monkeypatch.setattr(torch.cuda, "max_memory_reserved", lambda device: reserved)
    return calls


def test_cuda_candidate_has_finite_independent_peaks_and_reserved_can_exceed_allocated(monkeypatch):
    calls = _mock_cuda(monkeypatch, allocated=1024, reserved=4096)
    measurement = run._begin_candidate_cuda_memory_measurement("r__lstm", "cuda:0")
    result = run._finish_candidate_cuda_memory_measurement(measurement, "r__lstm")
    assert result["status"] == "success"
    assert result["telemetry_collected"] is True
    assert result["candidate_id"] == "r__lstm"
    assert result["device_name"] == "Mock CUDA GPU"
    assert result["device_index"] == 0
    assert result["peak_memory_allocated_bytes"] == 1024
    assert result["peak_memory_allocated_mib"] == pytest.approx(1024 / 1024**2)
    assert result["peak_memory_reserved_bytes"] == 4096
    assert result["peak_memory_reserved_mib"] == pytest.approx(4096 / 1024**2)
    assert result["peak_memory_reserved_bytes"] != result["peak_memory_allocated_bytes"]
    assert math.isfinite(result["measurement_duration_seconds"])
    assert [call[0] for call in calls].count("reset") == 1
    assert calls.index(("reset", "cuda:0")) > calls.index(("empty_cache", None))


def test_candidate_peak_statistics_reset_independently(monkeypatch):
    calls = _mock_cuda(monkeypatch)
    for candidate in ("r__lstm", "r__gru"):
        measurement = run._begin_candidate_cuda_memory_measurement(candidate, "cuda:0")
        run._finish_candidate_cuda_memory_measurement(measurement, candidate)
    assert [call[0] for call in calls].count("reset") == 2
    assert [call[0] for call in calls].count("empty_cache") == 2
    resets = [index for index, call in enumerate(calls) if call[0] == "reset"]
    for reset_index in resets:
        assert [call[0] for call in calls[reset_index - 3:reset_index + 1]] == [
            "synchronize", "empty_cache", "synchronize", "reset"
        ]


def test_cpu_candidate_records_not_applicable_telemetry():
    assert run._begin_candidate_cuda_memory_measurement("r__rf", "cpu") is None
    result = run._finish_candidate_cuda_memory_measurement(None, "r__rf")
    assert result["status"] == "not_applicable"
    assert result["telemetry_collected"] is False
    assert result["peak_memory_allocated_bytes"] is None
    assert result["peak_memory_reserved_bytes"] is None


def test_cuda_telemetry_failure_raises_instead_of_recording_zero(monkeypatch):
    _mock_cuda(monkeypatch)
    monkeypatch.setattr(torch.cuda, "max_memory_allocated", lambda device: (_ for _ in ()).throw(RuntimeError("counter unavailable")))
    measurement = run._begin_candidate_cuda_memory_measurement("r__tcn", "cuda:0")
    with pytest.raises(RuntimeError, match="telemetry collection failed"):
        run._finish_candidate_cuda_memory_measurement(measurement, "r__tcn")


def test_cuda_telemetry_survives_candidate_artifact_readback_and_resume(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "PROJECT_ROOT", tmp_path)
    run_id = "telemetry_artifact_test"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)
    common = {
        "configuration_fingerprint": "config-fp", "data_fingerprint": "data-fp",
        "split_fingerprint": "split-fp", "preprocessing_fingerprint": "preprocess-fp",
    }
    model_config = {"device": "cuda", "hidden_size": 24}
    provenance = run._candidate_provenance(run_id, "lstm", "deep_learning", 24, 1, 7, model_config, common)
    cid = provenance["candidate_id"]
    from bharatair.models.neural import build_neural_model

    payload = {"state_dict": build_neural_model("lstm", 24).state_dict(), **provenance}
    telemetry = {
        "status": "success", "telemetry_collected": True, "candidate_id": cid,
        "device_name": "Mock CUDA GPU", "device_index": 0,
        "peak_memory_allocated_bytes": 1234, "peak_memory_allocated_mib": 1234 / 1024**2,
        "peak_memory_reserved_bytes": 4567, "peak_memory_reserved_mib": 4567 / 1024**2,
        "measurement_scope": "test scope", "measurement_started_at_utc": "start",
        "measurement_completed_at_utc": "end", "measurement_duration_seconds": 0.5,
    }
    prediction = pd.DataFrame({
        "model": ["lstm"], "family": ["deep_learning"], "input_hours": [24],
        "horizon_hours": [1], "issue_timestamp": [pd.Timestamp("2020-01-01")],
        "target_timestamp": [pd.Timestamp("2020-01-01 01:00")], "actual": [2.0], "predicted": [2.5],
    })

    def writer(path):
        torch.save(payload, path)

    run._write_candidate(run_dir, run_id, "lstm", "deep_learning", 24, 1, 7,
                         model_config, provenance,
                         {"mae": 0.5, "cuda_memory_telemetry": telemetry}, prediction, writer)
    candidate_dir = next((run_dir / "candidates" / cid).glob("attempt_*"))
    marker = artifacts.verify_completed_candidate(candidate_dir)
    stored_metrics = json.loads((candidate_dir / "validation_metrics.json").read_text(encoding="utf-8"))
    assert stored_metrics["cuda_memory_telemetry"] == telemetry
    assert marker["artifact_sha256"]["validation_metrics.json"] == artifacts.file_sha256(candidate_dir / "validation_metrics.json")
    expected_common = {
        "run_id": run_id, "run_configuration_fingerprint": common["configuration_fingerprint"],
        "data_fingerprint": common["data_fingerprint"], "split_fingerprint": common["split_fingerprint"],
        "preprocessing_fingerprint": common["preprocessing_fingerprint"],
    }
    records, _ = run._load_completed(run_dir, expected_common)
    assert records[0]["cuda_memory_telemetry"] == telemetry
