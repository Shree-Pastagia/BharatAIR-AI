"""Phase 2 pipeline configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bharatair.config import PROJECT_ROOT


@dataclass(frozen=True)
class PipelineConfig:
    station_id: str = "site_1422"
    source: str = "cpcb_caaqm"
    parameter: str = "PM2.5"
    start_month: str = "2018-02"
    end_month: str = "2025-09"
    raw_dir: Path = PROJECT_ROOT / "data" / "raw" / "xkdr_monthly"
    processed_dir: Path = PROJECT_ROOT / "data" / "processed"
    report_dir: Path = PROJECT_ROOT / "reports"


CONFIG = PipelineConfig()
