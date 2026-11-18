# Phase 5 Validation-Only Compute Pilot Plan

Status: plan only. **Not launched.** This is a representative infrastructure pilot, not an early model comparison or authorization to train.

## Scope and immutable grid

Experiment A only, four station-specific series from four cities, with Tier A and Tier B represented:

| Station | City | Tier | Operator | Rows | Missingness | PM2.5 date range |
|---|---|---|---|---:|---:|---|
| site_1422 — Dwarka Sector 8 | Delhi | A | DPCC | 63,178 | 4.95% | 2018-02-01 10:00 to 2025-09-01 23:00 |
| site_294 — Sanathnagar | Hyderabad | A | TSPCB | 80,379 | 12.05% | 2015-03-31 00:00 to 2025-09-01 23:00 |
| site_5394 — Mazgaon | Mumbai | B | IITM | 32,046 | 23.98% | 2020-11-10 11:00 to 2025-09-01 23:00 |
| site_5450 — Gyaspur | Ahmedabad | B | IITM | 24,170 | 35.03% | 2021-06-04 22:00 to 2025-09-01 23:00 |

All 6 model families × 3 lookbacks × 4 horizons are retained for every station: **72 candidates/station, 288 candidate fits total** (144 CUDA neural fits, 144 CPU traditional fits). Add 32 station×horizon baseline outputs (persistence and seasonal naive); these are not model fits. Use the approved Phase 3 hyperparameters, optimizer, batch size, epochs, seed policy, target, split/purge policy, and no-imputation rule unchanged. Do not narrow the grid or alter parameters to make the pilot faster.

Pilot station selection is for varied runtime/data behavior and tier/city representation only; these stations are not asserted to represent all cities. All exact feasibility rows remain in `PHASE5_STATION_FEASIBILITY.csv`.

## Run and measurements

Only after explicit approval and after the Phase 5 multi-station runner passes its own synthetic tests, create a unique run ID and isolated `runs/<run_id>/`. The run must identify the input dataset and cohort fingerprints and write candidate artifacts atomically. The pilot default is validation-only; the test gate remains closed.

Record per candidate: start/end/duration; CPU/GPU device and actual device metadata; per-candidate CUDA peak allocated/reserved bytes and MiB; process RSS when available; batch/data-load/fit/validation/artifact-write timings; seed/config/data/split/preprocessing fingerprints; candidate and artifact checksums; validation row counts; checkpoint reload/provenance result; and completion/failure state. Collect system CPU/GPU utilization at one-second intervals using already available Windows counters and `nvidia-smi` if present; do not install monitoring packages. Separate data reading/window assembly from fit timing and record peak host/device memory. Report storage written and projected full-run storage from measured artifacts.

## Completion, resume and reproducibility checks

Before the pilot is considered complete, verify all 288 candidates and 32 baseline instances have expected validation output counts, complete artifact sets, checksums, manifest identity and provenance. Exercise candidate-boundary resume in an isolated test run: a verified completed candidate must be reused only when all provenance fields match; a deliberate fingerprint mismatch must be rejected. Do not alter or resume legacy run directories.

For a reproducibility probe, preregister one candidate per architecture (one configuration on each of the four pilot stations, six architecture candidates in total) and repeat it in a distinct run ID with the same seed/configuration. Compare validation prediction values within a documented numeric tolerance. This adds **6 repeat fits**, for **294 total fits**. This probe diagnoses reproducibility; it does not replace or remove any grid candidate.

## Runtime estimate and operational stop

The original Phase 5 preflight estimates primary A at 14.9 hours, including 7.6 CUDA fit hours and 7.3 CPU fit hours, using Phase 3 linear scaling by row count. For these four stations the row total is 199,773 versus the primary seven-city A total of 2,473,079 rows; simple row scaling gives about **1.20 hours**. That is a rough planning figure only; pilot-specific scaling, 288 artifact writes, utilization sampling and six repeat fits can increase elapsed time substantially. The prior rough pilot estimate of about 33.9 minutes was based on a different scaling basis and is not reconciled with the current 14.9-hour primary-A estimate; treat the 1.20-hour row-scaled number as the consistent baseline and recalibrate after this pilot. Do not promise a completion time.

Stop after validation artifacts, checksums, provenance/resume and reproducibility checks are reported. No test data access or test scoring. This plan does not authorize execution.

## Blocking prerequisites

1. Implement a Phase 5 runner supporting per-station series and this policy; the Phase 3 runner is hard-coded to the Delhi canonical dataset.
2. Demonstrate with tests/logging that validation mode never loads test values or constructs test windows.
3. Synthetic tests must cover atomic artifacts, candidate-level resume/provenance and telemetry.
4. Review below-floor station/configuration handling (the preflight flags them but does not authorize silent omission or threshold changes).
5. Approve the pilot run plan explicitly before launch.
