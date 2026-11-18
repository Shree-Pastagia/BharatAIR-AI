# BharatAir Phase 5 — Pre-Pilot Verification

**Status: synthetic software verification passed; CUDA smoke is blocked by the active Python environment. The CLI remains plan-only. No pilot authorization is implied.** No real CPCB PM2.5 values were loaded, no real run directory was created, and no test values were evaluated.

## Commands executed

| Command / operation | Result |
|---|---|
| `C:\Python313\python.exe -m py_compile src/bharatair/phase5/runner.py src/bharatair/phase5/engine.py tests/test_phase5_runner.py` | Passed. |
| `C:\Python313\python.exe -m pytest tests/test_phase5_runner.py -q` | 17 passed before the final orchestration additions. |
| `C:\Python313\python.exe -m pytest tests/test_phase5_runner.py::test_synthetic_full_a_b_c_orchestration_and_interrupted_resume -q` | Passed (rerun after adding report-artifact assertions; 22.14 s). |
| `C:\Python313\python.exe -m pytest -q` | 61 passed in 56.36 s. |
| CUDA smoke script with `C:\Python313\python.exe` | Did not start model fitting: `torch.cuda.is_available()` was false. |
| `C:\Python313\python.exe -c "import torch,sys; print(sys.executable); print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())"` | `C:\Python313\python.exe`; PyTorch `2.15.0+cpu`; CUDA build `None`; CUDA unavailable. |
| `py -0p` and read-only PyTorch checks in Python 3.12 / 3.11 | Python 3.12 and 3.11 are installed, but neither has PyTorch. |
| `nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader` | NVIDIA GeForce RTX 4060 Laptop GPU, 8188 MiB, driver 621.01 visible to the OS. |

No packages were installed and no environment was changed. The GPU is visible, but the available Python environment cannot run the requested CUDA LSTM/GRU/TCN smoke test. Therefore no CUDA memory or runtime measurements are available; this remains a blocking verification item.

## Synthetic A/B/C orchestration

`test_synthetic_full_a_b_c_orchestration_and_interrupted_resume` executes the orchestration function in a pytest temporary root with generated hourly observations and frozen chronological boundaries. It uses an explicit, small orchestration fixture rather than fitting the full 17,280-candidate design:

- A: one station-specific Linear Regression candidate completed.
- B: one pooled global-normalization Linear Regression candidate completed; a second station-aware candidate was deliberately failed to verify failure isolation. Separate synthetic fitter tests cover station-aware scaling and pooled station identity.
- C: one held-out-station Linear Regression candidate completed. Assertions verify that training contains only the peer station and validation only the held-out station.

The test asserts validation predictions, metrics, baseline outputs, selection output and station/city-tier/baseline-comparison report files exist. It also interrupts after the candidate commit, resumes the same incomplete run, and verifies the committed candidate is provenance-checked and reused. The B failure produces its own failure record while the already-completed candidate retains a valid completion marker.

The separate candidate-manifest tests verify that the entire **17,280 planned definitions** remain enumerated, including below-floor and structurally untrainable candidates. Zero-training configurations are marked structurally untrainable; below-floor train/validation configurations remain present and ineligible for selection.

## City, tier and baseline reporting

Validation reporting produces station-level metrics and city/tier/overall summaries with median station MAE/RMSE separated from observation-weighted MAE/RMSE. Tier A and Tier B remain separate; Pune remains a separate cohort. Candidate-versus-baseline comparisons join on station, horizon, issue timestamp and target timestamp, and report sample count and MAE/RMSE improvement against persistence and seasonal naive. Synthetic tests verify both baseline types, matched sample counts and separate cohorts/scopes.

## Test lock and leakage checks

- The Parquet source loader requests station values only under station-specific `collected_at < test_start` filters. It rejects any row returned at/after the station cutoff.
- `execute_validation` independently rejects an input panel containing a timestamp at/after that station's test cutoff before candidate planning, fingerprinting, feature construction or fitting. A synthetic test runs that rejection for A, B and C and verifies no run directory is created.
- `build_examples` creates only train/validation examples, purges issue-target boundary crossings, requires all same-station hourly observations, and checks the full interval for gaps. Synthetic test sentinels in the test partition do not appear in validation targets/predictions.
- B station-aware scalers and categories are fitted from training examples only; the held-out C station is absent from model/scaler training and has no learned identity. C uses the training-global fallback and causal held-out history only for validation inputs.
- As a precise limitation, Parquet predicate filtering prevents test rows from entering the validation pipeline; it does not guarantee physical row-group bytes containing test rows are never read.

## Phase 3/4 preservation

A SHA-256 and size snapshot was taken for 490 protected Phase 3/4 files (Phase 3 audit/run/smoke artifacts, Phase 4 reports/raw audit data and the canonical Delhi dataset), then compared after verification. **490/490 matched; no changed protected files.** The `runs/` directory still contains only the three pre-existing Phase 3 runs; no Phase 5 run directory was created.

## Remaining blocker

The CUDA smoke could not run because `C:\Python313` currently has CPU-only PyTorch `2.15.0+cpu`. The other installed interpreters have no PyTorch. Installing or changing the environment was outside this request, so the actual GPU fitting, checkpoint reload on CUDA and allocated/reserved memory measurements remain unverified. Keep the CLI plan-only until this is resolved and the CUDA smoke passes.

**No real training, CPCB PM2.5 access, or test evaluation occurred. Stop condition met; awaiting explicit pilot authorization after the CUDA verification blocker is resolved.**
