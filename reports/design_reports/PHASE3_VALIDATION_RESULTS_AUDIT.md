# Phase 3 Validation Results Audit

Run: `phase3_cuda_full_20261117_073000`

## Executive summary

This read-only audit used run manifests, candidate records, committed validation prediction files, and validation metrics only. It did not open the canonical dataset or any test artifact. All 72 model candidates and 8 baseline instances pass completion-marker checksum and provenance checks; each validation prediction row count matches stored `n`, and every target timestamp is before the test boundary. The test gate remains closed.

The existing validation-MAE selector chooses Random Forest at +1h, XGBoost at +6h and +12h, and TCN at +24h. Each selected candidate beats both simple baselines on validation MAE. This is a validation-only conclusion from one Delhi station and one contiguous validation interval.

## Artifact integrity and experiment context

- Status `validation_complete_test_not_evaluated`; manifest SHA-256 `6bf1bf6b2d70140e802988794b7f9058b35d0072205295168c7e20eaef6c33b3`.
- Configuration fingerprint recomputed: `74904a52167ee549e440b432211ec2d6a5b473eff394839e416a29c7f3c22c3b`.
- Dataset run fingerprint recomputed from the stored pre-test observations digest and timestamp count: `23d2c39cecb8aa8d978a883c262574afc14fe1ec9255e0b294134973b6c035f9`.
- Split fingerprint `f9b211363d0184647043fce8821f326efc09ae26f2d9a08421633f902c4ce377`; preprocessing fingerprint `9f53371c94e8429f363b1c6fc731d05baf16cecaae5ab558d9614828ebd6b9e3`.
- Validation-selection and telemetry-summary SHA-256 values match the manifest; telemetry summary has 80 candidate entries.
- Candidate completion/provenance/checksums: 72 model candidates + 8 baselines, all 80 committed and verified; zero incomplete attempts.
- Validation prediction files: 80/80 parsed; aggregate CSV has 580,620 rows (SHA-256 `268b6a43944c3e4f4510dcb5c4cc4a09784a5f2a4298a1e32e2ac380398d3b27`); every candidate row count equals stored `n`.
- Telemetry: 36/36 neural candidates have successful finite nonnegative CUDA peaks on NVIDIA GeForce RTX 4060 Laptop GPU; 44 CPU-path records are marked not applicable.
- Elapsed from manifest creation to validation completion: 11.88 min (712.8 s).
- Validation target interval: target timestamps from the validation boundary up to, but excluding, the test boundary; source timestamps are naive IST.
- Runtime: Python `C:\Python313\python.exe`, PyTorch `2.14.1+cu126`, CUDA `12.6`, GPU `NVIDIA GeForce RTX 4060 Laptop GPU`.
- Protocol: chronological 70/15/15 split, purged windows crossing partition boundaries, no imputation, train-only neural scaling, and selection on validation MAE.
- Test selection artifacts are absent; the stored selection record says `test_accessed=false`.

## Horizon-by-horizon candidate comparisons

The three input windows are separate candidates. Lower MAE/RMSE/MASE is better. Baseline rows have no input window.

### +1h

Winner by validation MAE: **random_forest L24** (11.2616); runner-up: **random_forest L48** (11.2884).

| Candidate | Input h | n | MAE | RMSE | MASE | Device |
| --- | --- | --- | --- | --- | --- | --- |
| persistence | — | 7360 | 14.1643 | 23.9081 | 0.9703 | CPU |
| seasonal_naive | — | 7360 | 41.6647 | 68.9105 | 2.8542 | CPU |
| gru L24 | 24 | 7360 | 11.5866 | 19.4985 | 0.7937 | CUDA |
| gru L48 | 48 | 7360 | 12.4735 | 19.9957 | 0.8545 | CUDA |
| gru L168 | 168 | 7360 | 12.5363 | 20.2201 | 0.8588 | CUDA |
| lstm L24 | 24 | 7360 | 11.6760 | 19.7142 | 0.7998 | CUDA |
| lstm L48 | 48 | 7360 | 12.4746 | 20.5921 | 0.8546 | CUDA |
| lstm L168 | 168 | 7360 | 12.7805 | 20.9107 | 0.8755 | CUDA |
| tcn L24 | 24 | 7360 | 13.3004 | 21.9369 | 0.9111 | CUDA |
| tcn L48 | 48 | 7360 | 12.2998 | 20.5441 | 0.8426 | CUDA |
| tcn L168 | 168 | 7360 | 12.9009 | 21.2774 | 0.8838 | CUDA |
| linear_regression L24 | 24 | 7360 | 11.8068 | 19.6838 | 0.8088 | CPU |
| linear_regression L48 | 48 | 7360 | 11.6602 | 19.5159 | 0.7988 | CPU |
| linear_regression L168 | 168 | 7360 | 11.6421 | 19.5172 | 0.7975 | CPU |
| random_forest L24 | 24 | 7360 | 11.2616 | 19.9269 | 0.7715 | CPU |
| random_forest L48 | 48 | 7360 | 11.2884 | 20.1484 | 0.7733 | CPU |
| random_forest L168 | 168 | 7360 | 11.5972 | 20.6658 | 0.7945 | CPU |
| xgboost L24 | 24 | 7360 | 11.9475 | 20.8324 | 0.8184 | CPU |
| xgboost L48 | 48 | 7360 | 11.9889 | 21.2278 | 0.8213 | CPU |
| xgboost L168 | 168 | 7360 | 12.1925 | 21.4845 | 0.8352 | CPU |

#### Improvement over both baselines (positive means candidate error is lower)

| Model | Window h | ΔMAE vs P | MAE % | ΔRMSE vs P | RMSE % | ΔMAE vs SN | MAE % | ΔRMSE vs SN | RMSE % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gru | 24 | 2.5777 | 18.20% | 4.4097 | 18.44% | 30.0782 | 72.19% | 49.4120 | 71.70% |
| gru | 48 | 1.6907 | 11.94% | 3.9125 | 16.36% | 29.1912 | 70.06% | 48.9148 | 70.98% |
| gru | 168 | 1.6280 | 11.49% | 3.6880 | 15.43% | 29.1285 | 69.91% | 48.6904 | 70.66% |
| linear_regression | 24 | 2.3575 | 16.64% | 4.2243 | 17.67% | 29.8580 | 71.66% | 49.2266 | 71.44% |
| linear_regression | 48 | 2.5041 | 17.68% | 4.3922 | 18.37% | 30.0046 | 72.01% | 49.3946 | 71.68% |
| linear_regression | 168 | 2.5222 | 17.81% | 4.3909 | 18.37% | 30.0227 | 72.06% | 49.3932 | 71.68% |
| lstm | 24 | 2.4883 | 17.57% | 4.1939 | 17.54% | 29.9888 | 71.98% | 49.1963 | 71.39% |
| lstm | 48 | 1.6897 | 11.93% | 3.3160 | 13.87% | 29.1902 | 70.06% | 48.3184 | 70.12% |
| lstm | 168 | 1.3838 | 9.77% | 2.9974 | 12.54% | 28.8843 | 69.33% | 47.9997 | 69.66% |
| random_forest | 24 | 2.9027 | 20.49% | 3.9812 | 16.65% | 30.4031 | 72.97% | 48.9835 | 71.08% |
| random_forest | 48 | 2.8759 | 20.30% | 3.7597 | 15.73% | 30.3764 | 72.91% | 48.7621 | 70.76% |
| random_forest | 168 | 2.5670 | 18.12% | 3.2423 | 13.56% | 30.0675 | 72.17% | 48.2447 | 70.01% |
| tcn | 24 | 0.8639 | 6.10% | 1.9712 | 8.24% | 28.3643 | 68.08% | 46.9736 | 68.17% |
| tcn | 48 | 1.8645 | 13.16% | 3.3640 | 14.07% | 29.3649 | 70.48% | 48.3664 | 70.19% |
| tcn | 168 | 1.2634 | 8.92% | 2.6307 | 11.00% | 28.7638 | 69.04% | 47.6330 | 69.12% |
| xgboost | 24 | 2.2168 | 15.65% | 3.0757 | 12.86% | 29.7172 | 71.32% | 48.0781 | 69.77% |
| xgboost | 48 | 2.1754 | 15.36% | 2.6803 | 11.21% | 29.6759 | 71.23% | 47.6826 | 69.20% |
| xgboost | 168 | 1.9718 | 13.92% | 2.4236 | 10.14% | 29.4723 | 70.74% | 47.4260 | 68.82% |

### +6h

Winner by validation MAE: **xgboost L168** (31.8100); runner-up: **xgboost L24** (32.0125).

| Candidate | Input h | n | MAE | RMSE | MASE | Device |
| --- | --- | --- | --- | --- | --- | --- |
| persistence | — | 7305 | 48.6508 | 74.3890 | 3.3328 | CPU |
| seasonal_naive | — | 7305 | 41.8342 | 69.1348 | 2.8658 | CPU |
| gru L24 | 24 | 7305 | 34.7212 | 54.2859 | 2.3785 | CUDA |
| gru L48 | 48 | 7305 | 35.7534 | 55.0950 | 2.4492 | CUDA |
| gru L168 | 168 | 7305 | 36.2275 | 56.1300 | 2.4817 | CUDA |
| lstm L24 | 24 | 7305 | 35.6703 | 55.2685 | 2.4435 | CUDA |
| lstm L48 | 48 | 7305 | 35.0725 | 55.4204 | 2.4026 | CUDA |
| lstm L168 | 168 | 7305 | 35.6936 | 55.7378 | 2.4451 | CUDA |
| tcn L24 | 24 | 7305 | 32.8085 | 52.1812 | 2.2475 | CUDA |
| tcn L48 | 48 | 7305 | 33.3923 | 51.9482 | 2.2875 | CUDA |
| tcn L168 | 168 | 7305 | 32.8375 | 51.7072 | 2.2495 | CUDA |
| linear_regression L24 | 24 | 7305 | 35.6577 | 54.3141 | 2.4427 | CPU |
| linear_regression L48 | 48 | 7305 | 34.2523 | 52.8021 | 2.3464 | CPU |
| linear_regression L168 | 168 | 7305 | 33.4223 | 51.6456 | 2.2895 | CPU |
| random_forest L24 | 24 | 7305 | 32.5038 | 52.6804 | 2.2266 | CPU |
| random_forest L48 | 48 | 7305 | 32.4070 | 52.6854 | 2.2200 | CPU |
| random_forest L168 | 168 | 7305 | 32.6804 | 52.8491 | 2.2387 | CPU |
| xgboost L24 | 24 | 7305 | 32.0125 | 51.7237 | 2.1930 | CPU |
| xgboost L48 | 48 | 7305 | 32.1313 | 52.1180 | 2.2011 | CPU |
| xgboost L168 | 168 | 7305 | 31.8100 | 51.2462 | 2.1791 | CPU |

