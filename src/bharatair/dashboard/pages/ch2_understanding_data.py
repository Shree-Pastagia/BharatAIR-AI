"""Chapter 2: Understanding the Data — BharatAir Presentation."""

import pandas as pd
import streamlit as st

from bharatair.dashboard.charts.distributions import build_annual_coverage_chart, build_monthly_seasonal_boxplot
from bharatair.dashboard.charts.time_series import build_diurnal_profile_chart, build_historical_pm25_chart
from bharatair.dashboard.components.presentation_nav import render_chapter_buttons, render_presentation_header
from bharatair.dashboard.config import PILOT_STATION
from bharatair.dashboard.data_loader import load_canonical_pm25, load_data_quality_summary


def render_page(chapter_idx: int = 1) -> None:
    """Render Chapter 2: Understanding Delhi's Air."""
    render_presentation_header(chapter_idx)

    st.markdown(
        """
        <div class="chapter-header">
            <h2 class="chapter-headline">Understanding Delhi's Air</h2>
        </div>
        <p class="chapter-desc">
            Before applying complex machine learning algorithms, we conducted an empirical, multi-year
            audit of authentic continuous ambient monitoring observations from the regulatory CPCB CAAQM network.
        </p>
        """,
        unsafe_allow_html=True,
    )

    df_pm25 = load_canonical_pm25()
    quality_summary = load_data_quality_summary()

    if df_pm25.empty:
        st.error("Canonical Delhi dataset not found at `data/processed/delhi_site_1422_pm25.parquet`.")
        render_chapter_buttons(chapter_idx)
        return

    # Key Data Facts Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="stat-tile">
                <div class="stat-label">Pilot Station</div>
                <div class="stat-value" style="font-size: 1.6rem; color: #2DD4BF;">Dwarka Sec-8</div>
                <div class="stat-sub">Delhi DPCC • site_1422</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="stat-tile">
                <div class="stat-label">Observed Records</div>
                <div class="stat-value">{PILOT_STATION['total_observations']:,}</div>
                <div class="stat-sub">Strictly Measured Hours</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="stat-tile">
                <div class="stat-label">Active Span Coverage</div>
                <div class="stat-value" style="color: #38BDF8;">{100 - PILOT_STATION['missingness_pct']:.2f}%</div>
                <div class="stat-sub">3,292 missing hours (4.95%)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            """
            <div class="stat-tile">
                <div class="stat-label">Data Hygiene</div>
                <div class="stat-value" style="color: #10B981;">100% Valid</div>
                <div class="stat-sub">0 Negative • 0 Duplicate</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Longitudinal Visualizer
    st.markdown("### The 7.5-Year Pollution Story (2018 – 2025)")
    st.caption("Daily average PM2.5 concentration (teal line) against the Indian National 24-hr Standard (60 µg/m³, dashed red) and WHO Guideline (15 µg/m³, dashed cyan).")

    col_view, _ = st.columns([1.5, 3])
    with col_view:
        view_mode = st.radio(
            "Select Time Scale:",
            options=["Daily Mean", "Monthly Mean"],
            horizontal=True,
            index=0,
        )

    chart_ts = build_historical_pm25_chart(df_pm25, aggregation=view_mode)
    st.altair_chart(chart_ts, use_container_width=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Seasonal and Diurnal Dynamics
    st.markdown("### Atmospheric Patterns: Seasonal Severity & Diurnal Commute Inversions")

    col_season, col_diurnal = st.columns(2)

    with col_season:
        st.markdown("#### The Seasonal Cycle")
        st.caption("Distribution of PM2.5 across months: severe winter peaks vs monsoon wet scavenging.")
        chart_box = build_monthly_seasonal_boxplot(df_pm25)
        st.altair_chart(chart_box, use_container_width=True)
        st.markdown(
            """
            <div style="font-size: 0.85rem; color: #94A3B8; line-height: 1.5;">
                • <strong>Monsoon (July – August):</strong> Rainfall scavenging and high wind speeds lower median PM2.5 below <strong>35 µg/m³</strong>.<br>
                • <strong>Winter (November – January):</strong> Low temperatures, shallow planetary boundary layers, and anticyclonic stagnation push medians past <strong>180 µg/m³</strong>.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_diurnal:
        st.markdown("#### The 24-Hour Diurnal Rhythm")
        st.caption("Hourly median concentration and interquartile band (25th–75th percentiles).")
        chart_diurnal = build_diurnal_profile_chart(df_pm25)
        st.altair_chart(chart_diurnal, use_container_width=True)
        st.markdown(
            """
            <div style="font-size: 0.85rem; color: #94A3B8; line-height: 1.5;">
                • <strong>Morning Commute (08:00 – 10:00 IST):</strong> Sharp spike from vehicular emissions.<br>
                • <strong>Afternoon Dispersion (14:00 – 16:00 IST):</strong> Solar heating expands boundary layer, reducing concentrations.<br>
                • <strong>Nocturnal Inversion (20:00 – 02:00 IST):</strong> Surface cooling traps ground-level emissions.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Missing Data & Quality Section
    st.markdown("### Transparent Missing-Data Accounting")
    st.markdown(
        """
        In real-world atmospheric monitoring, sensors experience periodic maintenance and transmission gaps.
        BharatAir maintains a strict **zero-imputation policy**: we never synthesize or forward-fill missing
        readings across outages, preserving authentic atmospheric physics.
        """
    )

    col_ann_chart, col_outage_desc = st.columns([1.3, 1])

    with col_ann_chart:
        st.markdown("#### Annual Data Completeness (% of Active Hours)")
        chart_ann = build_annual_coverage_chart(quality_summary)
        st.altair_chart(chart_ann, use_container_width=True)

    with col_outage_desc:
        st.markdown(
            """
            <div class="pres-card">
                <h4 style="color: #FBBF24; margin-top: 0; font-size: 1.05rem;">Audited Outage Findings</h4>
                <p style="color: #CBD5E1; font-size: 0.875rem; line-height: 1.6;">
                    • <strong>2018 to 2024:</strong> High sustained completeness (>96.8% each year, peaking at 99.74% in 2024).<br><br>
                    • <strong>The Q1 2025 Outage:</strong> A continuous 2,160-hour gap (January 1 to March 31, 2025) appears in the official CPCB record.
                    Rather than fabricating data across these 90 days, BharatAir explicitly excluded this interval from sequence training windows.<br><br>
                    • <strong>No Data Contamination:</strong> Zero negative values and zero duplicate timestamp offsets across 92 months.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Bottom navigation
    render_chapter_buttons(chapter_idx)

