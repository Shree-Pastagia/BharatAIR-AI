"""Compact PyTorch recurrent and temporal convolution regressors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from bharatair.features.scaling import TrainOnlyScaler


@dataclass
class NeuralFit:
    model: nn.Module
    scaler: TrainOnlyScaler
    training_seconds: float
    best_epoch: int
    train_loss_history: list[float]
    validation_loss_history: list[float]


class RecurrentRegressor(nn.Module):
    def __init__(self, kind: str, hidden_size: int, calendar_size: int = 6):
        super().__init__()
        layer = nn.LSTM if kind == "lstm" else nn.GRU
        self.rnn = layer(input_size=1, hidden_size=hidden_size, num_layers=1, batch_first=True)
        self.head = nn.Sequential(nn.Linear(hidden_size + calendar_size, 32), nn.ReLU(), nn.Dropout(0.1), nn.Linear(32, 1))

    def forward(self, sequence: torch.Tensor, calendar: torch.Tensor) -> torch.Tensor:
        encoded, _ = self.rnn(sequence)
        return self.head(torch.cat([encoded[:, -1, :], calendar], dim=1)).squeeze(-1)


class CausalBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int, dilation: int):
        super().__init__()
        self.padding = (kernel_size - 1) * dilation
        self.conv1 = nn.Conv1d(in_channels, out_channels, kernel_size, padding=self.padding, dilation=dilation)
        self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size, padding=self.padding, dilation=dilation)
        self.skip = nn.Conv1d(in_channels, out_channels, 1) if in_channels != out_channels else nn.Identity()
        self.dropout = nn.Dropout(0.1)
        self.activation = nn.ReLU()

    def _causal(self, layer: nn.Conv1d, x: torch.Tensor) -> torch.Tensor:
        return layer(x)[..., : x.shape[-1]]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.dropout(self.activation(self._causal(self.conv1, x)))
        y = self.dropout(self.activation(self._causal(self.conv2, y)))
        return self.activation(y + self.skip(x))


class TCNRegressor(nn.Module):
    def __init__(self, channels: int = 8, dilations: tuple[int, ...] = (1, 2, 4, 8, 16, 32), calendar_size: int = 6):
        super().__init__()
        blocks = [CausalBlock(1 if idx == 0 else channels, channels, kernel_size=3, dilation=dilation) for idx, dilation in enumerate(dilations)]
        self.network = nn.Sequential(*blocks)
        self.head = nn.Sequential(nn.Linear(channels + calendar_size, 32), nn.ReLU(), nn.Dropout(0.1), nn.Linear(32, 1))

    def forward(self, sequence: torch.Tensor, calendar: torch.Tensor) -> torch.Tensor:
        encoded = self.network(sequence.transpose(1, 2))
        return self.head(torch.cat([encoded[:, :, -1], calendar], dim=1)).squeeze(-1)


NEURAL_CONFIGS: dict[str, dict[str, Any]] = {
    "lstm": {"hidden_size": 24, "max_epochs": 8, "patience": 2, "batch_size": 512, "learning_rate": 0.001},
    "gru": {"hidden_size": 24, "max_epochs": 8, "patience": 2, "batch_size": 512, "learning_rate": 0.001},
    "tcn": {"channels": 8, "kernel_size": 3, "dilations": [1, 2, 4, 8, 16, 32], "max_epochs": 8, "patience": 2, "batch_size": 512, "learning_rate": 0.001},
}


def build_neural_model(name: str, input_length: int = 168) -> nn.Module:
    config = NEURAL_CONFIGS[name]
    if name in {"lstm", "gru"}:
        return RecurrentRegressor(name, int(config["hidden_size"]))
    if name == "tcn":
        dilations = tuple(int(value) for value in config["dilations"])
        receptive_field = 1 + 4 * sum(dilations)
        if receptive_field < input_length:
            raise ValueError(f"TCN receptive field {receptive_field} is shorter than the {input_length}-hour input")
        return TCNRegressor(int(config["channels"]), dilations=dilations)
    raise ValueError(f"Unknown neural model: {name}")


def fit_neural(
    name: str,
    train_sequences: np.ndarray,
    train_calendar: np.ndarray,
    train_targets: np.ndarray,
    validation_sequences: np.ndarray,
    validation_calendar: np.ndarray,
    validation_targets: np.ndarray,
    *,
    seed: int,
    input_length: int = 168,
    device: str = "cpu",
) -> NeuralFit:
    import time

    config = NEURAL_CONFIGS[name]
    torch.manual_seed(seed)
    np.random.seed(seed)
    generator = torch.Generator().manual_seed(seed)
    scaler = TrainOnlyScaler().fit(train_sequences, train_targets)
    tx = scaler.transform_x(train_sequences)
    vx = scaler.transform_x(validation_sequences)
    ty = scaler.transform_y(train_targets)
    vy = scaler.transform_y(validation_targets)
    train_ds = TensorDataset(torch.from_numpy(tx[..., None]), torch.from_numpy(train_calendar.astype(np.float32)), torch.from_numpy(ty))
    loader = DataLoader(train_ds, batch_size=config["batch_size"], shuffle=True, generator=generator, num_workers=0)
    model = build_neural_model(name, input_length=input_length).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config["learning_rate"])
    loss_fn = nn.MSELoss()
    v_seq = torch.from_numpy(vx[..., None]).to(device)
    v_cal = torch.from_numpy(validation_calendar.astype(np.float32)).to(device)
    v_y = torch.from_numpy(vy).to(device)
    best_state = None
    best_loss = float("inf")
    best_epoch = 0
    stale = 0
    train_history: list[float] = []
    validation_history: list[float] = []
    start_time = time.perf_counter()
    for epoch in range(1, int(config["max_epochs"]) + 1):
        model.train()
        weighted_loss = 0.0
        total = 0
        for seq, cal, target in loader:
            seq, cal, target = seq.to(device), cal.to(device), target.to(device)
            optimizer.zero_grad(set_to_none=True)
            prediction = model(seq, cal)
            loss = loss_fn(prediction, target)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            weighted_loss += float(loss.detach()) * len(target)
            total += len(target)
        train_loss = weighted_loss / max(total, 1)
        model.eval()
        with torch.no_grad():
            val_loss = float(loss_fn(model(v_seq, v_cal), v_y))
        train_history.append(train_loss)
        validation_history.append(val_loss)
        if val_loss < best_loss - 1e-7:
            best_loss, best_epoch, stale = val_loss, epoch, 0
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        else:
            stale += 1
            if stale >= int(config["patience"]):
                break
    if best_state is None:
        raise RuntimeError("Training did not produce a validation checkpoint")
    model.load_state_dict(best_state)
    model.to(device).eval()
    return NeuralFit(model, scaler, time.perf_counter() - start_time, best_epoch, train_history, validation_history)


def predict_neural(model: nn.Module, scaler: TrainOnlyScaler, sequences: np.ndarray, calendar: np.ndarray, *, device: str = "cpu", batch_size: int = 1024) -> np.ndarray:
    model.eval()
    scaled = scaler.transform_x(sequences)
    outputs: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(scaled), batch_size):
            seq = torch.from_numpy(scaled[start : start + batch_size, :, None]).to(device)
            cal = torch.from_numpy(calendar[start : start + batch_size].astype(np.float32)).to(device)
            prediction = model(seq, cal).cpu().numpy()
            outputs.append(prediction)
    return scaler.inverse_y(np.concatenate(outputs)).astype(np.float64)
