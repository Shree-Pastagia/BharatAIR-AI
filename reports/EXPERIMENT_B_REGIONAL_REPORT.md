# Phase 5 Experiment A Validation Report

Run: `phase5_B_primary_cuda_20261118_005044`

Completed fits: 515; failures: 0; ineligible/skipped: 0.

Runtime: `C:\Python313\python.exe`; PyTorch 2.14.1+cu126; CUDA 12.6; device NVIDIA GeForce RTX 4060 Laptop GPU.

The test gate remains closed. No test PM2.5 values, test windows, test predictions, or test metrics were accessed or produced.

## Validation-selected station and horizon candidates

| Station | Horizon | Model | Lookback | Validation MAE |
|---|---:|---|---:|---:|
| Ahmedabad | +1h | linear_regression | L168 | MAE 5.699 |
| Ahmedabad | +6h | random_forest | L48 | MAE 10.084 |
| Ahmedabad | +12h | random_forest | L48 | MAE 10.827 |
| Ahmedabad | +24h | tcn | L168 | MAE 11.432 |
| Bengaluru | +1h | random_forest | L48 | MAE 4.633 |
| Bengaluru | +6h | xgboost | L48 | MAE 8.743 |
| Bengaluru | +12h | tcn | L168 | MAE 9.395 |
| Bengaluru | +24h | xgboost | L24 | MAE 9.583 |
| Chennai | +1h | random_forest | L24 | MAE 4.052 |
| Chennai | +6h | tcn | L168 | MAE 7.723 |
| Chennai | +12h | tcn | L48 | MAE 8.321 |
| Chennai | +24h | xgboost | L48 | MAE 9.036 |
| Delhi | +1h | random_forest | L48 | MAE 14.653 |
| Delhi | +6h | tcn | L168 | MAE 35.063 |
| Delhi | +12h | xgboost | L168 | MAE 39.661 |
| Delhi | +24h | lstm | L24 | MAE 41.868 |
| Hyderabad | +1h | random_forest | L24 | MAE 4.871 |
| Hyderabad | +6h | random_forest | L24 | MAE 9.415 |
| Hyderabad | +12h | random_forest | L24 | MAE 10.150 |
| Hyderabad | +24h | gru | L24 | MAE 10.809 |
| Kolkata | +1h | random_forest | L24 | MAE 3.248 |
| Kolkata | +6h | random_forest | L24 | MAE 9.318 |
| Kolkata | +12h | gru | L48 | MAE 11.373 |
| Kolkata | +24h | xgboost | L24 | MAE 12.394 |
| Mumbai | +1h | tcn | L168 | MAE 7.919 |
| Mumbai | +6h | linear_regression | L168 | MAE 12.981 |
| Mumbai | +12h | linear_regression | L168 | MAE 13.993 |
| Mumbai | +24h | tcn | L168 | MAE 14.725 |

See `candidate_results.csv`, `candidate_manifest.csv`, and `metrics/` for the complete ledger and summaries.