#### Improvement over both baselines (positive means candidate error is lower)

| Model | Window h | ΔMAE vs P | MAE % | ΔRMSE vs P | RMSE % | ΔMAE vs SN | MAE % | ΔRMSE vs SN | RMSE % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gru | 24 | 13.9297 | 28.63% | 20.1031 | 27.02% | 7.1130 | 17.00% | 14.8489 | 21.48% |
| gru | 48 | 12.8974 | 26.51% | 19.2940 | 25.94% | 6.0807 | 14.54% | 14.0399 | 20.31% |
| gru | 168 | 12.4233 | 25.54% | 18.2590 | 24.55% | 5.6067 | 13.40% | 13.0048 | 18.81% |
| linear_regression | 24 | 12.9931 | 26.71% | 20.0749 | 26.99% | 6.1764 | 14.76% | 14.8208 | 21.44% |
| linear_regression | 48 | 14.3985 | 29.60% | 21.5869 | 29.02% | 7.5819 | 18.12% | 16.3327 | 23.62% |
| linear_regression | 168 | 15.2285 | 31.30% | 22.7434 | 30.57% | 8.4119 | 20.11% | 17.4892 | 25.30% |
| lstm | 24 | 12.9805 | 26.68% | 19.1206 | 25.70% | 6.1639 | 14.73% | 13.8664 | 20.06% |
| lstm | 48 | 13.5783 | 27.91% | 18.9686 | 25.50% | 6.7616 | 16.16% | 13.7144 | 19.84% |
| lstm | 168 | 12.9572 | 26.63% | 18.6512 | 25.07% | 6.1406 | 14.68% | 13.3970 | 19.38% |
| random_forest | 24 | 16.1470 | 33.19% | 21.7086 | 29.18% | 9.3304 | 22.30% | 16.4545 | 23.80% |
| random_forest | 48 | 16.2438 | 33.39% | 21.7036 | 29.18% | 9.4272 | 22.53% | 16.4494 | 23.79% |
| random_forest | 168 | 15.9704 | 32.83% | 21.5400 | 28.96% | 9.1538 | 21.88% | 16.2858 | 23.56% |
| tcn | 24 | 15.8423 | 32.56% | 22.2078 | 29.85% | 9.0257 | 21.57% | 16.9536 | 24.52% |
| tcn | 48 | 15.2586 | 31.36% | 22.4408 | 30.17% | 8.4419 | 20.18% | 17.1867 | 24.86% |
| tcn | 168 | 15.8134 | 32.50% | 22.6818 | 30.49% | 8.9967 | 21.51% | 17.4276 | 25.21% |
| xgboost | 24 | 16.6383 | 34.20% | 22.6653 | 30.47% | 9.8217 | 23.48% | 17.4111 | 25.18% |
| xgboost | 48 | 16.5195 | 33.96% | 22.2710 | 29.94% | 9.7028 | 23.19% | 17.0168 | 24.61% |
| xgboost | 168 | 16.8409 | 34.62% | 23.1428 | 31.11% | 10.0242 | 23.96% | 17.8886 | 25.87% |

### +12h

Winner by validation MAE: **xgboost L24** (35.1162); runner-up: **xgboost L168** (35.1916).

| Candidate | Input h | n | MAE | RMSE | MASE | Device |
| --- | --- | --- | --- | --- | --- | --- |
| persistence | — | 7243 | 57.5245 | 84.8695 | 3.9406 | CPU |
| seasonal_naive | — | 7243 | 41.8099 | 68.9554 | 2.8641 | CPU |
| gru L24 | 24 | 7243 | 36.9136 | 58.3549 | 2.5287 | CUDA |
| gru L48 | 48 | 7243 | 37.3703 | 58.5724 | 2.5600 | CUDA |
| gru L168 | 168 | 7243 | 37.2928 | 58.9993 | 2.5547 | CUDA |
| lstm L24 | 24 | 7243 | 37.4341 | 58.8823 | 2.5644 | CUDA |
| lstm L48 | 48 | 7243 | 37.4884 | 59.1745 | 2.5681 | CUDA |
| lstm L168 | 168 | 7243 | 37.9073 | 59.3941 | 2.5968 | CUDA |
| tcn L24 | 24 | 7243 | 37.0251 | 57.6594 | 2.5363 | CUDA |
| tcn L48 | 48 | 7243 | 36.0544 | 56.4196 | 2.4699 | CUDA |
| tcn L168 | 168 | 7243 | 35.9167 | 56.6158 | 2.4604 | CUDA |
| linear_regression L24 | 24 | 7243 | 38.6632 | 59.1576 | 2.6486 | CPU |
| linear_regression L48 | 48 | 7243 | 37.3686 | 57.6564 | 2.5599 | CPU |
| linear_regression L168 | 168 | 7243 | 36.6787 | 56.8441 | 2.5126 | CPU |
| random_forest L24 | 24 | 7243 | 35.7300 | 56.6347 | 2.4476 | CPU |
| random_forest L48 | 48 | 7243 | 35.6703 | 56.8473 | 2.4435 | CPU |
| random_forest L168 | 168 | 7243 | 35.8963 | 56.9295 | 2.4590 | CPU |
| xgboost L24 | 24 | 7243 | 35.1162 | 56.3038 | 2.4056 | CPU |
| xgboost L48 | 48 | 7243 | 35.1977 | 56.4056 | 2.4112 | CPU |
| xgboost L168 | 168 | 7243 | 35.1916 | 55.8215 | 2.4107 | CPU |

#### Improvement over both baselines (positive means candidate error is lower)

| Model | Window h | ΔMAE vs P | MAE % | ΔRMSE vs P | RMSE % | ΔMAE vs SN | MAE % | ΔRMSE vs SN | RMSE % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gru | 24 | 20.6108 | 35.83% | 26.5146 | 31.24% | 4.8963 | 11.71% | 10.6005 | 15.37% |
| gru | 48 | 20.1542 | 35.04% | 26.2971 | 30.99% | 4.4396 | 10.62% | 10.3830 | 15.06% |
| gru | 168 | 20.2317 | 35.17% | 25.8702 | 30.48% | 4.5171 | 10.80% | 9.9562 | 14.44% |
| linear_regression | 24 | 18.8613 | 32.79% | 25.7120 | 30.30% | 3.1467 | 7.53% | 9.7979 | 14.21% |
| linear_regression | 48 | 20.1559 | 35.04% | 27.2132 | 32.06% | 4.4413 | 10.62% | 11.2991 | 16.39% |
| linear_regression | 168 | 20.8457 | 36.24% | 28.0254 | 33.02% | 5.1312 | 12.27% | 12.1113 | 17.56% |
| lstm | 24 | 20.0903 | 34.92% | 25.9873 | 30.62% | 4.3758 | 10.47% | 10.0732 | 14.61% |
| lstm | 48 | 20.0361 | 34.83% | 25.6951 | 30.28% | 4.3215 | 10.34% | 9.7810 | 14.18% |
| lstm | 168 | 19.6172 | 34.10% | 25.4754 | 30.02% | 3.9026 | 9.33% | 9.5613 | 13.87% |
| random_forest | 24 | 21.7945 | 37.89% | 28.2349 | 33.27% | 6.0799 | 14.54% | 12.3208 | 17.87% |
| random_forest | 48 | 21.8542 | 37.99% | 28.0222 | 33.02% | 6.1396 | 14.68% | 12.1081 | 17.56% |
| random_forest | 168 | 21.6282 | 37.60% | 27.9400 | 32.92% | 5.9136 | 14.14% | 12.0259 | 17.44% |
| tcn | 24 | 20.4994 | 35.64% | 27.2101 | 32.06% | 4.7848 | 11.44% | 11.2960 | 16.38% |
| tcn | 48 | 21.4701 | 37.32% | 28.4499 | 33.52% | 5.7555 | 13.77% | 12.5358 | 18.18% |
| tcn | 168 | 21.6077 | 37.56% | 28.2537 | 33.29% | 5.8932 | 14.10% | 12.3396 | 17.90% |
| xgboost | 24 | 22.4082 | 38.95% | 28.5657 | 33.66% | 6.6936 | 16.01% | 12.6516 | 18.35% |
| xgboost | 48 | 22.3268 | 38.81% | 28.4639 | 33.54% | 6.6122 | 15.81% | 12.5499 | 18.20% |
| xgboost | 168 | 22.3329 | 38.82% | 29.0480 | 34.23% | 6.6183 | 15.83% | 13.1339 | 19.05% |

### +24h

Winner by validation MAE: **tcn L168** (36.7191); runner-up: **gru L168** (36.8892).

| Candidate | Input h | n | MAE | RMSE | MASE | Device |
| --- | --- | --- | --- | --- | --- | --- |
| persistence | — | 7123 | 42.1147 | 69.3716 | 2.8850 | CPU |
| seasonal_naive | — | 7123 | 42.1147 | 69.3716 | 2.8850 | CPU |
| gru L24 | 24 | 7123 | 37.3299 | 59.5941 | 2.5572 | CUDA |
| gru L48 | 48 | 7123 | 36.9147 | 59.3388 | 2.5288 | CUDA |
| gru L168 | 168 | 7123 | 36.8892 | 59.0000 | 2.5270 | CUDA |
| lstm L24 | 24 | 7123 | 37.4727 | 59.5840 | 2.5670 | CUDA |
| lstm L48 | 48 | 7123 | 37.6129 | 59.3972 | 2.5766 | CUDA |
| lstm L168 | 168 | 7123 | 37.8324 | 59.5491 | 2.5917 | CUDA |
| tcn L24 | 24 | 7123 | 37.8651 | 59.4718 | 2.5939 | CUDA |
| tcn L48 | 48 | 7123 | 38.0509 | 59.4998 | 2.6066 | CUDA |
| tcn L168 | 168 | 7123 | 36.7191 | 58.9782 | 2.5154 | CUDA |
| linear_regression L24 | 24 | 7123 | 39.1670 | 61.1078 | 2.6831 | CPU |
| linear_regression L48 | 48 | 7123 | 38.5196 | 60.4986 | 2.6387 | CPU |
| linear_regression L168 | 168 | 7123 | 38.2100 | 60.1561 | 2.6175 | CPU |
| random_forest L24 | 24 | 7123 | 37.9015 | 60.7354 | 2.5964 | CPU |
| random_forest L48 | 48 | 7123 | 37.8024 | 60.1489 | 2.5896 | CPU |
| random_forest L168 | 168 | 7123 | 37.7017 | 59.8851 | 2.5827 | CPU |
| xgboost L24 | 24 | 7123 | 36.9390 | 59.3414 | 2.5305 | CPU |
| xgboost L48 | 48 | 7123 | 37.1850 | 59.5686 | 2.5473 | CPU |
| xgboost L168 | 168 | 7123 | 37.5661 | 59.4514 | 2.5734 | CPU |

