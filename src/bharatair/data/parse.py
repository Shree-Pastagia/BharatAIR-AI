"""Read monthly Parquet schemas and select the Delhi CPCB PM2.5 series."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from bharatair.data.config import CONFIG, PipelineConfig
from bharatair.data.download import month_range

FIELD_ALIASES = {
    "station_id": ("station_id", "site_id"),
    "station_name": ("station_name", "site_name"),
    "city": ("city_name", "city"),
    "state": ("state_name", "state"),
    "parameter": ("parameter_name", "parameter"),
    "unit": ("unit", "units"),
    "timestamp": ("collected_at", "timestamp", "datetime"),
    "value": ("value", "measurement", "concentration"),
    "source": ("source", "network"),
}
REQUIRED = {"station_id", "parameter", "timestamp", "value", "source"}


def resolve_fields(columns: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for canonical, aliases in FIELD_ALIASES.items():
        found = [name for name in aliases if name in columns]
        if len(found) > 1:
            raise ValueError(f"Ambiguous columns for {canonical}: {found}")
        if found:
            mapping[canonical] = found[0]
    missing = REQUIRED - mapping.keys()
    if missing:
        raise ValueError(f"Missing required schema fields: {sorted(missing)}; columns={columns}")
    return mapping


def target_paths(config: PipelineConfig = CONFIG) -> list[tuple[str, Path]]:
    paths: list[tuple[str, Path]] = []
    for year, month in month_range(config.start_month, config.end_month):
        month_key = f"{year:04d}-{month:02d}"
        possible = [
            config.raw_dir / f"{year:04d}_{month:02d}.parquet",
            config.processed_dir.parent / "raw" / "verification_samples" / f"parquet_{year:04d}_{month:02d}.parquet",
            config.processed_dir.parent / "raw" / "verification_samples" / "authenticated_bulk_checks" / f"authenticated_{year:04d}_{month:02d}.parquet",
        ]
        path = next((candidate for candidate in possible if candidate.is_file()), None)
        if path is not None:
            paths.append((month_key, path))
    return paths


def read_target_observations(config: PipelineConfig = CONFIG) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read and filter source rows while retaining provenance and audit counters."""
    observations: list[pd.DataFrame] = []
    total_rows = 0
    schemas: dict[str, dict[str, str]] = {}
    schema_fingerprints: dict[str, int] = {}
    monthly_source_rows: dict[str, int] = {}
    station_parameter_rows = 0
    wrong_network_rows = 0
    invalid_timestamp_rows = 0
    nonnumeric_rows = 0
    missing_value_rows = 0
    missing_unit_rows = 0
    unit_values: set[str] = set()

    for month_key, path in target_paths(config):
        parquet = pq.ParquetFile(path)
        rows = parquet.metadata.num_rows
        total_rows += rows
        monthly_source_rows[month_key] = rows
        schema = parquet.schema_arrow
        fingerprint = str(schema)
        schema_fingerprints[fingerprint] = schema_fingerprints.get(fingerprint, 0) + 1
        mapping = resolve_fields(schema.names)
        schemas[month_key] = {canonical: source for canonical, source in mapping.items()}
        dataset = ds.dataset(path, format="parquet")
        station_field = ds.field(mapping["station_id"])
        parameter_field = ds.field(mapping["parameter"])
        filter_expr = (station_field == config.station_id) & (parameter_field == config.parameter)
        table = dataset.to_table(columns=list(dict.fromkeys(mapping.values())), filter=filter_expr)
        frame = table.to_pandas()
        frame = frame.rename(columns={source: canonical for canonical, source in mapping.items()})
        selected = frame.copy()
        station_parameter_rows += len(selected)
        if selected.empty:
            continue
        bad_source = ~selected["source"].astype("string").str.strip().str.casefold().eq(config.source.casefold())
        wrong_network_rows += int(bad_source.sum())
        selected = selected.loc[~bad_source].copy()
        if selected.empty:
            continue
        selected["timestamp_source"] = selected["timestamp"]
        parsed_timestamp = pd.to_datetime(selected["timestamp"], errors="coerce")
        invalid_timestamp_rows += int(parsed_timestamp.isna().sum())
        selected["timestamp_ist"] = parsed_timestamp
        numeric = pd.to_numeric(selected["value"], errors="coerce")
        nonnumeric_rows += int((selected["value"].notna() & numeric.isna()).sum())
        missing_value_rows += int(numeric.isna().sum())
        selected["value"] = numeric
        if "unit" not in selected:
            selected["unit"] = pd.NA
        missing_unit_rows += int(selected["unit"].isna().sum())
        unit_values.update(str(x).strip() for x in selected["unit"].dropna().unique())
        selected["source_file"] = str(path.relative_to(config.processed_dir.parent.parent))
        selected["source_month"] = month_key
        observations.append(selected)

    if not observations:
        raise FileNotFoundError("No station PM2.5 records found in available target Parquet files")
    combined = pd.concat(observations, ignore_index=True)
    audit = {
        "indexed_source_rows_in_target_files": total_rows,
        "available_months_processed": list(monthly_source_rows),
        "missing_target_months": [
            f"{year:04d}-{month:02d}"
            for year, month in month_range(config.start_month, config.end_month)
            if f"{year:04d}-{month:02d}" not in monthly_source_rows
        ],
        "monthly_source_rows": monthly_source_rows,
        "schema_fingerprints": schema_fingerprints,
        "schema_mapping_by_month": schemas,
        "station_parameter_rows_in_cpcb_source": int(len(combined)),
        "station_parameter_rows_before_source_filter": station_parameter_rows,
        "wrong_network_rows_excluded": wrong_network_rows,
        "invalid_timestamp_rows": invalid_timestamp_rows,
        "nonnumeric_measurement_rows": nonnumeric_rows,
        "missing_measurement_rows": missing_value_rows,
        "missing_unit_rows": missing_unit_rows,
        "unit_values": sorted(unit_values),
    }
    return combined, audit
