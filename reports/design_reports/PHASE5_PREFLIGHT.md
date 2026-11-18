# BharatAir Phase 5 — Preflight

**Status: preflight only; no training launched.** This report is prepared for review before any Phase 5 candidate is trained.

## Proposed cohort

Selection applies the Phase 4 predeclared eligibility bands. The seven primary cities include **all Tier A and Tier B** station IDs with CPCB PM2.5 records and nonblank city and state metadata. Tier C, zero-row stations, and stations without both city and state labels are excluded. Pune is kept separate as five Tier B sensitivity stations. Official-register operator identification is unverified for 15 of 112 selected stations; those cells are blank and flagged, never inferred from a station name.

**Primary: 107 stations** (66 Tier A, 41 Tier B). **Pune sensitivity: 5 Tier B stations.** Exact station IDs, names, operators, operator verification, first/latest timestamp, counts, missingness, and coverage months are in [PHASE5_STATION_COHORT.csv](PHASE5_STATION_COHORT.csv). The timestamp-only window inventory is [PHASE5_ELIGIBLE_WINDOWS.csv](PHASE5_ELIGIBLE_WINDOWS.csv).

| City | Stations | Tier A | Tier B | Candidate station IDs (operator in cohort CSV) | Split validation start (IST) | Split test start (IST) |
|---|---:|---:|---:|---|---|---|
| Delhi | 37 | 29 | 8 | site_103, site_104, site_105, site_106, site_107, site_108, site_109, site_113, site_114, site_115, site_117, site_118, site_119, site_122, site_124, site_125, site_1420, site_1421, site_1422, site_1423, site_1424, site_1425, site_1426, site_1427, site_1428, site_1429, site_1430, site_1431, site_1432, site_1434, site_1435, site_1560, site_1561, site_1562, site_1563, site_301, site_5024 | 2020-10-19T03:00:00 | 2023-02-10T13:00:00 |
| Hyderabad | 10 | 6 | 4 | site_199, site_251, site_262, site_275, site_294, site_298, site_5595, site_5596, site_5600, site_5604 | 2022-05-22T14:00:00 | 2023-11-27T19:00:00 |
| Bengaluru | 11 | 6 | 5 | site_1553, site_1554, site_1555, site_1556, site_1558, site_162, site_163, site_164, site_5681, site_5686, site_5729 | 2022-06-04T17:00:00 | 2023-12-04T08:00:00 |
| Mumbai | 29 | 13 | 16 | site_168, site_5102, site_5104, site_5106, site_5107, site_5112, site_5113, site_5115, site_5119, site_5120, site_5394, site_5396, site_5397, site_5398, site_5399, site_5400, site_5402, site_5403, site_5412, site_5413, site_5807, site_5810, site_5811, site_5814, site_5960, site_5961, site_5962, site_5963, site_5964 | 2022-06-24T14:00:00 | 2023-12-14T07:00:00 |
| Ahmedabad | 7 | 1 | 6 | site_308, site_5450, site_5451, site_5453, site_5454, site_5455, site_5456 | 2022-10-13T15:00:00 | 2024-02-09T21:00:00 |
| Chennai | 6 | 5 | 1 | site_288, site_306, site_5361, site_5363, site_5364, site_5365 | 2022-05-29T02:00:00 | 2023-12-01T01:00:00 |
| Kolkata | 7 | 6 | 1 | site_296, site_309, site_5110, site_5111, site_5126, site_5129, site_5238 | 2023-04-30T06:00:00 | 2024-05-17T03:00:00 |
| Pune (separate sensitivity) | 5 | 0 | 5 | site_5404, site_5409, site_5766, site_5988, site_5996 | 2024-03-26T22:00:00 | 2024-10-29T23:00:00 |

The seven-city group is complete with respect to Phase 4 Tier A/B and exact city/state metadata. It is not reduced to the lead stations from Phase 4. The complete row-by-row operator and coverage details are in the linked cohort CSV.

