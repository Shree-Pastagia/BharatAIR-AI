"""Chapter 5: Conclusion & Future Horizons — BharatAir Presentation."""

import streamlit as st
from bharatair.dashboard.components.presentation_nav import render_chapter_buttons, render_presentation_header


def render_page(chapter_idx: int = 4) -> None:
    """Render Chapter 5: What Comes Next?"""
    render_presentation_header(chapter_idx)

    st.markdown(
        """
        <div class="chapter-header">
            <h2 class="chapter-headline">What Comes Next?</h2>
        </div>
        <p class="chapter-desc">
            Reflecting on the findings of BharatAir, acknowledging current scientific limitations,
            and outlining the future roadmap for scalable air quality forecasting across Indian cities.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # What the Project Achieved
    st.markdown("### What BharatAir Successfully Achieved")

    col_a1, col_a2, col_a3 = st.columns(3)

    with col_a1:
        st.markdown(
            """
            <div class="pres-card" style="height: 100%;">
                <div style="font-size: 1.8rem; margin-bottom: 6px;">🏛️</div>
                <h4 style="color: #2DD4BF; margin: 4px 0 8px 0;">1. Regulatory Benchmark</h4>
                <p style="color: #CBD5E1; font-size: 0.875rem; line-height: 1.5;">
                    Established a 100% reproducible, zero-imputation benchmark on <strong>63,178 continuous CPCB hourly records</strong>,
                    proving that empirical atmospheric physics must not be artificially smoothed.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_a2:
        st.markdown(
            """
            <div class="pres-card" style="height: 100%;">
                <div style="font-size: 1.8rem; margin-bottom: 6px;">⚖️</div>
                <h4 style="color: #38BDF8; margin: 4px 0 8px 0;">2. Rigorous ML vs DL Test</h4>
                <p style="color: #CBD5E1; font-size: 0.875rem; line-height: 1.5;">
                    Demonstrated that <strong>gradient-boosted trees and random forests dominate short horizons (+1h, +6h, +12h)</strong>,
                    saving massive compute while matching or beating complex recurrent neural networks.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_a3:
        st.markdown(
            """
            <div class="pres-card" style="height: 100%;">
                <div style="font-size: 1.8rem; margin-bottom: 6px;">🧠</div>
                <h4 style="color: #A855F7; margin: 4px 0 8px 0;">3. Synoptic Deep Memory</h4>
                <p style="color: #CBD5E1; font-size: 0.875rem; line-height: 1.5;">
                    Showed that at <strong>+24 hours</strong>, <strong>Temporal Convolutional Networks (TCN)</strong> with 168-hour receptive
                    fields succeed where LSTMs struggle, capturing multi-day synoptic weather persistence.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Scientific Limitations & Honest Disclosure
    st.markdown("### Transparent Project Limitations")

    col_l1, col_l2 = st.columns(2)

    with col_l1:
        st.markdown(
            """
            <div class="pres-card">
                <h4 style="color: #FBBF24; margin-top: 0; font-size: 1.05rem;">1. Single-Station Geographic Scope</h4>
                <p style="color: #CBD5E1; font-size: 0.875rem; line-height: 1.6; margin-bottom: 0;">
                    To maintain absolute scientific integrity in Phase 3, evaluations were conducted on one top-ranked
                    CPCB pilot station (<strong>site_1422, Dwarka Sector 8, Delhi</strong>). Atmospheric conditions in Delhi
                    exhibit sharp micro-climate variations across industrial, traffic, and green zones that require multi-station modeling.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_l2:
        st.markdown(
            """
            <div class="pres-card">
                <h4 style="color: #FBBF24; margin-top: 0; font-size: 1.05rem;">2. Univariate Sequence Signals</h4>
                <p style="color: #CBD5E1; font-size: 0.875rem; line-height: 1.6; margin-bottom: 0;">
                    Models currently rely purely on autoregressive historical PM2.5 lags. While remarkably effective,
                    external physical drivers such as <strong>wind direction vectors, planetary boundary layer height (PBLH),
                    ambient temperature, and relative humidity</strong> were not directly coupled into the feature matrix.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Future Roadmap
    st.markdown("### The Future Research Roadmap")

    col_r1, col_r2 = st.columns(2)

    with col_r1:
        st.markdown(
            """
            <div class="pres-card-highlight">
                <div style="font-size: 0.8rem; color: #38BDF8; font-weight: 700; text-transform: uppercase;">Phase 4 Expansion</div>
                <h4 style="color: #FFFFFF; margin: 4px 0 10px 0;">India-Wide Multi-City CPCB Scaling</h4>
                <p style="color: #CBD5E1; font-size: 0.875rem; line-height: 1.6;">
                    The research methodology established in Delhi will scale across validated CPCB CAAQM monitoring stations
                    in <strong>Ahmedabad, Bengaluru, Mumbai, Kolkata, and Hyderabad</strong> once the ongoing Phase 4 audit is verified.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_r2:
        st.markdown(
            """
            <div class="pres-card-highlight">
                <div style="font-size: 0.8rem; color: #2DD4BF; font-weight: 700; text-transform: uppercase;">Next-Gen Modeling</div>
                <h4 style="color: #FFFFFF; margin: 4px 0 10px 0;">Spatiotemporal Graph Neural Networks (GNNs)</h4>
                <p style="color: #CBD5E1; font-size: 0.875rem; line-height: 1.6;">
                    Future architectures can connect city stations into a spatial graph where edges model atmospheric transport,
                    dispersion velocity, and wind advection vectors across urban airsheds.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Strong Closing Statement Banner
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, rgba(56, 189, 248, 0.15) 0%, rgba(45, 212, 191, 0.1) 100%); border: 1px solid rgba(45, 212, 191, 0.35); border-radius: 16px; padding: 36px 40px; margin-top: 36px; text-align: center; box-shadow: 0 12px 36px rgba(0,0,0,0.4);">
            <div style="font-size: 2.0rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.02em; margin-bottom: 12px;">
                "Data Science for Breathable Air"
            </div>
            <p style="font-size: 1.1rem; color: #CBD5E1; max-width: 800px; margin: 0 auto; line-height: 1.6;">
                By combining uncompromised regulatory ground truth, disciplined zero-imputation accounting,
                and empirical multi-horizon sequence modeling, BharatAir demonstrates how modern artificial intelligence
                can provide trustworthy environmental intelligence for public health action.
            </p>
            <div style="margin-top: 20px; font-size: 0.85rem; color: #2DD4BF; font-weight: 600;">
                Thank you! Questions and Discussion Welcome.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Bottom navigation
    render_chapter_buttons(chapter_idx)

