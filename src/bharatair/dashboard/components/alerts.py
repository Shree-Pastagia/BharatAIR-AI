"""Standard callouts, status badges, and protocol notices for BharatAir."""

import streamlit as st


def render_project_status_header(page_title: str, subtitle: str = "") -> None:
    """Render consistent page header with research-grade status badges."""
    st.markdown(f"## {page_title}")
    if subtitle:
        st.markdown(f"<p style='color: #64748B; font-size: 0.95rem; margin-top: -8px;'>{subtitle}</p>", unsafe_allow_html=True)
    
    badges_html = """
    <div class="badge-container">
        <span class="badge-pill badge-verified">✓ CPCB CAAQM Network Verified</span>
        <span class="badge-pill badge-verified">Station: site_1422 (Delhi Pilot)</span>
        <span class="badge-pill badge-preliminary">Phase 3 Preliminary Validation</span>
        <span class="badge-pill badge-locked">🔒 Test Partition Locked</span>
    </div>
    """
    st.markdown(badges_html, unsafe_allow_html=True)


def render_preliminary_validation_notice() -> None:
    """Display warning callout that validation audit is in progress by Codex."""
    st.markdown(
        """
        <div class="info-callout" style="border-left-color: #0284C7;">
            <strong>Preliminary Validation Results Notice:</strong> The Phase 3 validation run (<code>phase3_cuda_full_20261117_073000</code>)
            is presented as preliminary validation evidence. The formal validation results audit is currently in progress by Codex.
            Final model rankings and statistical verifications will be locked upon audit completion.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_test_partition_locked_callout() -> None:
    """Display locked test partition callout preserving scientific protocol."""
    st.markdown(
        """
        <div class="locked-callout">
            <div class="locked-icon">🔒</div>
            <h4 style="color: #0F172A; margin-bottom: 6px;">Final Test Partition Gate Locked</h4>
            <p style="color: #64748B; max-width: 680px; margin: 0 auto; font-size: 0.875rem;">
                In strict adherence to empirical research standards, the final test partition
                (<strong>2024-04-30 02:00:00 to 2025-09-01 23:00:00 IST</strong>, representing 15% out-of-sample data)
                is completely unaccessed. Test metrics, predictions, and model evaluation will remain
                locked until validation candidate selection is frozen and audited.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_backtest_disclaimer() -> None:
    """Display explicit historical backtest disclaimer banner for forecast explorer."""
    st.markdown(
        """
        <div class="info-callout" style="border-left-color: #B45309; background-color: #FFFBEB;">
            <strong style="color: #92400E;">Historical Validation Backtest Predictions Only:</strong>
            These predictions represent offline multi-horizon model evaluations against the historical validation partition
            (March 2023 – April 2024). They are <strong>not live or operational real-time forecasts</strong>. No models were retrained
            or evaluated on live streams.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pilot_station_restriction_notice() -> None:
    """Display notice that only verified pilot station site_1422 is currently populated."""
    st.markdown(
        """
        <div class="info-callout">
            <strong>Data Restriction Policy:</strong> In compliance with the BharatAir data integrity protocol,
            only verified CPCB CAAQM PM2.5 observations from the canonical Delhi pilot station (<strong>site_1422, Dwarka Sector 8</strong>)
            are displayed. Embassy monitors, low-cost sensor networks, foreign data, synthetic values, and unverified stations
            are strictly excluded.
        </div>
        """,
        unsafe_allow_html=True,
    )

