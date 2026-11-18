"""Time-series charts for BharatAir with presentation styling."""

import altair as alt
import pandas as pd
from bharatair.dashboard.charts.theme import apply_cinematic_theme
from bharatair.dashboard.config import NAAQS_PM25_24H_STANDARD, WHO_PM25_24H_GUIDELINE


def build_historical_pm25_chart(
    df: pd.DataFrame,
    start_date: str = None,
    end_date: str = None,
    aggregation: str = "Daily Mean",
) -> alt.Chart:
    """Build large, interactive historical time series chart with NAAQS benchmark overlay."""
    if df.empty:
        return alt.Chart(pd.DataFrame({"x": [], "y": []})).mark_line()

    df_plot = df.copy()
    if start_date:
        df_plot = df_plot[df_plot["timestamp_ist"] >= pd.to_datetime(start_date)]
    if end_date:
        df_plot = df_plot[df_plot["timestamp_ist"] <= pd.to_datetime(end_date)]

    # Aggregation
    if aggregation == "Daily Mean":
        df_plot = (
            df_plot.set_index("timestamp_ist")
            .resample("1D")["value"]
            .mean()
            .reset_index()
            .rename(columns={"timestamp_ist": "time", "value": "pm25"})
        )
    elif aggregation == "Monthly Mean":
        df_plot = (
            df_plot.set_index("timestamp_ist")
            .resample("1ME")["value"]
            .mean()
            .reset_index()
            .rename(columns={"timestamp_ist": "time", "value": "pm25"})
        )
    else:  # Hourly subsampled for snappy presentation
        df_plot = df_plot.rename(columns={"timestamp_ist": "time", "value": "pm25"})
        if len(df_plot) > 10000:
            df_plot = df_plot.iloc[::2]

    df_plot = df_plot.dropna(subset=["pm25"])

    # Base line chart
    base = alt.Chart(df_plot).encode(
        x=alt.X("time:T", title="Timeline (IST)", axis=alt.Axis(format="%b %Y")),
        y=alt.Y("pm25:Q", title="PM2.5 (µg/m³)", scale=alt.Scale(zero=True)),
        tooltip=[
            alt.Tooltip("time:T", title="Date (IST)", format="%Y-%m-%d %H:%M"),
            alt.Tooltip("pm25:Q", title="PM2.5 Concentration", format=".1f"),
        ],
    )

    line = base.mark_line(color="#2DD4BF", strokeWidth=1.8)

    # Reference rule for Indian National Standard (60 µg/m³)
    rule_naaqs = (
        alt.Chart(pd.DataFrame({"y": [NAAQS_PM25_24H_STANDARD], "label": ["NAAQS Standard (60 µg/m³)"]}))
        .mark_rule(color="#F43F5E", strokeDash=[4, 4], strokeWidth=1.5)
        .encode(y="y:Q")
    )

    # Reference rule for WHO 24-hr guideline (15 µg/m³)
    rule_who = (
        alt.Chart(pd.DataFrame({"y": [WHO_PM25_24H_GUIDELINE], "label": ["WHO Guideline (15 µg/m³)"]}))
        .mark_rule(color="#38BDF8", strokeDash=[2, 2], strokeWidth=1.2)
        .encode(y="y:Q")
    )

    chart = (line + rule_naaqs + rule_who).properties(height=360).interactive()
    return apply_cinematic_theme(chart)


def build_diurnal_profile_chart(df: pd.DataFrame) -> alt.Chart:
    """Build 24-hour diurnal cycle profile (hourly medians and IQR)."""
    if df.empty:
        return alt.Chart(pd.DataFrame({"hour": [], "pm25": []})).mark_line()

    df_diurnal = df.copy()
    df_diurnal["hour"] = df_diurnal["timestamp_ist"].dt.hour

    grouped = (
        df_diurnal.groupby("hour")["value"]
        .agg(
            median="median",
            p25=lambda x: x.quantile(0.25),
            p75=lambda x: x.quantile(0.75),
            mean="mean",
        )
        .reset_index()
    )

    # Area band for IQR (25th to 75th percentile)
    band = (
        alt.Chart(grouped)
        .mark_area(opacity=0.25, color="#2DD4BF")
        .encode(
            x=alt.X("hour:O", title="Hour of Day (IST: 00 to 23)"),
            y=alt.Y("p25:Q", title="PM2.5 (µg/m³)"),
            y2="p75:Q",
        )
    )

    # Median line
    median_line = (
        alt.Chart(grouped)
        .mark_line(color="#38BDF8", strokeWidth=2.8, point=alt.OverlayMarkDef(color="#38BDF8", size=50))
        .encode(
            x=alt.X("hour:O", title="Hour of Day (IST: 00 to 23)"),
            y=alt.Y("median:Q", title="PM2.5 (µg/m³)"),
            tooltip=[
                alt.Tooltip("hour:O", title="Hour (IST)"),
                alt.Tooltip("median:Q", title="Median PM2.5 (µg/m³)", format=".1f"),
                alt.Tooltip("mean:Q", title="Mean PM2.5 (µg/m³)", format=".1f"),
                alt.Tooltip("p25:Q", title="25th Percentile", format=".1f"),
                alt.Tooltip("p75:Q", title="75th Percentile", format=".1f"),
            ],
        )
    )

    chart = (band + median_line).properties(height=320)
    return apply_cinematic_theme(chart)


def build_forecast_backtest_chart(df_preds: pd.DataFrame) -> alt.Chart:
    """Build multi-horizon actual vs predicted time series overlay."""
    if df_preds.empty:
        return alt.Chart(pd.DataFrame({"time": [], "val": []})).mark_line()

    df_melt = pd.melt(
        df_preds,
        id_vars=["target_timestamp"],
        value_vars=["actual", "predicted"],
        var_name="Series",
        value_name="PM25",
    )
    df_melt["Series"] = df_melt["Series"].map({"actual": "Ground Truth Actual", "predicted": "Offline Model Prediction"})

    chart = (
        alt.Chart(df_melt)
        .mark_line(strokeWidth=2.2)
        .encode(
            x=alt.X("target_timestamp:T", title="Observation Timestamp (IST)"),
            y=alt.Y("PM25:Q", title="PM2.5 Concentration (µg/m³)"),
            color=alt.Color(
                "Series:N",
                scale=alt.Scale(
                    domain=["Ground Truth Actual", "Offline Model Prediction"],
                    range=["#94A3B8", "#2DD4BF"],
                ),
                legend=alt.Legend(orient="top", title=None),
            ),
            tooltip=[
                alt.Tooltip("target_timestamp:T", title="Time (IST)", format="%Y-%m-%d %H:%M"),
                alt.Tooltip("Series:N", title="Series"),
                alt.Tooltip("PM25:Q", title="PM2.5 (µg/m³)", format=".1f"),
            ],
        )
        .properties(height=360)
        .interactive()
    )
    return apply_cinematic_theme(chart)
