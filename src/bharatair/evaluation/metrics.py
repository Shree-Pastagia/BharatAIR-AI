"""Forecast scoring and grouped error summaries."""

from __future__ import annotations

import numpy as np
import pandas as pd


def score(actual: np.ndarray, predicted: np.ndarray, *, mase_scale: float) -> dict[str, float | int]:
    actual = np.asarray(actual, dtype=np.float64)
    predicted = np.asarray(predicted, dtype=np.float64)
    error = predicted - actual
    mae = float(np.mean(np.abs(error)))
    rmse = float(np.sqrt(np.mean(np.square(error))))
    return {"n": int(len(actual)), "mae": mae, "rmse": rmse, "mase": float(mae / mase_scale) if mase_scale > 0 else float("nan"), "bias": float(np.mean(error))}


def improvement_pct(reference_mae: float, model_mae: float) -> float:
    if reference_mae == 0:
        return float("nan")
    return float(100 * (reference_mae - model_mae) / reference_mae)


def grouped_metrics(predictions: pd.DataFrame, *, mase_scale: float, group: str) -> pd.DataFrame:
    rows = []
    for key, group_df in predictions.groupby(group, sort=True, dropna=False):
        metrics = score(group_df["actual"].to_numpy(), group_df["predicted"].to_numpy(), mase_scale=mase_scale)
        rows.append({group: key, **metrics})
    return pd.DataFrame(rows)


def daily_block_mae_improvement_interval(
    actual: np.ndarray,
    candidate: np.ndarray,
    baseline: np.ndarray,
    dates: pd.Series,
    *,
    seed: int = 42,
    replicates: int = 500,
) -> dict[str, float | int]:
    """Paired block bootstrap of persistence-minus-candidate MAE by target day."""
    frame = pd.DataFrame({
        "day": pd.to_datetime(dates).dt.strftime("%Y-%m-%d").to_numpy(),
        "candidate_abs_error": np.abs(np.asarray(candidate) - np.asarray(actual)),
        "baseline_abs_error": np.abs(np.asarray(baseline) - np.asarray(actual)),
    })
    days = frame["day"].unique()
    daily = frame.groupby("day", sort=True)[["candidate_abs_error", "baseline_abs_error"]].mean().to_numpy()
    differences = daily[:, 1] - daily[:, 0]
    rng = np.random.default_rng(seed)
    draws = np.empty(replicates, dtype=np.float64)
    for idx in range(replicates):
        sample = rng.integers(0, len(days), size=len(days))
        draws[idx] = differences[sample].mean()
    return {
        "target_days": int(len(days)),
        "replicates": int(replicates),
        "seed": int(seed),
        "mae_improvement_vs_persistence": float(differences.mean()),
        "ci_2_5_pct": float(np.quantile(draws, 0.025)),
        "ci_97_5_pct": float(np.quantile(draws, 0.975)),
    }
