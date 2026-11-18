"""Create read-only Phase 4 coverage artifacts from targeted CPCB PM2.5 extracts."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTContainer, LTTextLine


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data" / "phase4_audit"
RAW = AUDIT / "raw_cpcb_pm25" / "yearly"
SNAP = AUDIT / "source_snapshot_20261117T000000Z"
REPORTS = ROOT / "reports"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_register(path: Path) -> dict[str, dict]:
    """Read the official PDF's positioned table rows (site code is in its last column)."""
    rows: dict[str, dict] = {}

    def walk(obj):
        if isinstance(obj, LTTextLine):
            yield obj
        elif isinstance(obj, LTContainer):
            for child in obj:
                yield from walk(child)

    for page in extract_pages(path):
        by_y: dict[float, dict[int, str]] = defaultdict(dict)
        for line in walk(page):
            text = line.get_text().strip().replace("\n", " ")
            if not text:
                continue
            y = round(line.y0, 1)
            x = line.x0
            if x < 80:
                col = 0
            elif x < 280:
                col = 1
            elif x < 400:
                col = 2
            elif x < 460:
                col = 3
            elif x < 510:
                col = 4
            else:
                col = 5
            by_y[y][col] = text
        for cols in by_y.values():
            code = cols.get(5, "")
            match = re.fullmatch(r"#(\d+)", code)
            if not match:
                continue
            station_id = f"site_{match.group(1)}"
            rows[station_id] = {
                "station_id": station_id,
                "register_city": cols.get(0),
                "register_station_name": cols.get(1),
                "operator": cols.get(2),
                "register_latitude": cols.get(3),
                "register_longitude": cols.get(4),
            }
    return rows


def iter_parquet_batches(paths):
    for path in paths:
        pf = pq.ParquetFile(path)
        for rg in range(pf.num_row_groups):
            df = pf.read_row_group(rg, columns=["station_id", "unit", "collected_at", "value"]).to_pandas()
            if not df.empty:
                yield path.name, df


def longest_true_run(mask: np.ndarray) -> int:
    if not mask.size:
        return 0
    padded = np.concatenate(([False], mask, [False])).astype(np.int8)
    edges = np.diff(padded)
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    return int((ends - starts).max()) if starts.size else 0