## Proposed splits and sample eligibility

For each city, derive common Phase 5 split dates from the sorted union of unique observed CPCB IST timestamps across its selected stations: 70% train, next 15% validation, final 15% test. Use these same city boundaries for station-specific and pooled experiments so comparisons are aligned. A candidate is counted only when its full input-through-target hourly sequence exists at the same station; no interpolation or cross-station concatenation is allowed. Issue and target timestamps must lie in the same split, with crossing windows purged. The common comparison cohort uses the 168-hour lookback intersection across all lookbacks for each horizon.

The following are timestamp-only potential counts aggregated across selected stations. “Test eligible” is a count of timestamps only; no PM2.5 values were read and no test feature/target windows were built or scored.

| Cohort | Lookback | Horizon | Train windows | Validation windows | Test timestamp count only | Common 168h train | Common 168h validation |
|---|---:|---:|---:|---:|---:|---:|---:|
| Seven-city primary | 24 h | +1 h | 2,043,630 | 1,084,004 | 1,180,699 | 1,012,529 | 536,037 |
| Seven-city primary | 24 h | +6 h | 1,978,039 | 1,050,269 | 1,142,802 | 993,764 | 525,346 |
| Seven-city primary | 24 h | +12 h | 1,904,560 | 1,012,263 | 1,099,848 | 971,860 | 512,909 |
| Seven-city primary | 24 h | +24 h | 1,771,200 | 943,137 | 1,021,282 | 929,753 | 489,234 |
| Seven-city primary | 48 h | +1 h | 1,761,112 | 939,197 | 1,016,967 | 1,012,529 | 536,037 |
| Seven-city primary | 48 h | +6 h | 1,712,408 | 913,626 | 987,721 | 993,764 | 525,346 |
| Seven-city primary | 48 h | +12 h | 1,656,851 | 884,341 | 954,327 | 971,860 | 512,909 |
| Seven-city primary | 48 h | +24 h | 1,553,578 | 829,547 | 892,359 | 929,753 | 489,234 |
| Seven-city primary | 168 h | +1 h | 1,012,529 | 536,037 | 563,755 | 1,012,529 | 536,037 |
| Seven-city primary | 168 h | +6 h | 993,764 | 525,346 | 552,035 | 993,764 | 525,346 |
| Seven-city primary | 168 h | +12 h | 971,860 | 512,909 | 538,368 | 971,860 | 512,909 |
| Seven-city primary | 168 h | +24 h | 929,753 | 489,234 | 512,589 | 929,753 | 489,234 |
| Pune sensitivity | 24 h | +1 h | 43,014 | 13,830 | 18,811 | 22,710 | 4,371 |
| Pune sensitivity | 24 h | +6 h | 42,017 | 13,241 | 18,071 | 22,292 | 4,205 |
| Pune sensitivity | 24 h | +12 h | 40,856 | 12,565 | 17,233 | 21,831 | 4,030 |
| Pune sensitivity | 24 h | +24 h | 38,588 | 11,337 | 15,767 | 20,937 | 3,708 |
| Pune sensitivity | 48 h | +1 h | 38,405 | 11,276 | 15,682 | 22,710 | 4,371 |
| Pune sensitivity | 48 h | +6 h | 37,504 | 10,837 | 15,143 | 22,292 | 4,205 |
| Pune sensitivity | 48 h | +12 h | 36,455 | 10,348 | 14,509 | 21,831 | 4,030 |
| Pune sensitivity | 48 h | +24 h | 34,473 | 9,433 | 13,338 | 20,937 | 3,708 |
| Pune sensitivity | 168 h | +1 h | 22,710 | 4,371 | 7,693 | 22,710 | 4,371 |
| Pune sensitivity | 168 h | +6 h | 22,292 | 4,205 | 7,508 | 22,292 | 4,205 |
| Pune sensitivity | 168 h | +12 h | 21,831 | 4,030 | 7,286 | 21,831 | 4,030 |
| Pune sensitivity | 168 h | +24 h | 20,937 | 3,708 | 6,845 | 20,937 | 3,708 |