#### Improvement over both baselines (positive means candidate error is lower)

| Model | Window h | ΔMAE vs P | MAE % | ΔRMSE vs P | RMSE % | ΔMAE vs SN | MAE % | ΔRMSE vs SN | RMSE % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gru | 24 | 4.7847 | 11.36% | 9.7775 | 14.09% | 4.7847 | 11.36% | 9.7775 | 14.09% |
| gru | 48 | 5.2000 | 12.35% | 10.0328 | 14.46% | 5.2000 | 12.35% | 10.0328 | 14.46% |
| gru | 168 | 5.2254 | 12.41% | 10.3716 | 14.95% | 5.2254 | 12.41% | 10.3716 | 14.95% |
| linear_regression | 24 | 2.9477 | 7.00% | 8.2638 | 11.91% | 2.9477 | 7.00% | 8.2638 | 11.91% |
| linear_regression | 48 | 3.5950 | 8.54% | 8.8730 | 12.79% | 3.5950 | 8.54% | 8.8730 | 12.79% |
| linear_regression | 168 | 3.9047 | 9.27% | 9.2156 | 13.28% | 3.9047 | 9.27% | 9.2156 | 13.28% |
| lstm | 24 | 4.6419 | 11.02% | 9.7876 | 14.11% | 4.6419 | 11.02% | 9.7876 | 14.11% |
| lstm | 48 | 4.5018 | 10.69% | 9.9744 | 14.38% | 4.5018 | 10.69% | 9.9744 | 14.38% |
| lstm | 168 | 4.2823 | 10.17% | 9.8225 | 14.16% | 4.2823 | 10.17% | 9.8225 | 14.16% |
| random_forest | 24 | 4.2132 | 10.00% | 8.6362 | 12.45% | 4.2132 | 10.00% | 8.6362 | 12.45% |
| random_forest | 48 | 4.3122 | 10.24% | 9.2227 | 13.29% | 4.3122 | 10.24% | 9.2227 | 13.29% |
| random_forest | 168 | 4.4130 | 10.48% | 9.4865 | 13.67% | 4.4130 | 10.48% | 9.4865 | 13.67% |
| tcn | 24 | 4.2495 | 10.09% | 9.8999 | 14.27% | 4.2495 | 10.09% | 9.8999 | 14.27% |
| tcn | 48 | 4.0637 | 9.65% | 9.8718 | 14.23% | 4.0637 | 9.65% | 9.8718 | 14.23% |
| tcn | 168 | 5.3955 | 12.81% | 10.3934 | 14.98% | 5.3955 | 12.81% | 10.3934 | 14.98% |
| xgboost | 24 | 5.1757 | 12.29% | 10.0302 | 14.46% | 5.1757 | 12.29% | 10.0302 | 14.46% |
| xgboost | 48 | 4.9296 | 11.71% | 9.8030 | 14.13% | 4.9296 | 11.71% | 9.8030 | 14.13% |
| xgboost | 168 | 4.5486 | 10.80% | 9.9203 | 14.30% | 4.5486 | 10.80% | 9.9203 | 14.30% |

## Winners, family comparison, and recommendations

| Horizon | Winner | MAE | Runner-up | MAE | Persistence MAE | Seasonal-naive MAE | Beats both (MAE) | Beats both (RMSE) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| +1h | random_forest L24 | 11.2616 | random_forest L48 | 11.2884 | 14.1643 | 41.6647 | Yes | Yes |
| +6h | xgboost L168 | 31.8100 | xgboost L24 | 32.0125 | 48.6508 | 41.8342 | Yes | Yes |
| +12h | xgboost L24 | 35.1162 | xgboost L168 | 35.1916 | 57.5245 | 41.8099 | Yes | Yes |
| +24h | tcn L168 | 36.7191 | gru L168 | 36.8892 | 42.1147 | 42.1147 | Yes | Yes |

Best candidate in each model family by validation MAE:

| Horizon | Best traditional ML | MAE | Best deep model | MAE | Lower MAE family |
| --- | --- | --- | --- | --- | --- |
| +1h | random_forest L24 | 11.2616 | gru L24 | 11.5866 | Traditional ML |
| +6h | xgboost L168 | 31.8100 | tcn L24 | 32.8085 | Traditional ML |
| +12h | xgboost L24 | 35.1162 | tcn L168 | 35.9167 | Traditional ML |
| +24h | xgboost L24 | 36.9390 | tcn L168 | 36.7191 | Deep learning |

## Monthly validation error

Month is assigned by target timestamp. Full monthly MAE and RMSE are shown for the selected winner, overall runner-up, persistence, and seasonal-naive baseline. `n<30` is flagged as a small subgroup.

### +1h

| Series | Month | n | MAE | RMSE | Note |
| --- | --- | --- | --- | --- | --- |
| persistence | 2023-03 | 53 | 8.2547 | 12.4609 |  |
| persistence | 2023-04 | 720 | 14.9200 | 23.6573 |  |
| persistence | 2023-05 | 428 | 12.1628 | 20.3811 |  |
| persistence | 2023-06 | 364 | 5.3468 | 8.1603 |  |
| persistence | 2023-07 | 274 | 4.2905 | 5.7529 |  |
| persistence | 2023-08 | 262 | 4.1145 | 8.2535 |  |
| persistence | 2023-09 | 683 | 4.4344 | 6.2428 |  |
| persistence | 2023-10 | 399 | 10.1228 | 14.2635 |  |
| persistence | 2023-11 | 551 | 22.5672 | 38.8975 |  |
| persistence | 2023-12 | 744 | 21.0659 | 28.8971 |  |
| persistence | 2024-01 | 744 | 20.9597 | 30.8385 |  |
| persistence | 2024-02 | 696 | 13.7237 | 20.4709 |  |
| persistence | 2024-03 | 744 | 16.0354 | 26.1998 |  |
| persistence | 2024-04 | 698 | 16.3503 | 26.6080 |  |
| random_forest L24 | 2023-03 | 53 | 7.7987 | 12.3866 |  |
| random_forest L24 | 2023-04 | 720 | 11.1031 | 18.0372 |  |
| random_forest L24 | 2023-05 | 428 | 9.5919 | 15.7250 |  |
| random_forest L24 | 2023-06 | 364 | 5.0380 | 7.3095 |  |
| random_forest L24 | 2023-07 | 274 | 3.9572 | 5.4324 |  |
| random_forest L24 | 2023-08 | 262 | 3.8844 | 7.9602 |  |
| random_forest L24 | 2023-09 | 683 | 4.0261 | 5.6477 |  |
| random_forest L24 | 2023-10 | 399 | 7.3511 | 10.2369 |  |
| random_forest L24 | 2023-11 | 551 | 19.1197 | 37.3680 |  |
| random_forest L24 | 2023-12 | 744 | 14.7161 | 20.5826 |  |
| random_forest L24 | 2024-01 | 744 | 19.4896 | 27.7594 |  |
| random_forest L24 | 2024-02 | 696 | 10.9245 | 17.3232 |  |
| random_forest L24 | 2024-03 | 744 | 11.7420 | 20.5650 |  |
| random_forest L24 | 2024-04 | 698 | 12.0780 | 20.2125 |  |
| random_forest L48 | 2023-03 | 53 | 7.7621 | 12.2146 |  |
| random_forest L48 | 2023-04 | 720 | 11.0153 | 17.7858 |  |
| random_forest L48 | 2023-05 | 428 | 9.6431 | 16.0870 |  |
| random_forest L48 | 2023-06 | 364 | 5.0157 | 7.3041 |  |
| random_forest L48 | 2023-07 | 274 | 4.0195 | 5.4595 |  |
| random_forest L48 | 2023-08 | 262 | 3.9232 | 7.8819 |  |
| random_forest L48 | 2023-09 | 683 | 3.9608 | 5.6027 |  |
| random_forest L48 | 2023-10 | 399 | 7.4027 | 10.3841 |  |
| random_forest L48 | 2023-11 | 551 | 19.1892 | 38.2586 |  |
| random_forest L48 | 2023-12 | 744 | 14.8280 | 20.8764 |  |
| random_forest L48 | 2024-01 | 744 | 19.4487 | 28.1443 |  |
| random_forest L48 | 2024-02 | 696 | 10.7741 | 17.1484 |  |
| random_forest L48 | 2024-03 | 744 | 11.9559 | 20.7795 |  |
| random_forest L48 | 2024-04 | 698 | 12.2202 | 20.2805 |  |
| seasonal_naive | 2023-03 | 53 | 36.3396 | 44.9700 |  |
| seasonal_naive | 2023-04 | 720 | 32.6797 | 47.7506 |  |
| seasonal_naive | 2023-05 | 428 | 34.2644 | 57.1721 |  |
| seasonal_naive | 2023-06 | 364 | 17.3951 | 23.7987 |  |
| seasonal_naive | 2023-07 | 274 | 13.3285 | 15.8575 |  |
| seasonal_naive | 2023-08 | 262 | 10.3982 | 16.2260 |  |
| seasonal_naive | 2023-09 | 683 | 12.2679 | 15.7145 |  |
| seasonal_naive | 2023-10 | 399 | 19.2024 | 26.3842 |  |
| seasonal_naive | 2023-11 | 551 | 88.8940 | 126.3156 |  |
| seasonal_naive | 2023-12 | 744 | 52.5481 | 72.8899 |  |
| seasonal_naive | 2024-01 | 744 | 87.3353 | 116.7220 |  |
| seasonal_naive | 2024-02 | 696 | 46.8593 | 73.0100 |  |
| seasonal_naive | 2024-03 | 744 | 36.7140 | 56.3586 |  |
| seasonal_naive | 2024-04 | 698 | 35.5299 | 54.2990 |  |

