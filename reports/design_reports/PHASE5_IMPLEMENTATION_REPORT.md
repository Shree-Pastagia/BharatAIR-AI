# Phase 5 Implementation Report

## Status

The dedicated Phase 5 execution backend is implemented for validation-only A/B/C runs, but its CLI remains deliberately plan-only. No real CPCB data was passed through the backend, no real run directory was created, no model training was launched on the real cohort, and no test partition values were evaluated.

## Implemented

- `runner.py` keeps isolated planning and safety helpers. Candidate expansion retains the full **17,280 planned definitions**, across all 112 stations, all three experiments, all model families/lookbacks/horizons, both B normalization variants, and separate primary/Pune cohorts. Floors label candidates as selection-ineligible; zero-train candidates are structural failures. Planned definitions, skipped candidates, attempted fits and eligible completed results remain distinct.
- `engine.py` adds station timelines and same-station hourly windows. Inputs end at issue time; target is issue+h; input-to-target gaps invalidate a sample; issue/target split crossings are purged; validation input histories may use only causal earlier observations. Test values are unavailable to this API.
- Exact common validation issue-time intersections are computed for each station and horizon across 24/48/168-hour lookbacks and used for A/B/C validation arrays. Actual sample counts are checked against floors before fitting.
- A fits station-specific candidates; B pools station examples without concatenating time series, supports global and station-aware train-only scaling, adds training-derived categorical identity for traditional models and a learned embedding for neural models; C fits only peer-station training examples, uses global peer-only scaling, excludes station identity, and permits held-out station values only in its causal validation examples.
- Classical and neural candidates use the Phase 3 model classes/configurations and seed protocol; traditional execution is CPU and neural execution uses the selected device. Per-candidate CUDA memory peaks are captured and failures do not become zero-valued success records.
- Persistence and seasonal-naive validation metrics are emitted per station/horizon. Seasonal references are no later than issue time.
- Candidate checkpoints, validation metrics, predictions and metadata are written atomically, checksummed and committed only after row-count and checkpoint-reload checks. Resume checks run/candidate/config/data/split/preprocessing provenance; completed runs cannot be resumed or overwritten. Validation selection is per unit/horizon using eligible completed validation MAE only.
- `--evaluate-test` is rejected. The CLI requires `--plan-only` and cannot execute model fits; the execution backend is callable for later reviewed use.

## Test-lock evidence

The data loader uses Parquet predicate filters grouped by station: `station_id == station` and `collected_at < that station's frozen city test cutoff`. It checks all returned timestamps before building station timelines. Timelines contain only pre-test values; example assembly only emits train and validation arrays and stops before test issue processing. There is no test-window, prediction, or scoring API in the Phase 5 backend.

Synthetic tests verify the predicate arguments, rejection of a returned at/after-cutoff row, causal windows, boundary purging, absence of the synthetic test sentinel in validation arrays, and validation target timestamps before the test boundary. The claim is limited to preventing test rows from entering the validation pipeline; Parquet predicate filtering does not guarantee that physical row-group bytes containing such rows are never read.

## Verification

- `py_compile` succeeded for the Phase 5 runner, engine and tests.
- `python -m pytest tests/test_phase5_runner.py -q`: **17 passed**.
- `python -m pytest -q`: **57 passed**.
- Synthetic fits exercised all six model families; additional synthetic cases exercised pooled neural embedding, pooled traditional station identity, station-aware inverse scaling, and unseen-station C behavior.
- CUDA telemetry success/reset was verified with mocked CUDA APIs; telemetry failure and CPU not-applicable behavior were tested. No GPU training was run.

## Changed files

- `src/bharatair/phase5/runner.py`
- `src/bharatair/phase5/engine.py` (new)
- `tests/test_phase5_runner.py`
- `reports/PHASE5_IMPLEMENTATION_REPORT.md`

No Phase 3/4 files or artifacts were modified. Test gates remain unchanged.

## Remaining blockers and limitations

1. Full execution against the CPCB panel remains unverified. Before the pilot, review the code and run a synthetic end-to-end executor check in a temporary root; the present synthetic fit tests cover candidate families and A/B/C data paths but do not execute the 72-candidate orchestration across a full synthetic cohort.
2. No real RTX 4060 Phase 5 telemetry has been measured; only mocked unit coverage exists. CUDA runtime and memory behavior must be checked during the separately approved synthetic CUDA smoke test.
3. Candidate-level validation output exists; city/tier median and observation-weighted aggregate reporting still needs a separate reporting implementation before full Phase 5 interpretation.
4. The 17,280-grid candidate enumeration and below-floor disposition have unit coverage, but actual eligibility counts should be reconciled against exact issue-time windows on synthetic/full timestamp fixtures before any production pilot.
5. No Phase 5 test evaluator exists. Test scoring remains intentionally unavailable until a separate gate implementation and approval.

The real pilot and all real CPCB training remain unlaunched. Keep the CLI plan-only pending review of these remaining items.
