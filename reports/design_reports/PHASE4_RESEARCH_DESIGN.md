# Phase 4 Research Design Recommendations

## Data-supported scope

The CPCB CAAQM PM2.5 extract contains 549 station IDs in 245 cities. With the declared screening tiers, 310 stations are Tier A, 165 Tier B and 78 Tier C. Seven of the eight target-city lead stations below are Tier A; Pune's longest-history candidate is Tier B, with two more recent but shorter Tier B options. This is adequate for a carefully bounded multi-city historical study through 2025-09-01. It is not evidence of India-wide representativeness and provides no CPCB observations after 2025-09-01.

Use concentration in µg/m³ as the target. Preserve station-level CPCB series and exact IDs. Embassy monitor series stay in a separate dataset and experiment cohort.

## Design options

### A. One strong station per city, separate city forecasts

**Feasible; recommended for the first expansion.** Fit and evaluate independent city/station models, with metrics per station and per horizon. Use `site_1422` Dwarka-Sector 8 as the Delhi continuity anchor for direct comparison with Phase 3; include `site_113` Shadipur as a separate Delhi sensitivity station because it offers longer history. For other cities use the strongest observed candidates in the common-period report. In Pune, predeclare whether priority is history (`site_292`) or current coverage (`site_5404`); show the other as sensitivity rather than choosing after validation results.

This design avoids combining different monitors into a synthetic city mean. Date ranges and completeness differ by city, so compare model skill against same-station baselines and report the eligible validation/test sample count for each location.

### B. Pooled multi-station panel

**Feasible with safeguards; second-stage option.** Retain each station as a separate time series and include a station identity or validated station metadata representation. Do not average site values. Create examples only when every timestamp required for the input window and forecast target exists at that same station. Keep gaps missing and report how many examples each station contributes.

Fit all preprocessing and scaling on training observations only. A global scaler is a different estimand from station-specific scalers; choose and preregister one, then report it. If station-specific scaling is used, fit each station's transform on that station's training partition only. For any learned city/operator encodings, derive mappings from training stations only. Compare pooled results to station-specific persistence and seasonal-naive baselines; an overall pooled metric alone can hide large city differences.

### C. Leave-one-city-out generalization

**Feasible, but only for a carefully sized subset and with city-stratified reporting.** Hold every station in a selected city out of training and model selection. Do not allow station, coordinate, city, or operator identifiers from the held-out city to leak into fitted transforms. Evaluate each held-out city separately, and include cities with enough chronological history and complete windows. A broad count of 175 Tier A cities does not mean that every city has equivalent monitor quality or independent geographic coverage.

### D. Leave-one-station-out generalization

**Feasible and useful before city transfer.** Hold out one station while retaining other stations from the same city in training. This tests transfer to a new monitor in a known urban context; it is not city-level generalization. Report per-held-out-station results and compare against that station's own persistence/seasonal-naive scores, calculated only where valid timestamps exist.

## Chronology, purging and leakage controls

- Keep the approved Phase 3 horizons (+1, +6, +12, +24 h), input windows (24, 48, 168 h), hourly target definition, and the no-imputation rule for a follow-up experiment unless separately reviewed.
- Split chronologically by station; never random-split windows. Freeze date boundaries before model fitting. Do not construct a training example whose target crosses a split boundary. Carry forward the approved boundary-purging implementation; use its maximum-window/maximum-horizon purge consistently for every model and station.
- A station's observed history may supply lagged inputs only when those observations would be available at prediction time. Never use future station observations, future-based normalization, or cross-network data to bridge missing timestamps.
- Fit scalers and any data-derived transforms on the training partition only. Compare models on exactly the same station-specific eligible timestamps within each horizon.
- Keep final test evaluation behind the separate Phase 3 test gate. Validation results are for model selection only. This audit did not access Phase 3 test targets or construct test windows.
- Retain CPCB operator/source identity in metadata. DPCC, state boards, CPCB and IITM operate different stations inside the CAAQM feed; include operator in station-level reporting and consider operator-stratified sensitivity checks.

## Baselines and reporting

Use persistence and seasonal-naive baselines per station and horizon, evaluated on the same timestamps as each model. Also compare the selected Phase 3 Delhi model to a fresh result only when the dataset fingerprint, station, feature definitions, split/purge, preprocessing and metric implementation are identical. No legacy checkpoint or result is promoted by this audit.

For each city/station and horizon report MAE, RMSE, observation count, eligible window count, date range, coverage, missingness, and improvement against both simple baselines. Report medians or distributions across cities in addition to pooled counts; avoid weighting the result toward cities with the most monitors or observations. Keep extreme PM2.5 observations, including values ≥500 µg/m³, and provide a separately labeled sensitivity analysis rather than automatic removal.

## Recommendation

Proceed with **Design A** as the first multi-city comparison, retaining `site_1422` for the Delhi bridge to Phase 3 and one predeclared station per additional city. Treat Pune as a Tier B sensitivity case or defer it from the primary cohort. Use Design D next to test station transfer. Move to pooled Design B or leave-one-city-out Design C only after city/station sample counts and held-out validation results show that identity and missingness do not dominate performance. This is a research-design recommendation only; no model fitting was performed.
