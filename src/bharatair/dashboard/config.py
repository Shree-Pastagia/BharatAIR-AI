"""Configuration constants for BharatAir Streamlit Dashboard.

Defines styling palettes, navigation pages, pilot station metadata,
audited benchmark results, and NAAQS air quality thresholds.
"""

from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data" / "processed"
RUNS_DIR = REPO_ROOT / "runs"
DEFAULT_RUN_ID = "phase3_cuda_full_20261117_073000"
PHASE3_RUN_DIR = RUNS_DIR / DEFAULT_RUN_ID

# Verified pilot station metadata (Dwarka Sector 8, Delhi)
PILOT_STATION = {
    "station_id": "site_1422",
    "station_name": "Dwarka-Sector 8, Delhi - DPCC",
    "city": "Delhi",
    "state": "Delhi",
    "network": "CPCB CAAQM",
    "agency": "Delhi Pollution Control Committee (DPCC)",
    "parameter": "PM2.5",
    "unit": "µg/m³",
    "latitude": 28.5710274,
    "longitude": 77.0719006,
    "elevation_m": 216,
    "total_observations": 63178,
    "active_span_hours": 66470,
    "missingness_pct": 4.953,
    "start_date": "2018-02-01",
    "end_date": "2025-09-01",
    "active_months": 92,
}

# Audited Benchmark Winners
BENCHMARK_WINNERS = {
    1: {
        "model": "random_forest",
        "display_name": "Random Forest",
        "family": "traditional_ml",
        "input_hours": 24,
        "horizon_hours": 1,
        "mae": 11.2616,
        "rmse": 19.9269,
        "baseline_persistence_mae": 14.1643,
        "improvement_pct": 20.5,
        "candidate_id": "phase3_cuda_full_20261117_073000__random_forest__L24__H1",
    },
    6: {
        "model": "xgboost",
        "display_name": "XGBoost",
        "family": "traditional_ml",
        "input_hours": 168,
        "horizon_hours": 6,
        "mae": 31.8100,
        "rmse": 51.2462,
        "baseline_persistence_mae": 48.6508,
        "improvement_pct": 34.6,
        "candidate_id": "phase3_cuda_full_20261117_073000__xgboost__L168__H6",
    },
    12: {
        "model": "xgboost",
        "display_name": "XGBoost",
        "family": "traditional_ml",
        "input_hours": 24,
        "horizon_hours": 12,
        "mae": 35.1162,
        "rmse": 56.3038,
        "baseline_persistence_mae": 57.5245,
        "improvement_pct": 38.9,
        "candidate_id": "phase3_cuda_full_20261117_073000__xgboost__L24__H12",
    },
    24: {
        "model": "tcn",
        "display_name": "Temporal Convolutional Network (TCN)",
        "family": "deep_learning",
        "input_hours": 168,
        "horizon_hours": 24,
        "mae": 36.7191,
        "rmse": 58.9782,
        "baseline_persistence_mae": 42.1147,
        "improvement_pct": 12.8,
        "candidate_id": "phase3_cuda_full_20261117_073000__tcn__L168__H24",
    },
}

# Supported Horizons
HORIZONS = [1, 6, 12, 24]
HORIZON_LABELS = {
    1: "+1 Hour (Immediate)",
    6: "+6 Hours (Short-term)",
    12: "+12 Hours (Half-day)",
    24: "+24 Hours (Full-day)",
}

# Input Lookbacks
INPUT_LOOKBACKS = [24, 48, 168]

# Model Families and Types
MODEL_FAMILIES = {
    "baseline": ["persistence", "seasonal_naive"],
    "traditional_ml": ["linear_regression", "random_forest", "xgboost"],
    "deep_learning": ["lstm", "gru", "tcn"],
}

MODEL_DISPLAY_NAMES = {
    "persistence": "Persistence Baseline",
    "seasonal_naive": "Seasonal Naive (24h)",
    "linear_regression": "Linear Regression (Ridge)",
    "random_forest": "Random Forest",
    "xgboost": "XGBoost Regressor",
    "lstm": "LSTM (Recurrent Neural)",
    "gru": "GRU (Gated Recurrent Neural)",
    "tcn": "Temporal Convolutional Network (TCN)",
}

MODEL_FAMILY_DISPLAY = {
    "baseline": "Baselines",
    "traditional_ml": "Traditional ML",
    "deep_learning": "Deep Learning (PyTorch/CUDA)",
}

# Air Quality Standards (µg/m³)
NAAQS_PM25_24H_STANDARD = 60.0
NAAQS_PM25_ANNUAL_STANDARD = 40.0
WHO_PM25_24H_GUIDELINE = 15.0

# Indian National AQI PM2.5 Breakpoints (µg/m³)
AQI_CATEGORIES = [
    {"name": "Good", "min": 0, "max": 30, "color": "#10B981"},
    {"name": "Satisfactory", "min": 31, "max": 60, "color": "#84CC16"},
    {"name": "Moderate", "min": 61, "max": 90, "color": "#FBBF24"},
    {"name": "Poor", "min": 91, "max": 120, "color": "#FB923C"},
    {"name": "Very Poor", "min": 121, "max": 250, "color": "#F43F5E"},
    {"name": "Severe", "min": 251, "max": 1000, "color": "#BE123C"},
]

# Pollution Evaluation Tiers
POLLUTION_TIERS = [
    {"label": "< 60 µg/m³ (Within NAAQS Standard)", "min": 0.0, "max": 60.0},
    {"label": "60 - 120 µg/m³ (Moderate / Poor)", "min": 60.0, "max": 120.0},
    {"label": "120 - 250 µg/m³ (Very Poor)", "min": 120.0, "max": 250.0},
    {"label": "250 - 400 µg/m³ (Severe Smog)", "min": 250.0, "max": 400.0},
    {"label": "> 400 µg/m³ (Emergency / Extreme Inversion)", "min": 400.0, "max": 2000.0},
]
