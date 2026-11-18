"""Page 3: Historical Air Quality — BharatAir Dashboard."""

import numpy as np
import pandas as pd
import streamlit as st

from bharatair.dashboard.charts.distributions import build_monthly_seasonal_boxplot
from bharatair.dashboard.charts.time_series import build_diurnal_profile_chart, build_historical_pm25_chart
from bharatair.dashboard.components.footer import render_footer
from bharatair.dashboard.config import NAAQS_PM25_24H_STANDARD, WHO_PM25_24H_GUIDELINE
from bharatair.dashboard.data_loader import load_canonical_pm25


def render_page() -> None:
    """Render Historical Air Quality analytics page."""
    st.markdown(
        """
        <div class="page-header">
            <h1 class="page-title">Historical Air Quality</h1>
            <div class="page-subtitle">
                Longitudinal PM2.5 Time Series, Seasonal Dynamics, and Diurnal Profiles (2018 – 2025)
            </div>
            <div class="badge-row">
                <span class="status-pill pill-verified">Observed Ground Truth</span>
                <span class="status-pill pill-station">Dwarka Sector 8, Delhi</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_pm25 = load_canonical_pm25()
    if df_pm25.empty:
        st.error("Canonical Delhi dataset not available.")
        render_footer()
        return

    # Filter Controls
    col_preset, col_gran, col_date = st.columns([1.5, 1, 1.8])

    with col_preset:
        preset = st.selectbox(
            "Analytical Time Period:",
            options=[
                "Full Span (2018 – 2025)",
                "Severe Winter Smog (Nov 2023 – Jan 2024)",
                "Lockdown Clean Air Event (Mar – May 2020)",
                "Most Recent Full Year (2024)",
                "Custom Date Range",
            ],
            index=0,
        )

    with col_gran:
        granularity = st.selectbox(
            "Time Resolution:",
            options=["Daily Mean", "Monthly Mean", "Hourly (Subsampled)"],
            index=0,
        )

    min_ts = df_pm25["timestamp_ist"].min().date()
    max_ts = df_pm25["timestamp_ist"].max().date()

    if preset == "Severe Winter Smog (Nov 2023 – Jan 2024)":
        start_date = pd.to_datetime("2023-11-01")
        end_date = pd.to_datetime("2024-01-31")
    elif preset == "Lockdown Clean Air Event (Mar – May 2020)":
        start_date = pd.to_datetime("2020-03-15")
        end_date = pd.to_datetime("2020-05-31")
    elif preset == "Most Recent Full Year (2024)":
        start_date = pd.to_datetime("2024-01-01")
        end_date = pd.to_datetime("2024-12-31")
    elif preset == "Custom Date Range":
        with col_date:
            dates = st.date_input(
                "Custom Date Range:",
                value=(pd.to_datetime("2023-01-01"), pd.to_datetime("2024-12-31")),
                min_value=min_ts,
                max_value=max_ts,
            )
            if isinstance(dates, tuple) and len(dates) == 2:
                start_date = pd.to_datetime(dates[0])
                end_date = pd.to_datetime(dates[1])
            else:
                start_date = pd.to_datetime(min_ts)
                end_date = pd.to_datetime(max_ts)
    else:
        start_date = pd.to_datetime(min_ts)
        end_date = pd.to_datetime(max_ts)

    # Filtered window for summary stats
    mask = (df_pm25["timestamp_ist"] >= start_date) & (df_pm25["timestamp_ist"] <= end_date)
    df_window = df_pm25[mask]

    # Quick Summary Metrics for Selected Window
    if not df_window.empty:
        w_obs = len(df_window)
        w_mean = df_window["value"].mean()
        w_max = df_window["value"].max()
        w_exceed = (df_window["value"] > NAAQS_PM25_24H_STANDARD).mean() * 100

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Selected Records</div>
                    <div class="kpi-value">{w_obs:,}</div>
                    <div class="kpi-subtitle">{start_date.strftime('%b %Y')} to {end_date.strftime('%b %Y')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Period Average</div>
                    <div class="kpi-value" style="color: {'#F87171' if w_mean > 60 else '#34D399'};">{w_mean:.1f} <span style="font-size: 0.85rem; color: #94A3B8;">µg/m³</span></div>
                    <div class="kpi-subtitle">Standard: 60 µg/m³</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Peak Concentration</div>
                    <div class="kpi-value" style="color: #F43F5E;">{w_max:.1f} <span style="font-size: 0.85rem; color: #94A3B8;">µg/m³</span></div>
                    <div class="kpi-subtitle">Maximum Hourly Value</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Days Above Standard</div>
                    <div class="kpi-value" style="color: #FBBF24;">{w_exceed:.1f}%</div>
                    <div class="kpi-subtitle">> 60 µg/m³ Exposure</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Large Historical Time Series Chart
    st.markdown(
        """
        <div class="panel-heading">Longitudinal Time-Series Visualizer</div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Teal line: Measured PM2.5 • Dashed Red line: Indian 24-hr NAAQS standard (60 µg/m³) • Dashed Blue line: WHO 24-hr guideline (15 µg/m³).")

    chart_ts = build_historical_pm25_chart(
        df_pm25,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        aggregation=granularity,
    )
    st.altair_chart(chart_ts, use_container_width=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Seasonal and Diurnal Dynamics Tabs
    st.markdown(
        """
        <div class="panel-heading">Atmospheric Cycles: Diurnal Patterns & Seasonal Variations</div>
        """,
        unsafe_allow_html=True,
    )

    tab_diurnal, tab_seasonal = st.tabs(["24-Hour Diurnal Profile", "Monthly Seasonal Boxplots"])

    with tab_diurnal:
        st.caption("Hourly median concentration (blue line) and interquartile range (25th–75th percentiles, teal band) across the day.")
        chart_diurnal = build_diurnal_profile_chart(df_pm25)
        st.altair_chart(chart_diurnal, use_container_width=True)
        st.markdown(
            """
            <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 8px;">
                <strong>Diurnal Mechanics:</strong> Notice the sharp morning vehicular rush hour peak (08:00–10:00 IST),
                followed by enhanced vertical dispersion as solar heating expands the planetary boundary layer (14:00–16:00 IST),
                and ending with surface cooling that traps emissions in a nocturnal inversion layer (20:00–02:00 IST).
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tab_seasonal:
        st.caption("Monthly PM2.5 distributions (January through December) across the entire 2018–2025 timeline.")
        chart_box = build_monthly_seasonal_boxplot(df_pm25)
        st.altair_chart(chart_box, use_container_width=True)
        st.markdown(
            """
            <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 8px;">
                <strong>Seasonal Contrast:</strong> The monsoon season (July–August) provides natural wet scavenging with median concentrations
                below 35 µg/m³, while the post-monsoon and winter seasons (November–January) experience severe accumulation with medians exceeding 180 µg/m³.
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_footer()
