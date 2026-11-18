"""Cinematic chart theme for Altair visualizers in dark mode."""

import altair as alt


def apply_cinematic_theme(chart: alt.Chart) -> alt.Chart:
    """Apply high-contrast cinematic dark theme to any Altair chart."""
    return (
        chart.configure_view(
            strokeWidth=0,
            fill="#131C31",
        )
        .configure_axis(
            labelColor="#94A3B8",
            titleColor="#E2E8F0",
            labelFontSize=11,
            titleFontSize=12,
            gridColor="rgba(255, 255, 255, 0.07)",
            tickColor="rgba(255, 255, 255, 0.15)",
            domainColor="rgba(255, 255, 255, 0.15)",
        )
        .configure_legend(
            labelColor="#E2E8F0",
            titleColor="#F8FAFC",
            labelFontSize=11,
            titleFontSize=12,
            symbolSize=100,
        )
        .configure_title(
            color="#FFFFFF",
            fontSize=14,
            fontWeight=600,
        )
    )

