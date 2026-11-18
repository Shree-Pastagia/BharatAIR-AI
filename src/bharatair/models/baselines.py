"""Leakage-safe persistence and seasonal-naive forecasts."""

from __future__ import annotations

import numpy as np

from bharatair.features.windows import PreparedSeries, seasonal_naive_reference_indices


def persistence(series: PreparedSeries, issue_indices: np.ndarray) -> np.ndarray:
    return series.values[issue_indices].astype(np.float64)


def seasonal_naive(series: PreparedSeries, issue_indices: np.ndarray, horizon: int) -> np.ndarray:
    references = seasonal_naive_reference_indices(issue_indices, horizon)
    values = series.values[references]
    if not np.isfinite(values).all():
        raise ValueError("Seasonal naive reference must be an actual historical observation")
    return values.astype(np.float64)
