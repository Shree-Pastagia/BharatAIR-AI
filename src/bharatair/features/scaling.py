"""Train-only numerical normalization for neural networks."""

from __future__ import annotations

import numpy as np


class TrainOnlyScaler:
    def fit(self, train_sequences: np.ndarray, train_targets: np.ndarray) -> "TrainOnlyScaler":
        self.input_mean_ = float(train_sequences.mean())
        self.input_scale_ = float(train_sequences.std()) or 1.0
        self.target_mean_ = float(train_targets.mean())
        self.target_scale_ = float(train_targets.std()) or 1.0
        return self

    def transform_x(self, values: np.ndarray) -> np.ndarray:
        return ((values - self.input_mean_) / self.input_scale_).astype(np.float32)

    def transform_y(self, values: np.ndarray) -> np.ndarray:
        return ((values - self.target_mean_) / self.target_scale_).astype(np.float32)

    def inverse_y(self, values: np.ndarray) -> np.ndarray:
        return values * self.target_scale_ + self.target_mean_

    def state(self) -> dict[str, float]:
        return {"input_mean": self.input_mean_, "input_scale": self.input_scale_, "target_mean": self.target_mean_, "target_scale": self.target_scale_}
