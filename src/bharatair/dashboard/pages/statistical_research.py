"""Page 5: Statistical Research — BharatAir Dashboard."""

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from bharatair.dashboard.charts.distributions import build_pm25_distribution_chart
from bharatair.dashboard.charts.theme import apply_cinematic_theme
from bharatair.dashboard.components.footer import render_footer
from bharatair.dashboard.config import AQI_CATEGORIES
from bharatair.dashboard.data_loader import load_canonical_pm25


@st.cache_data(show_spinner=False)
def compute_autocorrelation(series: pd.Series, max_lags: int = 72) -> pd.DataFrame:
    """Compute autocorrelation coefficients up to max_lags."""
    lags = list(range(1, max_lags + 1))
    acf_vals = [float(series.autocorr(lag=lag)) for lag in lags]
    return pd.DataFrame({"lag": lags, "acf": acf_vals})


def render_page() -> None:
    """Render Statistical Research analytics page."""
    st.markdown(
        """
        <div class="page-header">
            <h1 class="page-title">Statistical Research</h1>
            <div class="page-subtitle">
                Distributional Characterization, Heavy-Tail Extremes, and Autocorrelation Structure
            </div>
            <div class="badge-row">
                <span class="status-pill pill-verified">Empirical Statistical Audit</span>
                <span class="status-pill pill-station">Dwarka Sector 8</span>
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

    vals = df_pm25["value"]

    # Top Statistical KPI Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Sample Mean</div>
                <div class="kpi-value">{vals.mean():.1f} <span style="font-size: 0.85rem; color: #94A3B8;">µg/m³</span></div>
                <div class="kpi-subtitle">Std Dev: {vals.std():.1f} µg/m³</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Median (P50)</div>
                <div class="kpi-value">{vals.median():.1f} <span style="font-size: 0.85rem; color: #94A3B8;">µg/m³</span></div>
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
                <div class="kpi-value" style="color: #F43F5E;">{vals.quantile(0.99):.1f} <span style="font-size: 0.85rem; color: #94A3B8;">µg/m³</span></div>
                <div class="kpi-subtitle">Maximum: {vals.max():.1f} µg/m³</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">24h Autocorrelation</div>
                <div class="kpi-value" style="color: #38BDF8;">{vals.autocorr(24):.3f}</div>
                <div class="kpi-subtitle">Strong Diurnal Memory</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Parametric & Distribution Overview
    st.markdown(
        """
        <div class="panel-heading">Empirical Distribution & Descriptors</div>
        """,
        unsafe_allow_html=True,
    )

    col_stats_tbl, col_dist_chart = st.columns([1, 1.4])

    with col_stats_tbl:
        stats_table = pd.DataFrame(
            [
                {"Metric": "Observations (N)", "Value": f"{len(vals):,}"},
                {"Metric": "Mean", "Value": f"{vals.mean():.2f} µg/m³"},
                {"Metric": "Standard Deviation", "Value": f"{vals.std():.2f} µg/m³"},
                {"Metric": "Median (P50)", "Value": f"{vals.median():.2f} µg/m³"},
                {"Metric": "Minimum", "Value": f"{vals.min():.1f} µg/m³"},
                {"Metric": "Maximum", "Value": f"{vals.max():.1f} µg/m³"},
                {"Metric": "1st Percentile (P1)", "Value": f"{vals.quantile(0.01):.1f} µg/m³"},
                {"Metric": "25th Percentile (P25)", "Value": f"{vals.quantile(0.25):.1f} µg/m³"},
                {"Metric": "75th Percentile (P75)", "Value": f"{vals.quantile(0.75):.1f} µg/m³"},
                {"Metric": "95th Percentile (P95)", "Value": f"{vals.quantile(0.95):.1f} µg/m³"},
                {"Metric": "99th Percentile (P99)", "Value": f"{vals.quantile(0.99):.1f} µg/m³"},
                {"Metric": "Values ≥ 500 µg/m³", "Value": f"{(vals >= 500).sum():,} ({((vals >= 500).mean()*100):.2f}%)"},
            ]
        )
        st.dataframe(stats_table, use_container_width=True, hide_index=True)

    with col_dist_chart:
        st.caption("Right-skewed, heavy-tailed empirical distribution of hourly PM2.5 concentrations in Delhi.")
        chart_dist = build_pm25_distribution_chart(df_pm25)
        st.altair_chart(chart_dist, use_container_width=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Autocorrelation (ACF) Structure
    st.markdown(
        """
        <div class="panel-heading">Autocorrelation Structure (ACF Lags 1 to 72 Hours)</div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Autocorrelation coefficient (Pearson r) over 72 hours. Note prominent peaks at 24h (r=0.748), 48h (r=0.662), and 72h (r=0.613) indicating strong diurnal cyclicity.")

    df_acf = compute_autocorrelation(vals, max_lags=72)
    chart_acf = (
        alt.Chart(df_acf)
        .mark_bar(color="#2DD4BF", size=3)
        .encode(
            x=alt.X("lag:Q", title="Lag (Hours)"),
            y=alt.Y("acf:Q", title="Autocorrelation (Pearson r)", scale=alt.Scale(domain=[0, 1])),
            tooltip=[
                alt.Tooltip("lag:Q", title="Lag (Hours)"),
                alt.Tooltip("acf:Q", title="ACF", format=".3f"),
            ],
        )
        .properties(height=260)
    )

    cycle_markers = alt.Chart(pd.DataFrame({"x": [24, 48, 72]})).mark_rule(
        color="#FBBF24", strokeDash=[3, 3], strokeWidth=1.2
    ).encode(x="x:Q")

    chart_layered = (chart_acf + cycle_markers).properties(height=260)
    st.altair_chart(apply_cinematic_theme(chart_layered), use_container_width=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # National AQI Breakdown Table
    st.markdown(
        """
        <div class="panel-heading">Concentration Distribution Across Indian National AQI Categories</div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Percentage of historical hours falling within official CPCB AQI concentration breakpoints.")

    aqi_rows = []
    total_count = len(vals)
    for cat in AQI_CATEGORIES:
        count = ((vals >= cat["min"]) & (vals <= cat["max"])).sum()
        pct = (count / total_count) * 100
        aqi_rows.append(
            {
                "AQI Category": cat["name"],
                "PM2.5 Range (µg/m³)": f"{cat['min']} – {cat['max']}",
                "Observed Hours": f"{count:,}",
                "Share of Timeline (%)": f"{pct:.2f}%",
            }
        )
    st.dataframe(pd.DataFrame(aqi_rows), use_container_width=True, hide_index=True)

    render_footer()
