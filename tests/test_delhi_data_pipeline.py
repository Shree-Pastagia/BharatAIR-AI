from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from bharatair.data import download, gaps
from bharatair.data.config import PipelineConfig
from bharatair.data.parse import read_target_observations, resolve_fields
from bharatair.data.validate import canonicalize, compare_reference_extract


def _measurements(timestamps: list[str], values: list[float]) -> pd.DataFrame:
    return pd.DataFrame({
        "station_id": "site_1422",
        "station_name": "Dwarka-Sector 8",
        "city": "Delhi",
        "state": "Delhi",
        "source": "cpcb_caaqm",
        "parameter": "PM2.5",
        "unit": "µg/m³",
        "timestamp_source": pd.to_datetime(timestamps),
        "timestamp_ist": pd.to_datetime(timestamps),
        "value": values,
        "source_file": "data/raw/example.parquet",
        "source_month": "2024-01",
    })


def test_auth_header_uses_key_without_logging(monkeypatch, caplog):
    secret = "do-not-log-this-token"
    monkeypatch.setattr(download, "get_xkdr_api_key", lambda: secret)

    class Response:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"files": []}

    def fake_get(url, headers, timeout):
        assert headers["Authorization"] == f"Bearer {secret}"
        return Response()

    monkeypatch.setattr(download.requests, "get", fake_get)
    assert download.authenticated_file_index() == {"files": []}
    assert secret not in caplog.text


def test_month_range_and_schema_mapping():
    assert download.month_range("2018-11", "2019-02") == [(2018, 11), (2018, 12), (2019, 1), (2019, 2)]
    mapping = resolve_fields(["station_id", "parameter_name", "collected_at", "value", "source"])
    assert mapping["timestamp"] == "collected_at"
    with pytest.raises(ValueError, match="Ambiguous"):
        resolve_fields(["station_id", "parameter", "parameter_name", "collected_at", "value", "source"])


def test_authenticated_monthly_file_is_validated_and_not_overwritten(tmp_path, monkeypatch):
    source = pa.table({
        "station_id": ["site_1422"],
        "parameter_name": ["PM2.5"],
        "collected_at": [pd.Timestamp("2024-01-01 00:00")],
        "value": [12.0],
        "source": ["cpcb_caaqm"],
    })
    parquet_path = tmp_path / "body.parquet"
    pq.write_table(source, parquet_path)
    body = parquet_path.read_bytes()

    class Response:
        status_code = 200
        content = body

    monkeypatch.setattr(download, "authenticated_file_index", lambda: {
        "files": [{"kind": "measurements", "year": 2024, "month": 1, "key": "month", "bytes": len(body), "rows": 1}]
    })
    monkeypatch.setattr(download, "_get_with_retries", lambda *args, **kwargs: Response())
    monkeypatch.setattr(download, "get_xkdr_api_key", lambda: "token")
    cfg = PipelineConfig(start_month="2024-01", end_month="2024-01", raw_dir=tmp_path / "raw", processed_dir=tmp_path / "processed", report_dir=tmp_path / "reports")
    monkeypatch.setattr(download, "CONFIG", cfg)
    manifest = download.acquire_target_months(cfg)
    record = manifest["files"][0]
    assert record["status"] == "success"
    assert record["disposition"] == "downloaded"
    assert record["bytes"] == len(body)
    assert record["sha256"] == download.sha256_file(cfg.raw_dir / "2024_01.parquet")

    second = download.acquire_target_months(cfg)
    assert second["files"][0]["disposition"] == "reused"
    assert record["sha256"] == download.sha256_file(cfg.raw_dir / "2024_01.parquet")


