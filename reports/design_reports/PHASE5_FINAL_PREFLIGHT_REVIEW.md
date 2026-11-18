# BharatAir Phase 5 — Final Preflight Review

**Status: NOT READY for training.** This review resolves the design questions and provides timestamp-only feasibility, but a multi-station execution runner and explicit disposition for below-floor configurations remain outstanding. No training was launched; no test PM2.5 values, test features, predictions, or scores were accessed. Phase 3 and Phase 4 artifacts were read only.

## Scope and preserved cohorts

The complete Phase 4 Tier A/B cohort with exact city and state metadata is retained: **107 primary stations** across Delhi 37, Hyderabad 10, Bengaluru 11, Mumbai 29, Ahmedabad 7, Chennai 6, Kolkata 7. Tier split is 66 A / 41 B. Pune remains a separate **five-station Tier B sensitivity cohort**. No lead-station-only restriction was applied. Missing/ambiguous metadata is not used to guess city membership. Operator is unverified for 15 of 112 selected stations, flagged in the cohort inventory.

The source data for feasibility came from verified CPCB CAAQM PM2.5 extracts. Feasibility generation used station IDs and timestamps only; it did not read PM2.5 values. Its machine-readable summary records `pm25_values_read=false`, `test_targets_read_or_scored=false`, and `test_feature_windows_materialized=false`.

## Split/window rule

Forecast issue `t` is the last input timestamp. Inputs are exactly L consecutive hourly same-station observations ending at `t`; target is same-station PM2.5 at `t+h`. There can be no feature later than `t`. The full input-through-target sequence must be present without filling. Issue and target must be in the same chronological partition; input history may cross backward into earlier partitions as known causal history. This rule applies to A/B/C. Full semantics and the separate test gate are in [PHASE5_SPLIT_WINDOW_POLICY.md](PHASE5_SPLIT_WINDOW_POLICY.md).

## Eligibility floors and observed feasibility

Floors were defined before examining model results. For each A station/configuration, require at least 5,000 training windows and at least 1,000 common validation issue times per horizon. For each B city/configuration, require at least 20,000 training examples and 2,500 common validation examples. For each C leave-one-station-out fold, require at least 20,000 peer training examples and 1,000 held-out station common validation examples. These are planning adequacy thresholds, not guarantees of statistical power. Test counts are timestamp-only and have no adequacy role.

| Cohort/design | Config rows passing / total | Candidate fits passing / total | Below-floor candidate fits |
|---|---:|---:|---:|
| Primary A, 107 stations | 911 / 1,284 | 5,466 / 7,704 | 2,238 |
| Pune A, 5 stations | 24 / 60 | 144 / 360 | 216 |
| Primary B, 7 city pools × 12 configs | 84 / 84 | 1,008 / 1,008 | 0 |
| Pune B, one pool × 12 configs | 12 / 12 | 144 / 144 | 0 |
| Primary C, 107 held-out folds | 1,081 / 1,284 | 6,486 / 7,704 | 1,218 |
| Pune C, 5 held-out folds | 14 / 60 | 84 / 360 | 276 |
| **All designs** | — | **13,332 / 17,280** | **3,948** |

The per-station × lookback × horizon CSV contains train, validation, timestamp-only test, common-lookback and A/B/C adequacy fields for all 112 stations. For primary A, 45 station IDs have at least one shortfall; 16 have zero training windows for at least one configuration and 2 have zero common validation windows. For Pune A, site_5988 and site_5996 have zero training windows; site_5766, site_5988 and site_5996 have a shortfall. The exact flags and station identities are in the CSV and summary JSON.

**Do not interpret “13,332 passing” as permission to drop 3,948 candidates.** The approved design says retain all stations and the full grid, while the new predeclared floors identify configurations whose evidence is inadequate. Before training, the owner must decide whether below-floor configurations are retained and labeled underpowered/ineligible for selection, or whether a formally revised cohort/grid is approved. No station is silently removed, and no floor may be lowered after seeing results.

## Candidate counts and runtime reconciliation

