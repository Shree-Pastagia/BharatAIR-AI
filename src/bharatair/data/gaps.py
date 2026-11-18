"""Hourly calendar, missing-period and forecasting-window eligibility audits."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def build_hourly_audits(measurements: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Build a separate active-span calendar and maximal missing-run table."""
    observed = measurements.dropna(subset=["timestamp_ist", "value"]).copy()
    observed = observed.sort_values("timestamp_ist", kind="mergesort")
    observed["timestamp_ist"] = pd.to_datetime(observed["timestamp_ist"])
    unique_timestamp_count = int(observed["timestamp_ist"].nunique())
    duplicates = int(observed.duplicated("timestamp_ist", keep=False).sum())
    if duplicates:
        observed = observed.drop_duplicates("timestamp_ist", keep="first")
    first, last = observed["timestamp_ist"].min(), observed["timestamp_ist"].max()
    if first.minute or first.second or first.microsecond or last.minute or last.second or last.microsecond:
        raise ValueError("CPCB timestamps are expected on minute 00")
    timestamps = pd.DatetimeIndex(observed["timestamp_ist"])
    off_hour = int(((timestamps.minute != 0) | (timestamps.second != 0) | (timestamps.microsecond != 0)).sum())
    calendar_index = pd.date_range(first, last, freq="h")
    present = calendar_index.isin(timestamps)
    calendar = pd.DataFrame({
        "timestamp_ist": calendar_index,
        "is_observed": present,
        "is_missing": ~present,
        "year": calendar_index.year,
        "month": calendar_index.month,
        "source_timezone": "IST (naive source clock)",
    })
    flags = calendar["is_missing"].to_numpy(dtype=bool)
    starts = np.flatnonzero(flags & np.r_[True, ~flags[:-1]])
    ends = np.flatnonzero(flags & np.r_[~flags[1:], True])
    gaps = pd.DataFrame([
        {
            "gap_start_ist": calendar_index[start],
            "gap_end_ist": calendar_index[end],
            "missing_hours": int(end - start + 1),
        }
        for start, end in zip(starts, ends)
    ], columns=["gap_start_ist", "gap_end_ist", "missing_hours"])
    monthly = calendar.groupby(["year", "month"], as_index=False).agg(
        expected_hours=("is_missing", "size"),
        missing_hours=("is_missing", "sum"),
    )
    monthly["observed_hours"] = monthly["expected_hours"] - monthly["missing_hours"]
    monthly["coverage_pct"] = monthly["observed_hours"] / monthly["expected_hours"] * 100
    monthly["month"] = monthly.apply(lambda row: f"{int(row.year):04d}-{int(row.month):02d}", axis=1)
    yearly = calendar.groupby("year", as_index=False).agg(
        expected_hours=("is_missing", "size"),
        missing_hours=("is_missing", "sum"),
    )
    yearly["observed_hours"] = yearly["expected_hours"] - yearly["missing_hours"]
    yearly["coverage_pct"] = yearly["observed_hours"] / yearly["expected_hours"] * 100
    gap_distribution = gaps["missing_hours"].value_counts().sort_index().to_dict()
    summary = {
        "first_observation_ist": first.isoformat(sep="T"),
        "last_observation_ist": last.isoformat(sep="T"),
        "unique_timestamps": unique_timestamp_count,
        "duplicate_timestamp_rows": duplicates,
        "expected_hourly_timestamps_active_span": int(len(calendar)),
        "missing_hourly_timestamps": int((~present).sum()),
        "missingness_pct": float((~present).mean() * 100),
        "longest_consecutive_missing_hours": int(gaps["missing_hours"].max()) if not gaps.empty else 0,
        "gap_length_distribution_hours_to_run_count": {str(k): int(v) for k, v in gap_distribution.items()},
        "months_ge_80pct_coverage": int((monthly["coverage_pct"] >= 80).sum()),
        "months_ge_90pct_coverage": int((monthly["coverage_pct"] >= 90).sum()),
        "months_assessed_active_span": int(len(monthly)),
        "off_hour_timestamps": off_hour,
        "monthly_missingness": monthly.to_dict(orient="records"),
        "yearly_missingness": yearly.to_dict(orient="records"),
    }
    return calendar, gaps, summary


def window_feasibility(
    calendar: pd.DataFrame,
    gaps: pd.DataFrame,
    input_lengths: tuple[int, ...] = (24, 48, 168),
    horizons: tuple[int, ...] = (1, 6, 12, 24),
    long_gap_hours: int = 24,
) -> pd.DataFrame:
    """Count feasible windows without filling missing values or training models.

    A candidate is eligible only if its full input span and target are observed,
    and no >=24h source gap intersects the full input-to-target interval.
    Reason counts are mutually exclusive, using the order boundary, long outage,
    input gap, missing target, eligible.
    """
    observed = calendar["is_observed"].to_numpy(dtype=bool)
    n_hours = len(observed)
    long_gap_mask = np.zeros(n_hours, dtype=bool)
    origin_time = pd.Timestamp(calendar.iloc[0]["timestamp_ist"])
    for row in gaps[gaps["missing_hours"] >= long_gap_hours].itertuples(index=False):
        start = int((pd.Timestamp(row.gap_start_ist) - origin_time).total_seconds() // 3600)
        end = int((pd.Timestamp(row.gap_end_ist) - origin_time).total_seconds() // 3600)
        long_gap_mask[start : end + 1] = True
    missing_prefix = np.r_[0, np.cumsum(~observed, dtype=np.int64)]
    long_gap_prefix = np.r_[0, np.cumsum(long_gap_mask, dtype=np.int64)]
    rows: list[dict[str, Any]] = []
    for input_length in input_lengths:
        for horizon in horizons:
            counts = {"boundary": 0, "long_outage": 0, "input_gap": 0, "missing_target": 0, "eligible": 0}
            for origin in range(n_hours):
                input_start = origin - input_length + 1
                target = origin + horizon
                if input_start < 0 or target >= n_hours:
                    counts["boundary"] += 1
                    continue
                if long_gap_prefix[target + 1] - long_gap_prefix[input_start] > 0:
                    counts["long_outage"] += 1
                    continue
                if missing_prefix[origin + 1] - missing_prefix[input_start] > 0:
                    counts["input_gap"] += 1
                    continue
                if not observed[target]:
                    counts["missing_target"] += 1
                    continue
                counts["eligible"] += 1
            rows.append({
                "input_hours": input_length,
                "horizon_hours": horizon,
                "candidate_origins": n_hours,
                **{f"excluded_{name}_windows": value for name, value in counts.items() if name != "eligible"},
                "eligible_windows": counts["eligible"],
                "long_gap_threshold_hours": long_gap_hours,
                "reason_precedence": "boundary > long_outage > input_gap > missing_target > eligible",
            })
    return pd.DataFrame(rows)
