# Phase 5 Split and Window Policy

Status: proposed frozen policy for approval before any Phase 5 run. This policy applies identically to Experiments A, B and C.

## Time and example definitions

All source timestamps are treated as naive India Standard Time (IST), exactly as represented in the verified CPCB extract; no UTC conversion or daylight adjustment is applied. A station is identified by its exact `site_*` identifier and remains an independent hourly series.

For lookback `L` and forecast horizon `h`:

- **Forecast issue time `t`** is the timestamp of the last observed PM2.5 input and the time at which the forecast is issued.
- **Input times** are `t-(L-1)h, ..., t-1h, t`, inclusive, exactly L hourly observations.
- **Target time** is `t+h` and target is that station's CPCB CAAQM PM2.5 concentration in µg/m³.
- Nothing later than `t` may enter the feature vector, scaler state, or any forecast-time computation.

An example is eligible only when every hourly timestamp from the first input through target exists at that same station. No imputation, interpolation, nearest-time matching, carry-forward, or synthetic records are allowed. Stations are never concatenated into continuous time series.

## Split and history semantics

Use the frozen city cutoffs in `PHASE5_PREFLIGHT.json`, derived from sorted unique timestamps across the selected city stations: 70% train, next 15% validation, final 15% test; Pune is a separate cohort with separate cutoffs. For every example, **issue time and target time must both be in the same split**. If they straddle a split boundary, purge the example. The input lookback may extend backward across a split boundary because it represents observations available by issue time. It may never extend forward past issue time. This is a rolling-origin evaluation policy, not a requirement that all input history belong to the target's partition.

This rule is uniform in A/B/C. For B, each station's examples keep their own history and station identity; pooling combines examples only. For C, the held-out station contributes no values to model/scaler fitting; its observed history up to a validation issue may be used as causal input only. All transforms, learned station mappings and model parameters are fitted from permitted training data only. C must use an explicitly defined unknown/global scaling path for held-out stations; it cannot fit station scaling from validation history.

The station/horizon comparison cohort is the intersection of eligible issue times for L=24,48,168 at each station and horizon. The feasibility file's common columns are based on L=168 counts. The implementation must verify the exact issue-time intersection rather than assume aggregate counts alone prove equality.

## Test gate

The Phase 5 validation path must stop before reading test PM2.5 values, constructing test features/windows, predicting test targets, scoring test outcomes, or making test-based selection decisions. It may use frozen split timestamps and, for feasibility planning only, timestamp-only counts that do not load PM2.5 values. Validation results and the selected model set must be saved, checksum/provenance verified, audited and frozen. Test use requires a separate explicit `--evaluate-test` action and separately recorded gate state. No training runner currently implements this multi-station policy, so these requirements are a pre-launch blocker until implemented and tested. Phase 3/4 gates and artifacts remain untouched.
