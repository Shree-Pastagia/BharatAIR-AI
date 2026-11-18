"""Diagnostic plots for frozen validation-selected test predictions."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def test_diagnostics(frame: pd.DataFrame, horizon: int, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ordered = frame.sort_values("target_timestamp").copy()
    ordered["target_timestamp"] = pd.to_datetime(ordered["target_timestamp"])
    ordered["residual"] = ordered["predicted"] - ordered["actual"]
    fig, axes = plt.subplots(3, 1, figsize=(12, 12), constrained_layout=True)
    show = ordered.head(24 * 14)
    axes[0].plot(show["target_timestamp"], show["actual"], label="Observed", linewidth=1)
    axes[0].plot(show["target_timestamp"], show["predicted"], label="Predicted", linewidth=1)
    axes[0].set_title(f"Test predictions, first 14 eligible days (+{horizon}h)")
    axes[0].set_ylabel("PM2.5 (µg/m³)")
    axes[0].legend()
    axes[1].scatter(ordered["predicted"], ordered["residual"], s=8, alpha=0.35)
    axes[1].axhline(0, color="black", linewidth=1)
    axes[1].set_title("Residuals versus prediction")
    axes[1].set_xlabel("Predicted PM2.5 (µg/m³)")
    axes[1].set_ylabel("Prediction − observed")
    axes[2].hist(ordered["residual"], bins=50, color="#4472C4", alpha=0.85)
    axes[2].axvline(0, color="black", linewidth=1)
    axes[2].set_title("Test residual distribution")
    axes[2].set_xlabel("Prediction − observed (µg/m³)")
    path = output_dir / f"test_diagnostics_h{horizon:02d}.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path
