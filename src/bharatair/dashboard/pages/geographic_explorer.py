"""Page 2: Geographic Explorer — BharatAir Dashboard."""

import streamlit as st

from bharatair.dashboard.charts.maps import render_station_map
from bharatair.dashboard.components.footer import render_footer
from bharatair.dashboard.config import PILOT_STATION


def render_page() -> None:
    """Render Geographic Explorer page."""
    st.markdown(
        """
        <div class="page-header">
            <h1 class="page-title">Geographic Explorer</h1>
            <div class="page-subtitle">
                Continuous Ambient Air Quality Monitoring Network — Delhi Pilot Station
            </div>
            <div class="badge-row">
                <span class="status-pill pill-verified">CPCB CAAQM Network</span>
                <span class="status-pill pill-station">site_1422 • Delhi NCR</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Station Information Panel
    st.markdown(
        f"""
        <div class="content-panel">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; flex-wrap: wrap;">
                <div>
                    <h3 style="margin: 0; color: #FFFFFF; font-size: 1.25rem;">{PILOT_STATION['station_name']}</h3>
                    <p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 0.85rem;">
                        Station Identifier: <code style="color: #38BDF8;">{PILOT_STATION['station_id']}</code> • Agency: <strong>{PILOT_STATION['agency']}</strong>
                    </p>
                </div>
                <span class="status-pill pill-verified">Verified Operational Station</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 16px;">
                <div>
                    <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">Geographic Coordinates</div>
                    <div style="font-size: 0.95rem; font-weight: 600; color: #FFFFFF; margin-top: 2px;">{PILOT_STATION['latitude']:.4f}° N, {PILOT_STATION['longitude']:.4f}° E</div>
                    <div style="font-size: 0.75rem; color: #64748B;">Elevation: {PILOT_STATION['elevation_m']} m above sea level</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">Monitored Parameter</div>
                    <div style="font-size: 0.95rem; font-weight: 600; color: #2DD4BF; margin-top: 2px;">PM2.5 (Fine Particulate Matter)</div>
                    <div style="font-size: 0.75rem; color: #64748B;">Unit: {PILOT_STATION['unit']} (Mass Concentration)</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">Temporal Record Span</div>
                    <div style="font-size: 0.95rem; font-weight: 600; color: #FFFFFF; margin-top: 2px;">{PILOT_STATION['start_date']} to {PILOT_STATION['end_date']}</div>
                    <div style="font-size: 0.75rem; color: #64748B;">{PILOT_STATION['active_months']} Continuous Calendar Months</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">Data Completeness</div>
                    <div style="font-size: 0.95rem; font-weight: 600; color: #34D399; margin-top: 2px;">{100 - PILOT_STATION['missingness_pct']:.2f}% Active Coverage</div>
                    <div style="font-size: 0.75rem; color: #64748B;">{PILOT_STATION['total_observations']:,} Verified Observed Hours</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Geospatial Map
    st.markdown(
        """
        <div class="panel-heading">Geospatial Station Location & Urban Context</div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Interactive 3D geospatial map centered on Dwarka Sector 8, Delhi. Use scroll wheel to zoom and drag to pan.")

    render_station_map(PILOT_STATION["station_id"])

    # Technical Sensor Notes
    st.markdown(
        """
        <div class="content-panel" style="margin-top: 20px;">
            <div class="panel-heading">Station Context & Siting Environment</div>
            <p style="color: #CBD5E1; font-size: 0.9rem; line-height: 1.6; margin-bottom: 0;">
                The Dwarka Sector 8 monitoring station operates as part of the continuous regulatory network
                maintained by the Delhi Pollution Control Committee (DPCC) under Central Pollution Control Board (CPCB) standards.
                Located in southwest Delhi, the site monitors urban residential, commercial, and transit background air quality,
                capturing both regional transboundary pollution plumes and local vehicular emissions.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_footer()
