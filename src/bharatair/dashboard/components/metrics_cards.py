"""Reusable research metric cards for BharatAir dashboard."""

import streamlit as st


def render_kpi_card(
    title: str,
    value: str,
    subtitle: str = "",
    status_color: str = "#0D9488",
    help_text: str = "",
) -> None:
    """Render a clean environmental analytics KPI metric card."""
    help_attr = f'title="{help_text}"' if help_text else ""
    st.markdown(
        f"""
        <div class="metric-card" {help_attr}>
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            {f'<div class="metric-subtitle" style="color: {status_color};">{subtitle}</div>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_row(cards: list[dict]) -> None:
    """Render a responsive horizontal grid of KPI cards."""
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            render_kpi_card(
                title=card.get("title", ""),
                value=card.get("value", ""),
                subtitle=card.get("subtitle", ""),
                status_color=card.get("status_color", "#0D9488"),
                help_text=card.get("help_text", ""),
            )

