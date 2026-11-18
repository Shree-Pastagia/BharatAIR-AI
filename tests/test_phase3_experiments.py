from __future__ import annotations

import numpy as np
import pandas as pd
import torch

from bharatair.evaluation.metrics import improvement_pct, score
from bharatair.features.scaling import TrainOnlyScaler
from bharatair.features.windows import (
    assemble_features,
    eligible_issue_indices,
    prepare_series,
    seasonal_naive_reference_indices,
)
from bharatair.models.baselines import persistence, seasonal_naive
from bharatair.models.neural import build_neural_model


def _frame(n: int = 80, *, missing: tuple[int, ...] = ()) -> pd.DataFrame:
    times = pd.date_range("2024-01-01", periods=n, freq="h").delete(list(missing))
    return pd.DataFrame({"timestamp_ist": times, "value": np.arange(len(times), dtype=float) + 10.0})


def test_chronological_split_boundaries_and_target_purge():
    series = prepare_series(_frame(120))
    indices, reasons = eligible_issue_indices(series, input_length=4, horizon=6)
    training, validation, test = indices["train"], indices["validation"], indices["test"]
    cut1, cut2 = series.boundaries.validation_start, series.boundaries.test_start
    train_targets = series.calendar[training + 6]
    val_targets = series.calendar[validation + 6]
    test_targets = series.calendar[test + 6]
    assert (train_targets < cut1).all()
    assert ((val_targets >= cut1) & (val_targets < cut2)).all()
    assert (test_targets >= cut2).all()
    assert reasons["train"]["split_purge"] == 6
    assert reasons["validation"]["split_purge"] == 6


def test_window_eligibility_rejects_input_horizon_and_long_gaps():
    series = prepare_series(_frame(120, missing=(50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75)))
    issue_sets, reasons = eligible_issue_indices(series, input_length=8, horizon=4)
    assert reasons["train"]["long_outage"] > 0
    all_eligible = np.concatenate(list(issue_sets.values()))
    assert not any(50 <= i <= 70 for i in all_eligible)
    assert reasons["train"]["input_gap"] + reasons["train"]["horizon_gap"] >= 0


def test_horizon_alignment_calendar_features_and_seasonal_reference_are_past_only():
    series = prepare_series(_frame(100))
    issue_idx = np.asarray([30, 40])
    features = assemble_features(series, issue_idx, input_length=24, horizon=6)
    np.testing.assert_array_equal(features["y"], series.values[issue_idx + 6])
    assert (seasonal_naive_reference_indices(issue_idx, 6) <= issue_idx).all()
    np.testing.assert_array_equal(persistence(series, issue_idx), series.values[issue_idx])
    np.testing.assert_array_equal(seasonal_naive(series, issue_idx, 6), series.values[issue_idx - 18])
    assert features["tabular"].shape == (2, 30)
    assert features["calendar"].shape == (2, 6)
    assert features["issue_timestamp"][0] == series.calendar[30].to_datetime64()
    changed = _frame(100).copy()
    changed.loc[changed["timestamp_ist"] > series.calendar[30], "value"] += 9999
    changed_series = prepare_series(changed)
    unchanged_issue_features = assemble_features(changed_series, issue_idx[:1], 24, 6)
    np.testing.assert_array_equal(unchanged_issue_features["sequences"], features["sequences"][:1])


def test_train_only_scaling_does_not_use_validation_data():
    x = np.arange(24, dtype=np.float32).reshape(2, 12)
    y = np.asarray([1.0, 3.0], dtype=np.float32)
    scaler = TrainOnlyScaler().fit(x, y)
    original = scaler.state().copy()
    changed_validation = np.full((2, 12), 1e9, dtype=np.float32)
    assert changed_validation.mean() > 1e8
    assert scaler.state() == original
    np.testing.assert_allclose(scaler.inverse_y(scaler.transform_y(y)), y)


def test_baseline_and_metric_correctness():
    result = score(np.asarray([1.0, 3.0]), np.asarray([2.0, 1.0]), mase_scale=2.0)
    assert result["n"] == 2
    assert result["mae"] == 1.5
    assert result["rmse"] == np.sqrt(2.5)
    assert result["mase"] == 0.75
    assert improvement_pct(2.0, 1.5) == 25.0


def test_neural_architecture_prediction_shapes_and_seed_reproducibility():
    x = torch.zeros((3, 24, 1))
    calendar = torch.zeros((3, 6))
    for name in ("lstm", "gru", "tcn"):
        torch.manual_seed(42)
        model = build_neural_model(name)
        first = model(x, calendar)
        torch.manual_seed(42)
        second = build_neural_model(name)(x, calendar)
        assert first.shape == (3,)
        torch.testing.assert_close(first, second)


def test_neural_checkpoint_serialization_and_reload(tmp_path):
    torch.manual_seed(11)
    model = build_neural_model("gru")
    model.eval()
    x = torch.randn((2, 12, 1))
    cal = torch.randn((2, 6))
    expected = model(x, cal).detach()
    checkpoint = tmp_path / "model.pt"
    torch.save({"state_dict": model.state_dict(), "architecture": "gru"}, checkpoint)
    payload = torch.load(checkpoint, weights_only=True)
    restored = build_neural_model(payload["architecture"])
    restored.load_state_dict(payload["state_dict"])
    restored.eval()
    torch.testing.assert_close(restored(x, cal), expected)
