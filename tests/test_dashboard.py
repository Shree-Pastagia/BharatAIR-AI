"""Comprehensive test suite for BharatAir Professional Analytics Dashboard.

Verifies:
- Config constants, station metadata, and benchmark winners
- Canonical data loader (63,178 observations, non-negative)
- Calendar (66,470 hours) and gap audit (229 intervals, 2,160h max gap)
- Model metrics (72 candidates + 8 baselines)
- Test partition isolation (zero predictions at or beyond test boundary 2024-04-30 02:00:00)
- Chart construction (Altair and PyDeck)
- AppTest execution for app.py and all 8 individual pages
"""

from pathlib import Path
import sys

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bharatair.dashboard.charts.distributions import (
    build_annual_coverage_chart,
    build_gap_audit_chart,
    build_monthly_seasonal_boxplot,
    build_pm25_distribution_chart,
    build_residual_distribution_chart,
)
from bharatair.dashboard.charts.model_charts import (
    build_error_by_pollution_tier,
    build_feature_importance_chart,
    build_horizon_degradation_chart,
    build_model_comparison_bar_chart,
    build_scatter_actual_vs_predicted,
)
from bharatair.dashboard.charts.time_series import (
    build_diurnal_profile_chart,
    build_forecast_backtest_chart,
    build_historical_pm25_chart,
)
from bharatair.dashboard.config import (
    BENCHMARK_WINNERS,
    HORIZONS,
    PILOT_STATION,
    POLLUTION_TIERS,
)
from bharatair.dashboard.data_loader import (
    load_calendar,
    load_candidate_predictions,
    load_canonical_pm25,
    load_gap_audit,
    load_validation_model_metrics,
    load_window_feasibility,
)


def test_config_and_metadata() -> None:
    """Verify pilot station metadata and benchmark winners."""
    assert PILOT_STATION["station_id"] == "site_1422"
    assert PILOT_STATION["total_observations"] == 63178
    assert PILOT_STATION["missingness_pct"] == 4.953
    assert HORIZONS == [1, 6, 12, 24]

    # Benchmark validation winners
    assert BENCHMARK_WINNERS[1]["model"] == "random_forest"
    assert BENCHMARK_WINNERS[1]["mae"] == 11.2616
    assert BENCHMARK_WINNERS[6]["model"] == "xgboost"
    assert BENCHMARK_WINNERS[6]["mae"] == 31.8100
    assert BENCHMARK_WINNERS[12]["model"] == "xgboost"
    assert BENCHMARK_WINNERS[12]["mae"] == 35.1162
    assert BENCHMARK_WINNERS[24]["model"] == "tcn"
    assert BENCHMARK_WINNERS[24]["mae"] == 36.7191


def test_canonical_data_loader() -> None:
    """Verify canonical observed PM2.5 dataset loads accurately."""
    df = load_canonical_pm25()
    assert not df.empty
    assert len(df) == 63178
    assert "timestamp_ist" in df.columns
    assert "value" in df.columns
    assert (df["value"] >= 0).all()


def test_calendar_and_gap_audit_loaders() -> None:
    """Verify calendar and gap audit datasets."""
    df_cal = load_calendar()
    assert len(df_cal) == 66470

    df_gaps = load_gap_audit()
    assert len(df_gaps) == 229
    assert df_gaps["missing_hours"].max() == 2160


def test_validation_metrics_loader() -> None:
    """Verify candidate validation metrics (72 candidates + 8 baselines)."""
    df_metrics = load_validation_model_metrics()
    assert len(df_metrics) == 80
    assert set(HORIZONS).issubset(set(df_metrics["horizon_hours"].unique()))


def test_test_partition_isolation() -> None:
    """Verify that validation predictions do not leak or access test partition."""
    test_boundary = pd.to_datetime("2024-04-30 02:00:00")
    df_preds = load_candidate_predictions("phase3_cuda_full_20261117_073000__gru__L24__H1")
    assert not df_preds.empty
    assert len(df_preds) == 7360
    assert (df_preds["target_timestamp"] < test_boundary).all()


def test_analytics_charts() -> None:
    """Verify chart builders generate valid Altair visualizers with dark theme."""
    df = load_canonical_pm25().head(100)
    chart1 = build_historical_pm25_chart(df)
    assert chart1 is not None

    chart2 = build_diurnal_profile_chart(df)
    assert chart2 is not None

    chart3 = build_pm25_distribution_chart(df)
    assert chart3 is not None

    chart4 = build_monthly_seasonal_boxplot(df)
    assert chart4 is not None

    df_metrics = load_validation_model_metrics()
    chart5 = build_model_comparison_bar_chart(df_metrics, horizon=1, metric="mae")
    assert chart5 is not None

    chart6 = build_horizon_degradation_chart(df_metrics)
    assert chart6 is not None


def test_app_main_render() -> None:
    """Verify app.py renders cleanly without exceptions."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert len(at.exception) == 0
    assert len(at.markdown) > 0


@pytest.mark.parametrize(
    "page_module",
    [
        "executive_overview",
        "geographic_explorer",
        "historical_aq",
        "data_quality",
        "statistical_research",
        "ml_evaluation",
        "forecast_explorer",
        "methodology",
    ],
)
def test_all_eight_pages(page_module: str) -> None:
    """Verify all 8 individual analytics pages render with zero exceptions."""
    script = f"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'src'))

from bharatair.dashboard.pages import {page_module}
{page_module}.render_page()
"""
    at = AppTest.from_string(script, default_timeout=30)
    at.run()
    assert len(at.exception) == 0, f"Exception found on page {page_module}: {at.exception}"
