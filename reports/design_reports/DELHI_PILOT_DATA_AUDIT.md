# Delhi `site_1422` PM2.5 data audit — Phase 2

## Outcome

The reproducible CPCB-only data pipeline is complete. The Parquet bulk scan reproduces the Phase 1B PM2.5 row count, range, duplicate count, active calendar, missingness, and longest gap. The canonical file contains observed numeric source records only. No values were interpolated, forward-filled, or removed as outliers. No model was trained.

## Source and acquisition

- Source: India Air Quality Database, XKDR Forum, authenticated monthly Parquet endpoint; provider export indexed at `2026-09-30T11:25:11+00:00`.
- Network, station, parameter: `cpcb_caaqm`, `site_1422` (Dwarka-Sector 8, Delhi — DPCC), PM2.5.
- Target months: 92 months, 2018-02 through 2025-09 inclusive.
- Acquired: 74 monthly files (269,767,033 bytes); reused: 18 locally verified files (109,633,178 bytes).
- Combined indexed/storage size: 379,400,211 bytes; indexed rows represented by the target monthly files: 183,836,067; the Arrow filter yielded 63,178 station/source/parameter rows.
- All 92 files were readable Parquet and matched indexed row and byte counts. The 183.8 million figure is the monthly Parquet metadata row total; it is not a claim that the pipeline materialized every non-target row into memory. Monthly SHA-256, URL, status, retrieval time, schema, and local path are recorded in `data/processed/delhi_site_1422_source_manifest.json`. For reused files, original retrieval timestamps and HTTP status were carried forward from the Phase 1 file manifests; no duplicate requests were made.
- Monthly schemas: 1 distinct schema fingerprint(s), across 92 months. Field mappings are recorded per month in the quality summary. Required names map from `station_id`, `parameter_name`, `collected_at`, `value`, and `source`; optional source fields map to station name, city, state, and unit.
- The API key was loaded through `python-dotenv`; it was not emitted to logs or artifacts. Authentication succeeded. Raw Parquet bytes are preserved at their original paths.

## Canonical station series and Phase 1B reproduction

| Measure | Recalculated result |
|---|---:|
| Station-filtered CPCB PM2.5 source records | 63,178 |
| Canonical numeric observed records | 63,178 |
| First observation (naive IST) | 2018-02-01T10:00:00 |
| Last observation (naive IST) | 2025-09-01T23:00:00 |
| Unique hourly timestamps | 63,178 |
| Duplicate timestamp rows | 0 |
| Expected hours, first-to-last active span | 66,470 |
| Missing hours / missingness | 3,292 / 4.953% |
| Longest consecutive missing interval | 2,160 hours |
| Months with ≥80% / ≥90% coverage | 88 / 88 of 92 active-span months |
| Timestamp offset violations | 0 |
| Difference from Phase 1B | 0 rows; same first/last timestamp, duplicate count, missingness (rounding), and longest gap |

A record-by-record comparison with the existing full-history station API CSV found all 63,178 timestamps matched and all values matched within 1e-9 µg/m³. Maximum floating-point serialization difference was 7.11e-15. This comparison is reproducible from the reference extract and is recorded in `data/processed/data_quality_summary.json`.

The worst gap is 2025-01-01 00:00 through 2025-03-31 23:00 IST (2,160 missing hours). The audit identifies 229 separate missing runs, with their exact boundaries and lengths in `data/processed/delhi_site_1422_gap_audit.csv`.

### Missing hours by year

| Year | Observed hours | Missing hours | Active-span coverage |
|---:|---:|---:|---:|
| 2018 | 7,883 | 123 | 98.46% |
| 2019 | 8,683 | 77 | 99.12% |
| 2020 | 8,565 | 219 | 97.51% |
| 2021 | 8,624 | 136 | 98.45% |
| 2022 | 8,583 | 177 | 97.98% |
| 2023 | 8,481 | 279 | 96.82% |
| 2024 | 8,761 | 23 | 99.74% |
| 2025 | 3,598 | 2,258 | 61.44% |


### Missing hours by month

