"""Standard research attribution and provenance footer."""

import streamlit as st


def render_footer() -> None:
    """Render consistent environmental data science footer."""
    st.markdown(
        """
        <div class="dashboard-footer">
            <strong>BharatAir: India Air Quality Intelligence & Deep Learning Forecasting</strong><br>
            Empirical CPCB CAAQM Research Benchmark • Canonical Station: Dwarka Sector 8, Delhi (<code>site_1422</code>)<br>
            Source: India Air Quality Database (XKDR Forum) • Phase 3 Validation Run: <code>phase3_cuda_full_20261117_073000</code><br>
            <em>Notice: All research metrics are preliminary validation results. Test partition is strictly locked. No live or synthetic forecasts.</em>
        </div>
        """,
        unsafe_allow_html=True,
    )

