"""Station information and telemetry component."""

import streamlit as st
from bharatair.dashboard.config import PILOT_STATION


def render_station_details_panel(station: dict = None) -> None:
    """Render comprehensive pilot station details panel."""
    if station is None:
        station = PILOT_STATION

    st.markdown(
        f"""
        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px;">
                <div>
                    <h3 style="margin: 0; color: #0F172A; font-size: 1.15rem;">{station['station_name']}</h3>
                    <p style="margin: 2px 0 0 0; color: #64748B; font-size: 0.825rem;">
                        Station ID: <code style="color: #0F766E;">{station['station_id']}</code> | Network: <strong>{station['network']}</strong>
                    </p>
                </div>
                <span class="badge-pill badge-verified">CPCB Verified Pilot</span>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-top: 10px;">
                <div>
                    <span style="font-size: 0.75rem; color: #64748B; text-transform: uppercase; font-weight: 600;">Agency</span>
                    <div style="font-size: 0.9rem; font-weight: 500; color: #1E293B;">{station['agency']}</div>
                </div>
                <div>
                    <span style="font-size: 0.75rem; color: #64748B; text-transform: uppercase; font-weight: 600;">Location Coordinates</span>
                    <div style="font-size: 0.9rem; font-weight: 500; color: #1E293B;">{station['latitude']:.4f}° N, {station['longitude']:.4f}° E</div>
                </div>
                <div>
                    <span style="font-size: 0.75rem; color: #64748B; text-transform: uppercase; font-weight: 600;">Verified Timeline</span>
                    <div style="font-size: 0.9rem; font-weight: 500; color: #1E293B;">{station['start_date']} to {station['end_date']} (92 Mos)</div>
                </div>
                <div>
                    <span style="font-size: 0.75rem; color: #64748B; text-transform: uppercase; font-weight: 600;">Regional Ranking</span>
                    <div style="font-size: 0.9rem; font-weight: 500; color: #0D9488;">Rank #{station['rank_in_region']} in Delhi NCR</div>
                </div>
                <div>
                    <span style="font-size: 0.75rem; color: #64748B; text-transform: uppercase; font-weight: 600;">Canonical Observations</span>
                    <div style="font-size: 0.9rem; font-weight: 500; color: #1E293B;">{station['total_observations']:,} Verified Hours</div>
                </div>
                <div>
                    <span style="font-size: 0.75rem; color: #64748B; text-transform: uppercase; font-weight: 600;">Active Missingness</span>
                    <div style="font-size: 0.9rem; font-weight: 500; color: #16A34A;">{station['missingness_pct']:.3f}% (95.05% Complete)</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