| Month | Observed hours | Missing hours | Active-span coverage |
|---|---:|---:|---:|
| 2018-02 | 660 | 2 | 99.70% |
| 2018-03 | 697 | 47 | 93.68% |
| 2018-04 | 715 | 5 | 99.31% |
| 2018-05 | 743 | 1 | 99.87% |
| 2018-06 | 679 | 41 | 94.31% |
| 2018-07 | 743 | 1 | 99.87% |
| 2018-08 | 744 | 0 | 100.00% |
| 2018-09 | 704 | 16 | 97.78% |
| 2018-10 | 741 | 3 | 99.60% |
| 2018-11 | 713 | 7 | 99.03% |
| 2018-12 | 744 | 0 | 100.00% |
| 2019-01 | 744 | 0 | 100.00% |
| 2019-02 | 662 | 10 | 98.51% |
| 2019-03 | 743 | 1 | 99.87% |
| 2019-04 | 720 | 0 | 100.00% |
| 2019-05 | 724 | 20 | 97.31% |
| 2019-06 | 719 | 1 | 99.86% |
| 2019-07 | 740 | 4 | 99.46% |
| 2019-08 | 743 | 1 | 99.87% |
| 2019-09 | 683 | 37 | 94.86% |
| 2019-10 | 744 | 0 | 100.00% |
| 2019-11 | 718 | 2 | 99.72% |
| 2019-12 | 743 | 1 | 99.87% |
| 2020-01 | 713 | 31 | 95.83% |
| 2020-02 | 677 | 19 | 97.27% |
| 2020-03 | 737 | 7 | 99.06% |
| 2020-04 | 720 | 0 | 100.00% |
| 2020-05 | 741 | 3 | 99.60% |
| 2020-06 | 711 | 9 | 98.75% |
| 2020-07 | 706 | 38 | 94.89% |
| 2020-08 | 680 | 64 | 91.40% |
| 2020-09 | 714 | 6 | 99.17% |
| 2020-10 | 722 | 22 | 97.04% |
| 2020-11 | 707 | 13 | 98.19% |
| 2020-12 | 737 | 7 | 99.06% |
| 2021-01 | 716 | 28 | 96.24% |
| 2021-02 | 671 | 1 | 99.85% |
| 2021-03 | 688 | 56 | 92.47% |
| 2021-04 | 720 | 0 | 100.00% |
| 2021-05 | 740 | 4 | 99.46% |
| 2021-06 | 719 | 1 | 99.86% |
| 2021-07 | 728 | 16 | 97.85% |
| 2021-08 | 726 | 18 | 97.58% |
| 2021-09 | 717 | 3 | 99.58% |
| 2021-10 | 741 | 3 | 99.60% |
| 2021-11 | 716 | 4 | 99.44% |
| 2021-12 | 742 | 2 | 99.73% |
| 2022-01 | 715 | 29 | 96.10% |
| 2022-02 | 671 | 1 | 99.85% |
| 2022-03 | 715 | 29 | 96.10% |
| 2022-04 | 687 | 33 | 95.42% |
| 2022-05 | 719 | 25 | 96.64% |
| 2022-06 | 701 | 19 | 97.36% |
| 2022-07 | 734 | 10 | 98.66% |
| 2022-08 | 744 | 0 | 100.00% |
| 2022-09 | 706 | 14 | 98.06% |
| 2022-10 | 737 | 7 | 99.06% |
| 2022-11 | 710 | 10 | 98.61% |
| 2022-12 | 744 | 0 | 100.00% |
| 2023-01 | 728 | 16 | 97.85% |
| 2023-02 | 672 | 0 | 100.00% |
| 2023-03 | 708 | 36 | 95.16% |
| 2023-04 | 720 | 0 | 100.00% |
| 2023-05 | 730 | 14 | 98.12% |
| 2023-06 | 706 | 14 | 98.06% |
| 2023-07 | 583 | 161 | 78.36% |
| 2023-08 | 716 | 28 | 96.24% |
| 2023-09 | 720 | 0 | 100.00% |
| 2023-10 | 735 | 9 | 98.79% |
| 2023-11 | 719 | 1 | 99.86% |
| 2023-12 | 744 | 0 | 100.00% |
| 2024-01 | 744 | 0 | 100.00% |
| 2024-02 | 696 | 0 | 100.00% |
| 2024-03 | 744 | 0 | 100.00% |
| 2024-04 | 720 | 0 | 100.00% |
| 2024-05 | 744 | 0 | 100.00% |
| 2024-06 | 715 | 5 | 99.31% |
| 2024-07 | 744 | 0 | 100.00% |
| 2024-08 | 741 | 3 | 99.60% |
| 2024-09 | 719 | 1 | 99.86% |
| 2024-10 | 739 | 5 | 99.33% |
| 2024-11 | 715 | 5 | 99.31% |
| 2024-12 | 740 | 4 | 99.46% |
| 2025-01 | 0 | 744 | 0.00% |
| 2025-02 | 0 | 672 | 0.00% |
| 2025-03 | 0 | 744 | 0.00% |
| 2025-04 | 717 | 3 | 99.58% |
| 2025-05 | 737 | 7 | 99.06% |
| 2025-06 | 686 | 34 | 95.28% |
| 2025-07 | 728 | 16 | 97.85% |
| 2025-08 | 708 | 36 | 95.16% |
| 2025-09 | 22 | 2 | 91.67% |

