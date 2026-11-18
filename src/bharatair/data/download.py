"""Authenticated monthly Parquet acquisition with integrity checks."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import requests

from bharatair.config import get_xkdr_api_key
from bharatair.data.config import CONFIG, PipelineConfig

LOG = logging.getLogger(__name__)
BASE_URL = "https://airquality.xkdr.org"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def month_range(start: str, end: str) -> list[tuple[int, int]]:
    sy, sm = (int(part) for part in start.split("-"))
    ey, em = (int(part) for part in end.split("-"))
    months: list[tuple[int, int]] = []
    year, month = sy, sm
    while (year, month) <= (ey, em):
        months.append((year, month))
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return months


def _get_with_retries(url: str, headers: dict[str, str], timeout: tuple[int, int], retries: int) -> requests.Response:
    last_error: requests.RequestException | None = None
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code not in {429, 500, 502, 503, 504}:
                return response
            last_error = requests.HTTPError(f"HTTP {response.status_code}", response=response)
        except requests.RequestException as exc:
            last_error = exc
        if attempt < retries:
            time.sleep(min(2**attempt, 8))
    assert last_error is not None
    raise last_error


def authenticated_file_index() -> dict[str, Any]:
    response = _get_with_retries(
        f"{BASE_URL}/v1/files",
        {"Authorization": f"Bearer {get_xkdr_api_key()}"},
        (10, 60),
        3,
    )
    response.raise_for_status()
    return response.json()


def _inspect_parquet(path: Path) -> tuple[int, list[dict[str, Any]]]:
    parquet = pq.ParquetFile(path)
    rows = parquet.metadata.num_rows
    schema = [
        {"name": field.name, "type": str(field.type), "nullable": field.nullable}
        for field in parquet.schema_arrow
    ]
    return rows, schema


def _prior_retrieval_record(path: Path, month_key: str, config: PipelineConfig) -> dict[str, Any]:
    """Find the original access time/status for reused Phase 1 verification files."""
    root = config.processed_dir.parent.parent
    relative = str(path.relative_to(root)).replace("\\", "/")
    candidates = [
        (config.processed_dir / "source_file_manifest.json").resolve(),
        (config.processed_dir / "historical_bulk_sample_checks.json").resolve(),
        (config.processed_dir / "delhi_site_1422_source_manifest.json").resolve(),
    ]
    for manifest_path in candidates:
        if not manifest_path.is_file():
            continue
        try:
            items = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(items, dict):
            items = items.get("files", [])
        if not isinstance(items, list):
            continue
        for item in items:
            item_path = str(item.get("path", item.get("saved_path", ""))).replace("\\", "/")
            month_match = f"{int(month_key[:4])}_{int(month_key[5:]):02d}.parquet" in item_path or f"authenticated_{month_key.replace('-', '_')}.parquet" in item_path
            if item_path == relative or (month_match and item_path.endswith(".parquet")):
                timestamp = item.get("accessed_at_utc")
                if not timestamp and item.get("accessed_and_saved_at_ist"):
                    timestamp = datetime.fromisoformat(item["accessed_and_saved_at_ist"]).astimezone(timezone.utc).isoformat()
                return {"retrieved_at_utc": timestamp, "http_status": item.get("http_status"), "prior_manifest": str(manifest_path.relative_to(root)).replace("\\", "/")}
    return {}


def acquire_target_months(
    config: PipelineConfig = CONFIG,
    *,
    retries: int = 3,
    timeout: tuple[int, int] = (15, 120),
) -> dict[str, Any]:
    """Download required months; reuse verified local source files without overwriting."""
    index = authenticated_file_index()
    indexed = {
        (int(item["year"]), int(item["month"])): item
        for item in index["files"]
        if item.get("kind") == "measurements"
    }
    target = month_range(config.start_month, config.end_month)
    config.raw_dir.mkdir(parents=True, exist_ok=True)
    headers = {"Authorization": f"Bearer {get_xkdr_api_key()}"}
    records: list[dict[str, Any]] = []
    unavailable: list[str] = []

    for year, month in target:
        month_key = f"{year:04d}-{month:02d}"
        entry = indexed.get((year, month))
        if entry is None:
            unavailable.append(month_key)
            records.append({"month": month_key, "status": "unavailable_in_index"})
            continue

        candidates = [
            config.raw_dir / f"{year:04d}_{month:02d}.parquet",
            CONFIG.processed_dir.parent / "raw" / "verification_samples" / f"parquet_{year:04d}_{month:02d}.parquet",
            CONFIG.processed_dir.parent / "raw" / "verification_samples" / "authenticated_bulk_checks" / f"authenticated_{year:04d}_{month:02d}.parquet",
        ]
        path = next((candidate for candidate in candidates if candidate.is_file()), None)
        disposition = "reused"
        downloaded_at = None
        status_code: int | None = None
        prior_access: dict[str, Any] = {}
        url = f"{BASE_URL}/v1/files/{entry['key']}"

        if path is None:
            path = config.raw_dir / f"{year:04d}_{month:02d}.parquet"
            if path.exists():
                raise FileExistsError(f"Refusing to overwrite existing source file: {path}")
            tmp_path = path.with_suffix(path.suffix + ".part")
            if tmp_path.exists():
                raise FileExistsError(f"Refusing to overwrite existing temporary file: {tmp_path}")
            response = _get_with_retries(url, headers, timeout, retries)
            status_code = response.status_code
            downloaded_at = datetime.now(timezone.utc).isoformat()
            if status_code != 200:
                records.append({"month": month_key, "status": "http_error", "http_status": status_code, "url": url, "retrieved_at_utc": downloaded_at})
                continue
            with tmp_path.open("xb") as handle:
                handle.write(response.content)
            path = tmp_path
            disposition = "downloaded"
        else:
            prior_access = _prior_retrieval_record(path, month_key, config)

        try:
            actual_rows, schema = _inspect_parquet(path)
            actual_bytes = path.stat().st_size
            if actual_bytes != int(entry["bytes"]) or actual_rows != int(entry["rows"]):
                raise ValueError(f"index mismatch for {month_key}: bytes={actual_bytes}, rows={actual_rows}")
            checksum = sha256_file(path)
            if disposition == "downloaded":
                final_path = config.raw_dir / f"{year:04d}_{month:02d}.parquet"
                os.replace(path, final_path)
                path = final_path
        except Exception:
            if disposition == "downloaded":
                path.unlink(missing_ok=True)
            raise

        records.append({
            "month": month_key,
            "status": "success",
            "disposition": disposition,
            "source_url": url,
            "retrieved_at_utc": downloaded_at or prior_access.get("retrieved_at_utc"),
            "http_status": status_code if status_code is not None else prior_access.get("http_status"),
            "retrieval_record": "new_authenticated_download" if disposition == "downloaded" else prior_access.get("prior_manifest", "prior retrieval time unavailable"),
            "path": str(path.relative_to(CONFIG.processed_dir.parent.parent)),
            "bytes": actual_bytes,
            "indexed_bytes": int(entry["bytes"]),
            "rows": actual_rows,
            "indexed_rows": int(entry["rows"]),
            "sha256": checksum,
            "schema": schema,
        })
        LOG.info("%s %s (%d bytes)", disposition, month_key, actual_bytes)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "authenticated": True,
        "source": "https://airquality.xkdr.org/v1/files",
        "target_months": [f"{year:04d}-{month:02d}" for year, month in target],
        "unavailable_months": unavailable,
        "files": records,
    }
    manifest_path = config.processed_dir / "delhi_site_1422_source_manifest.json"
    if manifest_path.exists():
        prior = json.loads(manifest_path.read_text(encoding="utf-8"))
        if prior != manifest:
            manifest_path = config.processed_dir / f"delhi_site_1422_source_manifest_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
