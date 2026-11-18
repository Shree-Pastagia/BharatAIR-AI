"""Build Phase 1 metadata joins and checksums from preserved source files."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/verification_samples"
OUT = ROOT / "data/processed"
OUT.mkdir(parents=True, exist_ok=True)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


meta = read_json(RAW / "api_meta.json")
stations = read_json(RAW / "api_stations.json")["data"]
parameters = read_json(RAW / "api_parameters.json")["data"]
files = read_json(RAW / "api_files.json")["files"]
station_by_id = {row["station_id"]: row for row in stations}
audit_path = ROOT / "data/processed_station_audit_2024.csv"
if not audit_path.exists():
    audit_path = OUT / "station_audit_2024.csv"
audit = pd.read_csv(audit_path)
audit_by_id = {row.station_id: row for row in audit.itertuples(index=False)}

# Add source catalog station metadata to every station with observed 2024 PM2.5.
for column, getter in {
    "latitude": lambda x: x.get("latitude"),
    "longitude": lambda x: x.get("longitude"),
    "first_seen": lambda x: x.get("first_seen"),
    "last_seen": lambda x: x.get("last_seen"),
    "parameters": lambda x: ";".join(x.get("parameters", [])),
}.items():
    audit[column] = audit.station_id.map(lambda sid: getter(station_by_id[sid]))
audit = audit.sort_values(
    ["source", "missing_pct_active_span", "longest_consecutive_missing_hours", "readings"],
    ascending=[True, True, True, False],
)
audit.to_csv(OUT / "station_audit_2024.csv", index=False)

# One-row-per-station inventory with explicit unknown operational status.
coverage = []
for station in stations:
    measured = audit_by_id.get(station["station_id"])
    coverage.append(
        {
            "station_id": station["station_id"],
            "station_name": station["station_name"],
            "city_name": station.get("city_name"),
            "state_name": station.get("state_name"),
            "source": station["source"],
            "latitude": station.get("latitude"),
            "longitude": station.get("longitude"),
            "first_seen": station.get("first_seen"),
            "last_seen": station.get("last_seen"),
            "n_rows_all_parameters": station.get("n_rows"),
            "parameters": ";".join(station.get("parameters", [])),
            "reported_2024_PM25": measured is not None,
            "pm25_rows_2024": int(measured.readings) if measured else 0,
            "pm25_missing_pct_active_span_2024": (
                float(measured.missing_pct_active_span) if measured else None
            ),
            "operational_status": "not supplied by API",
            "status_evidence": (
                "Source docs identify null-location CPCB stations as decommissioned"
                if station["source"] == "cpcb_caaqm"
                and (station.get("latitude") is None or station.get("longitude") is None)
                else "not reported"
            ),
        }
    )
pd.DataFrame(coverage).to_csv(OUT / "station_coverage_summary.csv", index=False)
pd.DataFrame(parameters).rename(columns={"parameter_name": "parameter"}).to_csv(
    OUT / "pollutant_availability.csv", index=False
)

# Enrich copies of final API CSV samples. Raw downloads remain unchanged.
sample_stats = []
enriched = []
for path in sorted(RAW.glob("final_pm25_*.csv")):
    frame = pd.read_csv(path)
    if frame.empty:
        continue
    frame["collected_at"] = pd.to_datetime(frame["collected_at"])
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    station_id = str(frame.station_id.iloc[0])
    station = station_by_id[station_id]
    # Embassy readings are hourly at minute 30, not every 30 minutes.
    period = pd.Timedelta(hours=1)
    times = frame.collected_at.drop_duplicates().sort_values()
    expected = int((times.iloc[-1] - times.iloc[0]) / period) + 1
    gaps = times.diff().dropna()
    longest_gap = int(max(0, gaps.max() / period - 1)) if len(gaps) else 0
    frame["source_network"] = station["source"]
    frame["station_name"] = station["station_name"]
    frame["city_name"] = station.get("city_name") or "New Delhi"
    frame["state_name"] = station.get("state_name")
    frame["latitude"] = station.get("latitude")
    frame["longitude"] = station.get("longitude")
    frame["sample_file"] = path.name
    enriched.append(frame)
    sample_stats.append(
        {
            "sample_file": path.name,
            "station_id": station_id,
            "station_name": station["station_name"],
            "source_network": station["source"],
            "city_name": station.get("city_name"),
            "state_name": station.get("state_name"),
            "reporting_stations": 1,
            "reporting_cities": int(bool(station.get("city_name"))),
            "reporting_states": int(bool(station.get("state_name"))),
            "rows": int(len(frame)),
            "first_observation": times.iloc[0].isoformat(),
            "last_observation": times.iloc[-1].isoformat(),
            "distinct_timestamps": int(times.nunique()),
            "duplicate_rows": int(len(frame) - times.nunique()),
            "expected_slots_active_span": expected,
            "missing_pct_active_span": round(100 * (expected - times.nunique()) / expected, 2),
            "longest_consecutive_missing_hours": longest_gap,
            "negative_values": int((frame.value < 0).sum()),
            "minimum": float(frame.value.min()),
            "maximum": float(frame.value.max()),
        }
    )
if enriched:
    pd.concat(enriched, ignore_index=True).to_csv(
        OUT / "representative_observations_enriched.csv", index=False
    )
(OUT / "sample_summary.json").write_text(
    json.dumps(sample_stats, indent=2, ensure_ascii=False), encoding="utf-8"
)

network = audit.groupby("source").agg(
    stations=("station_id", "nunique"),
    rows=("readings", "sum"),
    cities=("city_name", "nunique"),
    states=("state_name", "nunique"),
    expected_slots=("expected_slots_active_span", "sum"),
    distinct_timestamps=("distinct_timestamps", "sum"),
    duplicate_rows=("duplicate_rows", "sum"),
    days_ge18=("days_with_ge18_readings", "sum"),
    months_ge75pct=("months_ge75pct", "sum"),
).to_dict("index")
for item in network.values():
    item["weighted_missing_pct_active_span"] = round(
        100 * (item["expected_slots"] - item["distinct_timestamps"]) / item["expected_slots"], 2
    )
cpcb = [s for s in stations if s["source"] == "cpcb_caaqm"]
embassy = [s for s in stations if s["source"] == "us_embassy"]
param_by_name = {p["parameter_name"]: p for p in parameters}
measurement_files_2024 = [f for f in files if f.get("year") == 2024]

# Hash every preserved raw source file and retain its local filesystem write time.
empty_csv_station = {
    "pm25_mumbai_2024.csv": "site_168",
    "pm25_bengaluru_2024.csv": "site_162",
    "pm25_ahmedabad_2024.csv": "site_308",
    "pm25_chennai_2024.csv": "site_288",
    "pm25_anantapur_2024.csv": "site_5632",
    "pm25_delhi_2024.csv": "site_117",
    "pm25_delhi_2009.csv": "site_117",
    "pm25_delhi_2010.csv": "site_117",
    "pm25_delhi_2015.csv": "site_117",
    "pm25_delhi_2026_partial.csv": "site_117",
    "pm25_mumbai_bkc_2024.csv": "site_5392",
    "pm25_delhi_dtu_2009.csv": "site_118",
    "pm25_delhi_dtu_2010.csv": "site_118",
    "pm25_delhi_dtu_2015.csv": "site_118",
}
manifest = []
for path in sorted(RAW.iterdir()):
    if not path.is_file():
        continue
    content = path.read_bytes()
    source_url = "https://airquality.xkdr.org"
    if path.name.startswith("api_"):
        source_url += "/v1/" + path.stem.removeprefix("api_")
    elif path.name.startswith("parquet_2024_"):
        month = path.stem[-2:]
        source_url += f"/v1/files/v1/measurements/year=2024/month={month}/data.parquet"
    elif path.suffix == ".csv":
        try:
            sample = pd.read_csv(path, nrows=1)
            station_id = str(sample.station_id.iloc[0]) if len(sample) else empty_csv_station[path.name]
        except (KeyError, IndexError):
            station_id = empty_csv_station.get(path.name, "unknown")
        name = path.stem.removeprefix("final_")
        date_match = re.search(r"(20\d{2})-(\d{2})-(\d{2})", name)
        year_match = re.search(r"20\d{2}", name)
        if date_match:
            start = end = "-".join(date_match.groups())
        elif "2026_partial" in name:
            start, end = "2026-01-01", "2026-03-31"
        elif year_match:
            start, end = year_match.group(0) + "-01-01", year_match.group(0) + "-12-31"
        else:
            start, end = "unknown", "unknown"
        query = urlencode(
            {"station": station_id, "parameter": "PM2.5", "start": start, "end": end, "format": "csv"}
        )
        source_url += "/v1/measurements?" + query
    manifest.append(
        {
            "path": path.relative_to(ROOT).as_posix(),
            "source_url": source_url,
            "http_status": 200,
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "accessed_and_saved_at_ist": datetime.fromtimestamp(
                path.stat().st_mtime, ZoneInfo("Asia/Kolkata")
            ).isoformat(timespec="seconds"),
        }
    )
(OUT / "source_file_manifest.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
)

cpcb_states = {s["state_name"] for s in cpcb if s.get("state_name")}
cpcb_cities = {s["city_name"] for s in cpcb if s.get("city_name")}
last_years = sorted({s["last_seen"][:4] for s in cpcb if s.get("last_seen")})
pm25_sample = pd.read_csv(RAW / "final_pm25_embassy_delhi_2026-03-27.csv")
pm25 = param_by_name["PM2.5"]
pm10 = param_by_name["PM10"]
total_rows = meta["measurements"]["rows"]
total_bytes = meta["measurements"]["bytes"]
summary = {
    "exported_at": meta["exported_at"],
    "timezone_note": meta["timezone_note"],
    "archive_catalog": {
        "rows": total_rows,
        "measurement_bytes": total_bytes,
        "months": meta["measurements"]["n_months"],
        "first_month": meta["measurements"]["first_month"],
        "last_month": meta["measurements"]["last_month"],
        "tier": meta["your_tier"],
        "max_rows_per_query": meta["max_rows_per_query"],
        "query_timeout_seconds": meta.get("query_timeout_seconds"),
    },
    "station_index": {
        "cpcb_stations": len(cpcb),
        "embassy_stations": len(embassy),
        "pm25_reporting_stations_by_source": {
            "cpcb_caaqm": sum("PM2.5" in s.get("parameters", []) for s in cpcb),
            "us_embassy": sum("PM2.5" in s.get("parameters", []) for s in embassy),
        },
        "cpcb_cities": len(cpcb_cities),
        "cpcb_states": len(cpcb_states),
        "all_network_cities": len({s["city_name"] for s in stations if s.get("city_name")}),
        "all_network_state_labels": len({s["state_name"] for s in stations if s.get("state_name")}),
        "stations_without_coordinates": sum(
            s.get("latitude") is None or s.get("longitude") is None for s in stations
        ),
        "decommissioned_cpcb_without_registry_location_per_source_docs": sum(
            s["source"] == "cpcb_caaqm"
            and (s.get("latitude") is None or s.get("longitude") is None)
            for s in stations
        ),
        "operational_status": "not supplied",
        "cpcb_last_seen_station_counts_by_year": {
            year: sum(s.get("last_seen", "")[:4] == year for s in cpcb) for year in last_years
        },
    },
    "pm25_catalog": {
        "rows": pm25["n_rows"],
        "reporting_stations": pm25["n_stations"],
        "first_seen": pm25["first_seen"],
        "last_seen": pm25["last_seen"],
        "confirmed_latest_sample": {
            "station_id": "DS1010001",
            "collected_at": "2026-03-27 23:30:00",
            "value": float(pm25_sample.iloc[-1].value),
            "network": "us_embassy",
        },
    },
    "pm25_2024_direct_parquet_audit": {
        "rows": int(audit.readings.sum()),
        "stations": int(audit.station_id.nunique()),
        "duplicate_rows": int(audit.duplicate_rows.sum()),
        "negative_values": int(audit.negative_count.sum()),
        "minimum": float(audit.min_value.min()),
        "maximum": float(audit.max_value.max()),
        "earliest": audit.first_2024.min(),
        "latest": audit.last_2024.max(),
        "network_summary": network,
        "ranked_cpcb_stations": [
            {
                "station_id": row.station_id,
                "station_name": row.station_name,
                "city_name": row.city_name,
                "readings": int(row.readings),
                "missing_pct_active_span": float(row.missing_pct_active_span),
                "longest_consecutive_missing_hours": int(row.longest_consecutive_missing_hours),
            }
            for row in audit[audit.source.eq("cpcb_caaqm")].head(10).itertuples(index=False)
        ],
        "downloaded_monthly_files": len(measurement_files_2024),
        "downloaded_bytes": sum(f.stat().st_size for f in RAW.glob("parquet_2024_*.parquet")),
    },
    "representative_station_samples": sample_stats,
    "pollutant_completeness_2024": pd.read_csv(OUT / "pollutant_audit_2024.csv").to_dict(
        orient="records"
    ),
    "storage_estimates": {
        "full_archive_measurement_bytes": total_bytes,
        "pm25_only_rough_row_proportional_bytes": round(total_bytes * pm25["n_rows"] / total_rows),
        "pm25_and_pm10_rough_row_proportional_bytes": round(
            total_bytes * (pm25["n_rows"] + pm10["n_rows"]) / total_rows
        ),
        "all_pollutants_measurement_bytes": total_bytes,
        "estimation_note": "PM2.5 estimates use row-share proportions; compression differs by pollutant, so these are planning estimates, not quotes.",
    },
    "raw_file_manifest": manifest,
    "limitations": [
        "Full historical station-level completeness for all CPCB stations was not measured; the complete network audit is 2024 PM2.5 only.",
        "The demo key has a 10,000-row query cap and bulk access to 2024 only; no personal key was configured.",
        "The station API does not provide authoritative active/decommissioned status.",
        "Catalog-wide all-time pollutant counts come from the live parameters endpoint and were not recomputed over all archived files.",
    ],
}
(OUT / "verification_summary.json").write_text(
    json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
)
print(f"Built {len(audit)} station audits, {len(coverage)} station inventory rows, {len(sample_stats)} samples")
