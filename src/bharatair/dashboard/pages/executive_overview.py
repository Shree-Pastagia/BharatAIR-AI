"""Page 1: Executive Overview — BharatAir Dashboard."""

import numpy as np
import pandas as pd
import streamlit as st

from bharatair.dashboard.charts.time_series import build_historical_pm25_chart
from bharatair.dashboard.components.footer import render_footer
from bharatair.dashboard.config import BENCHMARK_WINNERS, PILOT_STATION
from bharatair.dashboard.data_loader import load_canonical_pm25


def render_page() -> None:
    """Render Executive Overview analytics landing page."""
    # Clean Page Header
    st.markdown(
        """
        <div class="page-header">
            <h1 class="page-title">Executive Overview</h1>
            <div class="page-subtitle">
                Delhi Air Quality Intelligence & Multi-Horizon Machine Learning Forecasting
            </div>
            <div class="badge-row">
                <span class="status-pill pill-verified">CPCB CAAQM Network</span>
                <span class="status-pill pill-station">Dwarka Sector 8, Delhi</span>
                <span class="status-pill pill-benchmark">Validation Benchmark</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_pm25 = load_canonical_pm25()
    if df_pm25.empty:
        st.error("Canonical Delhi dataset not found at `data/processed/delhi_site_1422_pm25.parquet`.")
        render_footer()
        return

    vals = df_pm25["value"]

    # Top KPI Cards Row
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Average PM2.5</div>
                <div class="kpi-value">{vals.mean():.1f} <span style="font-size: 0.9rem; font-weight: 500; color: #94A3B8;">µg/m³</span></div>
                <div class="kpi-subtitle" style="color: #F87171;">NAAQS Limit: 60 µg/m³</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Median PM2.5</div>
                <div class="kpi-value">{vals.median():.1f} <span style="font-size: 0.9rem; font-weight: 500; color: #94A3B8;">µg/m³</span></div>
                <div class="kpi-subtitle">IQR: {vals.quantile(0.75) - vals.quantile(0.25):.1f} µg/m³</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">99th Percentile</div>
                <div class="kpi-value" style="color: #F43F5E;">{vals.quantile(0.99):.1f} <span style="font-size: 0.9rem; font-weight: 500; color: #94A3B8;">µg/m³</span></div>
                <div class="kpi-subtitle">Max: {vals.max():.1f} µg/m³</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Observations</div>
                <div class="kpi-value">{len(vals):,}</div>
                <div class="kpi-subtitle">92 Calendar Months</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c5:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Completeness</div>
                <div class="kpi-value" style="color: #34D399;">{100 - PILOT_STATION['missingness_pct']:.2f}%</div>
                <div class="kpi-subtitle">4.95% Missing (3,292 hrs)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Main Longitudinal Trend Chart
    st.markdown(
        """
        <div class="panel-heading">Longitudinal Air Quality Trend (2018 – 2025)</div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Daily mean PM2.5 (teal) against Indian 24-hr NAAQS standard (60 µg/m³, dashed red) and WHO guideline (15 µg/m³, dashed blue).")

    chart_trend = build_historical_pm25_chart(df_pm25, aggregation="Daily Mean")
    st.altair_chart(chart_trend, use_container_width=True)

    # Monthly and Seasonal Analysis Row
    col_monthly, col_seasonal = st.columns([1.2, 1])

    with col_monthly:
        st.markdown(
            """
            <div class="panel-heading">Monthly Pollution Profile</div>
            """,
            unsafe_allow_html=True,
        )
        df_month_grp = df_pm25.copy()
        df_month_grp["month_num"] = df_month_grp["timestamp_ist"].dt.month
        df_month_grp["month_name"] = df_month_grp["timestamp_ist"].dt.strftime("%b")

        month_stats = (
            df_month_grp.groupby(["month_num", "month_name"])["value"]
            .agg(Mean="mean", Median="median", P95=lambda x: x.quantile(0.95))
            .reset_index()
            .sort_values(by="month_num")
        )
        month_stats_display = month_stats[["month_name", "Mean", "Median", "P95"]].rename(
            columns={"month_name": "Month", "Mean": "Mean (µg/m³)", "Median": "Median (µg/m³)", "P95": "P95 (µg/m³)"}
        )
        st.dataframe(
            month_stats_display.style.format(
                {"Mean (µg/m³)": "{:.1f}", "Median (µg/m³)": "{:.1f}", "P95 (µg/m³)": "{:.1f}"}
            ),
            use_container_width=True,
            hide_index=True,
        )

    with col_seasonal:
        st.markdown(
            """
            <div class="panel-heading">Seasonal Comparison</div>
            """,
            unsafe_allow_html=True,
        )
        df_season = df_pm25.copy()
        m = df_season["timestamp_ist"].dt.month
        conds = [m.isin([12, 1, 2]), m.isin([3, 4, 5, 6]), m.isin([7, 8, 9]), m.isin([10, 11])]
        choices = ["Winter", "Summer", "Monsoon", "Post-Monsoon"]
        df_season["Season"] = np.select(conds, choices, default="Other")

        season_tbl = (
            df_season.groupby("Season")["value"]
            .agg(
                Observations="count",
                Mean=lambda x: f"{x.mean():.1f} µg/m³",
                Median=lambda x: f"{x.median():.1f} µg/m³",
                ExceedingNAAQS=lambda x: f"{(x > 60).mean()*100:.1f}%",
            )
            .loc[["Winter", "Post-Monsoon", "Summer", "Monsoon"]]
            .reset_index()
        )
        st.dataframe(season_tbl, use_container_width=True, hide_index=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Compact Model Performance Summary
    st.markdown(
        """
        <div class="panel-heading">Forecasting Model Benchmark Summary</div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Validation performance across 72 machine learning/deep learning configurations and 8 baseline heuristics.")

    model_summary_data = [
        {
            "Forecast Horizon": "+1 Hour (Immediate)",
            "Top Architecture": "Random Forest",
            "Optimal Lookback": "24 Hours (1 Day)",
            "Validation MAE": "11.26 µg/m³",
            "Validation RMSE": "19.93 µg/m³",
            "Baseline MAE": "14.16 µg/m³ (Persistence)",
            "Improvement": "↓ 20.5%",
        },
        {
            "Forecast Horizon": "+6 Hours (Short-term)",
            "Top Architecture": "XGBoost",
            "Optimal Lookback": "168 Hours (1 Week)",
            "Validation MAE": "31.81 µg/m³",
            "Validation RMSE": "51.25 µg/m³",
            "Baseline MAE": "48.65 µg/m³ (Persistence)",
            "Improvement": "↓ 34.6%",
        },
        {
            "Forecast Horizon": "+12 Hours (Half-day)",
            "Top Architecture": "XGBoost",
            "Optimal Lookback": "24 Hours (1 Day)",
            "Validation MAE": "35.12 µg/m³",
            "Validation RMSE": "56.30 µg/m³",
            "Baseline MAE": "57.52 µg/m³ (Persistence)",
            "Improvement": "↓ 38.9%",
        },
        {
            "Forecast Horizon": "+24 Hours (Full-day)",
            "Top Architecture": "Temporal Convolutional Network (TCN)",
            "Optimal Lookback": "168 Hours (1 Week)",
            "Validation MAE": "36.72 µg/m³",
            "Validation RMSE": "58.98 µg/m³",
            "Baseline MAE": "42.11 µg/m³ (Persistence)",
            "Improvement": "↓ 12.8%",
        },
    ]
    st.dataframe(pd.DataFrame(model_summary_data), use_container_width=True, hide_index=True)

    # Key Research Findings Panel
    st.markdown(
        """
        <div class="insight-callout">
            <strong>Key Analytics Findings:</strong><br>
            • <strong>Short-Horizon Precision:</strong> Gradient-boosted decision trees (XGBoost) and Random Forests achieved top accuracy at +1h, +6h, and +12h horizons, outperforming recurrent neural networks (LSTM and GRU) with substantially lower computational cost.<br>
            • <strong>Deep Learning Synoptic Memory:</strong> At the +24h horizon, the Temporal Convolutional Network (TCN) with a 168-hour receptive field delivered the best overall validation performance (MAE 36.72 µg/m³), successfully capturing multi-day weather persistence.<br>
            • <strong>Empirical Ground Truth:</strong> All models were trained and validated on strictly observed numeric CPCB measurements under a zero-imputation protocol to preserve true atmospheric dynamics.
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_footer()
