"""Page 7: Forecast Explorer — BharatAir Dashboard."""

import pandas as pd
import streamlit as st

from bharatair.dashboard.charts.time_series import build_forecast_backtest_chart
from bharatair.dashboard.components.footer import render_footer
from bharatair.dashboard.data_loader import (
    load_candidate_predictions,
    load_validation_model_metrics,
)


def render_page() -> None:
    """Render Forecast Explorer analytics page."""
    st.markdown(
        """
        <div class="page-header">
            <h1 class="page-title">Forecast Explorer</h1>
            <div class="page-subtitle">
                Historical Offline Validation Predictions vs Ground Truth (Dwarka Sector 8, Delhi)
            </div>
            <div class="badge-row">
                <span class="status-pill pill-verified">Historical Backtests Only</span>
                <span class="status-pill pill-station">Offline Validation</span>
                <span class="status-pill pill-benchmark">Not Live Forecasts</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_metrics = load_validation_model_metrics()
    if df_metrics.empty:
        st.error("Model metrics dataset not available.")
        render_footer()
        return

    # Horizon, Model, and Episode Filters
    col_horizon, col_model, col_episode = st.columns([1, 1.6, 1.4])

    with col_horizon:
        selected_horizon = st.selectbox(
            "Forecast Horizon Ahead:",
            options=[1, 6, 12, 24],
            format_func=lambda h: f"+{h} Hour{'s' if h > 1 else ''}",
            index=0,
        )

    candidates_for_h = df_metrics[df_metrics["horizon_hours"] == selected_horizon].sort_values(by="mae")
    candidate_list = candidates_for_h["candidate_id"].tolist()

    with col_model:
        selected_candidate = st.selectbox(
            "Model Candidate:",
            options=candidate_list,
            format_func=lambda cid: (
                cid.split("__")[1].upper()
                + f" (L={cid.split('__')[2].replace('L','') if len(cid.split('__'))>2 else 'base'}, MAE: {candidates_for_h[candidates_for_h['candidate_id']==cid]['mae'].values[0]:.2f} µg/m³)"
            ),
            index=0,
        )

    with col_episode:
        event_preset = st.selectbox(
            "Historical Atmospheric Episode:",
            options=[
                "Diwali & Severe Winter Smog (Nov 01 – Nov 15, 2023)",
                "Severe Cold Wave Inversion (Jan 10 – Jan 25, 2024)",
                "Spring Clean Air Transition (Mar 01 – Mar 15, 2024)",
                "Monsoon Scavenging (Jul 10 – Jul 25, 2023)",
                "Full Validation Timeline (Mar 2023 – Apr 2024)",
            ],
            index=0,
        )

    df_preds = load_candidate_predictions(selected_candidate)
    if df_preds.empty:
        st.warning("Candidate predictions dataset not available.")
        render_footer()
        return

    # Date boundary filter
    if event_preset == "Diwali & Severe Winter Smog (Nov 01 – Nov 15, 2023)":
        start_ts = pd.to_datetime("2023-11-01 00:00:00")
        end_ts = pd.to_datetime("2023-11-15 23:00:00")
    elif event_preset == "Severe Cold Wave Inversion (Jan 10 – Jan 25, 2024)":
        start_ts = pd.to_datetime("2024-01-10 00:00:00")
        end_ts = pd.to_datetime("2024-01-25 23:00:00")
    elif event_preset == "Spring Clean Air Transition (Mar 01 – Mar 15, 2024)":
        start_ts = pd.to_datetime("2024-03-01 00:00:00")
        end_ts = pd.to_datetime("2024-03-15 23:00:00")
    elif event_preset == "Monsoon Scavenging (Jul 10 – Jul 25, 2023)":
        start_ts = pd.to_datetime("2023-07-10 00:00:00")
        end_ts = pd.to_datetime("2023-07-25 23:00:00")
    else:
        start_ts = df_preds["target_timestamp"].min()
        end_ts = df_preds["target_timestamp"].max()

    mask = (df_preds["target_timestamp"] >= start_ts) & (df_preds["target_timestamp"] <= end_ts)
    window_preds = df_preds[mask]

    # Selected Window Performance KPIs
    if not window_preds.empty:
        win_mae = (window_preds["predicted"] - window_preds["actual"]).abs().mean()
        win_rmse = ((window_preds["predicted"] - window_preds["actual"]) ** 2).mean() ** 0.5
        win_bias = (window_preds["predicted"] - window_preds["actual"]).mean()
        corr = window_preds["actual"].corr(window_preds["predicted"])

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Window MAE</div>
                    <div class="kpi-value">{win_mae:.2f} <span style="font-size: 0.85rem; color: #94A3B8;">µg/m³</span></div>
                    <div class="kpi-subtitle">{len(window_preds):,} Evaluated Hours</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Window RMSE</div>
                    <div class="kpi-value">{win_rmse:.2f} <span style="font-size: 0.85rem; color: #94A3B8;">µg/m³</span></div>
                    <div class="kpi-subtitle">Root Mean Squared Error</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Mean Error Bias</div>
                    <div class="kpi-value" style="color: {'#34D399' if abs(win_bias) < 5 else '#FBBF24'};">{win_bias:+.2f} <span style="font-size: 0.85rem; color: #94A3B8;">µg/m³</span></div>
                    <div class="kpi-subtitle">{"Slight Underprediction" if win_bias < 0 else "Slight Overprediction"}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Forecast Correlation</div>
                    <div class="kpi-value" style="color: #38BDF8;">r = {corr:.3f}</div>
                    <div class="kpi-subtitle">Pearson Correlation Coefficient</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Large Actual vs Predicted Backtest Chart
    st.markdown(
        """
        <div class="panel-heading">Actual vs. Offline Predicted PM2.5 Time-Series Overlay</div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Grey line: Observed ground truth PM2.5 • Teal line: Model offline backtest prediction.")

    chart_fc = build_forecast_backtest_chart(window_preds)
    st.altair_chart(chart_fc, use_container_width=True)

    # Point-by-Point Inspection
    with st.expander("Inspect Point-by-Point Prediction Records", expanded=False):
        table_view = window_preds[["target_timestamp", "actual", "predicted", "residual", "abs_error"]].rename(
            columns={
                "target_timestamp": "Timestamp (IST)",
                "actual": "Actual PM2.5 (µg/m³)",
                "predicted": "Predicted PM2.5 (µg/m³)",
                "residual": "Residual (Pred - Act)",
                "abs_error": "Absolute Error",
            }
        )
        st.dataframe(
            table_view.style.format(
                {
                    "Actual PM2.5 (µg/m³)": "{:.1f}",
                    "Predicted PM2.5 (µg/m³)": "{:.1f}",
                    "Residual (Pred - Act)": "{:+.1f}",
                    "Absolute Error": "{:.1f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    render_footer()