def test_filtering_keeps_only_station_parameter_and_cpcb(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    path = raw_dir / "2024_01.parquet"
    pq.write_table(pa.table({
        "station_id": ["site_1422", "site_1422", "site_other"],
        "station_name": ["Dwarka"] * 3,
        "city_name": ["Delhi"] * 3,
        "state_name": ["Delhi"] * 3,
        "parameter_name": ["PM2.5", "PM10", "PM2.5"],
        "unit": ["µg/m³"] * 3,
        "collected_at": [pd.Timestamp("2024-01-01 00:00")] * 3,
        "value": [10.0, 20.0, 30.0],
        "source": ["cpcb_caaqm"] * 3,
    }), path)
    cfg = PipelineConfig(start_month="2024-01", end_month="2024-01", raw_dir=raw_dir, processed_dir=tmp_path / "processed", report_dir=tmp_path / "reports")
    frame, audit = read_target_observations(cfg)
    assert len(frame) == 1
    assert frame.iloc[0]["value"] == 10
    assert audit["indexed_source_rows_in_target_files"] == 3
    assert audit["station_parameter_rows_before_source_filter"] == 1


def test_canonical_preserves_naive_ist_extremes_and_flags():
    source = _measurements(["2024-01-01 00:00", "2024-01-01 01:00", "2024-01-01 03:00"], [-1.0, 500.0, 7.0])
    result, counts = canonicalize(source)
    assert str(result["timestamp_ist"].dtype) == "datetime64[ns]"
    assert result["timestamp_ist"].dt.tz is None
    assert result["quality_negative"].tolist() == [True, False, False]
    assert result["quality_extreme_ge_500"].tolist() == [False, True, False]
    assert counts["negative_measurements_preserved"] == 1
    assert counts["extreme_measurements_ge_500_preserved"] == 1
    assert result["timestamp_ist"].tolist() == sorted(result["timestamp_ist"].tolist())


def test_gap_detection_and_window_eligibility():
    timestamps = pd.date_range("2024-01-01", periods=12, freq="h").delete([3, 7, 8, 9])
    source = pd.DataFrame({"timestamp_ist": timestamps, "value": 1.0})
    calendar, missing, audit = gaps.build_hourly_audits(source)
    assert audit["expected_hourly_timestamps_active_span"] == 12
    assert audit["missing_hourly_timestamps"] == 4
    assert audit["longest_consecutive_missing_hours"] == 3
    assert missing["missing_hours"].tolist() == [1, 3]
    feasibility = gaps.window_feasibility(calendar, missing, input_lengths=(2,), horizons=(1,), long_gap_hours=3)
    row = feasibility.iloc[0]
    assert row["excluded_long_outage_windows"] > 0
    assert row["eligible_windows"] > 0
    assert row["candidate_origins"] == 12


def test_duplicate_timestamps_are_counted_not_silently_collapsed():
    source = _measurements(["2024-01-01 00:00", "2024-01-01 00:00", "2024-01-01 01:00"], [4.0, 5.0, 6.0])
    calendar, _, audit = gaps.build_hourly_audits(source)
    assert audit["duplicate_timestamp_rows"] == 2
    assert audit["unique_timestamps"] == 2
    assert len(calendar) == 2
    canonical, counts = canonicalize(source)
    assert canonical["quality_duplicate_timestamp"].tolist() == [True, True, False]
    assert counts["duplicate_timestamp_rows_flagged"] == 2


def test_unit_values_are_consistent_in_station_records(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    path = raw_dir / "2024_01.parquet"
    pq.write_table(pa.table({
        "station_id": ["site_1422", "site_1422"],
        "station_name": ["Dwarka"] * 2,
        "city_name": ["Delhi"] * 2,
        "state_name": ["Delhi"] * 2,
        "parameter_name": ["PM2.5"] * 2,
        "unit": ["µg/m³", "mg/m³"],
        "collected_at": [pd.Timestamp("2024-01-01 00:00"), pd.Timestamp("2024-01-01 01:00")],
        "value": [10.0, 20.0],
        "source": ["cpcb_caaqm"] * 2,
    }), path)
    cfg = PipelineConfig(start_month="2024-01", end_month="2024-01", raw_dir=raw_dir, processed_dir=tmp_path / "processed", report_dir=tmp_path / "reports")
    frame, audit = read_target_observations(cfg)
    assert len(frame) == 2
    assert set(audit["unit_values"]) == {"µg/m³", "mg/m³"}


def test_deterministic_canonical_sort_and_checksum(tmp_path):
    frame = _measurements(["2024-01-01 01:00", "2024-01-01 00:00"], [2.0, 1.0])
    one, _ = canonicalize(frame)
    two, _ = canonicalize(frame.sample(frac=1, random_state=42))
    pd.testing.assert_frame_equal(one, two)
    path = tmp_path / "bytes.bin"
    path.write_bytes(b"checksum fixture")
    assert download.sha256_file(path) == "4191d7d2f5f1960b7fac8168756a58090829157f780a45bbd5ba4aa020cfe86a"


def test_reference_extract_comparison_allows_float_serialization_rounding():
    bulk = _measurements(["2024-01-01 00:00", "2024-01-01 01:00"], [59.66666666666667, 31.333333333333336])
    canonical, _ = canonicalize(bulk)
    reference = pd.DataFrame({
        "timestamp_ist": pd.to_datetime(["2024-01-01 00:00", "2024-01-01 01:00"]),
        "value": [59.666666666666664, 31.333333333333332],
    })
    result = compare_reference_extract(canonical, reference)
    assert result["timestamps_match"] is True
    assert result["values_match_within_tolerance"] is True