### +6h

| Series | Month | n | MAE | RMSE | Note |
| --- | --- | --- | --- | --- | --- |
| persistence | 2023-03 | 43 | 20.9477 | 31.3394 |  |
| persistence | 2023-04 | 720 | 51.8336 | 72.1737 |  |
| persistence | 2023-05 | 423 | 46.6546 | 74.3199 |  |
| persistence | 2023-06 | 359 | 15.4991 | 22.7832 |  |
| persistence | 2023-07 | 264 | 11.4593 | 14.9227 |  |
| persistence | 2023-08 | 257 | 10.5613 | 15.7201 |  |
| persistence | 2023-09 | 678 | 11.2659 | 14.9600 |  |
| persistence | 2023-10 | 389 | 36.8689 | 47.6563 |  |
| persistence | 2023-11 | 546 | 76.4516 | 111.8858 |  |
| persistence | 2023-12 | 744 | 75.4792 | 97.3108 |  |
| persistence | 2024-01 | 744 | 70.4255 | 97.4887 |  |
| persistence | 2024-02 | 696 | 48.7349 | 66.2009 |  |
| persistence | 2024-03 | 744 | 55.5195 | 77.8433 |  |
| persistence | 2024-04 | 698 | 55.3481 | 79.7647 |  |
| seasonal_naive | 2023-03 | 43 | 38.3837 | 47.9357 |  |
| seasonal_naive | 2023-04 | 720 | 32.6797 | 47.7506 |  |
| seasonal_naive | 2023-05 | 423 | 34.5412 | 57.4916 |  |
| seasonal_naive | 2023-06 | 359 | 17.4557 | 23.8767 |  |
| seasonal_naive | 2023-07 | 264 | 13.3608 | 15.9102 |  |
| seasonal_naive | 2023-08 | 257 | 10.1754 | 16.0840 |  |
| seasonal_naive | 2023-09 | 678 | 12.3241 | 15.7664 |  |
| seasonal_naive | 2023-10 | 389 | 19.2037 | 26.4843 |  |
| seasonal_naive | 2023-11 | 546 | 89.3234 | 126.7872 |  |
| seasonal_naive | 2023-12 | 744 | 52.5481 | 72.8899 |  |
| seasonal_naive | 2024-01 | 744 | 87.3353 | 116.7220 |  |
| seasonal_naive | 2024-02 | 696 | 46.8593 | 73.0100 |  |
| seasonal_naive | 2024-03 | 744 | 36.7140 | 56.3586 |  |
| seasonal_naive | 2024-04 | 698 | 35.5299 | 54.2990 |  |
| xgboost L168 | 2023-03 | 43 | 28.8874 | 35.2033 |  |
| xgboost L168 | 2023-04 | 720 | 29.9094 | 41.2127 |  |
| xgboost L168 | 2023-05 | 423 | 30.6091 | 49.6328 |  |
| xgboost L168 | 2023-06 | 359 | 13.4069 | 18.2601 |  |
| xgboost L168 | 2023-07 | 264 | 10.9557 | 13.2491 |  |
| xgboost L168 | 2023-08 | 257 | 8.7679 | 13.2615 |  |
| xgboost L168 | 2023-09 | 678 | 9.3425 | 12.0807 |  |
| xgboost L168 | 2023-10 | 389 | 17.3812 | 23.6517 |  |
| xgboost L168 | 2023-11 | 546 | 57.9625 | 90.2380 |  |
| xgboost L168 | 2023-12 | 744 | 40.0279 | 53.5694 |  |
| xgboost L168 | 2024-01 | 744 | 61.7564 | 83.1531 |  |
| xgboost L168 | 2024-02 | 696 | 34.8050 | 51.2578 |  |
| xgboost L168 | 2024-03 | 744 | 29.4601 | 43.8495 |  |
| xgboost L168 | 2024-04 | 698 | 28.7612 | 44.0369 |  |
| xgboost L24 | 2023-03 | 43 | 30.9789 | 37.7182 |  |
| xgboost L24 | 2023-04 | 720 | 29.7879 | 40.5795 |  |
| xgboost L24 | 2023-05 | 423 | 29.5746 | 48.0140 |  |
| xgboost L24 | 2023-06 | 359 | 13.9676 | 18.7392 |  |
| xgboost L24 | 2023-07 | 264 | 11.1163 | 13.7385 |  |
| xgboost L24 | 2023-08 | 257 | 9.6263 | 14.3015 |  |
| xgboost L24 | 2023-09 | 678 | 9.2285 | 11.9860 |  |
| xgboost L24 | 2023-10 | 389 | 18.0075 | 23.3283 |  |
| xgboost L24 | 2023-11 | 546 | 57.7429 | 91.4288 |  |
| xgboost L24 | 2023-12 | 744 | 39.8123 | 53.1402 |  |
| xgboost L24 | 2024-01 | 744 | 64.1592 | 86.8251 |  |
| xgboost L24 | 2024-02 | 696 | 32.8881 | 48.8963 |  |
| xgboost L24 | 2024-03 | 744 | 30.0318 | 44.0237 |  |
| xgboost L24 | 2024-04 | 698 | 29.7436 | 44.8508 |  |

### +12h

| Series | Month | n | MAE | RMSE | Note |
| --- | --- | --- | --- | --- | --- |
| persistence | 2023-03 | 31 | 23.6129 | 31.8203 |  |
| persistence | 2023-04 | 720 | 63.5756 | 85.7920 |  |
| persistence | 2023-05 | 417 | 56.6373 | 89.8851 |  |
| persistence | 2023-06 | 353 | 18.1617 | 25.2013 |  |
| persistence | 2023-07 | 252 | 14.0751 | 17.7034 |  |
| persistence | 2023-08 | 251 | 12.6736 | 17.7950 |  |
| persistence | 2023-09 | 672 | 13.1589 | 16.9448 |  |
| persistence | 2023-10 | 381 | 42.8694 | 51.6449 |  |
| persistence | 2023-11 | 540 | 85.5460 | 116.8883 |  |
| persistence | 2023-12 | 744 | 85.4570 | 105.9043 |  |
| persistence | 2024-01 | 744 | 88.5482 | 120.0057 |  |
| persistence | 2024-02 | 696 | 56.8967 | 77.2859 |  |
| persistence | 2024-03 | 744 | 68.5401 | 91.3281 |  |
| persistence | 2024-04 | 698 | 60.1172 | 85.2986 |  |
| seasonal_naive | 2023-03 | 31 | 35.7339 | 42.8656 |  |
| seasonal_naive | 2023-04 | 720 | 32.6797 | 47.7506 |  |
| seasonal_naive | 2023-05 | 417 | 34.2354 | 57.3621 |  |
| seasonal_naive | 2023-06 | 353 | 17.4443 | 23.9592 |  |
| seasonal_naive | 2023-07 | 252 | 13.5337 | 16.1025 |  |
| seasonal_naive | 2023-08 | 251 | 10.0989 | 16.1372 |  |
| seasonal_naive | 2023-09 | 672 | 12.4289 | 15.8365 |  |
| seasonal_naive | 2023-10 | 381 | 18.7972 | 26.1390 |  |
| seasonal_naive | 2023-11 | 540 | 87.9557 | 124.6196 |  |
| seasonal_naive | 2023-12 | 744 | 52.5481 | 72.8899 |  |
| seasonal_naive | 2024-01 | 744 | 87.3353 | 116.7220 |  |
| seasonal_naive | 2024-02 | 696 | 46.8593 | 73.0100 |  |
| seasonal_naive | 2024-03 | 744 | 36.7140 | 56.3586 |  |
| seasonal_naive | 2024-04 | 698 | 35.5299 | 54.2990 |  |
| xgboost L168 | 2023-03 | 31 | 27.1897 | 35.5658 |  |
| xgboost L168 | 2023-04 | 720 | 31.5168 | 43.0050 |  |
| xgboost L168 | 2023-05 | 417 | 32.1915 | 52.4955 |  |
| xgboost L168 | 2023-06 | 353 | 14.4300 | 19.3611 |  |
| xgboost L168 | 2023-07 | 252 | 12.4548 | 14.6087 |  |
| xgboost L168 | 2023-08 | 251 | 9.5846 | 14.1277 |  |
| xgboost L168 | 2023-09 | 672 | 10.8365 | 13.6348 |  |
| xgboost L168 | 2023-10 | 381 | 17.5046 | 23.7944 |  |
| xgboost L168 | 2023-11 | 540 | 65.9975 | 96.9106 |  |
| xgboost L168 | 2023-12 | 744 | 44.8935 | 60.5628 |  |
| xgboost L168 | 2024-01 | 744 | 70.0908 | 91.8318 |  |
| xgboost L168 | 2024-02 | 696 | 40.8612 | 59.2827 |  |
| xgboost L168 | 2024-03 | 744 | 30.8987 | 46.0100 |  |
| xgboost L168 | 2024-04 | 698 | 29.6980 | 44.4173 |  |
| xgboost L24 | 2023-03 | 31 | 34.0253 | 44.0140 |  |
| xgboost L24 | 2023-04 | 720 | 30.0326 | 41.2959 |  |
| xgboost L24 | 2023-05 | 417 | 30.9595 | 51.0779 |  |
| xgboost L24 | 2023-06 | 353 | 15.3748 | 19.9303 |  |
| xgboost L24 | 2023-07 | 252 | 13.1398 | 15.7225 |  |
| xgboost L24 | 2023-08 | 251 | 10.4188 | 14.9584 |  |
| xgboost L24 | 2023-09 | 672 | 10.8048 | 13.5606 |  |
| xgboost L24 | 2023-10 | 381 | 18.6251 | 24.3026 |  |
| xgboost L24 | 2023-11 | 540 | 64.9889 | 98.1551 |  |
| xgboost L24 | 2023-12 | 744 | 44.5129 | 59.7952 |  |
| xgboost L24 | 2024-01 | 744 | 70.7505 | 95.2521 |  |
| xgboost L24 | 2024-02 | 696 | 39.7107 | 58.4911 |  |
| xgboost L24 | 2024-03 | 744 | 31.4961 | 45.8896 |  |
| xgboost L24 | 2024-04 | 698 | 30.2668 | 45.0583 |  |