The three months of 2025-01, 2025-02 and 2025-03 have no measurements; there is also a 161-hour gap in July 2023.

## Measurement quality

| Measure | Result |
|---|---:|
| Unit(s) in station source rows | µg/m³; consistent=True |
| Minimum / maximum | 1.0 / 973.0 µg/m³ |
| Mean / median | 103.024 / 66.000 µg/m³ |
| Sample standard deviation | 97.832 µg/m³ |
| Negative values | 0 |
| Values ≥500 µg/m³ | 406 (maximum 973.0 µg/m³) |
| Invalid timestamps / missing or nonnumeric values | 0 / 0 |

Negative and extreme flags are retained in the canonical dataset. No automatic exclusion or calibration was applied. Source timestamps remain naive datetimes and are interpreted as IST; they were not converted to UTC. All audited CPCB timestamps were at minute 00.

## Window feasibility counts (not model results)

A candidate origin `t` uses the current and preceding `input_hours` timestamps, all of which must be observed, and the single target at `t + horizon_hours`, which must be observed. No imputation is used. Candidates outside the active calendar bounds are boundaries. A missing run of ≥24 hours intersecting the input-to-target interval is classified as a long-outage exclusion; remaining reasons are mutually exclusive in order: input gap, missing target, eligible. These rules are initial engineering policy for feasibility accounting, not a selected modeling window or accuracy result.

| Input hours | Horizon hours | Eligible | Boundary | Long outage | Input gap | Missing target |
|---:|---:|---:|---:|---:|---:|---:|
| 24 | 1 | 58,708 | 24 | 2,549 | 5,039 | 150 |
| 24 | 6 | 58,410 | 29 | 2,574 | 5,036 | 421 |
| 24 | 12 | 58,239 | 35 | 2,604 | 5,036 | 556 |
| 24 | 24 | 58,049 | 47 | 2,664 | 5,036 | 674 |
| 48 | 1 | 55,136 | 48 | 2,669 | 8,480 | 137 |
| 48 | 6 | 54,857 | 53 | 2,694 | 8,477 | 389 |
| 48 | 12 | 54,692 | 59 | 2,724 | 8,477 | 518 |
| 48 | 24 | 54,505 | 71 | 2,784 | 8,477 | 633 |
| 168 | 1 | 40,585 | 168 | 3,269 | 22,355 | 93 |
| 168 | 6 | 40,396 | 173 | 3,294 | 22,340 | 267 |
| 168 | 12 | 40,289 | 179 | 3,324 | 22,322 | 356 |
| 168 | 24 | 40,187 | 191 | 3,384 | 22,286 | 422 |

Full machine-readable counts are in `data/processed/delhi_site_1422_window_feasibility.csv`. Even with 168-hour inputs, over 40,000 windows remain eligible per horizon; counts alone do not justify choosing an input length.

## Output artifacts and assumptions

- `data/processed/delhi_site_1422_pm25.parquet` and `.csv`: observed measurements only, with station identity, CPCB source, parameter, source unit, original naive source timestamp, normalized naive IST timestamp, value, source file/month, and quality flags.
- `data/processed/delhi_site_1422_hourly_calendar.parquet`: one row per active-span hour with separate `is_observed`/`is_missing` flags; it is not a measurement dataset.
- `data/processed/delhi_site_1422_gap_audit.csv`: maximal consecutive missing runs, with exact timestamps and duration.
- `data/processed/delhi_site_1422_window_feasibility.csv`: eligibility counts under the stated rule.
- `data/processed/data_quality_summary.json`: machine-readable source, schema, quality, timestamp, monthly/yearly missingness, and window audit.
- `data/processed/delhi_site_1422_source_manifest.json`: file-level provenance and integrity checks.

## Remaining limitations

The last verified CPCB measurement is 2025-09-01 23:00 IST. This dataset supports only an offline historical single-station research study; it does not establish current data availability or operational forecasting capability. The three-month outage and other gaps must stay explicit. Extreme values are preserved but should be investigated before scientific interpretation. CPCB and embassy networks were not mixed. No other city was added, and no training, tuning, or application work was performed.
