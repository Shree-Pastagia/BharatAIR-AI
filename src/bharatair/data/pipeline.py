"""End-to-end acquisition/offline processing for Delhi site_1422 PM2.5."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from bharatair.data.config import CONFIG, PipelineConfig
from bharatair.data.download import acquire_target_months
from bharatair.data.gaps import build_hourly_audits, window_feasibility
from bharatair.data.parse import read_target_observations, target_paths
from bharatair.data.validate import canonicalize, compare_reference_extract, measurement_statistics

LOG = logging.getLogger(__name__)


def run_pipeline(config: PipelineConfig = CONFIG, *, acquire: bool = False) -> dict[str, Any]:
    """Build canonical outputs. Set acquire=True to refresh absent raw months."""
    acquisition = acquire_target_months(config) if acquire else None
    measurements, source_audit = read_target_observations(config)
    canonical, flags = canonicalize(measurements)
    if canonical.empty:
        raise ValueError("No numeric source observations for the configured station/parameter")
    calendar, gaps, continuity = build_hourly_audits(canonical)
    windows = window_feasibility(calendar, gaps)
    stats = measurement_statistics(canonical)
    reference_path = config.processed_dir.parent / "raw" / "historical_station_year" / "site_1422_pm25_full_history.csv"
    if reference_path.is_file():
        reference_raw = pd.read_csv(reference_path, usecols=["collected_at", "value"])
        reference = pd.DataFrame({
            "timestamp_ist": pd.to_datetime(reference_raw["collected_at"], errors="coerce"),
            "value": pd.to_numeric(reference_raw["value"], errors="coerce"),
        }).dropna(subset=["timestamp_ist", "value"])
        reference_check: dict[str, Any] = {
            "path": str(reference_path.relative_to(config.processed_dir.parent.parent)),
            **compare_reference_extract(canonical, reference),
        }
    else:
        reference_check = {"status": "not_available"}
    monthly_observed = canonical.assign(month=canonical["timestamp_ist"].dt.strftime("%Y-%m")).groupby("month").size()
    coverage = continuity["monthly_missingness"]
    months_by_key = {row["month"]: row for row in coverage}
    for month in sorted(set(months_by_key) | set(monthly_observed.index)):
        if month in months_by_key:
            months_by_key[month]["observed_hours"] = int(monthly_observed.get(month, 0))
            months_by_key[month]["coverage_pct"] = 100 * months_by_key[month]["observed_hours"] / months_by_key[month]["expected_hours"]
    continuity["months_ge_80pct_coverage"] = sum(row["coverage_pct"] >= 80 for row in months_by_key.values())
    continuity["months_ge_90pct_coverage"] = sum(row["coverage_pct"] >= 90 for row in months_by_key.values())
    continuity["monthly_missingness"] = list(months_by_key.values())

    output_dir = config.processed_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    config.report_dir.mkdir(parents=True, exist_ok=True)
    canonical_path = output_dir / "delhi_site_1422_pm25.parquet"
    csv_path = output_dir / "delhi_site_1422_pm25.csv"
    calendar_path = output_dir / "delhi_site_1422_hourly_calendar.parquet"
    gap_path = output_dir / "delhi_site_1422_gap_audit.csv"
    windows_path = output_dir / "delhi_site_1422_window_feasibility.csv"
    summary_path = output_dir / "data_quality_summary.json"
    canonical.to_parquet(canonical_path, index=False)
    canonical.to_csv(csv_path, index=False, date_format="%Y-%m-%dT%H:%M:%S")
    calendar.to_parquet(calendar_path, index=False)
    gaps.to_csv(gap_path, index=False, date_format="%Y-%m-%dT%H:%M:%S")
    windows.to_csv(windows_path, index=False)

    # Gaps by year/month are based on the observed hourly calendar, including zero-gap periods.
    gaps["start_year"] = pd.to_datetime(gaps.get("gap_start_ist", pd.Series(dtype="datetime64[ns]"))).dt.year
    gaps["start_month"] = pd.to_datetime(gaps.get("gap_start_ist", pd.Series(dtype="datetime64[ns]"))).dt.strftime("%Y-%m")
    gap_impact = {
        "gap_hours_by_start_year": {str(int(k)): int(v) for k, v in gaps.groupby("start_year")["missing_hours"].sum().items()} if not gaps.empty else {},
        "gap_hours_by_start_month": {str(k): int(v) for k, v in gaps.groupby("start_month")["missing_hours"].sum().items()} if not gaps.empty else {},
        "gap_runs_by_length_hours": continuity["gap_length_distribution_hours_to_run_count"],
    }
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "station": {"station_id": config.station_id, "station_name": "Dwarka-Sector 8, Delhi - DPCC", "city": "Delhi", "state": "Delhi", "source": config.source},
        "target": {"parameter": config.parameter, "unit": "µg/m³", "timestamp_timezone": "naive Indian Standard Time (IST)", "source_timestamp_convention": "CPCB minute 00"},
        "acquisition": acquisition,
        "source_audit": source_audit,
        "canonical_observation_count": len(canonical),
        "reference_station_extract_cross_check": reference_check,
        "timestamp_audit": continuity,
        "measurement_quality": {
            **stats,
            **flags,
            "unit_values": source_audit["unit_values"],
            "missing_unit_rows": source_audit["missing_unit_rows"],
            "unit_consistent": source_audit["missing_unit_rows"] == 0 and len(source_audit["unit_values"]) == 1 and all("g/m" in unit for unit in source_audit["unit_values"]),
        },
        "gap_impact": gap_impact,
        "window_feasibility_policy": {
            "input_lengths_hours": [24, 48, 168],
            "horizons_hours": [1, 6, 12, 24],
            "input_requires_actual_observation_each_hour": True,
            "target_requires_actual_observation": True,
            "no_interpolation_or_forward_fill": True,
            "long_outage_threshold_hours": 24,
            "candidate_interval_with_long_gap_excluded": True,
            "reason_counts_mutually_exclusive_order": "boundary > long_outage > input_gap > missing_target > eligible",
        },
        "window_feasibility": windows.to_dict(orient="records"),
        "outputs": {
            "canonical_parquet": str(canonical_path.relative_to(config.processed_dir.parent.parent)),
            "canonical_csv": str(csv_path.relative_to(config.processed_dir.parent.parent)),
            "hourly_calendar_parquet": str(calendar_path.relative_to(config.processed_dir.parent.parent)),
            "gap_audit_csv": str(gap_path.relative_to(config.processed_dir.parent.parent)),
            "window_feasibility_csv": str(windows_path.relative_to(config.processed_dir.parent.parent)),
        },
        "limitations": [
            "Missing periods remain missing; the hourly calendar is an audit artifact, not a measurement series.",
            "Monthly source files may be unavailable or fail integrity checks; see acquisition manifest.",
            "Threshold-based long-outage exclusion is a documented feasibility policy, not a model selection or accuracy result.",
            "No model was trained and no operational forecast claim is supported.",
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")
    LOG.info("Audited %d indexed rows represented by monthly files; selected %d station readings", source_audit["indexed_source_rows_in_target_files"], len(canonical))
    return summary


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if pd.isna(value):
        return None
    raise TypeError(f"Not JSON serializable: {type(value).__name__}")