### +24h

| Series | Month | n | MAE | RMSE | Note |
| --- | --- | --- | --- | --- | --- |
| gru L168 | 2023-03 | 7 | 26.2790 | 27.4591 | small |
| gru L168 | 2023-04 | 720 | 31.5464 | 42.5576 |  |
| gru L168 | 2023-05 | 405 | 33.3198 | 53.1134 |  |
| gru L168 | 2023-06 | 341 | 14.6226 | 20.1029 |  |
| gru L168 | 2023-07 | 228 | 12.5171 | 14.8763 |  |
| gru L168 | 2023-08 | 239 | 10.7074 | 15.2539 |  |
| gru L168 | 2023-09 | 660 | 12.5168 | 15.3247 |  |
| gru L168 | 2023-10 | 377 | 17.1770 | 22.8474 |  |
| gru L168 | 2023-11 | 520 | 75.7088 | 106.6621 |  |
| gru L168 | 2023-12 | 744 | 45.6866 | 61.4717 |  |
| gru L168 | 2024-01 | 744 | 70.1494 | 98.6390 |  |
| gru L168 | 2024-02 | 696 | 43.3220 | 62.0642 |  |
| gru L168 | 2024-03 | 744 | 32.5946 | 47.4298 |  |
| gru L168 | 2024-04 | 698 | 30.4885 | 45.2121 |  |
| persistence | 2023-03 | 7 | 24.4286 | 26.3127 | small |
| persistence | 2023-04 | 720 | 32.6797 | 47.7506 |  |
| persistence | 2023-05 | 405 | 33.5683 | 56.5410 |  |
| persistence | 2023-06 | 341 | 17.4680 | 24.0657 |  |
| persistence | 2023-07 | 228 | 13.4408 | 16.1068 |  |
| persistence | 2023-08 | 239 | 10.3351 | 16.4793 |  |
| persistence | 2023-09 | 660 | 12.5841 | 15.9655 |  |
| persistence | 2023-10 | 377 | 18.6419 | 26.0436 |  |
| persistence | 2023-11 | 520 | 90.5002 | 126.8850 |  |
| persistence | 2023-12 | 744 | 52.5481 | 72.8899 |  |
| persistence | 2024-01 | 744 | 87.3353 | 116.7220 |  |
| persistence | 2024-02 | 696 | 46.8593 | 73.0100 |  |
| persistence | 2024-03 | 744 | 36.7140 | 56.3586 |  |
| persistence | 2024-04 | 698 | 35.5299 | 54.2990 |  |
| seasonal_naive | 2023-03 | 7 | 24.4286 | 26.3127 | small |
| seasonal_naive | 2023-04 | 720 | 32.6797 | 47.7506 |  |
| seasonal_naive | 2023-05 | 405 | 33.5683 | 56.5410 |  |
| seasonal_naive | 2023-06 | 341 | 17.4680 | 24.0657 |  |
| seasonal_naive | 2023-07 | 228 | 13.4408 | 16.1068 |  |
| seasonal_naive | 2023-08 | 239 | 10.3351 | 16.4793 |  |
| seasonal_naive | 2023-09 | 660 | 12.5841 | 15.9655 |  |
| seasonal_naive | 2023-10 | 377 | 18.6419 | 26.0436 |  |
| seasonal_naive | 2023-11 | 520 | 90.5002 | 126.8850 |  |
| seasonal_naive | 2023-12 | 744 | 52.5481 | 72.8899 |  |
| seasonal_naive | 2024-01 | 744 | 87.3353 | 116.7220 |  |
| seasonal_naive | 2024-02 | 696 | 46.8593 | 73.0100 |  |
| seasonal_naive | 2024-03 | 744 | 36.7140 | 56.3586 |  |
| seasonal_naive | 2024-04 | 698 | 35.5299 | 54.2990 |  |
| tcn L168 | 2023-03 | 7 | 27.5297 | 28.5470 | small |
| tcn L168 | 2023-04 | 720 | 30.8776 | 42.4241 |  |
| tcn L168 | 2023-05 | 405 | 33.4642 | 53.0327 |  |
| tcn L168 | 2023-06 | 341 | 15.5071 | 20.8681 |  |
| tcn L168 | 2023-07 | 228 | 12.2788 | 14.5882 |  |
| tcn L168 | 2023-08 | 239 | 9.3583 | 14.3231 |  |
| tcn L168 | 2023-09 | 660 | 11.8592 | 14.7761 |  |
| tcn L168 | 2023-10 | 377 | 17.9725 | 23.9660 |  |
| tcn L168 | 2023-11 | 520 | 75.0179 | 106.3926 |  |
| tcn L168 | 2023-12 | 744 | 46.3184 | 62.2206 |  |
| tcn L168 | 2024-01 | 744 | 68.9763 | 97.9719 |  |
| tcn L168 | 2024-02 | 696 | 45.4345 | 63.5447 |  |
| tcn L168 | 2024-03 | 744 | 32.0601 | 46.7699 |  |
| tcn L168 | 2024-04 | 698 | 29.2011 | 44.5292 |  |

## Seasonal validation error

Approved grouping by target month: winter=Dec–Feb, pre-monsoon=Mar–May, monsoon=Jun–Sep, post-monsoon=Oct–Nov. Counts are provided for all four seasons, including empty groups.

### +1h

| Series | Season | n | MAE | RMSE | Bias | Note |
| --- | --- | --- | --- | --- | --- | --- |
| persistence | Monsoon (Jun–Sep) | 1583 | 4.5663 | 7.0093 | -0.0242 |  |
| persistence | Post-monsoon (Oct–Nov) | 950 | 17.3405 | 31.0322 | -0.9026 |  |
| persistence | Pre-monsoon (Mar–May) | 2643 | 15.0316 | 24.5570 | 0.0523 |  |
| persistence | Winter (Dec–Feb) | 2184 | 18.6899 | 27.2393 | 0.0314 |  |
| random_forest L24 | Monsoon (Jun–Sep) | 1583 | 4.2234 | 6.4531 | 0.5701 |  |
| random_forest L24 | Post-monsoon (Oct–Nov) | 950 | 14.1769 | 29.2217 | -1.0704 |  |
| random_forest L24 | Pre-monsoon (Mar–May) | 2643 | 11.2294 | 18.9392 | 0.2470 |  |
| random_forest L24 | Winter (Dec–Feb) | 2184 | 15.1339 | 22.4156 | -0.1281 |  |
| random_forest L48 | Monsoon (Jun–Sep) | 1583 | 4.2073 | 6.4228 | 0.5531 |  |
| random_forest L48 | Post-monsoon (Oct–Nov) | 950 | 14.2389 | 29.9040 | -1.2054 |  |
| random_forest L48 | Pre-monsoon (Mar–May) | 2643 | 11.3108 | 19.0064 | 0.1715 |  |
| random_forest L48 | Winter (Dec–Feb) | 2184 | 15.1102 | 22.6278 | -0.2563 |  |
| seasonal_naive | Monsoon (Jun–Sep) | 1583 | 13.3210 | 17.9967 | -0.9189 |  |
| seasonal_naive | Post-monsoon (Oct–Nov) | 950 | 59.6235 | 97.7069 | -2.8768 |  |
| seasonal_naive | Pre-monsoon (Mar–May) | 2643 | 34.8981 | 53.5143 | -0.3447 |  |
| seasonal_naive | Winter (Dec–Feb) | 2184 | 62.5858 | 90.2761 | 2.0119 |  |

### +6h

| Series | Season | n | MAE | RMSE | Bias | Note |
| --- | --- | --- | --- | --- | --- | --- |
| persistence | Monsoon (Jun–Sep) | 1558 | 12.1578 | 17.1900 | -0.2095 |  |
| persistence | Post-monsoon (Oct–Nov) | 935 | 59.9835 | 90.8576 | -1.9687 |  |
| persistence | Pre-monsoon (Mar–May) | 2628 | 52.4716 | 75.7470 | 0.0264 |  |
| persistence | Winter (Dec–Feb) | 2184 | 65.2347 | 88.6573 | 0.4527 |  |
| seasonal_naive | Monsoon (Jun–Sep) | 1558 | 13.3278 | 18.0307 | -0.9853 |  |
| seasonal_naive | Post-monsoon (Oct–Nov) | 935 | 60.1506 | 98.3816 | -2.7091 |  |
| seasonal_naive | Pre-monsoon (Mar–May) | 2628 | 34.9718 | 53.6341 | -0.3644 |  |
| seasonal_naive | Winter (Dec–Feb) | 2184 | 62.5858 | 90.2761 | 2.0119 |  |
| xgboost L168 | Monsoon (Jun–Sep) | 1558 | 10.4576 | 14.1102 | 0.8742 |  |
| xgboost L168 | Post-monsoon (Oct–Nov) | 935 | 41.0790 | 70.6246 | -7.8222 |  |
| xgboost L168 | Pre-monsoon (Mar–May) | 2628 | 29.5731 | 44.0629 | -1.1989 |  |
| xgboost L168 | Winter (Dec–Feb) | 2184 | 45.7655 | 64.5782 | 0.2103 |  |
| xgboost L24 | Monsoon (Jun–Sep) | 1558 | 10.7060 | 14.4622 | 2.3188 |  |
| xgboost L24 | Post-monsoon (Oct–Nov) | 935 | 41.2113 | 71.4692 | -4.1511 |  |
| xgboost L24 | Pre-monsoon (Mar–May) | 2628 | 29.8303 | 43.9142 | 1.3558 |  |
| xgboost L24 | Winter (Dec–Feb) | 2184 | 45.8997 | 65.5133 | -2.4933 |  |

### +12h

