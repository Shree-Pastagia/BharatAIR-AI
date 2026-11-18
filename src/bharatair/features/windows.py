"""Chronological target-time splits and gap-safe direct forecast windows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

INPUT_LENGTHS = (24, 48, 168)
HORIZONS = (1, 6, 12, 24)
LONG_GAP_THRESHOLD = 24


@dataclass(frozen=True)
class SplitBoundaries:
    train_start: pd.Timestamp
    validation_start: pd.Timestamp
    test_start: pd.Timestamp
    data_end: pd.Timestamp
    observed_timestamp_count: int
    train_quantile_index: int
    validation_quantile_index: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "train_target_start": self.train_start.isoformat(),
            "validation_target_start": self.validation_start.isoformat(),
            "test_target_start": self.test_start.isoformat(),
            "data_last_timestamp": self.data_end.isoformat(),
            "train_cut_fraction": 0.70,
            "validation_cut_fraction": 0.85,
            "quantile_basis": "sorted unique observed target timestamps",
            "observed_timestamp_count": self.observed_timestamp_count,
            "train_cut_index": self.train_quantile_index,
            "validation_cut_index": self.validation_quantile_index,
            "timezone": "naive IST source timestamps; no UTC conversion",
        }


@dataclass
class PreparedSeries:
    start: pd.Timestamp
    calendar: pd.DatetimeIndex
    values: np.ndarray
    observed: np.ndarray
    boundaries: SplitBoundaries


def prepare_series(frame: pd.DataFrame, *, split_timestamps: pd.DatetimeIndex | None = None,
                   data_end: pd.Timestamp | None = None) -> PreparedSeries:
    ordered = frame.sort_values("timestamp_ist", kind="mergesort")
    if ordered["timestamp_ist"].dt.tz is not None:
        raise ValueError("Expected naive IST source timestamps; UTC conversion is not allowed here")
    if ordered["timestamp_ist"].duplicated().any():
        raise ValueError("Duplicate timestamps must be reviewed before feature construction")
    target_times = (pd.DatetimeIndex(split_timestamps) if split_timestamps is not None
                    else pd.DatetimeIndex(ordered["timestamp_ist"].drop_duplicates().sort_values()))
    start = pd.Timestamp(target_times[0])
    end = pd.Timestamp(data_end if data_end is not None else ordered["timestamp_ist"].iloc[-1])
    # Restricted validation-only frames end before the test split by construction.
    calendar_end = pd.Timestamp(ordered["timestamp_ist"].iloc[-1])
    calendar = pd.date_range(start, calendar_end, freq="h")
    values = np.full(len(calendar), np.nan, dtype=np.float64)
    offsets = ((ordered["timestamp_ist"] - start) / pd.Timedelta(hours=1)).astype(int).to_numpy()
    values[offsets] = ordered["value"].astype(float).to_numpy()
    observed = np.isfinite(values)
    n = len(target_times)
    train_idx = int(np.floor(0.70 * n))
    validation_idx = int(np.floor(0.85 * n))
    boundaries = SplitBoundaries(
        train_start=target_times[0],
        validation_start=target_times[train_idx],
        test_start=target_times[validation_idx],
        data_end=target_times[-1],
        observed_timestamp_count=n,
        train_quantile_index=train_idx,
        validation_quantile_index=validation_idx,
    )
    return PreparedSeries(start, calendar, values, observed, boundaries)


def split_name(issue: pd.Timestamp, boundaries: SplitBoundaries) -> str:
    if issue < boundaries.validation_start:
        return "train"
    if issue < boundaries.test_start:
        return "validation"
    return "test"


def eligible_issue_indices(
    series: PreparedSeries,
    input_length: int,
    horizon: int,
    *,
    long_gap_threshold: int = LONG_GAP_THRESHOLD,
    splits: tuple[str, ...] = ("train", "validation", "test"),
) -> tuple[dict[str, np.ndarray], dict[str, dict[str, int]]]:
    """Return split-safe windows and mutually exclusive feasibility exclusions.

    Gaps anywhere in the complete input-to-target interval invalidate a sample.
    Gaps of at least ``long_gap_threshold`` hours are reported separately.
    """
    if input_length <= 0 or horizon <= 0:
        raise ValueError("Input length and horizon must be positive")
    n = len(series.calendar)
    missing = ~series.observed
    missing_prefix = np.r_[0, np.cumsum(missing, dtype=np.int64)]
    long_mask = np.zeros(n, dtype=bool)
    gap_starts = np.flatnonzero(missing & np.r_[True, ~missing[:-1]])
    gap_ends = np.flatnonzero(missing & np.r_[~missing[1:], True])
    for gap_start, gap_end in zip(gap_starts, gap_ends):
        if gap_end - gap_start + 1 >= long_gap_threshold:
            long_mask[gap_start : gap_end + 1] = True
    long_prefix = np.r_[0, np.cumsum(long_mask, dtype=np.int64)]
    allowed_splits = tuple(splits)
    if not allowed_splits or any(name not in {"train", "validation", "test"} for name in allowed_splits):
        raise ValueError("splits must contain train, validation, and/or test")
    split_candidates: dict[str, list[int]] = {name: [] for name in allowed_splits}
    keys = ("candidate_issue_times", "eligible", "dataset_boundary", "split_purge", "long_outage", "input_gap", "missing_target", "horizon_gap")
    reasons = {split: {key: 0 for key in keys} for split in split_candidates}
    bounds = series.boundaries
    # Validation-only callers stop at test_start without iterating or classifying
    # any test partition issue timestamps. Test labels are therefore unreachable
    # through this routine unless "test" is explicitly requested.
    end_idx = len(series.calendar)
    if "test" not in allowed_splits:
        end_idx = int(series.calendar.searchsorted(bounds.test_start, side="left"))
    for issue_idx in range(end_idx):
        issue_time = series.calendar[issue_idx]
        split = split_name(issue_time, bounds)
        if split not in allowed_splits:
            continue
        record = reasons[split]
        record["candidate_issue_times"] += 1
        input_start = issue_idx - input_length + 1
        target_idx = issue_idx + horizon
        if input_start < 0 or target_idx >= n:
            record["dataset_boundary"] += 1
            continue
        target_time = series.calendar[target_idx]
        if (split == "train" and target_time >= bounds.validation_start) or (
            split == "validation" and target_time >= bounds.test_start
        ):
            record["split_purge"] += 1
            continue
        if long_prefix[target_idx + 1] - long_prefix[input_start] > 0:
            record["long_outage"] += 1
            continue
        if missing_prefix[issue_idx + 1] - missing_prefix[input_start] > 0:
            record["input_gap"] += 1
            continue
        if not series.observed[target_idx]:
            record["missing_target"] += 1
            continue
        if missing_prefix[target_idx] - missing_prefix[issue_idx + 1] > 0:
            record["horizon_gap"] += 1
            continue
        record["eligible"] += 1
        split_candidates[split].append(issue_idx)
    return {key: np.asarray(value, dtype=np.int64) for key, value in split_candidates.items()}, reasons


def feature_names(input_length: int) -> list[str]:
    return [f"pm25_lag_{lag:03d}h" for lag in range(input_length)] + [
        "issue_hour_sin", "issue_hour_cos", "issue_weekday_sin", "issue_weekday_cos", "issue_month_sin", "issue_month_cos"
    ]


def calendar_features(timestamps: pd.DatetimeIndex) -> np.ndarray:
    hour = timestamps.hour.to_numpy(dtype=np.float64)
    weekday = timestamps.dayofweek.to_numpy(dtype=np.float64)
    month = timestamps.month.to_numpy(dtype=np.float64) - 1
    return np.column_stack([
        np.sin(2 * np.pi * hour / 24), np.cos(2 * np.pi * hour / 24),
        np.sin(2 * np.pi * weekday / 7), np.cos(2 * np.pi * weekday / 7),
        np.sin(2 * np.pi * month / 12), np.cos(2 * np.pi * month / 12),
    ]).astype(np.float32)


def assemble_features(series: PreparedSeries, issue_indices: np.ndarray, input_length: int, horizon: int) -> dict[str, np.ndarray]:
    sequences = np.stack([series.values[i - input_length + 1 : i + 1] for i in issue_indices]).astype(np.float32)
    issue_times = series.calendar[issue_indices]
    target_indices = issue_indices + horizon
    return {
        "sequences": sequences,
        "tabular": np.column_stack([sequences[:, ::-1], calendar_features(issue_times)]).astype(np.float32),
        "calendar": calendar_features(issue_times),
        "y": series.values[target_indices].astype(np.float32),
        "issue_index": issue_indices,
        "target_index": target_indices,
        "issue_timestamp": issue_times.to_numpy(),
        "target_timestamp": series.calendar[target_indices].to_numpy(),
    }


def common_issue_indices(index_sets: dict[int, dict[str, np.ndarray]], split: str) -> np.ndarray:
    """Return issue times eligible at every requested input length."""
    arrays = [index_sets[length][split] for length in sorted(index_sets)]
    if not arrays:
        return np.asarray([], dtype=np.int64)
    common = arrays[0]
    for array in arrays[1:]:
        common = np.intersect1d(common, array, assume_unique=True)
    return common.astype(np.int64)


def seasonal_naive_reference_indices(issue_indices: np.ndarray, horizon: int) -> np.ndarray:
    """The t+h-24 reference is available at issue time for h <= 24."""
    if not 1 <= horizon <= 24:
        raise ValueError("Seasonal naive is defined for horizons from 1 to 24 hours")
    reference = issue_indices + horizon - 24
    if (reference > issue_indices).any():
        raise AssertionError("Seasonal naive uses a future observation")
    return reference
