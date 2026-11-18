"""BharatAir — Professional Air Quality Analytics Dashboard.

Production-grade environmental intelligence and multi-horizon deep learning
forecasting platform built on authentic CPCB CAAQM monitoring observations.
"""

from pathlib import Path
import sys

# Ensure src is on sys.path
repo_root = Path(__file__).resolve().parent
src_dir = repo_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import streamlit as st

from bharatair.dashboard.config import PILOT_STATION
from bharatair.dashboard.pages import (
    data_quality,
    executive_overview,
    forecast_explorer,
    geographic_explorer,
    historical_aq,
    methodology,
    ml_evaluation,
    statistical_research,
)
from bharatair.dashboard.styles import apply_custom_styles


def main() -> None:
    """Initialize and run the multi-page Streamlit analytics dashboard."""
    st.set_page_config(
        page_title="BharatAir — Air Quality Intelligence Dashboard",
        page_icon="🌫️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Apply modern dark-navy dashboard stylesheet
    apply_custom_styles()

    # Sidebar Brand Header
    st.sidebar.markdown(
        """
        <div style="padding: 10px 4px 16px 4px;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.02em;">
                🌫️ BharatAir
            </div>
            <div style="font-size: 0.8rem; color: #38BDF8; font-weight: 600; margin-top: 2px;">
                Air Quality Intelligence & Forecasting
            </div>
            <div style="display: flex; gap: 6px; margin-top: 10px;">
                <span style="background: rgba(56, 189, 248, 0.12); color: #38BDF8; font-size: 0.7rem; font-weight: 600; padding: 2px 8px; border-radius: 9999px; border: 1px solid rgba(56, 189, 248, 0.28);">
                    Delhi site_1422
                </span>
                <span style="background: rgba(16, 185, 129, 0.12); color: #34D399; font-size: 0.7rem; font-weight: 600; padding: 2px 8px; border-radius: 9999px; border: 1px solid rgba(16, 185, 129, 0.28);">
                    CPCB CAAQM
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 8-Page Navigation Definition
    pages = [
        st.Page(
            executive_overview.render_page,
            title="Executive Overview",
            icon="📊",
            url_path="overview",
            default=True,
        ),
        st.Page(
            geographic_explorer.render_page,
            title="Geographic Explorer",
            icon="🗺️",
            url_path="geographic",
        ),
        st.Page(
            historical_aq.render_page,
            title="Historical Air Quality",
            icon="📈",
            url_path="historical",
        ),
        st.Page(
            data_quality.render_page,
            title="Data Quality",
            icon="🔬",
            url_path="quality",
        ),
        st.Page(
            statistical_research.render_page,
            title="Statistical Research",
            icon="📉",
            url_path="statistics",
        ),
        st.Page(
            ml_evaluation.render_page,
            title="ML Model Evaluation",
            icon="🤖",
            url_path="evaluation",
        ),
        st.Page(
            forecast_explorer.render_page,
            title="Forecast Explorer",
            icon="🔮",
            url_path="forecasts",
        ),
        st.Page(
            methodology.render_page,
            title="Methodology & Sources",
            icon="📚",
            url_path="methodology",
        ),
    ]

    nav = st.navigation(pages)

    # Sidebar Summary Info
    st.sidebar.markdown("<hr style='border-color: rgba(255,255,255,0.08); margin: 20px 0;'>", unsafe_allow_html=True)
    st.sidebar.markdown(
        f"""
        <div style="font-size: 0.75rem; color: #94A3B8; padding: 0 4px; line-height: 1.6;">
            <div>Station: <strong>Dwarka Sector 8, Delhi</strong></div>
            <div>Observations: <strong>{PILOT_STATION['total_observations']:,} hours</strong></div>
            <div>Span: <strong>Feb 2018 – Sep 2025</strong></div>
            <div style="margin-top: 8px; color: #64748B; font-size: 0.7rem;">
                72 ML/DL Candidates + 8 Baselines<br>
                Source: XKDR India AQ Database
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Run the selected page
    nav.run()


if __name__ == "__main__":
    main()
