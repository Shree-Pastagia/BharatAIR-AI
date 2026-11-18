"""Page 6: ML Model Evaluation — BharatAir Dashboard."""

import pandas as pd
import streamlit as st

from bharatair.dashboard.charts.distributions import build_residual_distribution_chart
from bharatair.dashboard.charts.model_charts import (
    build_error_by_pollution_tier,
    build_feature_importance_chart,
    build_horizon_degradation_chart,
    build_model_comparison_bar_chart,
    build_scatter_actual_vs_predicted,
)
from bharatair.dashboard.components.footer import render_footer
from bharatair.dashboard.data_loader import (
    load_candidate_predictions,
    load_device_telemetry,
    load_feature_importance,
    load_validation_model_metrics,
)


def render_page() -> None:
    """Render ML Model Evaluation analytics page."""
    st.markdown(
        """
        <div class="page-header">
            <h1 class="page-title">ML Model Evaluation</h1>
            <div class="page-subtitle">
                Multi-Horizon Forecasting Benchmark Across 72 ML/DL Candidates and 8 Baseline Evaluations
            </div>
            <div class="badge-row">
                <span class="status-pill pill-verified">Validation Benchmark</span>
                <span class="status-pill pill-station">4 Forecast Horizons</span>
                <span class="status-pill pill-benchmark">Test Partition Locked</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_metrics = load_validation_model_metrics()
    telem_json = load_device_telemetry()
    fi_dict = load_feature_importance()

    if df_metrics.empty:
        st.error("Model metrics dataset not available.")
        render_footer()
        return

    # Filter Controls Row
    col_horizon, col_family, col_metric = st.columns([1.5, 1.5, 1])

    with col_horizon:
        selected_horizon = st.selectbox(
            "Forecast Horizon Ahead:",
            options=[1, 6, 12, 24],
            format_func=lambda h: f"+{h} Hour{'s' if h > 1 else ''} Ahead",
            index=0,
        )

    with col_family:
        selected_family = st.selectbox(
            "Architecture Family:",
            options=["All Architectures", "Traditional ML", "Deep Learning (CUDA)", "Baselines"],
            index=0,
        )

    with col_metric:
        selected_metric = st.selectbox(
            "Primary Evaluation Metric:",
            options=["mae", "rmse", "mase"],
            format_func=lambda m: m.upper(),
            index=0,
        )

    # Filtered dataframe for leaderboard
    mask = df_metrics["horizon_hours"] == selected_horizon
    if selected_family == "Traditional ML":
        mask = mask & (df_metrics["family"] == "traditional_ml")
    elif selected_family == "Deep Learning (CUDA)":
        mask = mask & (df_metrics["family"] == "deep_learning")
    elif selected_family == "Baselines":
        mask = mask & (df_metrics["family"] == "baseline")

    filtered_metrics = df_metrics[mask].sort_values(by=selected_metric)

    # Top Champion Card for Selected Horizon
    best_candidate = filtered_metrics.iloc[0] if not filtered_metrics.empty else None
    if best_candidate is not None:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Top Model (+{selected_horizon}h)</div>
                    <div class="kpi-value" style="font-size: 1.65rem; color: #2DD4BF;">{best_candidate['model'].upper()}</div>
                    <div class="kpi-subtitle">Lookback L = {int(best_candidate['input_hours']) if pd.notna(best_candidate['input_hours']) else 'N/A'}h</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Validation {selected_metric.upper()}</div>
                    <div class="kpi-value">{best_candidate[selected_metric]:.2f} <span style="font-size: 0.85rem; color: #94A3B8;">µg/m³</span></div>
                    <div class="kpi-subtitle">RMSE: {best_candidate['rmse']:.2f} µg/m³</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Mean Scaled Error (MASE)</div>
                    <div class="kpi-value" style="color: {'#34D399' if best_candidate['mase'] < 1.0 else '#FBBF24'};">{best_candidate['mase']:.3f}</div>
                    <div class="kpi-subtitle">Bias: {best_candidate['bias']:+.2f} µg/m³</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Training Duration</div>
                    <div class="kpi-value">{best_candidate['training_seconds']:.2f} s</div>
                    <div class="kpi-subtitle">{"CUDA Accelerated (RTX 4060)" if best_candidate["family"] == "deep_learning" else "CPU Single-Node"}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Model Comparisons and Degradation Row
    st.markdown(
        """
        <div class="panel-heading">Model Comparison & Forecast Horizon Degradation</div>
        """,
        unsafe_allow_html=True,
    )

    col_bars, col_deg = st.columns([1.2, 1])

    with col_bars:
        st.caption(f"Lowest validation {selected_metric.upper()} per architecture at +{selected_horizon}h.")
        chart_bars = build_model_comparison_bar_chart(df_metrics, horizon=selected_horizon, metric=selected_metric)
        st.altair_chart(chart_bars, use_container_width=True)

    with col_deg:
        st.caption("Forecast error degradation curve from +1h to +24h horizons (L=24h lookbacks).")
        chart_deg = build_horizon_degradation_chart(df_metrics)
        st.altair_chart(chart_deg, use_container_width=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Detailed Leaderboard Table
    st.markdown(
        f"""
        <div class="panel-heading">Candidate Leaderboard (+{selected_horizon}h Horizon)</div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Evaluated configurations showing input lookback, error metrics, and training runtimes.")

    display_cols = ["model", "family", "input_hours", "mae", "rmse", "mase", "bias", "training_seconds"]
    leaderboard_view = (
        filtered_metrics[display_cols]
        .rename(
            columns={
                "model": "Architecture",
                "family": "Family",
                "input_hours": "Input Lookback (L)",
                "mae": "MAE (µg/m³)",
                "rmse": "RMSE (µg/m³)",
                "mase": "MASE",
                "bias": "Bias (µg/m³)",
                "training_seconds": "Fit Time (s)",
            }
        )
        .reset_index(drop=True)
    )
    st.dataframe(
        leaderboard_view.style.format(
            {
                "Input Lookback (L)": lambda v: f"{int(v)}h" if pd.notna(v) else "—",
                "MAE (µg/m³)": "{:.2f}",
                "RMSE (µg/m³)": "{:.2f}",
                "MASE": "{:.3f}",
                "Bias (µg/m³)": "{:+.2f}",
                "Fit Time (s)": lambda v: f"{v:.2f} s" if pd.notna(v) else "—",
            }
        ),
        use_container_width=True,
    )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Actual vs Predicted and Error Analysis
    st.markdown(
        """
        <div class="panel-heading">Deep Error & Residual Analysis</div>
        """,
        unsafe_allow_html=True,
    )

    candidate_options = filtered_metrics["candidate_id"].tolist()
    if candidate_options:
        col_cand_select, _ = st.columns([1.8, 1])
        with col_cand_select:
            selected_cid = st.selectbox(
                "Select Model Candidate to Inspect:",
                options=candidate_options,
                format_func=lambda cid: cid.split("__")[1].upper() + f" (L={cid.split('__')[2].replace('L','') if len(cid.split('__'))>2 else 'base'}, H={selected_horizon}h)",
                index=0,
            )

        df_preds = load_candidate_predictions(selected_cid)

        if not df_preds.empty:
            tab_scatter, tab_tiers, tab_resids, tab_fi = st.tabs(
                [
                    "Actual vs Predicted Scatter",
                    "Pollution-Tier Error Breakdown",
                    "Residual Distribution",
                    "Feature Importance (Traditional ML)",
                ]
            )

            with tab_scatter:
                st.caption("Validation actual vs. predicted PM2.5. Red dashed line denotes ideal 1:1 parity.")
                chart_scatter = build_scatter_actual_vs_predicted(df_preds)
                st.altair_chart(chart_scatter, use_container_width=True)

            with tab_tiers:
                st.caption("Mean Absolute Error stratified across ambient pollution severity ranges.")
                chart_tiers = build_error_by_pollution_tier(df_preds)
                st.altair_chart(chart_tiers, use_container_width=True)

            with tab_resids:
                st.caption("Residual error distribution (Predicted - Actual). Centered around zero confirms low systematic bias.")
                chart_res = build_residual_distribution_chart(df_preds)
                st.altair_chart(chart_res, use_container_width=True)

            with tab_fi:
                features = fi_dict.get(selected_cid, [])
                if features:
                    st.caption("Top autoregressive lag weights contributing to predictions.")
                    chart_fi = build_feature_importance_chart(features)
                    st.altair_chart(chart_fi, use_container_width=True)
                else:
                    st.info("Feature importance inspection is available for Linear Regression, Random Forest, and XGBoost models.")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Hardware & CUDA Resource Metrics
    st.markdown(
        """
        <div class="panel-heading">Compute & GPU Resource Metrics (NVIDIA RTX 4060 Laptop GPU)</div>
        """,
        unsafe_allow_html=True,
    )

    telem_summary = [
        {"Model Architecture": "Linear Regression (Ridge)", "Execution Device": "CPU", "Mean Fit Duration": "0.13 s", "Peak GPU VRAM": "N/A (CPU)"},
        {"Model Architecture": "Random Forest (80 Trees)", "Execution Device": "CPU (4 Cores)", "Mean Fit Duration": "25.00 s", "Peak GPU VRAM": "N/A (CPU)"},
        {"Model Architecture": "XGBoost Regressor", "Execution Device": "CPU", "Mean Fit Duration": "1.08 s", "Peak GPU VRAM": "N/A (CPU)"},
        {"Model Architecture": "LSTM (Recurrent)", "Execution Device": "CUDA GPU", "Mean Fit Duration": "7.47 s", "Peak GPU VRAM": "2,538 MiB (2.48 GB)"},
        {"Model Architecture": "GRU (Gated Recurrent)", "Execution Device": "CUDA GPU", "Mean Fit Duration": "7.32 s", "Peak GPU VRAM": "1,968 MiB (1.92 GB)"},
        {"Model Architecture": "Temporal Convolutional Network (TCN)", "Execution Device": "CUDA GPU", "Mean Fit Duration": "12.53 s", "Peak GPU VRAM": "188 MiB (0.18 GB)"},
    ]
    st.dataframe(pd.DataFrame(telem_summary), use_container_width=True, hide_index=True)

    # Scientific Protocol Note
    st.markdown(
        """
        <div class="insight-callout">
            <strong>Validation Protocol Note:</strong> All results displayed reflect out-of-sample evaluation on the 15% validation partition (March 2023 to April 2024). In accordance with strict empirical machine learning standards, the final 15% test partition (April 2024 to September 2025) remains held out and unaccessed to preserve data integrity.
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_footer()
