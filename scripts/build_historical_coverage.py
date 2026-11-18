"""Build authenticated historical station audits and metro rankings."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_STATIONS = ROOT / "data/raw/historical_station_year"
RAW_CITIES = ROOT / "data/raw/historical_city_monthly"
OUT = ROOT / "data/processed"
stations = json.loads(
    (ROOT / "data/raw/verification_samples/authenticated_stations.json").read_text(encoding="utf-8")
)["data"]
station_by_id = {row["station_id"]: row for row in stations}
hour = pd.Timedelta(hours=1)

exact = []
monthly_coverage = []
raw_frames = {}
for path in sorted(RAW_STATIONS.glob("*_pm25_full_history.csv")):
    station_id = path.name.split("_pm25_")[0]
    station = station_by_id[station_id]
    if station.get("source") != "cpcb_caaqm":
        raise ValueError(f"Unexpected non-CPCB station in CPCB audit: {station_id}")
    frame = pd.read_csv(path)
    if frame.empty:
        continue
    if set(frame.station_id) != {station_id} or set(frame.parameter_name) != {"PM2.5"}:
        raise ValueError(f"Unexpected data in {path.name}")
    frame["collected_at"] = pd.to_datetime(frame.collected_at)
    frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    raw_frames[station_id] = frame
    timestamps = frame.collected_at.sort_values().drop_duplicates()
    first, last = timestamps.iloc[0], timestamps.iloc[-1]
    expected = int((last - first) / hour) + 1
    differences = timestamps.diff().dropna()
    longest_gap = int(max(0, differences.max() / hour - 1)) if len(differences) else 0
    month_rows = []
    for period in pd.period_range(first.to_period("M"), last.to_period("M"), freq="M"):
        lo = max(first, period.start_time)
        hi = min(last, period.end_time.floor("h"))
        expected_month = int((hi - lo) / hour) + 1 if hi >= lo else 0
        observed = int(timestamps[(timestamps >= lo) & (timestamps <= hi)].size)
        coverage_pct = 100 * observed / expected_month if expected_month else 0.0
        month_rows.append({"month": str(period), "observations": observed, "expected_active_hours": expected_month, "coverage_pct": coverage_pct})
        monthly_coverage.append({"station_id": station_id, **month_rows[-1]})
    window_start, window_end = pd.Timestamp("2018-01-01"), pd.Timestamp("2026-04-01")
    window_count = int(frame.loc[frame.collected_at.ge(window_start) & frame.collected_at.lt(window_end)].shape[0])
    exact.append(
        {
            "station_id": station_id,
            "station_name": station["station_name"],
            "city_name": station.get("city_name"),
            "state_name": station.get("state_name"),
            "source": station["source"],
            "unit": str(frame.unit.iloc[0]),
            "first_pm25_observation": first.isoformat(),
            "latest_pm25_observation": last.isoformat(),
            "total_pm25_observations": int(len(frame)),
            "distinct_hourly_timestamps": int(timestamps.size),
            "duplicate_timestamps": int(len(frame) - timestamps.size),
            "distinct_reporting_days": int(timestamps.dt.date.nunique()),
            "distinct_reporting_months": int(timestamps.dt.to_period("M").nunique()),
            "expected_hourly_observations_active_period": expected,
            "missing_observations_active_period": int(expected - timestamps.size),
            "missingness_pct_active_period": round(100 * (expected - timestamps.size) / expected, 3),
            "longest_consecutive_missing_hours": longest_gap,
            "months_ge80pct_active_span": sum(row["coverage_pct"] >= 80 for row in month_rows),
            "months_ge90pct_active_span": sum(row["coverage_pct"] >= 90 for row in month_rows),
            "months_assessed_active_span": len(month_rows),
            "off_hour_timestamps": int(((frame.collected_at.dt.minute != 0) | (frame.collected_at.dt.second != 0) | (frame.collected_at.dt.microsecond != 0)).sum()),
            "negative_values": int((frame.value < 0).sum()),
            "values_le_zero": int((frame.value <= 0).sum()),
            "values_ge500": int((frame.value >= 500).sum()),
            "values_ge1000": int((frame.value >= 1000).sum()),
            "minimum": float(frame.value.min()),
            "p99": float(frame.value.quantile(0.99)),
            "maximum": float(frame.value.max()),
            "observations_2018_2026_03": window_count,
            "monthly_coverage": month_rows,
        }
    )

pd.DataFrame(exact).to_csv(OUT / "historical_station_exact_audit.csv", index=False)
pd.DataFrame(monthly_coverage).to_csv(OUT / "historical_station_monthly_coverage.csv", index=False)

# All candidate rankings use observed monthly measurement counts from the API,
# not station first_seen/last_seen metadata. Boundary months are excluded from
# the interior monthly coverage score because their exact active hours are not
# available in a monthly aggregate.
metro_city_map = {
    "Delhi": "Delhi NCR", "Faridabad": "Delhi NCR", "Gurugram": "Delhi NCR",
    "Ghaziabad": "Delhi NCR", "Greater Noida": "Delhi NCR", "Noida": "Delhi NCR",
}
city_frames = []
for path in sorted(RAW_CITIES.glob("*_pm25_monthly_2018_2026.csv")):
    city = path.name.split("_pm25_monthly_")[0].replace("_", " ").title()
    data = pd.read_csv(path)
    if data.empty:
        continue
    data["period_start"] = pd.to_datetime(data.period_start)
    data["n"] = pd.to_numeric(data.n, errors="coerce").fillna(0).astype(int)
    data["query_city"] = city
    city_frames.append(data)
monthly = pd.concat(city_frames, ignore_index=True)
monthly = monthly.drop_duplicates(["station_id", "period_start"], keep="last")
ranking = []
for station_id, group in monthly.groupby("station_id", sort=False):
    station = station_by_id.get(station_id)
    if not station or station.get("source") != "cpcb_caaqm":
        continue
    group = group.sort_values("period_start").copy()
    periods = group.period_start.dt.to_period("M")
    group["period"] = periods
    group["expected_calendar_hours"] = periods.map(lambda p: p.days_in_month * 24)
    group["coverage_pct"] = 100 * group.n / group.expected_calendar_hours
    first_period, last_period = periods.min(), periods.max()
    interior = group[(periods > first_period) & (periods < last_period)].copy()
    all_months = pd.period_range(first_period, last_period, freq="M")
    interior_periods = set(interior.period)
    n_by_period = group.set_index("period").n.to_dict()
    coverage_by_period = group.set_index("period").coverage_pct.to_dict()
    zero_months = [p for p in all_months if n_by_period.get(p, 0) == 0]
    usable_months = [p for p in all_months if coverage_by_period.get(p, 0) >= 80]
    longest_zero_run = longest_usable_run = 0
    zero_run = usable_run = 0
    for period in all_months:
        zero_run = zero_run + 1 if n_by_period.get(period, 0) == 0 else 0
        usable_run = usable_run + 1 if period in interior_periods and coverage_by_period.get(period, 0) >= 80 else 0
        longest_zero_run = max(longest_zero_run, zero_run)
        longest_usable_run = max(longest_usable_run, usable_run)
    def count_qualifying(start: str, end: str, threshold: float) -> int:
        return int(((group.period >= pd.Period(start, freq="M")) & (group.period <= pd.Period(end, freq="M")) & (group.coverage_pct >= threshold)).sum())
    exact_row = next((row for row in exact if row["station_id"] == station_id), None)
    meta_row = {
        "station_id": station_id,
        "station_name": station["station_name"],
        "city_name": station.get("city_name"),
        "state_name": station.get("state_name"),
        "source": station["source"],
        "latitude": station.get("latitude"),
        "longitude": station.get("longitude"),
        "rank_region": metro_city_map.get(station.get("city_name"), station.get("city_name")),
        "first_pm25_month_in_window": str(first_period),
        "last_pm25_month_in_window": str(last_period),
        "monthly_rows_2018_mar2026": int(group.n.sum()),
        "months_reporting_in_window": int((group.n > 0).sum()),
        "months_in_window": len(all_months),
        "interior_months_assessed": int(len(interior)),
        "interior_mean_monthly_coverage_pct": round(float(interior.coverage_pct.mean()), 2) if len(interior) else None,
        "interior_months_ge80pct": int((interior.coverage_pct >= 80).sum()),
        "interior_months_ge90pct": int((interior.coverage_pct >= 90).sum()),
        "longest_run_months_ge80pct": longest_usable_run,
        "zero_measurement_months_within_span": len(zero_months),
        "longest_zero_measurement_month_run": longest_zero_run,
        "months_ge80pct_2024": count_qualifying("2024-01", "2024-12", 80),
        "months_ge90pct_2024": count_qualifying("2024-01", "2024-12", 90),
        "months_ge80pct_2025": count_qualifying("2025-01", "2025-12", 80),
        "months_ge90pct_2025": count_qualifying("2025-01", "2025-12", 90),
        "months_ge80pct_2026": count_qualifying("2026-01", "2026-03", 80),
        "at_least_two_consecutive_usable_years": longest_usable_run >= 24,
        "exact_raw_history_audited": exact_row is not None,
    }
    if exact_row:
        for key in [
            "first_pm25_observation", "latest_pm25_observation", "total_pm25_observations",
            "distinct_reporting_days", "distinct_reporting_months", "expected_hourly_observations_active_period",
            "distinct_hourly_timestamps", "missingness_pct_active_period", "longest_consecutive_missing_hours",
            "duplicate_timestamps", "months_ge80pct_active_span", "months_ge90pct_active_span",
            "off_hour_timestamps", "negative_values", "values_ge500", "values_ge1000", "minimum", "p99", "maximum",
        ]:
            meta_row["exact_" + key] = exact_row[key]
        lo, hi = pd.Timestamp("2018-01-01"), pd.Timestamp("2026-04-01")
        api_month_sum = int(group.loc[group.period_start.ge(lo) & group.period_start.lt(hi), "n"].sum())
        meta_row["monthly_aggregate_matches_raw_2018_2026"] = api_month_sum == exact_row["observations_2018_2026_03"]
        meta_row["monthly_aggregate_rows_2018_2026"] = api_month_sum
    else:
        meta_row["monthly_aggregate_matches_raw_2018_2026"] = None
        meta_row["monthly_aggregate_rows_2018_2026"] = None
    ranking.append(meta_row)

ranked = pd.DataFrame(ranking)
ranked = ranked.sort_values(
    ["rank_region", "months_ge80pct_2024", "months_ge80pct_2025", "interior_mean_monthly_coverage_pct", "interior_months_ge80pct", "months_in_window"],
    ascending=[True, False, False, False, False, False],
)
ranked["rank_within_region"] = ranked.groupby("rank_region").cumcount() + 1
ranked.to_csv(OUT / "pilot_station_ranking.csv", index=False)

meta = json.loads((ROOT / "data/raw/verification_samples/authenticated_meta.json").read_text(encoding="utf-8"))
bulk = json.loads((OUT / "historical_bulk_index_summary.json").read_text(encoding="utf-8"))
bulk_checks = json.loads((OUT / "historical_bulk_sample_checks.json").read_text(encoding="utf-8"))
network_latest = json.loads((OUT / "network_latest_period_audit.json").read_text(encoding="utf-8"))
sample_logs = []
for name in ["historical_pilot_api_log.json", "metro_top_station_raw_query_log_part1.json", "metro_top_station_raw_query_log_part2.json"]:
    payload = json.loads((OUT / name).read_text(encoding="utf-8"))
    sample_logs.extend([x for x in payload if x.get("kind") == "pilot_station_measurements" or "station_id" in x])
summary = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "authentication": "success; key omitted from all logs",
    "authenticated_exported_at": meta["exported_at"],
    "catalog": bulk,
    "authenticated_monthly_file_probes": bulk_checks,
    "pilot_station_full_history_audits": exact,
    "metro_network_comparison_after_2025_09_01": network_latest,
    "metro_candidate_count": int(len(ranked)),
    "metro_candidate_ranking": ranked.to_dict(orient="records"),
    "ranking_method": "Authenticated monthly PM2.5 aggregate counts by station for 2018-01 through 2026-03; compare 2024/2025 months at 80/90% of full-calendar hours, interior-month coverage, usable-month runs and observed window length. Raw timestamps were independently fetched for the shortlisted alternatives and three pilot candidates.",
    "authenticated_raw_station_query_logs": sample_logs,
    "limitations": [
        "Bulk month index row counts are provider index values. Selected full Parquet months were independently downloaded and verified by file size and Parquet row count; the entire 2018-2026 range was not downloaded.",
        "The CPCB metro station ranking uses actual monthly aggregate measurement counts, which cannot reveal intra-month maximum hourly gaps or duplicate timestamps for every station. Exact raw hourly audits are included for the three prior pilot stations and top/alternate stations selected in the eight metro regions.",
        "All completeness calculations use station-specific observed PM2.5 active spans; they do not imply coverage before the first or after the latest observation.",
        "The API's nationwide CPCB PM2.5 monthly query returned zero observations from 2025-09-02 through 2026-03-31, while embassy PM2.5 continued in two stations."
    ],
}
(OUT / "historical_coverage_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
pd.DataFrame(sample_logs).to_json(OUT / "historical_raw_query_checksums.json", orient="records", indent=2, force_ascii=False)
print(f"Exact raw station audits: {len(exact)}; metro CPCB candidates ranked: {len(ranked)}")
for region, group in ranked.groupby("rank_region", sort=False):
    print(region, 'top', group.iloc[0].station_id, group.iloc[0].station_name, 'rows/window', group.iloc[0].monthly_rows_2018_mar2026, 'months_ge80_2024_2025', group.iloc[0].months_ge80pct_2024, group.iloc[0].months_ge80pct_2025)
