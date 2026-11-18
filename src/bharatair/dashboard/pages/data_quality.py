"""Page 4: Data Quality & Sensor Reliability — BharatAir Dashboard."""

import pandas as pd
import streamlit as st

from bharatair.dashboard.charts.distributions import build_annual_coverage_chart, build_gap_audit_chart
from bharatair.dashboard.components.footer import render_footer
from bharatair.dashboard.config import PILOT_STATION
from bharatair.dashboard.data_loader import (
    load_calendar,
    load_data_quality_summary,
    load_gap_audit,
    load_window_feasibility,
)


def render_page() -> None:
    """Render Data Quality & Sensor Reliability analytics page."""
    st.markdown(
        """
        <div class="page-header">
            <h1 class="page-title">Data Quality & Sensor Reliability</h1>
            <div class="page-subtitle">
                Longitudinal Completeness, Sensor Outage Accounting, and Sequence Feasibility
            </div>
            <div class="badge-row">
                <span class="status-pill pill-verified">Zero Imputation Policy</span>
                <span class="status-pill pill-station">63,178 Observed Hours</span>
                <span class="status-pill pill-benchmark">95.05% Completeness</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    quality_summary = load_data_quality_summary()
    df_gaps = load_gap_audit()
    df_feasibility = load_window_feasibility()

    # Completeness Scorecard KPI Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Observed Records</div>
                <div class="kpi-value">{PILOT_STATION['total_observations']:,}</div>
                <div class="kpi-subtitle">Strictly Measured Hours</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Active Completeness</div>
                <div class="kpi-value" style="color: #34D399;">{100 - PILOT_STATION['missingness_pct']:.2f}%</div>
                <div class="kpi-subtitle">3,292 missing hours (4.95%)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div class="kpi-card">
                <div class="kpi-label">Negative Readings</div>
                <div class="kpi-value" style="color: #38BDF8;">0</div>
                <div class="kpi-subtitle">100% Non-Negative</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            """
            <div class="kpi-card">
                <div class="kpi-label">Duplicate Offsets</div>
                <div class="kpi-value" style="color: #38BDF8;">0</div>
                <div class="kpi-subtitle">Zero Duplicate Timestamps</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Annual Completeness Section
    st.markdown(
        """
        <div class="panel-heading">Longitudinal Completeness by Calendar Year</div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Active-span coverage percentage. High sustained completeness (>96.8%) maintained from 2018 through 2024.")

    col_chart, col_tbl = st.columns([1.3, 1])

    with col_chart:
        chart_annual = build_annual_coverage_chart(quality_summary)
        st.altair_chart(chart_annual, use_container_width=True)

    with col_tbl:
        annual_data = [
            {"Year": "2018", "Observed Hours": "7,883", "Missing Hours": "123", "Coverage": "98.46%"},
            {"Year": "2019", "Observed Hours": "8,683", "Missing Hours": "77", "Coverage": "99.12%"},
            {"Year": "2020", "Observed Hours": "8,565", "Missing Hours": "219", "Coverage": "97.51%"},
            {"Year": "2021", "Observed Hours": "8,624", "Missing Hours": "136", "Coverage": "98.45%"},
            {"Year": "2022", "Observed Hours": "8,583", "Missing Hours": "177", "Coverage": "97.98%"},
            {"Year": "2023", "Observed Hours": "8,481", "Missing Hours": "279", "Coverage": "96.82%"},
            {"Year": "2024", "Observed Hours": "8,761", "Missing Hours": "23", "Coverage": "99.74%"},
            {"Year": "2025", "Observed Hours": "3,598", "Missing Hours": "2,258", "Coverage": "61.44%"},
        ]
        st.dataframe(pd.DataFrame(annual_data), use_container_width=True, hide_index=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Missing Interval Duration Visualization
    st.markdown(
        """
        <div class="panel-heading">Sensor Outage Duration & Gap Analysis</div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Longest consecutive missing periods in the canonical CPCB timeline. Gaps are explicitly tracked rather than interpolated.")

    col_gap_c, col_gap_desc = st.columns([1.4, 1])

    with col_gap_c:
        chart_gaps = build_gap_audit_chart(df_gaps)
        st.altair_chart(chart_gaps, use_container_width=True)

    with col_gap_desc:
        st.markdown(
            """
            <div class="content-panel">
                <div style="font-weight: 700; color: #FBBF24; margin-bottom: 8px;">Documented Sensor Gaps</div>
                <p style="color: #CBD5E1; font-size: 0.85rem; line-height: 1.55;">
                    • <strong>Q1 2025 Outage:</strong> The longest gap in the dataset occurred from <strong>January 1 to March 31, 2025</strong> (2,160 consecutive hours / 90 full calendar days), reflecting station maintenance in the CPCB record.<br><br>
                    • <strong>July 2023 Gap:</strong> A secondary 161-hour gap occurred during July 2023.<br><br>
                    • <strong>Zero-Imputation Policy:</strong> BharatAir strictly avoids synthesizing, forward-filling, or interpolating data across these outages. Artificial smoothing introduces false signals that distort machine learning sequence training.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Modeling Window Feasibility
    st.markdown(
        """
        <div class="panel-heading">Modeling Window Feasibility Under Zero Imputation</div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Eligible sequence training windows requiring all L input lookback hours and the target hour to be observed. Outage intervals (≥24h missing) are excluded.")

    if not df_feasibility.empty:
        st.dataframe(df_feasibility, use_container_width=True, hide_index=True)
    else:
        feasibility_table = [
            {"Input Lookback (L)": "24 Hours", "Horizon (+H)": "+1 Hour", "Eligible Windows": "58,708", "Boundary Excluded": "24", "Outage Excluded": "2,549", "Input Gap Excluded": "5,039"},
            {"Input Lookback (L)": "24 Hours", "Horizon (+H)": "+6 Hours", "Eligible Windows": "58,410", "Boundary Excluded": "29", "Outage Excluded": "2,574", "Input Gap Excluded": "5,036"},
            {"Input Lookback (L)": "24 Hours", "Horizon (+H)": "+12 Hours", "Eligible Windows": "58,239", "Boundary Excluded": "35", "Outage Excluded": "2,604", "Input Gap Excluded": "5,036"},
            {"Input Lookback (L)": "24 Hours", "Horizon (+H)": "+24 Hours", "Eligible Windows": "58,049", "Boundary Excluded": "47", "Outage Excluded": "2,664", "Input Gap Excluded": "5,036"},
            {"Input Lookback (L)": "48 Hours", "Horizon (+H)": "+1 Hour", "Eligible Windows": "55,136", "Boundary Excluded": "48", "Outage Excluded": "2,669", "Input Gap Excluded": "8,480"},
            {"Input Lookback (L)": "48 Hours", "Horizon (+H)": "+24 Hours", "Eligible Windows": "54,505", "Boundary Excluded": "71", "Outage Excluded": "2,784", "Input Gap Excluded": "8,477"},
            {"Input Lookback (L)": "168 Hours", "Horizon (+H)": "+1 Hour", "Eligible Windows": "40,585", "Boundary Excluded": "168", "Outage Excluded": "3,269", "Input Gap Excluded": "22,355"},
            {"Input Lookback (L)": "168 Hours", "Horizon (+H)": "+24 Hours", "Eligible Windows": "40,187", "Boundary Excluded": "191", "Outage Excluded": "3,384", "Input Gap Excluded": "22,286"},
        ]
        st.dataframe(pd.DataFrame(feasibility_table), use_container_width=True, hide_index=True)

    render_footer()