| Series | Season | n | MAE | RMSE | Bias | Note |
| --- | --- | --- | --- | --- | --- | --- |
| persistence | Monsoon (Jun–Sep) | 1528 | 14.3860 | 19.4089 | -0.5551 |  |
| persistence | Post-monsoon (Oct–Nov) | 921 | 67.8915 | 95.4682 | -0.5117 |  |
| persistence | Pre-monsoon (Mar–May) | 2610 | 62.4827 | 87.5026 | -0.2648 |  |
| persistence | Winter (Dec–Feb) | 2184 | 77.4084 | 103.1030 | 1.0209 |  |
| seasonal_naive | Monsoon (Jun–Sep) | 1528 | 13.3871 | 18.1232 | -1.1737 |  |
| seasonal_naive | Post-monsoon (Oct–Nov) | 921 | 59.3462 | 96.8927 | -1.0315 |  |
| seasonal_naive | Pre-monsoon (Mar–May) | 2610 | 34.8768 | 53.5766 | -0.4214 |  |
| seasonal_naive | Winter (Dec–Feb) | 2184 | 62.5858 | 90.2761 | 2.0119 |  |
| xgboost L168 | Monsoon (Jun–Sep) | 1528 | 11.7279 | 15.3734 | 1.5373 |  |
| xgboost L168 | Post-monsoon (Oct–Nov) | 921 | 45.9369 | 75.7676 | -12.2363 |  |
| xgboost L168 | Pre-monsoon (Mar–May) | 2610 | 30.9106 | 45.7882 | -0.6309 |  |
| xgboost L168 | Winter (Dec–Feb) | 2184 | 52.1922 | 72.4036 | 1.4767 |  |
| xgboost L24 | Monsoon (Jun–Sep) | 1528 | 12.1822 | 15.8165 | 2.9955 |  |
| xgboost L24 | Post-monsoon (Oct–Nov) | 921 | 45.8091 | 76.7670 | -5.2469 |  |
| xgboost L24 | Pre-monsoon (Mar–May) | 2610 | 30.7079 | 45.3159 | 3.1016 |  |
| xgboost L24 | Winter (Dec–Feb) | 2184 | 51.9206 | 73.4784 | -3.6025 |  |

### +24h

| Series | Season | n | MAE | RMSE | Bias | Note |
| --- | --- | --- | --- | --- | --- | --- |
| gru L168 | Monsoon (Jun–Sep) | 1468 | 12.7114 | 16.4837 | 1.6513 |  |
| gru L168 | Post-monsoon (Oct–Nov) | 897 | 51.1085 | 82.5508 | -12.6530 |  |
| gru L168 | Pre-monsoon (Mar–May) | 2574 | 31.8272 | 46.4444 | 1.1750 |  |
| gru L168 | Winter (Dec–Feb) | 2184 | 53.2665 | 76.3500 | -4.0254 |  |
| persistence | Monsoon (Jun–Sep) | 1468 | 13.4855 | 18.2657 | -1.3165 |  |
| persistence | Post-monsoon (Oct–Nov) | 897 | 60.2989 | 98.0729 | -0.9351 |  |
| persistence | Pre-monsoon (Mar–May) | 2574 | 34.7361 | 53.4817 | -0.5212 |  |
| persistence | Winter (Dec–Feb) | 2184 | 62.5858 | 90.2761 | 2.0119 |  |
| seasonal_naive | Monsoon (Jun–Sep) | 1468 | 13.4855 | 18.2657 | -1.3165 |  |
| seasonal_naive | Post-monsoon (Oct–Nov) | 897 | 60.2989 | 98.0729 | -0.9351 |  |
| seasonal_naive | Pre-monsoon (Mar–May) | 2574 | 34.7361 | 53.4817 | -0.5212 |  |
| seasonal_naive | Winter (Dec–Feb) | 2184 | 62.5858 | 90.2761 | 2.0119 |  |
| tcn L168 | Monsoon (Jun–Sep) | 1468 | 12.3646 | 16.3025 | 2.7900 |  |
| tcn L168 | Post-monsoon (Oct–Nov) | 897 | 51.0423 | 82.4825 | -13.4456 |  |
| tcn L168 | Pre-monsoon (Mar–May) | 2574 | 31.1626 | 46.0232 | 0.6404 |  |
| tcn L168 | Winter (Dec–Feb) | 2184 | 53.7553 | 76.6515 | -3.8014 |  |

## Error by observed PM2.5 range

Audit bins use validation actuals in µg/m³: <0, [0,30), [30,60), [60,90), [90,120), [120,250), [250,500), and ≥500. The final bin uses the pre-existing 500 µg/m³ extreme threshold. No values were removed. Each subgroup count is shown; n<30 is flagged.

### +1h

| Series | Actual range | n | MAE | RMSE | Bias | P95 |error| | Max |error| | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| persistence | <0 | 0 | — | — | — | — | — |  |
| persistence | 0–<30 | 1164 | 4.0758 | 6.8520 | 1.4729 | 10.7500 | 84.5000 |  |
| persistence | 30–<60 | 1964 | 7.1952 | 11.0422 | 1.4275 | 22.0000 | 87.2500 |  |
| persistence | 60–<90 | 911 | 12.9340 | 19.5815 | 2.1035 | 37.5000 | 139.0000 |  |
| persistence | 90–<120 | 674 | 17.2065 | 24.9171 | 0.1175 | 49.1750 | 184.7500 |  |
| persistence | 120–<250 | 1767 | 20.5368 | 28.9577 | -0.4175 | 60.7500 | 189.5000 |  |
| persistence | 250–<500 | 848 | 27.2562 | 37.8588 | -5.8287 | 76.8250 | 184.7500 |  |
| persistence | ≥500 | 32 | 80.9844 | 118.3119 | -47.5625 | 289.5125 | 360.7500 | small tail sample |
| random_forest L24 | <0 | 0 | — | — | — | — | — |  |
| random_forest L24 | 0–<30 | 1164 | 3.9112 | 6.4107 | 2.4631 | 10.7074 | 73.6653 |  |
| random_forest L24 | 30–<60 | 1964 | 5.6937 | 8.9753 | 1.4992 | 16.3911 | 88.6946 |  |
| random_forest L24 | 60–<90 | 911 | 9.8270 | 15.2614 | 2.8865 | 27.6967 | 150.4965 |  |
| random_forest L24 | 90–<120 | 674 | 12.4384 | 18.1396 | 1.6600 | 36.8314 | 157.1228 |  |
| random_forest L24 | 120–<250 | 1767 | 14.9295 | 21.0212 | 0.2310 | 42.1243 | 168.2573 |  |
| random_forest L24 | 250–<500 | 848 | 24.4493 | 34.1040 | -8.9238 | 67.8022 | 174.0910 |  |
| random_forest L24 | ≥500 | 32 | 84.4161 | 126.9116 | -66.9428 | 273.9452 | 470.3453 | small tail sample |
| random_forest L48 | <0 | 0 | — | — | — | — | — |  |
| random_forest L48 | 0–<30 | 1164 | 3.9116 | 6.3555 | 2.5019 | 10.8373 | 72.6499 |  |
| random_forest L48 | 30–<60 | 1964 | 5.7187 | 8.8757 | 1.5272 | 16.2244 | 84.8562 |  |
| random_forest L48 | 60–<90 | 911 | 9.9668 | 15.4677 | 2.9467 | 27.8027 | 143.9737 |  |
| random_forest L48 | 90–<120 | 674 | 12.0888 | 17.9193 | 1.4334 | 36.5631 | 156.8366 |  |
| random_forest L48 | 120–<250 | 1767 | 14.8891 | 21.0352 | 0.2550 | 41.8043 | 167.5040 |  |
| random_forest L48 | 250–<500 | 848 | 24.4405 | 33.7412 | -9.1756 | 68.2335 | 173.7729 |  |
| random_forest L48 | ≥500 | 32 | 94.8597 | 137.4378 | -81.4974 | 282.1385 | 508.5737 | small tail sample |
| seasonal_naive | <0 | 0 | — | — | — | — | — |  |
| seasonal_naive | 0–<30 | 1164 | 15.4036 | 29.8092 | 11.4401 | 42.2500 | 362.0000 |  |
| seasonal_naive | 30–<60 | 1964 | 20.9075 | 40.3625 | 7.7441 | 62.8875 | 356.7500 |  |
| seasonal_naive | 60–<90 | 911 | 32.8781 | 50.8498 | 10.3512 | 102.7500 | 331.7500 |  |
| seasonal_naive | 90–<120 | 674 | 42.2897 | 57.7393 | 3.9845 | 124.2750 | 265.5000 |  |
| seasonal_naive | 120–<250 | 1767 | 57.3047 | 78.7850 | 6.7937 | 159.2500 | 461.5000 |  |
| seasonal_naive | 250–<500 | 848 | 92.7257 | 118.5113 | -53.1426 | 232.4000 | 367.2500 |  |
| seasonal_naive | ≥500 | 32 | 291.1406 | 317.9818 | -258.9219 | 423.9750 | 798.0000 | small tail sample |

### +6h

