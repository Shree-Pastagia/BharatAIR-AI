"""Atomic run artifacts and strict candidate provenance validation."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import math
from pathlib import Path
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_bytes(path: Path, writer) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temporary = Path(temp_name)
    try:
        writer(temporary)
        with temporary.open("rb+") as stream:
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_json(path: Path, payload: Any) -> None:
    def safe(value):
        if isinstance(value, dict):
            return {str(key): safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [safe(item) for item in value]
        if hasattr(value, "item"):
            value = value.item()
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return value
    data = json.dumps(safe(payload), indent=2, ensure_ascii=False, default=str, allow_nan=False).encode("utf-8")
    atomic_bytes(path, lambda target: target.write_bytes(data))


def atomic_csv(path: Path, frame, **kwargs) -> None:
    atomic_bytes(path, lambda target: frame.to_csv(target, index=False, **kwargs))


def atomic_torch(path: Path, payload: Any, torch_module) -> None:
    atomic_bytes(path, lambda target: torch_module.save(payload, target))


def validate_run_id(run_id: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", run_id):
        raise ValueError("run_id must be 1-80 safe filename characters")
    return run_id


def validate_manifest(existing: dict[str, Any], requested: dict[str, Any]) -> None:
    """Require exact scientific provenance before resuming a run."""
    required = ("run_id", "config_fingerprint", "data_fingerprint", "split_fingerprint", "preprocessing_fingerprint")
    for key in required:
        if existing.get(key) != requested.get(key):
            raise ValueError(f"Resume refused: manifest {key} does not match")
    for key in ("device", "torch_version", "cuda_version"):
        if existing.get("runtime", {}).get(key) != requested.get("runtime", {}).get(key):
            raise ValueError(f"Resume refused: runtime {key} does not match")


def candidate_identity(run_id: str, model: str, input_hours: int | None, horizon_hours: int) -> str:
    suffix = "baseline" if input_hours is None else f"L{input_hours}"
    safe_model = re.sub(r"[^A-Za-z0-9_-]", "_", model)
    return f"{run_id}__{safe_model}__{suffix}__H{horizon_hours}"


def validate_candidate_provenance(payload: dict[str, Any], expected: dict[str, str]) -> None:
    for key in ("run_id", "candidate_id", "configuration_fingerprint", "data_fingerprint", "split_fingerprint", "preprocessing_fingerprint"):
        if payload.get(key) != expected.get(key):
            raise ValueError(f"Checkpoint provenance mismatch for {key}")


def verify_completed_candidate(candidate_dir: Path) -> dict[str, Any] | None:
    """Return marker only when all committed artifacts exist and match hashes."""
    marker_path = candidate_dir / "complete.json"
    if not marker_path.is_file():
        return None
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    for rel_path, expected_hash in marker.get("artifact_sha256", {}).items():
        path = candidate_dir / rel_path
        if not path.is_file() or file_sha256(path) != expected_hash:
            raise ValueError(f"Completed candidate artifact failed verification: {path}")
    return marker


def commit_candidate(candidate_dir: Path, *, provenance: dict[str, str], artifact_paths: list[Path]) -> dict[str, Any]:
    hashes = {path.relative_to(candidate_dir).as_posix(): file_sha256(path) for path in artifact_paths}
    marker = {**provenance, "artifact_sha256": hashes, "status": "complete"}
    atomic_json(candidate_dir / "complete.json", marker)
    verified = verify_completed_candidate(candidate_dir)
    if verified != marker:
        raise RuntimeError("Candidate artifact commit verification failed")
    return marker
