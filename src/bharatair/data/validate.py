"""Data quality flags and deterministic canonicalization."""

from __future__ import annotations

import pandas as pd


def canonicalize(observations: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Return observed numeric measurements only with preserved source provenance."""
    frame = observations.copy()
    frame["timestamp_ist"] = pd.to_datetime(frame["timestamp_ist"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    invalid_timestamp = int(frame["timestamp_ist"].isna().sum())
    missing_or_nonnumeric = int(frame["value"].isna().sum())
    frame = frame.dropna(subset=["timestamp_ist", "value"]).copy()
    frame["quality_negative"] = frame["value"] < 0
    frame["quality_extreme_ge_500"] = frame["value"] >= 500
    frame["quality_off_hour"] = (
        frame["timestamp_ist"].dt.minute.ne(0)
        | frame["timestamp_ist"].dt.second.ne(0)
        | frame["timestamp_ist"].dt.microsecond.ne(0)
    )
    frame["quality_duplicate_timestamp"] = frame["timestamp_ist"].duplicated(keep=False)
    frame = frame.sort_values(["timestamp_ist", "source_month", "source_file"], kind="mergesort").reset_index(drop=True)
    counts = {
        "invalid_timestamp_rows_excluded": invalid_timestamp,
        "missing_or_nonnumeric_values_excluded": missing_or_nonnumeric,
        "negative_measurements_preserved": int(frame["quality_negative"].sum()),
        "extreme_measurements_ge_500_preserved": int(frame["quality_extreme_ge_500"].sum()),
        "off_hour_timestamps_flagged": int(frame["quality_off_hour"].sum()),
        "duplicate_timestamp_rows_flagged": int(frame["quality_duplicate_timestamp"].sum()),
    }
    return frame, counts


def measurement_statistics(frame: pd.DataFrame) -> dict[str, float | int | None]:
    values = frame["value"].astype(float)
    return {
        "observations": int(values.count()),
        "minimum_ug_m3": float(values.min()) if len(values) else None,
        "maximum_ug_m3": float(values.max()) if len(values) else None,
        "mean_ug_m3": float(values.mean()) if len(values) else None,
        "median_ug_m3": float(values.median()) if len(values) else None,
        "standard_deviation_sample_ug_m3": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
        "negative_count": int((values < 0).sum()),
        "extreme_ge_500_count": int((values >= 500).sum()),
        "minimum_value_count": int((values == values.min()).sum()) if len(values) else 0,
        "p01_ug_m3": float(values.quantile(0.01)) if len(values) else None,
        "p99_ug_m3": float(values.quantile(0.99)) if len(values) else None,
    }


def compare_reference_extract(
    canonical: pd.DataFrame,
    reference: pd.DataFrame,
    tolerance: float = 1e-9,
) -> dict[str, int | float | bool]:
    """Compare timestamps and values to a previously acquired station CSV."""
    left = canonical[["timestamp_ist", "value"]].rename(columns={"value": "bulk_value"})
    right = reference[["timestamp_ist", "value"]].rename(columns={"value": "reference_value"})
    joined = left.merge(right, on="timestamp_ist", how="outer", indicator=True, validate="one_to_one")
    matched = joined["_merge"].eq("both")
    deltas = (joined.loc[matched, "bulk_value"] - joined.loc[matched, "reference_value"]).abs()
    max_delta = float(deltas.max()) if not deltas.empty else None
    timestamps_match = bool(matched.all() and len(left) == len(right))
    values_match = bool(timestamps_match and max_delta is not None and max_delta <= tolerance)
    return {
        "reference_rows": int(len(right)),
        "bulk_rows": int(len(left)),
        "matched_timestamps": int(matched.sum()),
        "timestamps_match": timestamps_match,
        "maximum_absolute_value_difference": max_delta if max_delta is not None else 0.0,
        "value_tolerance": tolerance,
        "values_match_within_tolerance": values_match,
    }
