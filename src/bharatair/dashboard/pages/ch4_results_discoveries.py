"""Chapter 4: Results and Discoveries — BharatAir Presentation."""

import pandas as pd
import streamlit as st

from bharatair.dashboard.charts.model_charts import (
    build_error_by_pollution_tier,
    build_horizon_degradation_chart,
    build_model_comparison_bar_chart,
    build_scatter_actual_vs_predicted,
)
from bharatair.dashboard.charts.time_series import build_forecast_backtest_chart
from bharatair.dashboard.components.presentation_nav import render_chapter_buttons, render_presentation_header
from bharatair.dashboard.config import AUDITED_PHASE3_WINNERS
from bharatair.dashboard.data_loader import (
    load_candidate_predictions,
    load_validation_model_metrics,
)


def render_page(chapter_idx: int = 3) -> None:
    """Render Chapter 4: What Did the Models Discover?"""
    render_presentation_header(chapter_idx)

    st.markdown(
        """
        <div class="chapter-header">
            <h2 class="chapter-headline">What Did the Models Discover?</h2>
        </div>
        <p class="chapter-desc">
            The Phase 3 systematic validation benchmark tested 72 machine learning candidates and 8 baselines.
            The findings challenge conventional assumptions about deep learning in environmental time series.
        </p>
        """,
        unsafe_allow_html=True,
    )

    df_metrics = load_validation_model_metrics()
    if df_metrics.empty:
        st.error("Validation metrics not found at `runs/phase3_cuda_full_20261117_073000/metrics/validation_model_metrics.csv`.")
        render_chapter_buttons(chapter_idx)
        return

    # PROMINENT DISCOVERY CALLOUT BOX
    st.markdown(
        """
        <div class="discovery-box">
            <div class="discovery-headline">
                <span>💡</span> <strong>The Core Empirical Discovery</strong>
            </div>
            <div class="discovery-text">
                <strong>Traditional Machine Learning (Random Forest and XGBoost) outperformed Deep Learning across three of four horizons (+1h, +6h, +12h).</strong>
                Deep Learning did <em>not</em> beat classical methods across the board. However, at the longest +24-hour horizon,
                the <strong>Temporal Convolutional Network (TCN) with a 168-hour receptive field achieved the overall best validation MAE (36.72 µg/m³)</strong>,
                demonstrating that deep dilated causal convolutions excel when long-range weekly synoptic context is required.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Winners Showcase Cards
    st.markdown("### Audited Validation Champion Models by Horizon")
    w_cols = st.columns(4)

    for idx, h in enumerate([1, 6, 12, 24]):
        w = AUDITED_PHASE3_WINNERS[h]
        with w_cols[idx]:
            border_color = "rgba(45, 212, 191, 0.4)" if h == 24 else "rgba(56, 189, 248, 0.4)"
            st.markdown(
                f"""
                <div class="pres-card" style="border: 1px solid {border_color};">
                    <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 700;">
                        +{h} Hour{'s' if h > 1 else ''} Ahead
                    </div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #FFFFFF; margin: 4px 0;">
                        {w['display_name']}
                    </div>
                    <div style="font-size: 0.8rem; color: #38BDF8; margin-bottom: 8px;">
                        Input Lookback: L = {w['input_hours']}h
                    </div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: #2DD4BF; line-height: 1.1;">
                        {w['mae']:.2f} <span style="font-size: 0.85rem; font-weight: 500; color: #94A3B8;">µg/m³ MAE</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #10B981; margin-top: 6px; font-weight: 600;">
                        ↓ {w['improvement_pct']:.1f}% vs Persistence ({w['baseline_persistence_mae']:.1f})
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Interactive Horizon Evaluation Tab
    st.markdown("### Interactive Model Comparisons & Horizon Degradation")

    col_h_select, _ = st.columns([1.5, 2.5])
    with col_h_select:
        selected_h = st.selectbox(
            "Inspect Horizon Comparison Chart:",
            options=[1, 6, 12, 24],
            format_func=lambda x: f"+{x} Hour{'s' if x > 1 else ''} Horizon Ahead",
            index=0,
        )

    col_c1, col_c2 = st.columns([1.2, 1])

    with col_c1:
        st.markdown(f"#### Model Architectures at +{selected_h}h")
        st.caption(f"Lowest validation MAE per architecture at +{selected_h}h. Notice traditional ML leading short horizons.")
        chart_bars = build_model_comparison_bar_chart(df_metrics, horizon=selected_h, metric="mae")
        st.altair_chart(chart_bars, use_container_width=True)

    with col_c2:
        st.markdown("#### Forecast Degradation Curve")
        st.caption("How prediction error scales as we forecast further into the future (L=24h candidates).")
        chart_deg = build_horizon_degradation_chart(df_metrics)
        st.altair_chart(chart_deg, use_container_width=True)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Actual vs Predicted Backtest Section
    st.markdown("### Model Predictions vs Ground Truth (Diwali Smog Episode)")
    st.caption("Offline backtest predictions from champion model during the severe November 2023 pollution surge.")

    # Load predictions for the selected horizon's winner
    winner_cid = AUDITED_PHASE3_WINNERS[selected_h]["candidate_id"]
    df_preds = load_candidate_predictions(winner_cid)

    if not df_preds.empty:
        # Filter to a dramatic smog window (Nov 1 - Nov 15, 2023)
        diwali_mask = (df_preds["target_timestamp"] >= "2023-11-01") & (df_preds["target_timestamp"] <= "2023-11-15")
        df_diwali = df_preds[diwali_mask]

        chart_fc = build_forecast_backtest_chart(df_diwali if not df_diwali.empty else df_preds.head(300))
        st.altair_chart(chart_fc, use_container_width=True)

        col_scatter, col_tiers = st.columns([1, 1.2])

        with col_scatter:
            st.markdown("#### Actual vs Predicted Scatter")
            st.caption("Correlation along the dashed red 1:1 diagonal across validation data.")
            chart_scat = build_scatter_actual_vs_predicted(df_preds)
            st.altair_chart(chart_scat, use_container_width=True)

        with col_tiers:
            st.markdown("#### Error Across Pollution Severity Tiers")
            st.caption("Models perform with high precision on clean days (<60 µg/m³), but error expands during extreme smog.")
            chart_tiers = build_error_by_pollution_tier(df_preds)
            st.altair_chart(chart_tiers, use_container_width=True)

    # Scientific Protocol Guard: Distinguishing Validation from Test
    st.markdown(
        """
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px dashed rgba(255,255,255,0.15); border-radius: 12px; padding: 18px 24px; margin-top: 24px;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                <span style="font-size: 1.2rem;">🔒</span>
                <strong style="color: #F8FAFC; font-size: 0.95rem;">Empirical Protocol Distinction: Preliminary Validation Results Only</strong>
            </div>
            <p style="color: #94A3B8; font-size: 0.85rem; line-height: 1.5; margin: 0;">
                All metrics and charts presented above represent the <strong>chronological validation split (March 2023 to April 2024)</strong>.
                In accordance with rigorous empirical standards, the <strong>15% test partition (April 2024 to September 2025)</strong>
                remains strictly locked and unaccessed to guarantee zero test leakage.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Bottom navigation
    render_chapter_buttons(chapter_idx)

