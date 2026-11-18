"""Render the reviewable Phase 5 preflight from machine-readable timestamp counts."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def main() -> None:
    pre = json.loads((REPORTS / "PHASE5_PREFLIGHT.json").read_text(encoding="utf-8"))
    stations = pd.read_csv(REPORTS / "PHASE5_STATION_COHORT.csv", keep_default_na=False)
    windows = pd.read_csv(REPORTS / "PHASE5_ELIGIBLE_WINDOWS.csv")
    unverified_operators = int(stations.operator.eq("").sum())
    city_order = ["Delhi", "Hyderabad", "Bengaluru", "Mumbai", "Ahmedabad", "Chennai", "Kolkata"]
    lines = [
        "# BharatAir Phase 5 — Preflight", "",
        "**Status: preflight only; no training launched.** This report is prepared for review before any Phase 5 candidate is trained.", "",
        "## Proposed cohort", "",
        f"Selection applies the Phase 4 predeclared eligibility bands. The seven primary cities include **all Tier A and Tier B** station IDs with CPCB PM2.5 records and nonblank city and state metadata. Tier C, zero-row stations, and stations without both city and state labels are excluded. Pune is kept separate as five Tier B sensitivity stations. Official-register operator identification is unverified for {unverified_operators} of 112 selected stations; those cells are blank and flagged, never inferred from a station name.", "",
        f"**Primary: {pre['station_count_primary']} stations** (66 Tier A, 41 Tier B). **Pune sensitivity: {pre['station_count_pune']} Tier B stations.** Exact station IDs, names, operators, operator verification, first/latest timestamp, counts, missingness, and coverage months are in [PHASE5_STATION_COHORT.csv](PHASE5_STATION_COHORT.csv). The timestamp-only window inventory is [PHASE5_ELIGIBLE_WINDOWS.csv](PHASE5_ELIGIBLE_WINDOWS.csv).", "",
        "| City | Stations | Tier A | Tier B | Candidate station IDs (operator in cohort CSV) | Split validation start (IST) | Split test start (IST) |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for city in city_order:
        group = stations[(stations.cohort == "primary_seven_city_a_b") & (stations.city == city)]
        ids = ", ".join(row.station_id for row in group.itertuples())
        cuts = pre["splits"]["city_cutoffs"][city]
        tier_a = int((group.eligibility_tier == "A").sum())
        tier_b = int((group.eligibility_tier == "B").sum())
        lines.append(f"| {city} | {len(group)} | {tier_a} | {tier_b} | {ids} | {cuts['validation_start_ist']} | {cuts['test_start_ist']} |")
    pune = stations[stations.cohort == "pune_tier_b_sensitivity"]
    pune_ids = ", ".join(row.station_id for row in pune.itertuples())
    pune_cuts = pre["splits"]["city_cutoffs"]["Pune"]
    lines.append(f"| Pune (separate sensitivity) | {len(pune)} | 0 | {len(pune)} | {pune_ids} | {pune_cuts['validation_start_ist']} | {pune_cuts['test_start_ist']} |")
    lines += [
        "", "The seven-city group is complete with respect to Phase 4 Tier A/B and exact city/state metadata. It is not reduced to the lead stations from Phase 4. The complete row-by-row operator and coverage details are in the linked cohort CSV.", "",
        "## Proposed splits and sample eligibility", "",
        "For each city, derive common Phase 5 split dates from the sorted union of unique observed CPCB IST timestamps across its selected stations: 70% train, next 15% validation, final 15% test. Use these same city boundaries for station-specific and pooled experiments so comparisons are aligned. A candidate is counted only when its full input-through-target hourly sequence exists at the same station; no interpolation or cross-station concatenation is allowed. Issue and target timestamps must lie in the same split, with crossing windows purged. The common comparison cohort uses the 168-hour lookback intersection across all lookbacks for each horizon.", "",
        "The following are timestamp-only potential counts aggregated across selected stations. “Test eligible” is a count of timestamps only; no PM2.5 values were read and no test feature/target windows were built or scored.", "",
        "| Cohort | Lookback | Horizon | Train windows | Validation windows | Test timestamp count only | Common 168h train | Common 168h validation |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for cohort, label in [("primary_seven_city_a_b", "Seven-city primary"), ("pune_tier_b_sensitivity", "Pune sensitivity")]:
        grouped = windows[windows.cohort == cohort].groupby(["lookback_hours", "horizon_hours"]).agg(
            train=("train_eligible_windows", "sum"), val=("validation_eligible_windows", "sum"),
            test=("test_eligible_timestamps_only", "sum"), common_train=("common_168h_cohort_train", "sum"),
            common_val=("common_168h_cohort_validation", "sum")).reset_index()
        for row in grouped.itertuples():
            lines.append(f"| {label} | {row.lookback_hours} h | +{row.horizon_hours} h | {row.train:,} | {row.val:,} | {row.test:,} | {row.common_train:,} | {row.common_val:,} |")
    counts = pre["candidate_counts"]
    lines += [
        "", "## Candidate count and runtime estimate", "",
        "The candidate grid is 6 model families × 3 lookbacks × 4 horizons = **72 model configurations** per station or fold. Deep models (LSTM/GRU/TCN) use CUDA; Linear Regression, Random Forest and XGBoost use CPU. B includes two preprocessing variants: pooled global train-only scaling and station-aware train-only scaling. C uses leave-one-station-out folds with global train-only scaling and no learned station-ID embedding for unseen stations.", "",
        "| Experiment | Primary model candidates | Pune sensitivity candidates |", "|---|---:|---:|",
        f"| A. Station-specific | {counts['experiment_a_station_specific_primary']:,} | {counts['experiment_a_pune_sensitivity']:,} |",
        f"| B. Pooled city (two scaling variants) | {counts['experiment_b_pooled_primary']:,} | {counts['experiment_b_pooled_pune_sensitivity']:,} |",
        f"| C. Leave-one-station-out | {counts['experiment_c_leave_one_station_out_primary']:,} | {counts['experiment_c_leave_one_station_out_pune_sensitivity']:,} |",
        f"| **All three experiments** | **{counts['total_if_all_three_designs_are_run']:,}** | included above |", "",
        f"In total that is **{counts['total_if_all_three_designs_are_run']:,} trained model candidates** and {counts['baseline_station_horizon_instances_primary_and_pune']:,} station × horizon × baseline result instances (persistence and seasonal-naive). Baselines are calculated once per station/horizon and reused for comparable A/B/C comparisons.", "",
        f"Runtime is calibrated to the completed Phase 3 run (642.45 seconds of fit time for the full 72-candidate grid on 63,178 observations: about 328 CUDA fit seconds and 315 CPU fit seconds), scaled linearly by selected station row counts and leave-one-out training exposure. It estimates **{pre['runtime_estimate']['total_all_designs_estimated_wall_hours']:.1f} wall hours**, including approximately **{pre['runtime_estimate']['total_all_designs_estimated_cuda_fit_hours']:.1f} CUDA fit hours** if all designs run sequentially. The estimate is approximate; expect substantial variance from model/sample scaling, CPU Random Forest, convergence and I/O. This is not a timing benchmark.", "",
        f"Experiment C is the dominant cost: approximately {pre['runtime_estimate']['primary_loso_training_data_multiplier_vs_A']:.2f}× the station-specific primary training-data exposure because each of 107 folds retrains on the other stations in its city. A staged launch is recommended: A first, B after verifying normalization and pooling artifacts, then C as a separate run. Do not reduce the candidate grid or epochs silently.", "",
        "## Model protocol", "",
        "- Target: hourly CPCB CAAQM PM2.5 concentration in µg/m³. Use the approved Phase 3 hyperparameters and seed 42 as the controlled starting point; do not compare old CPU neural candidates with the CUDA run.",
        "- A: train a separate model per station. Station-specific scaling is fitted on that station’s training split only.",
        "- B: one separate pooled model per city; examples retain station identity and temporal history. Compare global train-only scaling with per-station train-only scaling. Traditional models use a station categorical feature; neural models use a station embedding. Inverse target transforms using the matching station’s train-only scale.",
        "- C: leave one station completely out of training in each fold. Train on the other stations in the same city; evaluate the held-out station by validation and, only after a separate test-gate approval, by test. Do not use a learned station ID for C; use only a common global train-only scaler and station-neutral inputs so the holdout is genuinely unseen.",
        "- Pooled training combines station-specific examples in a dataset, never the end of one station’s series with another. Require all W+H timestamps within the same station. No interpolation, synthetic records, Embassy data or city averages.",
        "- Keep the Phase 3 Delhi run and test gate untouched. Phase 5 gets unique run IDs, independent city cut dates and a separate test gate. Validation-only model selection must freeze before any Phase 5 test evaluation.", "",
        "## Test gate and review boundary", "",
        "This preflight read only `station_id` and `collected_at` from verified CPCB Parquet files. The JSON records `pm25_values_read=false`, `test_targets_read_or_scored=false`, and `test_feature_windows_materialized=false`. No model was trained. The Phase 3 split/configuration/run artifacts were read only for protocol and runtime calibration. Full Phase 5 training remains unstarted pending review of this report and the linked complete cohort/window CSVs.", "",
        "Supporting files: [Experiment design](PHASE5_EXPERIMENT_DESIGN.md), [machine-readable preflight](PHASE5_PREFLIGHT.json), [complete station cohort](PHASE5_STATION_COHORT.csv), [eligible timestamp-window counts](PHASE5_ELIGIBLE_WINDOWS.csv).",
    ]
    (REPORTS / "PHASE5_PREFLIGHT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORTS / 'PHASE5_PREFLIGHT.md'} with {len(lines)} lines")


if __name__ == "__main__":
    main()
