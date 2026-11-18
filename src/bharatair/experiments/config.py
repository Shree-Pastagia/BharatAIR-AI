"""Frozen, bounded Phase 3 experiment settings."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from bharatair.features.windows import HORIZONS, INPUT_LENGTHS, LONG_GAP_THRESHOLD
from bharatair.models.classical import CLASSICAL_CONFIGS
from bharatair.models.neural import NEURAL_CONFIGS


@dataclass(frozen=True)
class ExperimentConfig:
    seed: int = 42
    train_fraction: float = 0.70
    validation_fraction: float = 0.15
    input_lengths: tuple[int, ...] = INPUT_LENGTHS
    horizons: tuple[int, ...] = HORIZONS
    long_gap_threshold_hours: int = LONG_GAP_THRESHOLD
    common_comparison_cohort: str = "intersection of eligible issue times across 24/48/168h windows"
    split_rule: str = "issue and target timestamps must lie in same chronological partition; windows crossing next split target boundary are purged"
    continuity_rule: str = "all hourly timestamps from first input through forecast target must be observed"
    seasonal_naive_rule: str = "actual observation at t+h-24; for h<=24, confirmed no later than issue time t"
    season_definition: str = "winter=Dec-Feb; pre-monsoon=Mar-May; monsoon=Jun-Sep; post-monsoon=Oct-Nov"
    neural_epochs: int = 8
    neural_patience: int = 2
    neural_batch_size: int = 512
    neural_hidden_size: int = 24
    tcn_channels: int = 8
    bootstrap_replicates: int = 500

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["input_lengths"] = list(self.input_lengths)
        data["horizons"] = list(self.horizons)
        data["traditional_models"] = CLASSICAL_CONFIGS
        data["deep_models"] = NEURAL_CONFIGS
        return data