| Series | Actual range | n | MAE | RMSE | Bias | P95 |error| | Max |error| | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| persistence | <0 | 0 | — | — | — | — | — |  |
| persistence | 0–<30 | 1145 | 27.6571 | 55.6533 | 24.4954 | 129.2500 | 365.2500 |  |
| persistence | 30–<60 | 1946 | 29.3179 | 49.4636 | 17.7997 | 112.8125 | 361.7500 |  |
| persistence | 60–<90 | 906 | 35.4229 | 50.8854 | 4.3479 | 107.1250 | 259.5000 |  |
| persistence | 90–<120 | 673 | 53.8523 | 70.7802 | -1.7864 | 135.2000 | 354.7500 |  |
| persistence | 120–<250 | 1756 | 65.9748 | 84.4153 | -5.9638 | 154.3125 | 456.2500 |  |
| persistence | 250–<500 | 847 | 88.5217 | 114.7139 | -58.2461 | 231.4250 | 373.0000 |  |
| persistence | ≥500 | 32 | 234.6562 | 292.6010 | -210.1406 | 467.4000 | 911.5000 | small tail sample |
| seasonal_naive | <0 | 0 | — | — | — | — | — |  |
| seasonal_naive | 0–<30 | 1145 | 15.3882 | 29.9431 | 11.4052 | 42.2500 | 362.0000 |  |
| seasonal_naive | 30–<60 | 1946 | 20.9749 | 40.5212 | 7.8329 | 63.1875 | 356.7500 |  |
| seasonal_naive | 60–<90 | 906 | 32.9053 | 50.9435 | 10.4676 | 103.2500 | 331.7500 |  |
| seasonal_naive | 90–<120 | 673 | 42.3217 | 57.7766 | 3.9596 | 124.3500 | 265.5000 |  |
| seasonal_naive | 120–<250 | 1756 | 57.5302 | 79.0046 | 6.9275 | 159.3125 | 461.5000 |  |
| seasonal_naive | 250–<500 | 847 | 92.7130 | 118.5279 | -53.0831 | 232.4500 | 367.2500 |  |
| seasonal_naive | ≥500 | 32 | 291.1406 | 317.9818 | -258.9219 | 423.9750 | 798.0000 | small tail sample |
| xgboost L168 | <0 | 0 | — | — | — | — | — |  |
| xgboost L168 | 0–<30 | 1145 | 16.1302 | 25.7949 | 15.5480 | 40.4262 | 344.5258 |  |
| xgboost L168 | 30–<60 | 1946 | 16.8881 | 27.5387 | 10.9870 | 51.5816 | 326.6622 |  |
| xgboost L168 | 60–<90 | 906 | 22.7697 | 31.6772 | 8.3809 | 63.2187 | 231.3685 |  |
| xgboost L168 | 90–<120 | 673 | 30.4305 | 41.4494 | 3.2414 | 81.7833 | 252.3645 |  |
| xgboost L168 | 120–<250 | 1756 | 41.3780 | 54.2141 | -1.6070 | 107.7901 | 263.5275 |  |
| xgboost L168 | 250–<500 | 847 | 68.8840 | 89.2281 | -54.1371 | 185.0571 | 324.1671 |  |
| xgboost L168 | ≥500 | 32 | 278.9007 | 304.9829 | -278.9007 | 410.9299 | 810.9830 | small tail sample |
| xgboost L24 | <0 | 0 | — | — | — | — | — |  |
| xgboost L24 | 0–<30 | 1145 | 16.9940 | 26.6218 | 16.2657 | 41.8953 | 351.3555 |  |
| xgboost L24 | 30–<60 | 1946 | 17.5618 | 28.1881 | 12.3442 | 56.7882 | 335.0585 |  |
| xgboost L24 | 60–<90 | 906 | 22.6612 | 31.4813 | 10.8282 | 63.2877 | 211.5611 |  |
| xgboost L24 | 90–<120 | 673 | 28.7696 | 40.3758 | 5.9410 | 77.9161 | 270.9388 |  |
| xgboost L24 | 120–<250 | 1756 | 40.4084 | 53.4236 | -1.3230 | 107.0247 | 292.2842 |  |
| xgboost L24 | 250–<500 | 847 | 70.8254 | 90.0177 | -55.3760 | 181.9797 | 333.7136 |  |
| xgboost L24 | ≥500 | 32 | 293.0927 | 321.8836 | -293.0927 | 415.1287 | 811.2633 | small tail sample |

### +12h

| Series | Actual range | n | MAE | RMSE | Bias | P95 |error| | Max |error| | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| persistence | <0 | 0 | — | — | — | — | — |  |
| persistence | 0–<30 | 1121 | 32.1954 | 60.0399 | 29.0872 | 152.2500 | 361.2500 |  |
| persistence | 30–<60 | 1927 | 36.7740 | 60.7395 | 25.5338 | 131.4250 | 375.2500 |  |
| persistence | 60–<90 | 903 | 41.0853 | 57.5916 | 6.2010 | 112.6500 | 337.2500 |  |
| persistence | 90–<120 | 672 | 60.2898 | 76.2631 | -2.5730 | 151.9500 | 387.5000 |  |
| persistence | 120–<250 | 1746 | 78.0310 | 96.7791 | -10.7450 | 177.5000 | 464.5000 |  |
| persistence | 250–<500 | 844 | 103.3459 | 131.5066 | -68.9104 | 256.7500 | 492.0000 |  |
| persistence | ≥500 | 30 | 287.1417 | 324.9083 | -284.6750 | 449.3750 | 860.2500 | small tail sample |
| seasonal_naive | <0 | 0 | — | — | — | — | — |  |
| seasonal_naive | 0–<30 | 1121 | 15.1220 | 29.6124 | 11.0680 | 41.2500 | 362.0000 |  |
| seasonal_naive | 30–<60 | 1927 | 21.0752 | 40.6993 | 7.8778 | 63.2500 | 356.7500 |  |
| seasonal_naive | 60–<90 | 903 | 32.8806 | 50.9700 | 10.6364 | 103.5500 | 331.7500 |  |
| seasonal_naive | 90–<120 | 672 | 42.2842 | 57.7610 | 4.0660 | 124.4250 | 265.5000 |  |
| seasonal_naive | 120–<250 | 1746 | 57.5948 | 79.1254 | 7.2321 | 159.4375 | 461.5000 |  |
| seasonal_naive | 250–<500 | 844 | 92.5011 | 118.3462 | -52.7304 | 232.6000 | 367.2500 |  |
| seasonal_naive | ≥500 | 30 | 284.2583 | 312.2052 | -249.8917 | 409.1875 | 798.0000 | small tail sample |
| xgboost L168 | <0 | 0 | — | — | — | — | — |  |
| xgboost L168 | 0–<30 | 1121 | 17.6884 | 26.7257 | 17.3552 | 40.9431 | 309.4397 |  |
| xgboost L168 | 30–<60 | 1927 | 18.7784 | 31.6358 | 12.5153 | 61.1419 | 287.1104 |  |
| xgboost L168 | 60–<90 | 903 | 26.4074 | 36.3611 | 11.4311 | 70.0632 | 252.0884 |  |
| xgboost L168 | 90–<120 | 672 | 32.6206 | 44.4362 | 5.8305 | 96.8548 | 202.6065 |  |
| xgboost L168 | 120–<250 | 1746 | 43.6407 | 56.3676 | 0.5650 | 114.0894 | 247.0176 |  |
| xgboost L168 | 250–<500 | 844 | 80.1356 | 100.4909 | -67.3715 | 196.2014 | 322.7717 |  |
| xgboost L168 | ≥500 | 30 | 309.3251 | 329.0795 | -309.3251 | 413.7434 | 780.3551 | small tail sample |
| xgboost L24 | <0 | 0 | — | — | — | — | — |  |
| xgboost L24 | 0–<30 | 1121 | 18.9128 | 29.1549 | 18.4292 | 43.6513 | 308.8338 |  |
| xgboost L24 | 30–<60 | 1927 | 20.7165 | 35.4975 | 15.2413 | 65.4384 | 331.7219 |  |
| xgboost L24 | 60–<90 | 903 | 26.0065 | 36.5199 | 15.2273 | 70.7437 | 257.6072 |  |
| xgboost L24 | 90–<120 | 672 | 29.1406 | 41.2552 | 9.4820 | 94.6388 | 221.7861 |  |
| xgboost L24 | 120–<250 | 1746 | 41.8616 | 54.4021 | -1.4265 | 110.8848 | 235.9397 |  |
| xgboost L24 | 250–<500 | 844 | 79.7063 | 99.9934 | -68.5926 | 192.8672 | 334.3319 |  |
| xgboost L24 | ≥500 | 30 | 326.5416 | 347.6478 | -326.5416 | 435.3189 | 789.6456 | small tail sample |

### +24h

| Series | Actual range | n | MAE | RMSE | Bias | P95 |error| | Max |error| | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gru L168 | <0 | 0 | — | — | — | — | — |  |
| gru L168 | 0–<30 | 1080 | 20.8565 | 29.8812 | 20.5852 | 45.9049 | 288.6202 |  |
| gru L168 | 30–<60 | 1884 | 20.4506 | 33.6149 | 14.3390 | 59.7861 | 272.0298 |  |
| gru L168 | 60–<90 | 898 | 26.9111 | 38.2183 | 15.2123 | 66.0755 | 233.4084 |  |
| gru L168 | 90–<120 | 670 | 30.7111 | 43.6945 | 8.7521 | 110.9207 | 204.3401 |  |
| gru L168 | 120–<250 | 1720 | 42.2780 | 54.3622 | -2.0743 | 110.0141 | 192.1436 |  |
| gru L168 | 250–<500 | 841 | 88.1257 | 110.1234 | -82.9519 | 211.6750 | 362.8869 |  |
| gru L168 | ≥500 | 30 | 337.7861 | 357.2679 | -337.7861 | 456.7012 | 770.7032 | small tail sample |
| persistence | <0 | 0 | — | — | — | — | — |  |
| persistence | 0–<30 | 1080 | 15.0134 | 29.6751 | 10.8944 | 39.7750 | 362.0000 |  |
| persistence | 30–<60 | 1884 | 21.1286 | 40.9772 | 7.9729 | 63.8875 | 356.7500 |  |
| persistence | 60–<90 | 898 | 32.8568 | 51.0287 | 10.5907 | 103.9750 | 331.7500 |  |
| persistence | 90–<120 | 670 | 42.2560 | 57.7468 | 4.1818 | 124.5750 | 265.5000 |  |
| persistence | 120–<250 | 1720 | 57.9117 | 79.4181 | 7.6286 | 159.5125 | 461.5000 |  |
| persistence | 250–<500 | 841 | 92.7576 | 118.5484 | -52.8450 | 232.7500 | 367.2500 |  |
| persistence | ≥500 | 30 | 284.2583 | 312.2052 | -249.8917 | 409.1875 | 798.0000 | small tail sample |
| seasonal_naive | <0 | 0 | — | — | — | — | — |  |
| seasonal_naive | 0–<30 | 1080 | 15.0134 | 29.6751 | 10.8944 | 39.7750 | 362.0000 |  |
| seasonal_naive | 30–<60 | 1884 | 21.1286 | 40.9772 | 7.9729 | 63.8875 | 356.7500 |  |
| seasonal_naive | 60–<90 | 898 | 32.8568 | 51.0287 | 10.5907 | 103.9750 | 331.7500 |  |
| seasonal_naive | 90–<120 | 670 | 42.2560 | 57.7468 | 4.1818 | 124.5750 | 265.5000 |  |
| seasonal_naive | 120–<250 | 1720 | 57.9117 | 79.4181 | 7.6286 | 159.5125 | 461.5000 |  |
| seasonal_naive | 250–<500 | 841 | 92.7576 | 118.5484 | -52.8450 | 232.7500 | 367.2500 |  |
| seasonal_naive | ≥500 | 30 | 284.2583 | 312.2052 | -249.8917 | 409.1875 | 798.0000 | small tail sample |
| tcn L168 | <0 | 0 | — | — | — | — | — |  |
| tcn L168 | 0–<30 | 1080 | 19.9688 | 29.2505 | 19.5288 | 48.0929 | 282.2819 |  |
| tcn L168 | 30–<60 | 1884 | 20.2187 | 33.7649 | 14.7630 | 58.2252 | 274.4260 |  |
| tcn L168 | 60–<90 | 898 | 27.0847 | 38.4444 | 16.2409 | 71.2688 | 231.9632 |  |
| tcn L168 | 90–<120 | 670 | 30.6532 | 43.2645 | 10.0444 | 105.7729 | 197.6448 |  |
| tcn L168 | 120–<250 | 1720 | 41.7614 | 53.4729 | -2.0701 | 108.0307 | 177.9284 |  |
| tcn L168 | 250–<500 | 841 | 89.1207 | 110.4834 | -84.4528 | 213.7093 | 354.3013 |  |
| tcn L168 | ≥500 | 30 | 341.7406 | 362.3892 | -341.7406 | 459.2831 | 765.1829 | small tail sample |

