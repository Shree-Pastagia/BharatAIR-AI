"""Bounded traditional regression candidates."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor


CLASSICAL_CONFIGS: dict[str, dict[str, Any]] = {
    "linear_regression": {"estimator": "LinearRegression", "scale_features": True},
    "random_forest": {"n_estimators": 80, "max_depth": 14, "min_samples_leaf": 3, "max_features": 0.8, "n_jobs": 12},
    "xgboost": {"n_estimators": 180, "max_depth": 4, "learning_rate": 0.05, "subsample": 0.85, "colsample_bytree": 0.8, "reg_lambda": 1.0, "n_jobs": 8, "tree_method": "hist", "objective": "reg:squarederror"},
}


def make_classical_model(name: str, seed: int, device: str = "cpu") -> Any:
    if name == "linear_regression":
        return Pipeline([("scale", StandardScaler()), ("estimator", LinearRegression())])
    if name == "random_forest":
        return RandomForestRegressor(**CLASSICAL_CONFIGS[name], random_state=seed)
    if name == "xgboost":
        cfg = dict(CLASSICAL_CONFIGS[name])
        if device == "cuda":
            try:
                import torch
                if torch.cuda.is_available():
                    cfg["device"] = "cuda"
            except Exception:
                pass
        return XGBRegressor(**cfg, random_state=seed, verbosity=0)
    raise ValueError(f"Unknown traditional model: {name}")


def predict_classical(model: Any, features: np.ndarray) -> np.ndarray:
    return np.asarray(model.predict(features), dtype=np.float64).reshape(-1)


def classical_importance(model: Any, name: str, feature_names: list[str]) -> list[dict[str, Any]]:
    if name == "linear_regression":
        estimator = model.named_steps["estimator"]
        values = np.asarray(estimator.coef_).reshape(-1)
        return sorted([{"feature": key, "coefficient": float(value), "importance": abs(float(value))} for key, value in zip(feature_names, values)], key=lambda item: item["importance"], reverse=True)
    values = np.asarray(model.feature_importances_).reshape(-1)
    return sorted([{"feature": key, "importance": float(value)} for key, value in zip(feature_names, values)], key=lambda item: item["importance"], reverse=True)