def main():
    REPORTS.mkdir(exist_ok=True)
    raw_manifest = json.loads((RAW / "retrieval_manifest.json").read_text(encoding="utf-8"))
    raw_files = [RAW / f"{year}.parquet" for year in range(2009, 2027)]
    for f in raw_files:
        if not f.exists():
            raise FileNotFoundError(f)
    # Store compact numpy blocks per station; no synthetic or filled values are created.
    blocks: dict[str, list[tuple[np.ndarray, np.ndarray, np.ndarray]]] = defaultdict(list)
    unit_sets: dict[str, set[str]] = defaultdict(set)
    row_counts: dict[str, int] = defaultdict(int)
    null_counts: dict[str, int] = defaultdict(int)
    null_timestamp_counts: dict[str, int] = defaultdict(int)
    file_row_counts: dict[str, int] = defaultdict(int)
    offhour_counts: dict[str, int] = defaultdict(int)
    for fname, df in iter_parquet_batches(raw_files):
        file_row_counts[fname] += len(df)
        df["station_id"] = df["station_id"].astype(str)
        df["collected_at"] = pd.to_datetime(df["collected_at"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        for sid, g in df.groupby("station_id", sort=False):
            ts = g["collected_at"].to_numpy(dtype="datetime64[ns]")
            vals = g["value"].to_numpy(dtype=np.float64, na_value=np.nan)
            valid_ts = ~np.isnat(ts)
            null_timestamp_counts[sid] += int((~valid_ts).sum())
            ts, vals = ts[valid_ts], vals[valid_ts]
            ns = ts.astype("int64")
            aligned = (ns % (60 * 60 * 1_000_000_000)) == 0
            blocks[sid].append((ns, vals, aligned))
            row_counts[sid] += len(g)
            null_counts[sid] += int(np.isnan(g["value"].to_numpy(dtype=np.float64, na_value=np.nan)).sum())
            unit_sets[sid].update(str(x) for x in g["unit"].dropna().unique())
            offhour_counts[sid] += int((~aligned).sum())

    station_meta = json.loads((SNAP / "stations_cpcb.json").read_text(encoding="utf-8"))["data"]
    meta = {x["station_id"]: x for x in station_meta}
    official_pdf = SNAP / "cpcb_all_india_station_register.pdf"
    official = extract_register(official_pdf)
    historical_ids = set(blocks)
    all_ids = historical_ids | set(meta)

    monthly_rows = []
    station_rows = []
    for sid in sorted(all_ids):
        m = meta.get(sid, {})
        obs = blocks.get(sid, [])
        if obs:
            ns = np.concatenate([x[0] for x in obs])
            vals = np.concatenate([x[1] for x in obs])
            aligned_mask = np.concatenate([x[2] for x in obs])
            # Sort once. Duplicates are counted against exact source timestamps.
            order = np.argsort(ns, kind="mergesort")
            ns, vals, aligned_mask = ns[order], vals[order], aligned_mask[order]
            ts = ns.astype("datetime64[ns]")
            first = pd.Timestamp(ts[0])
            last = pd.Timestamp(ts[-1])
            uniq_ns = np.unique(ns)
            duplicate_rows = len(ns) - len(uniq_ns)
            hour_ns = 60 * 60 * 1_000_000_000
            aligned_ns = np.unique(ns[aligned_mask])
            first_hour = (int(aligned_ns[0]) // hour_ns) * hour_ns if len(aligned_ns) else None
            last_hour = (int(aligned_ns[-1]) // hour_ns) * hour_ns if len(aligned_ns) else None
            expected = int((last_hour - first_hour) // hour_ns + 1) if first_hour is not None else 0
            missing = max(expected - len(aligned_ns), 0)
            missing_pct = 100.0 * missing / expected if expected else np.nan
            diffs = np.diff(aligned_ns) // hour_ns if len(aligned_ns) > 1 else np.array([], dtype=np.int64)
            longest_gap = int(max(diffs.max() - 1, 0)) if len(diffs) else 0
            neg = int(np.sum(np.isfinite(vals) & (vals < 0)))
            extreme500 = int(np.sum(np.isfinite(vals) & (vals >= 500)))
            extreme1000 = int(np.sum(np.isfinite(vals) & (vals >= 1000)))
            valid_values = vals[np.isfinite(vals)]
            values_min = float(valid_values.min()) if valid_values.size else np.nan
            values_max = float(valid_values.max()) if valid_values.size else np.nan
            # Monthly hour coverage uses the station's active period; partial endpoint months are bounded by first/last observed hour.
            month_of = pd.to_datetime(aligned_ns).to_period("M") if len(aligned_ns) else pd.PeriodIndex([], freq="M")
            unique_hours = pd.Series(month_of).value_counts().to_dict()
            source_month_counts = pd.Series(pd.to_datetime(ns).to_period("M")).value_counts().to_dict()
            if len(aligned_ns):
                first_period, last_period = month_of.min(), month_of.max()
                for period in pd.period_range(first_period, last_period, freq="M"):
                    period_start = max(first_hour, int(period.start_time.value // hour_ns * hour_ns))
                    period_end = min(last_hour, int(period.end_time.value // hour_ns * hour_ns))
                    exp_m = max(int((period_end - period_start) // hour_ns + 1), 0)
                    calendar_hours = int((period.end_time - period.start_time) // pd.Timedelta(hours=1) + 1)
                    actual_m = int(unique_hours.get(period, 0))
                    cov_m = 100.0 * actual_m / exp_m if exp_m else np.nan
                    monthly_rows.append({"station_id": sid, "month": str(period), "expected_hourly_slots": exp_m,
                                         "actual_unique_hourly_timestamps": actual_m, "coverage_pct": cov_m,
                                         "source_rows": int(source_month_counts.get(period, 0)),
                                         "calendar_hour_slots": calendar_hours,
                                         "full_calendar_month_observed_span": exp_m == calendar_hours})
        else:
            first = last = pd.NaT
            duplicate_rows = expected = missing = longest_gap = 0
            missing_pct = values_min = values_max = np.nan
            neg = extreme500 = extreme1000 = 0
        stat_months = [r for r in monthly_rows if r["station_id"] == sid]
        m80 = sum(r["coverage_pct"] >= 80 for r in stat_months)
        m90 = sum(r["coverage_pct"] >= 90 for r in stat_months)
        active_months = len(stat_months)
        high_month_ratio = m80 / active_months if active_months else 0
        years_covered = len({r["month"][:4] for r in stat_months})
        recent_months = [r for r in stat_months if "2024-01" <= r["month"] <= "2025-09"]
        recent80 = sum(r["coverage_pct"] >= 80 for r in recent_months)
        recent_ratio = recent80 / len(recent_months) if recent_months else 0
        register = official.get(sid, {})
        station_name = m.get("station_name") or register.get("register_station_name")
        city = m.get("city_name") or register.get("register_city")
        state = m.get("state_name")
        # Exact operational qualification is determined from measured span and hourly quality, not directory metadata.
        if row_counts.get(sid, 0) == 0:
            tier = "C"
        elif years_covered >= 2 and (np.isnan(missing_pct) or missing_pct <= 30) and high_month_ratio >= 0.75 and recent_ratio >= 0.60 and neg == 0 and offhour_counts.get(sid, 0) == 0 and duplicate_rows == 0 and null_counts.get(sid, 0) == 0 and null_timestamp_counts.get(sid, 0) == 0:
            tier = "A"
        elif years_covered >= 1 and (np.isnan(missing_pct) or missing_pct <= 50) and high_month_ratio >= 0.50:
            tier = "B"
        else:
            tier = "C"
        operator = register.get("operator", "")
        station_rows.append({
            "station_id": sid, "station_name": station_name, "state": state, "city": city,
            "source_network": "CPCB CAAQM", "operator_official_register": operator,
            "operator_status": "matched official CPCB register" if register else "not present in 2026-11-17 CPCB register snapshot",
            "official_register_name": register.get("register_station_name"),
            "latitude": m.get("latitude") if m else register.get("register_latitude"),
            "longitude": m.get("longitude") if m else register.get("register_longitude"),
            "metadata_status": "current XKDR station metadata" if m else ("official register only" if register else "historic measurements; current metadata absent"),
            "available_pollutants": "|".join(m.get("parameters", [])),
            "units": "|".join(sorted(unit_sets.get(sid, set()))),
            "first_pm25_ist": first.isoformat() if not pd.isna(first) else "",
            "last_pm25_ist": last.isoformat() if not pd.isna(last) else "",
            "pm25_observation_rows": row_counts.get(sid, 0),
            "distinct_hourly_timestamps": int(len(np.unique(np.concatenate([x[0][x[2]] for x in obs])))) if obs else 0,
            "distinct_reporting_days": int(pd.to_datetime(ns).normalize().nunique()) if obs else 0,
            "distinct_reporting_months": active_months,
            "years_represented": years_covered,
            "expected_hour_slots_active_span": expected,
            "actual_unique_aligned_hour_slots": int(len(np.unique(np.concatenate([x[0][x[2]] for x in obs])))) if obs else 0,
            "missing_hour_slots": missing, "missingness_pct_active_span": missing_pct,
            "longest_internal_missing_interval_hours": longest_gap,
            "duplicate_timestamp_rows": duplicate_rows,
            "off_hour_timestamp_rows": offhour_counts.get(sid, 0),
            "null_or_nonnumeric_values": null_counts.get(sid, 0),
            "null_timestamps": null_timestamp_counts.get(sid, 0),
            "negative_values": neg, "extreme_ge_500_ugm3": extreme500,
            "extreme_ge_1000_ugm3": extreme1000, "min_valid_value": values_min,
            "max_valid_value": values_max, "months_coverage_ge_80pct": m80,
            "months_coverage_ge_90pct": m90, "recent_2024_2025_months_ge_80pct": recent80,
            "recent_month_coverage_ratio": recent_ratio, "eligibility_tier": tier,
            "rank_years_covered": years_covered, "rank_active_span_coverage_pct": 100-missing_pct if not pd.isna(missing_pct) else 0,
            "rank_months_ge_80pct": m80, "rank_recent_coverage_ratio": recent_ratio,
        })

    inv = pd.DataFrame(station_rows)
    monthly = pd.DataFrame(monthly_rows)
    if not monthly.empty:
        monthly.to_csv(AUDIT / "station_monthly_coverage.csv", index=False, encoding="utf-8")
    inv.to_csv(REPORTS / "PHASE4_STATION_INVENTORY.csv", index=False, encoding="utf-8")
    ranking = inv.sort_values(["eligibility_tier", "rank_years_covered", "rank_recent_coverage_ratio",
                               "rank_active_span_coverage_pct", "rank_months_ge_80pct", "pm25_observation_rows"],
                              ascending=[True, False, False, False, False, False])
    ranking.insert(0, "rank", range(1, len(ranking)+1))
    ranking.to_csv(REPORTS / "PHASE4_STATION_ELIGIBILITY.csv", index=False, encoding="utf-8")
    city_rows = []
    for (state, city), g in inv[inv["pm25_observation_rows"] > 0].groupby(["state", "city"], dropna=False):
        city_rows.append({"state": state, "city": city, "cpcb_pm25_stations": len(g),
                          "stations_tier_a": int((g.eligibility_tier == "A").sum()),
                          "stations_tier_b": int((g.eligibility_tier == "B").sum()),
                          "stations_tier_c": int((g.eligibility_tier == "C").sum()),
                          "total_pm25_rows": int(g.pm25_observation_rows.sum()),
                          "longest_station_history_years": int(g.years_represented.max()),
                          "best_station_id": g.sort_values(["eligibility_tier", "rank_recent_coverage_ratio", "rank_active_span_coverage_pct", "pm25_observation_rows"], ascending=[True, False, False, False]).iloc[0].station_id,
                          "best_station_name": g.sort_values(["eligibility_tier", "rank_recent_coverage_ratio", "rank_active_span_coverage_pct", "pm25_observation_rows"], ascending=[True, False, False, False]).iloc[0].station_name})
    city_df = pd.DataFrame(city_rows).sort_values(["stations_tier_a", "stations_tier_b", "longest_station_history_years", "total_pm25_rows"], ascending=False)
    city_df.to_csv(REPORTS / "PHASE4_CITY_COVERAGE_SUMMARY.csv", index=False, encoding="utf-8")

    # All-city common periods are computed from the union of measured station coverage.
    per_city_month = monthly.merge(inv[["station_id", "city", "state"]], on="station_id", how="left")
    city_periods = per_city_month.groupby(["state", "city", "month"], dropna=False).agg(
        station_months=("station_id", "nunique"), rows=("source_rows", "sum"),
        station_months_ge_80=("coverage_pct", lambda x: int((x >= 80).sum()))).reset_index()
    observed_city_months = per_city_month[per_city_month.source_rows > 0].groupby(["state", "city", "month"], dropna=False).station_id.nunique().rename("stations_reporting_any")
    city_periods = city_periods.merge(observed_city_months, on=["state", "city", "month"], how="left")
    city_periods["stations_reporting_any"] = city_periods.stations_reporting_any.fillna(0).astype(int)
    city_periods.to_csv(AUDIT / "city_monthly_coverage.csv", index=False, encoding="utf-8")

    retrieval_bytes = sum(x["bytes"] for x in raw_manifest["records"])
    retrieval_rows = sum(int(x["x_row_count"]) for x in raw_manifest["records"])
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "XKDR India Air Quality Database, source=cpcb_caaqm, parameter=PM2.5",
        "raw_scope": "only station-level CPCB CAAQM PM2.5 observations; no Embassy records; no filling or outlier removal",
        "methodology": {"station_identity": "exact XKDR site_NNN station_id; operator cross-referenced by site code to official CPCB CCR PDF where present", "timestamp_tz": "naive IST as documented by XKDR", "expected_cadence": "hourly; verified from returned timestamps", "hourly_coverage": "distinct exact HH:00 timestamps divided by expected hourly timestamps from first to last observed hour inclusive", "monthly_coverage": "actual distinct on-hour timestamps divided by active-span expected hours in that calendar month; first/last partial months flagged", "longest_gap": "largest internal run of absent hourly slots between adjacent distinct on-hour observations; excludes leading/trailing span", "extreme_thresholds_ug_m3": [500, 1000], "outliers_removed": False, "imputation": "none"},
        "retrieval": {"start": "2009-01-01", "end": "2026-03-31 (inclusive query bound)", "actual_latest_observation_ist": str(pd.to_datetime(inv.last_pm25_ist, errors="coerce").max()),
                      "total_rows": retrieval_rows, "bytes": retrieval_bytes, "files": len(raw_manifest["records"]),
                      "year_2026_query_rows": int(raw_manifest["records"][-1]["x_row_count"]), "truncation": "false for all 18 year-bounded queries"},
        "station_universe": {"measurement_station_ids": len(historical_ids), "current_cpcb_metadata_rows": len(meta),
                              "stations_with_pm25": int((inv.pm25_observation_rows > 0).sum()),
                              "official_register_rows": len(official),
                              "historical_ids_missing_current_metadata": int((inv.metadata_status == "historic measurements; current metadata absent").sum())},
        "eligibility": {"tier_a": int((inv.eligibility_tier == "A").sum()), "tier_b": int((inv.eligibility_tier == "B").sum()),
                        "tier_c": int((inv.eligibility_tier == "C").sum()),
                        "tier_rule": "A: >=2 represented years, >=70% active-span coverage, >=75% active months >=80% hourly coverage, >=60% Jan-2024–Sep-2025 active months >=80%, and no duplicate, off-hour, null, nonnumeric, or negative records. B: >=1 represented year, >=50% active-span coverage, >=50% active months >=80%; otherwise C. This is a screening tier, not a regulatory grade."},
        "data_quality": {"timestamp_timezone": "naive Asia/Kolkata (IST), per XKDR docs", "hourly_expected_grid": "top-of-hour timestamps; only on-hour timestamps count toward hourly coverage", "unit_variants": sorted({u for x in unit_sets.values() for u in x}), "negative_rows": int(inv.negative_values.sum()), "extreme_ge_500_rows": int(inv.extreme_ge_500_ugm3.sum()), "extreme_ge_1000_rows": int(inv.extreme_ge_1000_ugm3.sum()), "duplicate_timestamp_rows": int(inv.duplicate_timestamp_rows.sum()), "off_hour_rows": int(inv.off_hour_timestamp_rows.sum()), "null_or_nonnumeric_rows": int(inv.null_or_nonnumeric_values.sum()), "null_timestamp_rows": int(inv.null_timestamps.sum())},
        "network_separation": {"CPCB CAAQM PM2.5 rows retrieved": retrieval_rows, "US Embassy data excluded from all coverage/rankings": True},
        "source_artifacts": {"xkdr_file_index_sha256": sha256(SNAP / "files.json"), "xkdr_station_metadata_sha256": sha256(SNAP / "stations_cpcb.json"), "official_register_sha256": sha256(official_pdf), "yearly_extract_manifest": str(RAW / "retrieval_manifest.json").replace("\\", "/")},
    }
    (AUDIT / "historical_coverage_summary.json").write_text(json.dumps(summary, indent=2, default=lambda x: str(x)), encoding="utf-8")
    (AUDIT / "official_register_station_map.json").write_text(json.dumps(official, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=lambda x: str(x)))


if __name__ == "__main__":
    main()
