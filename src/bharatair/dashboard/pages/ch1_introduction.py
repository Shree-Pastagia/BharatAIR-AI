"""Chapter 1: Introduction — BharatAir Presentation."""

import streamlit as st
from bharatair.dashboard.components.presentation_nav import render_chapter_buttons, render_presentation_header
from bharatair.dashboard.config import PILOT_STATION


def render_page(chapter_idx: int = 0) -> None:
    """Render Chapter 1: Introduction."""
    render_presentation_header(chapter_idx)

    # Hero Banner
    st.markdown(
        """
        <div class="hero-banner">
            <div style="display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap;">
                <span class="badge-pill-cyan">CPCB CAAQM Network</span>
                <span class="badge-pill-teal">Delhi Pilot Benchmark</span>
                <span class="badge-pill-amber">Zero Synthetic Data</span>
            </div>
            <div class="hero-title">BharatAir</div>
            <div style="font-size: 1.35rem; font-weight: 600; color: #2DD4BF; margin-bottom: 8px;">
                India Air Quality Intelligence & Deep Learning Forecasting
            </div>
            <div class="hero-subtitle">
                An empirical, research-grade environmental data science presentation investigating whether
                deep recurrent and convolutional neural networks can outperform classical machine learning
                when forecasting severe PM2.5 pollution in Delhi across multi-hour horizons.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # High-Impact Stat Tiles
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="stat-tile">
                <div class="stat-label">Verified Observations</div>
                <div class="stat-value">{PILOT_STATION['total_observations']:,}</div>
                <div class="stat-sub">Hourly Continuous Records</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="stat-tile">
                <div class="stat-label">Active Time Span</div>
                <div class="stat-value">{PILOT_STATION['active_months']} Mos</div>
                <div class="stat-sub">Feb 2018 to Sep 2025</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="stat-tile">
                <div class="stat-label">Evaluated Models</div>
                <div class="stat-value">72 + 8</div>
                <div class="stat-sub">72 ML/DL + 8 Baselines</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            """
            <div class="stat-tile">
                <div class="stat-label">Forecast Horizons</div>
                <div class="stat-value">4 Steps</div>
                <div class="stat-sub">+1h, +6h, +12h, +24h Ahead</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    # Section 1: The Air Pollution Crisis
    st.markdown("### The Challenge: Understanding Delhi's Atmospheric Crisis")

    col_crisis_text, col_crisis_vis = st.columns([1.2, 1])

    with col_crisis_text:
        st.markdown(
            """
            <div class="pres-card">
                <h4 style="color: #FFFFFF; margin-top: 0; font-size: 1.15rem;">Why PM2.5 Matters</h4>
                <p style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.6;">
                    Fine particulate matter (<strong>PM2.5</strong>) consists of suspended atmospheric particles with aerodynamic
                    diameters smaller than 2.5 micrometers. Because of their microscopic scale, these particles bypass the
                    body's natural defenses, penetrating deep into alveolar tissue and directly entering the bloodstream.
                </p>
                <p style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.6;">
                    In northern India and the Indo-Gangetic Plain, seasonal meteorological stagnation, biomass emissions,
                    and nocturnal temperature inversions create severe pollution episodes where concentrations regularly exceed
                    <strong>500 to 900 µg/m³</strong> — more than <strong>8× the Indian National Ambient Standard (60 µg/m³)</strong>
                    and <strong>30× the World Health Organization 24-hr guideline (15 µg/m³)</strong>.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_crisis_vis:
        st.markdown(
            """
            <div class="pres-card-highlight">
                <h4 style="color: #38BDF8; margin-top: 0; font-size: 1.15rem;">National Air Quality Standards (NAAQS)</h4>
                <div style="margin: 14px 0;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">
                        <span>WHO 24-Hour Guideline</span>
                        <strong style="color: #38BDF8;">15 µg/m³</strong>
                    </div>
                    <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden;">
                        <div style="width: 5%; height: 100%; background: #38BDF8;"></div>
                    </div>
                </div>
                <div style="margin: 14px 0;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">
                        <span>Indian National Standard (24-Hour)</span>
                        <strong style="color: #FBBF24;">60 µg/m³</strong>
                    </div>
                    <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden;">
                        <div style="width: 18%; height: 100%; background: #FBBF24;"></div>
                    </div>
                </div>
                <div style="margin: 14px 0;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">
                        <span>Delhi Severe Winter Episodes</span>
                        <strong style="color: #F43F5E;">500 – 973 µg/m³</strong>
                    </div>
                    <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden;">
                        <div style="width: 100%; height: 100%; background: linear-gradient(90deg, #FBBF24, #F43F5E);"></div>
                    </div>
                </div>
                <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 14px;">
                    Peak recorded in audited canonical dataset: <strong>973.0 µg/m³</strong> (Dwarka Sector 8).
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Section 2: What BharatAir Does
    st.markdown("### What Does the BharatAir Platform Do?")
    col_p1, col_p2, col_p3 = st.columns(3)

    with col_p1:
        st.markdown(
            """
            <div class="pres-card">
                <div style="font-size: 1.8rem; margin-bottom: 8px;">🔬</div>
                <h4 style="color: #FFFFFF; margin: 0 0 6px 0;">Audits Real Regulatory Data</h4>
                <p style="color: #94A3B8; font-size: 0.875rem; line-height: 1.5;">
                    Extracts and verifies 92 continuous months of Central Pollution Control Board (CPCB) observations,
                    rejecting unphysical interpolations, synthetic fills, and uncalibrated consumer sensors.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_p2:
        st.markdown(
            """
            <div class="pres-card">
                <div style="font-size: 1.8rem; margin-bottom: 8px;">🤖</div>
                <h4 style="color: #FFFFFF; margin: 0 0 6px 0;">Trains Diverse AI Families</h4>
                <p style="color: #94A3B8; font-size: 0.875rem; line-height: 1.5;">
                    Systematically builds classical baselines, gradient-boosted trees (XGBoost, Random Forest),
                    and deep neural sequence networks (LSTM, GRU, TCN) across 3 distinct lookbacks.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_p3:
        st.markdown(
            """
            <div class="pres-card">
                <div style="font-size: 1.8rem; margin-bottom: 8px;">🎯</div>
                <h4 style="color: #FFFFFF; margin: 0 0 6px 0;">Reveals Atmospheric Horizons</h4>
                <p style="color: #94A3B8; font-size: 0.875rem; line-height: 1.5;">
                    Evaluates multi-hour horizons (+1h, +6h, +12h, +24h ahead) to rigorously answer:
                    at what forecast distance do deep sequence models truly add value over classical ML?
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Bottom navigation
    render_chapter_buttons(chapter_idx)

