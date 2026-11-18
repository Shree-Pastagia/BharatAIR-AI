# BharatAIR Automation & Data Scripts

This directory contains standalone execution tools for live telemetry ingestion, model monitoring, dataset compilation, and web synchronization.

---

## Active Scripts

| Script | Purpose & Function |
|---|---|
| **`poll_live_cpcb_daemon.py`** | Automated continuous background daemon that polls government CPCB CAAQMS observations via `data.gov.in` every hour and appends them to the rolling 72-hour telemetry history. |
| **`fetch_live_cpcb.py`** | One-shot CLI tool to fetch the latest instantaneous PM2.5 readings across all 7 megacities. |
| **`sync_experiments_to_web.py`** | Compiles validated model evaluation metrics, champion architectures, and MAE scores from `runs/` into the production web application (`BharatAIR_Web`). |
| **`monitor_gpu_training.py`** | Real-time terminal dashboard tracking CUDA training progress, candidate fit completion rates, and validation loss across experiments. |
| **`rolling_accuracy_logger.py`** | Continually logs the accuracy of prior 24h AI predictions against incoming ground-truth CPCB sensor readings. |
| **`build_multiyear_timeseries.py`** | Builds the multi-year (2018–2024) longitudinal PM2.5 dataset used for retrospective historical forecasting in the Forecast Studio. |
| **`build_historical_coverage.py`** | Audits hourly sensor uptime and completeness across all 107 stations in the national cohort. |

---

## Archived Pipeline Scripts

Historical or phase-specific pipeline runners are organized in **`pipeline_archive/`**:
- `run_delhi_site_1422_pipeline.py`: Legacy Phase 3 single-station Delhi Dwarka Sector 8 pipeline.
- `run_phase3_experiments.py`: Pilot multi-model training harness.
- `phase4_multicity_audit.py`: Multi-city data validation script.
- `phase5_preflight.py` & `build_phase5_preflight_report.py`: Phase 5 GPU preflight checks.
- `build_phase1_artifacts.py`: Initial data checksums and joins.
