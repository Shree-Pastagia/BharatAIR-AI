# BharatAir Phase 5 — Multi-Station CPCB Experiment Design

**Status: design/preflight only. Training has not started.** The complete cohort and timestamp-only window estimates are available for review in [PHASE5_PREFLIGHT.md](PHASE5_PREFLIGHT.md), [PHASE5_STATION_COHORT.csv](PHASE5_STATION_COHORT.csv), [PHASE5_ELIGIBLE_WINDOWS.csv](PHASE5_ELIGIBLE_WINDOWS.csv), and [PHASE5_PREFLIGHT.json](PHASE5_PREFLIGHT.json).

## 1. Cohort definition

### Seven-city primary cohort

Use every station in the Phase 4 inventory that meets all conditions:

1. The audited source is XKDR `cpcb_caaqm` and pollutant is PM2.5.
2. At least one observed PM2.5 value exists.
3. City and state metadata are both present and city exactly matches Delhi, Hyderabad, Bengaluru, Mumbai, Ahmedabad, Chennai or Kolkata.
4. The station meets the predeclared Phase 4 Tier A or Tier B screen.

Tier A criteria: at least two represented years; at least 70% active-span hourly coverage; at least 75% of active months at ≥80% hourly coverage; at least 60% of active Jan-2024–Sep-2025 months at ≥80%; and no duplicate, off-hour, null/nonnumeric or negative observations. Tier B criteria: at least one represented year; at least 50% active-span coverage; at least 50% of active months at ≥80%. Tier C is excluded from the primary cohort. These are Phase 4 screening rules, not regulatory grades.

This yields **107 primary stations**: Delhi 37 (29 A, 8 B); Hyderabad 10 (6 A, 4 B); Bengaluru 11 (6 A, 5 B); Mumbai 29 (13 A, 16 B); Ahmedabad 7 (1 A, 6 B); Chennai 6 (5 A, 1 B); Kolkata 7 (6 A, 1 B). This includes all qualifying Phase 4 stations, not only the city lead stations.

Stations missing city or state metadata are excluded from city membership. No city is inferred from a station name, coordinates or operator. Operator is retained from an exact CPCB register match; if no match exists, the cohort CSV records the operator as unverified/blank. CPCB CAAQM may include CPCB, DPCC, state board, IITM, IMD or other operators; network source and operator are distinct fields.

### Pune sensitivity cohort

Keep Pune outside the seven-city primary analysis. Include all **five Tier B** Pune stations with PM2.5 and valid city/state metadata as a separate sensitivity cohort. Report their lower tier, missingness and differing recency individually; do not pool them into another city.

## 2. Common model grid and baselines

For each station-specific model, pooled city model, or leave-one-station-out fold, use:

- Linear Regression, Random Forest, XGBoost, LSTM, GRU, TCN.
- Input windows: 24, 48, 168 hours.
- Forecast horizons: +1, +6, +12, +24 hours.
- 72 configurations per station, pool or fold.
- Persistence and seasonal-naive baselines, calculated per station and horizon on the same eligible issue times. They are not fitted models and can be reused for A/B/C comparisons.

Use PM2.5 concentration in µg/m³. Retain extreme values and report an explicit ≥500 µg/m³ sensitivity analysis; do not automatically remove them. Use the Phase 3 model hyperparameters, seed 42 and optimizer settings as the controlled starting point. Deep models use CUDA and traditional models use CPU. The candidate run must record its actual runtime/device and per-candidate memory telemetry.

## 3. Independent Phase 5 chronological splits

Phase 5 uses new cut dates, separate from Phase 3. Within each city, construct cut dates from the sorted union of unique CPCB PM2.5 timestamps for that city's selected stations: first 70% train, next 15% validation, final 15% test. Apply the same city cut dates to every station-specific and pooled model in that city. Pune gets its own cuts. Exact proposed boundaries are in `PHASE5_PREFLIGHT.json` and `PHASE5_STATION_COHORT.csv`.

Create an example only if every required hourly observation exists from the first input timestamp through the forecast target at the *same station*. Never interpolate gaps or carry a window across stations. The issue and target timestamp must be in the same split; purge boundary-crossing examples. To compare 24/48/168-hour windows fairly, use the intersection of eligible issue times across all three windows for each station and horizon, as in the Phase 3 comparison rule.

The preflight counts use `station_id` and `collected_at` columns only. Its test counts are timestamp-eligibility counts, not test observations. The runner must separately enforce a validation-only default: no test values, test features, predictions or metrics until model selection is frozen, audited and explicitly released through the independent Phase 5 test gate.

## 4. Experiment A — station-specific models

