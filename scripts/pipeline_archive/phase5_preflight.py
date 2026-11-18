"""Timestamp-only Phase 5 station/window preflight; does not read PM2.5 values or train models."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data" / "phase4_audit"
RAW = AUDIT / "raw_cpcb_pm25" / "yearly"
REPORTS = ROOT / "reports"
CITIES = ["Delhi", "Hyderabad", "Bengaluru", "Mumbai", "Ahmedabad", "Chennai", "Kolkata"]
LOOKBACKS = [24, 48, 168]
HORIZONS = [1, 6, 12, 24]
HOUR_NS = 3_600_000_000_000


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    eligibility_path = REPORTS / "PHASE4_STATION_ELIGIBILITY.csv"
    eligibility = pd.read_csv(
        eligibility_path,
        usecols=["station_id", "station_name", "state", "city", "operator_official_register",
                 "operator_status", "first_pm25_ist", "last_pm25_ist", "pm25_observation_rows",
                 "missingness_pct_active_span", "months_coverage_ge_80pct", "months_coverage_ge_90pct",
                 "eligibility_tier"],
        keep_default_na=False,
    )
    eligible = eligibility[
        eligibility["city"].isin(CITIES)
        & eligibility["state"].ne("")
        & eligibility["city"].ne("")
        & eligibility["pm25_observation_rows"].astype(int).gt(0)
        & eligibility["eligibility_tier"].isin(["A", "B"])
    ].copy()
    pune = eligibility[
        eligibility["city"].eq("Pune")
        & eligibility["state"].ne("")
        & eligibility["pm25_observation_rows"].astype(int).gt(0)
        & eligibility["eligibility_tier"].eq("B")
    ].copy()
    cohort = pd.concat([eligible.assign(cohort="primary_seven_city_a_b"), pune.assign(cohort="pune_tier_b_sensitivity")], ignore_index=True)
    if cohort.station_id.duplicated().any():
        raise ValueError("Duplicate station IDs in selected cohorts")
    selected_ids = set(cohort.station_id)

    station_times: dict[str, list[np.ndarray]] = {sid: [] for sid in selected_ids}
    for path in sorted(RAW.glob("*.parquet")):
        pf = pq.ParquetFile(path)
        for rg in range(pf.num_row_groups):
            # Values are deliberately not read. This preflight counts timestamp-only eligible windows.
            table = pf.read_row_group(rg, columns=["station_id", "collected_at"])
            df = table.to_pandas()
            df = df[df.station_id.isin(selected_ids)]
            if not df.empty:
                for sid, group in df.groupby("station_id", sort=False):
                    ts = pd.to_datetime(group.collected_at, errors="coerce").dropna().drop_duplicates().sort_values()
                    station_times[str(sid)].append(ts.to_numpy(dtype="datetime64[ns]").astype("int64"))

    times_by_station: dict[str, np.ndarray] = {}
    for sid, pieces in station_times.items():
        arr = np.unique(np.concatenate(pieces)) if pieces else np.array([], dtype=np.int64)
        if arr.size and np.any(np.diff(arr) % HOUR_NS != 0):
            raise ValueError(f"Unexpected off-hour timestamp for {sid}")
        times_by_station[sid] = arr

    # City-wide cut dates keep A/B validation cohorts comparable and prevent pooled training
    # examples from using later dates at one site than validation dates at another.
    city_cutoffs = {}
    for city in CITIES + ["Pune"]:
        ids = cohort.loc[cohort.city.eq(city), "station_id"].tolist()
        union = np.unique(np.concatenate([times_by_station[sid] for sid in ids if times_by_station[sid].size]))
        if not union.size:
            raise ValueError(f"No timestamps for selected cohort {city}")
        val_ns = int(union[int(np.floor(0.70 * len(union)))])
        test_ns = int(union[int(np.floor(0.85 * len(union)))])
        city_cutoffs[city] = (val_ns, test_ns, len(union))

    def count_windows(sid: str, lookback: int, horizon: int, val_ns: int, test_ns: int):
        arr = times_by_station[sid]
        if not arr.size:
            return {"train": 0, "validation": 0, "test": 0, "purged": 0}
        # Break at every missing hour. A candidate is eligible only if every hour from
        # the first input through the forecast target is genuinely observed.
        breaks = np.flatnonzero(np.diff(arr) != HOUR_NS) + 1
        bounds = np.concatenate(([0], breaks, [len(arr)]))
        counts = {"train": 0, "validation": 0, "test": 0, "purged": 0}
        for left, right in zip(bounds[:-1], bounds[1:]):
            length = int(right-left)
            first_issue = int(left + lookback - 1)
            last_issue = int(right - horizon - 1)
            if first_issue > last_issue:
                continue
            issue_pos = np.arange(first_issue, last_issue + 1)
            target_pos = issue_pos + horizon
            issue_ns = arr[issue_pos]
            target_ns = arr[target_pos]
            train = (issue_ns < val_ns) & (target_ns < val_ns)
            val = (issue_ns >= val_ns) & (target_ns < test_ns)
            test = (issue_ns >= test_ns)
            counts["train"] += int(train.sum())
            counts["validation"] += int(val.sum())
            counts["test"] += int(test.sum())
            counts["purged"] += int(len(issue_pos) - train.sum() - val.sum() - test.sum())
        return counts

    window_rows = []
    station_rows = []
    common_counts = {}
    for _, row in cohort.iterrows():
        sid, city = row.station_id, row.city
        arr = times_by_station[sid]
        val_ns, test_ns, city_unique_times = city_cutoffs[city]
        station_rows.append({
            "station_id": sid,
            "station_name": row.station_name,
            "city": city,
            "state": row.state,
            "operator": row.operator_official_register,
            "operator_status": row.operator_status,
            "network": "CPCB CAAQM",
            "cohort": row.cohort,
            "eligibility_tier": row.eligibility_tier,
            "first_pm25_ist": row.first_pm25_ist,
            "last_pm25_ist": row.last_pm25_ist,
            "pm25_observation_rows": int(row.pm25_observation_rows),
            "distinct_hourly_timestamps": int(len(arr)),
            "missingness_pct_active_span": float(row.missingness_pct_active_span),
            "months_coverage_ge_80pct": int(row.months_coverage_ge_80pct),
            "months_coverage_ge_90pct": int(row.months_coverage_ge_90pct),
            "city_split_validation_start_ist": pd.Timestamp(val_ns).isoformat(),
            "city_split_test_start_ist": pd.Timestamp(test_ns).isoformat(),
            "city_union_unique_timestamps": city_unique_times,
        })
        for h in HORIZONS:
            common = count_windows(sid, max(LOOKBACKS), h, val_ns, test_ns)
            common_counts[(sid, h)] = common
            for w in LOOKBACKS:
                c = count_windows(sid, w, h, val_ns, test_ns)
                window_rows.append({
                    "station_id": sid, "station_name": row.station_name, "city": city,
                    "cohort": row.cohort, "eligibility_tier": row.eligibility_tier,
                    "lookback_hours": w, "horizon_hours": h,
                    "train_eligible_windows": c["train"],
                    "validation_eligible_windows": c["validation"],
                    "test_eligible_timestamps_only": c["test"],
                    "purged_cross_boundary_windows": c["purged"],
                    "common_168h_cohort_train": common["train"],
                    "common_168h_cohort_validation": common["validation"],
                    "common_168h_cohort_test_timestamp_only": common["test"],
                })

    station_df = pd.DataFrame(station_rows).sort_values(["cohort", "city", "station_id"])
    windows_df = pd.DataFrame(window_rows).sort_values(["cohort", "city", "station_id", "horizon_hours", "lookback_hours"])
    station_df.to_csv(REPORTS / "PHASE5_STATION_COHORT.csv", index=False, encoding="utf-8")
    windows_df.to_csv(REPORTS / "PHASE5_ELIGIBLE_WINDOWS.csv", index=False, encoding="utf-8")

    city_counts = station_df.groupby(["cohort", "city"]).size().to_dict()
    model_configs_per_series = len(LOOKBACKS) * len(HORIZONS) * 6
    primary_station_specific = int((station_df.cohort == "primary_seven_city_a_b").sum()) * model_configs_per_series
    pune_station_specific = int((station_df.cohort == "pune_tier_b_sensitivity").sum()) * model_configs_per_series
    city_pools = len(CITIES)
    pooled_candidates = city_pools * model_configs_per_series * 2  # global vs train-only station-aware scaling
    pune_pool_candidates = model_configs_per_series * 2
    # City-local leave-one-station-out folds require at least one remaining training station.
    primary_loso_folds = int(sum(int(city_counts.get(("primary_seven_city_a_b", c), 0)) if int(city_counts.get(("primary_seven_city_a_b", c), 0)) >= 2 else 0 for c in CITIES))
    pune_station_count = int(city_counts.get(("pune_tier_b_sensitivity", "Pune"), 0))
    pune_loso_folds = pune_station_count if pune_station_count >= 2 else 0
    primary_loso_candidates = primary_loso_folds * model_configs_per_series
    pune_loso_candidates = pune_loso_folds * model_configs_per_series
    candidate_counts = {
        "configs_per_station_or_fold": model_configs_per_series,
        "experiment_a_station_specific_primary": primary_station_specific,
        "experiment_a_pune_sensitivity": pune_station_specific,
        "experiment_b_pooled_primary": pooled_candidates,
        "experiment_b_pooled_pune_sensitivity": pune_pool_candidates,
        "experiment_c_leave_one_station_out_primary": primary_loso_candidates,
        "experiment_c_leave_one_station_out_pune_sensitivity": pune_loso_candidates,
        "total_if_all_three_designs_are_run": primary_station_specific + pune_station_specific + pooled_candidates + pune_pool_candidates + primary_loso_candidates + pune_loso_candidates,
        "baseline_station_horizon_instances_primary_and_pune": int(len(station_df) * len(HORIZONS) * 2),
    }

    # Runtime estimate calibrated from the completed Phase 3 run (72 candidates, same
    # model families/settings, 63,178 observed timestamps, 632.45 fit seconds).
    phase3_seconds = 642.4489581
    phase3_cuda_seconds = 89.6540392 + 87.8647004 + 150.4082304
    phase3_cpu_seconds = 1.5756128 + 300.0431675 + 12.9036082
    p3_rows = 63178
    total_primary_rows = int(station_df.loc[station_df.cohort == "primary_seven_city_a_b", "pm25_observation_rows"].sum())
    total_pune_rows = int(station_df.loc[station_df.cohort == "pune_tier_b_sensitivity", "pm25_observation_rows"].sum())
    primary_a_hours = phase3_seconds * total_primary_rows / p3_rows / 3600
    pune_a_hours = phase3_seconds * total_pune_rows / p3_rows / 3600
    primary_city_rows = station_df[station_df.cohort == "primary_seven_city_a_b"].groupby("city").pm25_observation_rows.sum().to_dict()
    primary_city_n = station_df[station_df.cohort == "primary_seven_city_a_b"].groupby("city").size().to_dict()
    primary_c_multiplier = sum(max(primary_city_n[c]-1, 0) * primary_city_rows[c] for c in CITIES) / max(total_primary_rows, 1)
    pune_c_multiplier = max(pune_station_count-1, 0)
    runtime = {
        "calibration": "Phase 3 completed run fit duration (642.45 sec total, including 328 sec CUDA and 315 sec CPU for 72 models, 63,178 timestamps); linear scaling by station timestamp row count, not a benchmark",
        "primary_experiment_a_estimated_wall_hours": round(primary_a_hours, 1),
        "primary_experiment_a_estimated_cuda_fit_hours": round(phase3_cuda_seconds * total_primary_rows / p3_rows / 3600, 1),
        "primary_experiment_a_estimated_cpu_fit_hours": round(phase3_cpu_seconds * total_primary_rows / p3_rows / 3600, 1),
        "primary_experiment_b_one_normalization_variant_estimated_wall_hours": round(primary_a_hours, 1),
        "primary_experiment_b_two_normalization_variants_estimated_wall_hours": round(primary_a_hours*2, 1),
        "primary_experiment_b_two_variants_estimated_cuda_fit_hours": round(phase3_cuda_seconds * total_primary_rows / p3_rows / 3600 * 2, 1),
        "primary_experiment_c_loso_estimated_wall_hours": round(primary_a_hours*primary_c_multiplier, 1),
        "primary_experiment_c_loso_estimated_cuda_fit_hours": round(phase3_cuda_seconds * total_primary_rows / p3_rows / 3600 * primary_c_multiplier, 1),
        "primary_loso_training_data_multiplier_vs_A": round(primary_c_multiplier, 2),
        "pune_experiment_a_estimated_wall_hours": round(pune_a_hours, 1),
        "pune_experiment_b_two_normalization_variants_estimated_wall_hours": round(pune_a_hours*2, 1),
        "pune_experiment_c_loso_estimated_wall_hours": round(pune_a_hours*pune_c_multiplier, 1),
        "total_all_designs_estimated_wall_hours": round(primary_a_hours*(3+primary_c_multiplier)+pune_a_hours*(3+pune_c_multiplier), 1),
        "total_all_designs_estimated_cuda_fit_hours": round(phase3_cuda_seconds * total_primary_rows / p3_rows / 3600 * (3+primary_c_multiplier) + phase3_cuda_seconds * total_pune_rows / p3_rows / 3600 * (3+pune_c_multiplier), 1),
        "runtime_uncertainty": "approximately 0.7x to 1.8x these estimates; CPU Random Forest and pooled candidate memory may dominate, and timings vary by sample count and convergence",
    }
    inventory_path = REPORTS / "PHASE4_STATION_INVENTORY.csv"
    inventory_sha = file_sha(inventory_path)
    eligibility_sha = file_sha(eligibility_path)
    source_manifest_path = RAW / "retrieval_manifest.json"
    summary = {
        "preflight_only": True,
        "pm25_values_read": False,
        "test_targets_read_or_scored": False,
        "test_feature_windows_materialized": False,
        "source": "Phase 4 verified raw CPCB CAAQM PM2.5 extracts; timestamp and station ID columns only",
        "phase4_inventory_sha256": inventory_sha,
        "phase4_eligibility_sha256": eligibility_sha,
        "raw_retrieval_manifest_sha256": file_sha(source_manifest_path),
        "primary_city_station_counts": {c: int(city_counts.get(("primary_seven_city_a_b", c), 0)) for c in CITIES},
        "primary_city_tier_breakdown": {c: {tier: int(len(station_df[(station_df.cohort == "primary_seven_city_a_b") & (station_df.city == c) & (station_df.eligibility_tier == tier)])) for tier in ["A", "B"]} for c in CITIES},
        "pune_tier_b_station_count": int(city_counts.get(("pune_tier_b_sensitivity", "Pune"), 0)),
        "station_count_primary": int((station_df.cohort == "primary_seven_city_a_b").sum()),
        "station_count_pune": int((station_df.cohort == "pune_tier_b_sensitivity").sum()),
        "eligible_windows": {
            "total_train": int(windows_df.train_eligible_windows.sum()),
            "total_validation": int(windows_df.validation_eligible_windows.sum()),
            "test_timestamp_eligibility_counts_only": int(windows_df.test_eligible_timestamps_only.sum()),
            "warning": "counts only; test PM2.5 values and test feature windows were never loaded or built",
        },
        "candidate_counts": candidate_counts,
        "runtime_estimate": runtime,
        "splits": {"rule": "within each city, sorted union of unique observed IST timestamps; first 70% train, next 15% validation, last 15% test; station-specific windows require all timestamps from first input through target and issue/target in the same partition", "city_cutoffs": {c: {"validation_start_ist": pd.Timestamp(v).isoformat(), "test_start_ist": pd.Timestamp(t).isoformat(), "unique_union_timestamps": n} for c,(v,t,n) in city_cutoffs.items()}},
        "selected_station_ids": station_df.station_id.tolist(),
    }
    (REPORTS / "PHASE5_PREFLIGHT.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
