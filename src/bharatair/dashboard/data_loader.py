"""Data access layer for BharatAir Streamlit Dashboard.

Provides memoized, robust loaders for verified CPCB Delhi datasets,
gap audits, Phase 3 validation run outputs, model metrics, and predictions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st

from bharatair.dashboard.config import DATA_DIR, PHASE3_RUN_DIR


@st.cache_data(show_spinner="Loading canonical Delhi PM2.5 dataset...")
def load_canonical_pm25() -> pd.DataFrame:
    """Load canonical observed Delhi site_1422 PM2.5 dataset."""
    path = DATA_DIR / "delhi_site_1422_pm25.parquet"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(path)
    if "timestamp_ist" in df.columns:
        df["timestamp_ist"] = pd.to_datetime(df["timestamp_ist"])
    return df


@st.cache_data(show_spinner=False)
def load_calendar() -> pd.DataFrame:
    """Load hourly calendar for active period span."""
    path = DATA_DIR / "delhi_site_1422_hourly_calendar.parquet"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(path)
    if "timestamp_ist" in df.columns:
        df["timestamp_ist"] = pd.to_datetime(df["timestamp_ist"])
    return df


@st.cache_data(show_spinner=False)
def load_gap_audit() -> pd.DataFrame:
    """Load maximal consecutive missing runs audit."""
    path = DATA_DIR / "delhi_site_1422_gap_audit.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "gap_start_ist" in df.columns:
        df["gap_start_ist"] = pd.to_datetime(df["gap_start_ist"])
    if "gap_end_ist" in df.columns:
        df["gap_end_ist"] = pd.to_datetime(df["gap_end_ist"])
    return df


@st.cache_data(show_spinner=False)
def load_window_feasibility() -> pd.DataFrame:
    """Load input-horizon feasibility counts."""
    path = DATA_DIR / "delhi_site_1422_window_feasibility.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_data_quality_summary() -> Dict[str, Any]:
    """Load comprehensive data quality summary JSON."""
    path = DATA_DIR / "data_quality_summary.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_modeling_manifest() -> Dict[str, Any]:
    """Load modeling dataset manifest JSON."""
    path = DATA_DIR / "modeling_dataset_manifest.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_source_manifest() -> Dict[str, Any]:
    """Load source file manifest JSON."""
    path = DATA_DIR / "delhi_site_1422_source_manifest.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner="Loading Phase 3 validation metrics...")
def load_validation_model_metrics() -> pd.DataFrame:
    """Load all candidate validation metrics."""
    path = PHASE3_RUN_DIR / "metrics" / "validation_model_metrics.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    # Parse numeric columns safely
    numeric_cols = ["input_hours", "horizon_hours", "n", "mae", "rmse", "mase", "bias", "training_seconds"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_validation_model_selection() -> Dict[str, Any]:
    """Load validation selection outcome JSON."""
    path = PHASE3_RUN_DIR / "metrics" / "validation_model_selection.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_device_telemetry() -> Dict[str, Any]:
    """Load device hardware and CUDA memory telemetry JSON."""
    path = PHASE3_RUN_DIR / "metrics" / "candidate_device_telemetry.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_feature_importance() -> Dict[str, List[Dict[str, Any]]]:
    """Load traditional ML feature importance JSON."""
    path = PHASE3_RUN_DIR / "metrics" / "traditional_feature_importance.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner="Loading candidate validation predictions...")
def load_candidate_predictions(candidate_id: str) -> pd.DataFrame:
    """Load isolated validation predictions for a specific candidate.

    Read-only from candidate's attempt_001 folder (~4.4MB).
    """
    path = PHASE3_RUN_DIR / "candidates" / candidate_id / "attempt_001" / "validation_predictions.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "target_timestamp" in df.columns:
        df["target_timestamp"] = pd.to_datetime(df["target_timestamp"])
    if "issue_timestamp" in df.columns:
        df["issue_timestamp"] = pd.to_datetime(df["issue_timestamp"])
    if "actual" in df.columns and "predicted" in df.columns:
        df["residual"] = df["predicted"] - df["actual"]
        df["abs_error"] = (df["predicted"] - df["actual"]).abs()
    return df


@st.cache_data(show_spinner=False)
def load_pilot_rankings() -> pd.DataFrame:
    """Load pilot station coverage rankings."""
    path = DATA_DIR / "pilot_station_ranking.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