The gross design count remains **17,280 trained candidates**: A 8,064 total (7,704 primary + 360 Pune), B 1,152 (1,008 + 144; two normalization variants), C 8,064 (7,704 + 360). There are 896 station×horizon baseline result instances. The preflight's combined estimate remains approximately **409.6 wall hours**, including **209.1 CUDA fit hours**, with stated uncertainty of roughly 0.7×–1.8× and no guarantee. It is extrapolated from Phase 3 runtime and is not a benchmark. The A/B/C estimates are 15.2 h / 30.2 h / 364.3 h including Pune, respectively (rounding may differ from component sums).

The proposed representative A pilot keeps the complete 72-candidate grid for four stations (288 fits, plus 32 baseline instances) and six preregistered repeat fits for reproducibility. The updated row-scaled estimate is about **1.20 h before repeats/monitoring overhead**. An earlier approximately 33.9-minute estimate used a different scale basis; it is superseded because it does not reconcile with the preflight's 14.9-hour primary-A estimate. Runtime remains uncertain and the pilot must measure it.

## Reporting protocol

Report each candidate's station-level validation metrics and sample count, plus (1) median across stations, (2) observation-weighted aggregate over comparable validation predictions, and (3) city-level summaries. Stratify Tier A and Tier B; keep Pune separate. Report improvements against persistence and seasonal-naive on the same station/horizon/issue-time cohort, absolute and percentage, with undefined percentage cases explicitly handled. Distinguish per-station best candidate selections from model-family comparisons aggregated over stations; do not let the larger stations dominate the median. Disclose that selecting among many candidates on the same validation interval creates selection optimism and that stations are not independent random samples. Report uncertainty/sample sizes and avoid causal claims. Exact model-selection tables and caveats must be frozen before any test release.

## Required experiment components

- **A:** independently fit 72 candidates per station.
- **B:** separate pooled model per city and normalization variant; keep station sequences separate, preserve station identity where appropriate, and compare against A on matched station validation cohorts.
- **C:** city-local leave-one-station-out folds; held-out station labels and measurements cannot fit the model or scaler.
- Baselines: station-specific persistence and seasonal naive, aligned to the same forecast issues; no future observation may be used by seasonal naive.
- Target/horizons/lookbacks remain PM2.5 µg/m³, +1/+6/+12/+24 hours, 24/48/168 hours. No interpolation or automatic outlier deletion.

## Blocking issues before any pilot

1. The current Phase 3 runner is hard-coded to one canonical Delhi dataset and cannot execute this panel design. A dedicated Phase 5 runner is required.
2. The feasibility CSV's “common” fields must be checked against exact common issue-time intersections across all lookbacks, not only counts, before finalizing matched comparisons.
3. Below-floor candidate disposition needs an explicit decision consistent with retaining the full cohort/grid.
4. The station-aware pooled scaling, categorical/embedding identity handling, and unseen-station C fallback need implementation and leakage tests.
5. A validation-only test-value lock needs tests proving no test value load, feature construction, predictions, or scoring; test-gate timestamps alone do not establish that.
6. Runtime estimates and the four-station pilot estimate are rough and should be replaced by measured telemetry after the pilot.
7. Official operator verification is absent for 15 stations; keep those marked unknown and report sensitivity if needed.

## Decision

**Phase 5 preflight outcome: CONDITIONAL GO for a validation-only compute pilot after the blocking runner, leakage, and below-floor handling issues are resolved and reviewed. No authorization to start the pilot is implied by this report.** Full training remains a separate decision. The separate Phase 5 test gate stays closed. Phase 3/4 artifacts and the canonical dataset were not modified.

## Deliverables

- [Station feasibility table](PHASE5_STATION_FEASIBILITY.csv) (1,344 station×lookback×horizon rows)
- [Split/window policy](PHASE5_SPLIT_WINDOW_POLICY.md)
- [Pilot plan](PHASE5_PILOT_PLAN.md)
- [Timestamp-only feasibility summary](PHASE5_FEASIBILITY_SUMMARY.json)