## Candidate count and runtime estimate

The candidate grid is 6 model families × 3 lookbacks × 4 horizons = **72 model configurations** per station or fold. Deep models (LSTM/GRU/TCN) use CUDA; Linear Regression, Random Forest and XGBoost use CPU. B includes two preprocessing variants: pooled global train-only scaling and station-aware train-only scaling. C uses leave-one-station-out folds with global train-only scaling and no learned station-ID embedding for unseen stations.

| Experiment | Primary model candidates | Pune sensitivity candidates |
|---|---:|---:|
| A. Station-specific | 7,704 | 360 |
| B. Pooled city (two scaling variants) | 1,008 | 144 |
| C. Leave-one-station-out | 7,704 | 360 |
| **All three experiments** | **17,280** | included above |

In total that is **17,280 trained model candidates** and 896 station × horizon × baseline result instances (persistence and seasonal-naive). Baselines are calculated once per station/horizon and reused for comparable A/B/C comparisons.

Runtime is calibrated to the completed Phase 3 run (642.45 seconds of fit time for the full 72-candidate grid on 63,178 observations: about 328 CUDA fit seconds and 315 CPU fit seconds), scaled linearly by selected station row counts and leave-one-out training exposure. It estimates **409.6 wall hours**, including approximately **209.1 CUDA fit hours** if all designs run sequentially. The estimate is approximate; expect substantial variance from model/sample scaling, CPU Random Forest, convergence and I/O. This is not a timing benchmark.

Experiment C is the dominant cost: approximately 24.44× the station-specific primary training-data exposure because each of 107 folds retrains on the other stations in its city. A staged launch is recommended: A first, B after verifying normalization and pooling artifacts, then C as a separate run. Do not reduce the candidate grid or epochs silently.

## Model protocol

- Target: hourly CPCB CAAQM PM2.5 concentration in µg/m³. Use the approved Phase 3 hyperparameters and seed 42 as the controlled starting point; do not compare old CPU neural candidates with the CUDA run.
- A: train a separate model per station. Station-specific scaling is fitted on that station’s training split only.
- B: one separate pooled model per city; examples retain station identity and temporal history. Compare global train-only scaling with per-station train-only scaling. Traditional models use a station categorical feature; neural models use a station embedding. Inverse target transforms using the matching station’s train-only scale.
- C: leave one station completely out of training in each fold. Train on the other stations in the same city; evaluate the held-out station by validation and, only after a separate test-gate approval, by test. Do not use a learned station ID for C; use only a common global train-only scaler and station-neutral inputs so the holdout is genuinely unseen.
- Pooled training combines station-specific examples in a dataset, never the end of one station’s series with another. Require all W+H timestamps within the same station. No interpolation, synthetic records, Embassy data or city averages.
- Keep the Phase 3 Delhi run and test gate untouched. Phase 5 gets unique run IDs, independent city cut dates and a separate test gate. Validation-only model selection must freeze before any Phase 5 test evaluation.

## Test gate and review boundary

This preflight read only `station_id` and `collected_at` from verified CPCB Parquet files. The JSON records `pm25_values_read=false`, `test_targets_read_or_scored=false`, and `test_feature_windows_materialized=false`. No model was trained. The Phase 3 split/configuration/run artifacts were read only for protocol and runtime calibration. Full Phase 5 training remains unstarted pending review of this report and the linked complete cohort/window CSVs.

Supporting files: [Experiment design](PHASE5_EXPERIMENT_DESIGN.md), [machine-readable preflight](PHASE5_PREFLIGHT.json), [complete station cohort](PHASE5_STATION_COHORT.csv), [eligible timestamp-window counts](PHASE5_ELIGIBLE_WINDOWS.csv).