## Error distributions and high-pollution observations

Residual is prediction minus actual; positive bias means overprediction. `≥250` is an audit high-pollution grouping and `≥500` is the preserved extreme threshold. Interpret small extreme groups cautiously.

| Horizon | Series | n | Bias | Median residual | MAE | RMSE | Median |e| | P90 |e| | P95 |e| | Max |e| | n ≥250 | n ≥500 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| +24h | gru L168 | 7123 | -2.0627 | 5.5545 | 36.8892 | 59.0000 | 21.8954 | 85.8531 | 124.7210 | 770.7032 | 871 | 30 |
| +1h | persistence | 7360 | -0.0936 | -0.2500 | 14.1643 | 23.9081 | 7.5000 | 35.2500 | 48.7500 | 360.7500 | 880 | 32 |
| +12h | persistence | 7243 | 0.0303 | 0.0000 | 57.5245 | 84.8695 | 36.5000 | 137.2000 | 181.0000 | 860.2500 | 874 | 30 |
| +24h | persistence | 7123 | 0.0395 | -1.2500 | 42.1147 | 69.3716 | 22.2500 | 107.7500 | 153.9500 | 798.0000 | 871 | 30 |
| +6h | persistence | 7305 | -0.1518 | -0.7500 | 48.6508 | 74.3890 | 28.5000 | 117.0000 | 159.4500 | 911.5000 | 879 | 32 |
| +1h | random_forest L24 | 7360 | 0.0351 | 0.5613 | 11.2616 | 19.9269 | 6.1653 | 27.0325 | 39.1313 | 470.3453 | 880 | 32 |
| +1h | random_forest L48 | 7360 | -0.0511 | 0.5950 | 11.2884 | 20.1484 | 6.2272 | 26.7347 | 38.9158 | 508.5737 | 880 | 32 |
| +1h | seasonal_naive | 7360 | -0.0957 | -1.0000 | 41.6647 | 68.9105 | 22.0000 | 106.7500 | 150.2875 | 798.0000 | 880 | 32 |
| +12h | seasonal_naive | 7243 | 0.0761 | -1.2500 | 41.8099 | 68.9554 | 22.0000 | 107.0000 | 152.2250 | 798.0000 | 874 | 30 |
| +24h | seasonal_naive | 7123 | 0.0395 | -1.2500 | 42.1147 | 69.3716 | 22.2500 | 107.7500 | 153.9500 | 798.0000 | 871 | 30 |
| +6h | seasonal_naive | 7305 | -0.0865 | -1.0000 | 41.8342 | 69.1348 | 22.0000 | 107.0000 | 152.2000 | 798.0000 | 879 | 32 |
| +24h | tcn L168 | 7123 | -2.0523 | 5.6596 | 36.7191 | 58.9782 | 21.6365 | 87.0607 | 123.8679 | 765.1829 | 871 | 30 |
| +12h | xgboost L168 | 7243 | -1.0137 | 4.3915 | 35.1916 | 55.8215 | 20.5956 | 83.5202 | 117.9287 | 780.3551 | 874 | 30 |
| +6h | xgboost L168 | 7305 | -1.1832 | 3.5680 | 31.8100 | 51.2462 | 18.8286 | 74.5658 | 104.4470 | 810.9830 | 879 | 32 |
| +12h | xgboost L24 | 7243 | -0.0038 | 6.2520 | 35.1162 | 56.3038 | 20.9348 | 82.4333 | 115.0100 | 789.6456 | 874 | 30 |
| +6h | xgboost L24 | 7305 | -0.2945 | 5.0880 | 32.0125 | 51.7237 | 19.0433 | 74.1975 | 102.8070 | 811.2633 | 879 | 32 |

### Largest validation absolute errors for each selected candidate

| Horizon | Selected candidate | Target time | Actual | Predicted | Residual | |error| |
| --- | --- | --- | --- | --- | --- | --- |
| +1h | random_forest L24 | 2023-11-12 23:00:00 | 973.000 | 502.655 | -470.345 | 470.345 |
| +1h | random_forest L24 | 2023-11-12 22:00:00 | 612.250 | 305.628 | -306.622 | 306.622 |
| +1h | random_forest L24 | 2023-11-20 06:00:00 | 550.250 | 303.040 | -247.210 | 247.210 |
| +1h | random_forest L24 | 2024-03-25 02:00:00 | 402.000 | 227.909 | -174.091 | 174.091 |
| +1h | random_forest L24 | 2023-11-05 13:00:00 | 233.250 | 401.507 | 168.257 | 168.257 |
| +24h | tcn L168 | 2023-11-12 23:00:00 | 973.000 | 207.817 | -765.183 | 765.183 |
| +24h | tcn L168 | 2024-01-13 21:00:00 | 781.500 | 310.741 | -470.759 | 470.759 |
| +24h | tcn L168 | 2024-01-13 20:00:00 | 734.250 | 288.994 | -445.256 | 445.256 |
| +24h | tcn L168 | 2024-01-13 22:00:00 | 744.500 | 301.808 | -442.692 | 442.692 |
| +24h | tcn L168 | 2024-01-14 04:00:00 | 672.250 | 240.209 | -432.041 | 432.041 |
| +6h | xgboost L168 | 2023-11-12 23:00:00 | 973.000 | 162.017 | -810.983 | 810.983 |
| +6h | xgboost L168 | 2023-11-12 22:00:00 | 612.250 | 173.718 | -438.532 | 438.532 |
| +6h | xgboost L168 | 2023-11-20 07:00:00 | 591.500 | 203.154 | -388.346 | 388.346 |
| +6h | xgboost L168 | 2024-01-13 20:00:00 | 734.250 | 360.884 | -373.366 | 373.366 |
| +6h | xgboost L168 | 2023-11-04 14:00:00 | 580.500 | 230.338 | -350.162 | 350.162 |
| +12h | xgboost L24 | 2023-11-12 23:00:00 | 973.000 | 183.354 | -789.646 | 789.646 |
| +12h | xgboost L24 | 2024-01-13 21:00:00 | 781.500 | 335.089 | -446.411 | 446.411 |
| +12h | xgboost L24 | 2023-11-12 22:00:00 | 612.250 | 190.488 | -421.762 | 421.762 |
| +12h | xgboost L24 | 2024-01-13 20:00:00 | 734.250 | 313.506 | -420.744 | 420.744 |
| +12h | xgboost L24 | 2024-01-13 22:00:00 | 744.500 | 347.871 | -396.629 | 396.629 |

## Scientific interpretation

1. **Deep learning versus traditional ML:** the best traditional candidate has lower validation MAE at +1h, +6h, and +12h; the best deep candidate wins at +24h. Deep learning therefore does not outperform traditional ML consistently in this experiment.
2. **Both simple baselines:** a horizon-specific validation winner beats both simple baselines on both MAE and RMSE at all four horizons. No single candidate wins all horizons; the selected candidate changes by horizon.
3. **Horizon-specific winner:** Random Forest at +1h, XGBoost at +6h/+12h, and TCN at +24h.
4. **24h TCN monthly robustness:** the selected TCN has lower monthly MAE than each baseline in 13/14 months, but beats the overall runner-up in only 8/14 months. The baseline advantage is broadly consistent month to month; its lead over the next-best candidate is less consistent. These are descriptive counts, not a statistical robustness test.
5. **Extreme values:** selected-candidate MAE rises sharply on actuals ≥500 µg/m³: 84.42 (n=32) at +1h, 278.90 (n=32) at +6h, 326.54 (n=30) at +12h, and 341.74 (n=30) at +24h, versus overall MAEs of 11.26, 31.81, 35.12, and 36.72. Bias is negative in these groups, indicating underprediction. Each extreme subgroup is sparse relative to roughly 7,000 total rows, so these estimates are uncertain.
6. **Limitations:** one Delhi CPCB/DPCC station, one contiguous validation period, one seed per candidate, and a single target variable with lag/calendar features. Comparing many candidates on the same validation interval can make selected performance optimistic. These results do not establish India-wide representativeness or cross-city generalization; test performance remains unknown.

### +24h TCN monthly paired wins

| Comparator | TCN lower-MAE months / paired months | Winning months |
|---|---:|---|
| Persistence | 13/14 | 2023-04, 2023-05, 2023-06, 2023-07, 2023-08, 2023-09, 2023-10, 2023-11, 2023-12, 2024-01, 2024-02, 2024-03, 2024-04 |
| Seasonal naive | 13/14 | 2023-04, 2023-05, 2023-06, 2023-07, 2023-08, 2023-09, 2023-10, 2023-11, 2023-12, 2024-01, 2024-02, 2024-03, 2024-04 |
| Overall runner-up | 8/14 | 2023-04, 2023-07, 2023-08, 2023-09, 2023-11, 2024-01, 2024-03, 2024-04 |

## Recommended validation-selected candidates

| Horizon | Candidate | MAE | RMSE | MASE | Beats both baselines on MAE |
| --- | --- | --- | --- | --- | --- |
| +1h | random_forest L24 | 11.2616 | 19.9269 | 0.7715 | Yes |
| +6h | xgboost L168 | 31.8100 | 51.2462 | 2.1791 | Yes |
| +12h | xgboost L24 | 35.1162 | 56.3038 | 2.4056 | Yes |
| +24h | tcn L168 | 36.7191 | 58.9782 | 2.5154 | Yes |

These are validation-based recommendations only. A final test-set evaluation requires a separate explicit decision and approval.

## Test gate

**CLOSED.** This audit read run artifacts and validation prediction files only. It did not open the canonical dataset, construct test windows, read test-period PM2.5 values, generate test predictions, or calculate test scores. No model was retrained and no run artifacts were modified.
