"""Geospatial PyDeck map components for BharatAir."""

import pandas as pd
import pydeck as pdk
import streamlit as st

from bharatair.dashboard.config import PILOT_STATION


def render_station_map(selected_station_id: str = "site_1422") -> None:
    """Render PyDeck interactive map showing verified CPCB station in Delhi NCR."""
    data = [
        {
            "station_id": PILOT_STATION["station_id"],
            "station_name": PILOT_STATION["station_name"],
            "city": PILOT_STATION["city"],
            "agency": PILOT_STATION["agency"],
            "latitude": PILOT_STATION["latitude"],
            "longitude": PILOT_STATION["longitude"],
            "observations": f"{PILOT_STATION['total_observations']:,}",
            "coverage": f"{100 - PILOT_STATION['missingness_pct']:.2f}%",
            "status": "Verified Continuous Station",
            "color": [45, 212, 191, 230],  # Teal
            "radius": 500,
        }
    ]
    df_map = pd.DataFrame(data)

    view_state = pdk.ViewState(
        latitude=28.5710,
        longitude=77.0719,
        zoom=11.2,
        pitch=30,
        bearing=0,
    )

    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_map,
        get_position=["longitude", "latitude"],
        get_color="color",
        get_radius="radius",
        pickable=True,
        auto_highlight=True,
    )

    column_layer = pdk.Layer(
        "ColumnLayer",
        data=df_map,
        get_position=["longitude", "latitude"],
        get_elevation=900,
        elevation_scale=1,
        radius=250,
        get_fill_color=[56, 189, 248, 200],  # Cyan
        pickable=True,
        auto_highlight=True,
    )

    tooltip = {
        "html": """
        <div style="font-family: sans-serif; padding: 8px 10px; font-size: 12px; color: #FFFFFF; background-color: #0F172A; border-radius: 6px; border: 1px solid rgba(255,255,255,0.15);">
            <strong style="color: #2DD4BF;">{station_name}</strong><br/>
            Station ID: <code style="color: #38BDF8;">{station_id}</code><br/>
            Agency: {agency}<br/>
            Verified Records: <b>{observations} hrs</b><br/>
            Active Completeness: <b>{coverage}</b><br/>
            Network: <span style="color: #34D399; font-weight: 600;">CPCB CAAQM</span>
        </div>
        """,
        "style": {
            "backgroundColor": "transparent",
            "color": "#FFFFFF",
        },
    }

    deck = pdk.Deck(
        layers=[scatter_layer, column_layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="dark",
    )

    st.pydeck_chart(deck, use_container_width=True)