Fit each of the 72 candidates independently for each of the 107 primary stations (7,704 model runs) and each of the five Pune stations (360 sensitivity runs). No station identity feature is needed within an independent series. Neural input and target scaling is fit using only that station's training split; inverse-scale predictions with the matching train-only scaler.

Report candidate metrics per station and aggregate by city, with Tier A and Tier B results kept visible. Report sample counts, dates, missingness and baseline improvements. City summaries should include the distribution or median of station results in addition to any pooled row-weighted score.

## 5. Experiment B — pooled city models

Train a separate model for each city using its eligible stations, producing 7 city models per configuration family. Pune is a separate pooled sensitivity model. Pool training examples, not time series: every example remains linked to its station ID and its own past observations. Do not append one station's final observation to another station's first observation.

Run two predeclared normalization variants:

1. **Global train-only scaling:** fit transforms from the pooled training portion only.
2. **Station-aware train-only scaling:** fit per-station transforms using only that station's training portion, retain station ID, and inverse-transform with the corresponding station's train-only target scale.

For traditional models, represent station identity with a training-defined categorical encoding. For LSTM/GRU/TCN, use a station embedding alongside each station's own sequence and calendar features. Do not fit categories or scalers using validation/test measurements. Compare both variants to Experiment A on a common per-station validation cohort. B costs 1,008 primary model runs (two variants) and 144 Pune sensitivity runs.

## 6. Experiment C — unseen-station generalization

Use city-local leave-one-station-out folds. In each fold, remove the held-out station's full labeled history from training and fit on the remaining eligible stations in that city. Score validation windows for the held-out station and report every held-out station and its city. This yields 107 primary folds and five Pune sensitivity folds (7,704 and 360 model candidates respectively).

Do not use a learned station-ID embedding for C: a held-out station has no training identity. Use station-neutral observed lag/time features and a global scaler fit only on non-held-out training stations. The held-out station's prior observed hourly readings may be used as causal inputs at its validation issue time, but not as training labels or scaler-fitting observations. If a future version adds static station features, only use fields verified for every included fold and freeze mappings from training stations; do not guess missing coordinates or operators.

## 7. Pooled leakage, missingness and comparisons

- Keep station histories, timestamps and windows grouped by station throughout preparation, fitting, validation and reporting.
- Use the common city cut dates for A and B. For C, train only on non-held-out stations and validate on the held-out station under the same city cut dates.
- Fit all preprocessing on training records only. Do not use validation or test to calculate scalers, imputations, categorical vocabularies or feature selection.
- No imputation or synthetic observations. Omit examples whenever required input/target hours are absent.
- Keep persistence and seasonal-naive calculations station-specific. Seasonal naive must use only an observation available no later than issue time, consistent with the approved Phase 3 definition.
- Use identical eligible timestamps across lookbacks/models within each horizon when reporting direct comparisons. Report by city, station, tier, operator and forecast horizon; distinguish macro station averages from observation-weighted summaries.
- Preserve high values. Report extreme-event counts and metrics as a separately specified validation/test sensitivity without deleting records.

## 8. Candidate count and execution staging

The three experiments together imply **17,280 trained model candidates**: A 7,704 primary + 360 Pune; B 1,008 primary + 144 Pune; C 7,704 primary + 360 Pune. There are 896 station × horizon × baseline combinations across the 112 stations. The Phase 3-calibrated rough estimate is approximately 409.6 wall hours and 209.1 CUDA fit hours if run sequentially; estimated uncertainty is substantial and Experiment C dominates at roughly 24.44 times the primary A training-data exposure. Full assumptions are in `PHASE5_PREFLIGHT.json`.

Run A, B and C as separate isolated runs with unique IDs and resumable, provenance-checked artifacts. Recommended order is A first, then B after validating both normalization paths and pooled memory behavior, then C as a distinct generalization study. The 8 GB GPU has headroom in the one-station Phase 3 run, but pooled batches and folds still require streaming data to the device rather than materializing the entire pooled window set in VRAM. Do not reduce model grid, epochs, batch size or candidate folds silently. Before a real launch, perform a separate synthetic/small validation-only infrastructure check and recheck storage, CUDA runtime and complete artifact verification.

## 9. Preservation and test gates

Phase 3 artifacts, including the canonical Delhi dataset, Phase 3 splits, checkpoints, validation results and its closed test gate, remain untouched. Phase 5 has separate datasets/artifacts, manifests, split fingerprints and test-gate state. Model selection uses validation only. Test evaluation is a separate explicit operation after selections, validation summaries and provenance have been reviewed and frozen. No Phase 5 training or test scoring has occurred during this design/preflight.
