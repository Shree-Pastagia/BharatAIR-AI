"""Model comparison and error analysis charts with presentation styling."""

import altair as alt
import pandas as pd
from bharatair.dashboard.charts.theme import apply_cinematic_theme
from bharatair.dashboard.config import POLLUTION_TIERS


def build_model_comparison_bar_chart(
    df_metrics: pd.DataFrame,
    horizon: int = 1,
    metric: str = "mae",
) -> alt.Chart:
    """Build bar chart comparing model validation metrics for a specific horizon."""
    if df_metrics.empty:
        return alt.Chart(pd.DataFrame({"model": [], "metric": []})).mark_bar()

    subset = df_metrics[df_metrics["horizon_hours"] == horizon].copy()
    if subset.empty:
        return alt.Chart(pd.DataFrame({"model": [], "metric": []})).mark_bar()

    # Best input length L per model
    best_per_model = subset.sort_values(by=metric).groupby("model").first().reset_index()

    metric_title = "Validation MAE (µg/m³)" if metric == "mae" else "Validation RMSE (µg/m³)"

    chart = (
        alt.Chart(best_per_model)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X(f"{metric}:Q", title=metric_title),
            y=alt.Y("model:N", sort="x", title="Model Architecture"),
            color=alt.Color(
                "family:N",
                scale=alt.Scale(
                    domain=["baseline", "traditional_ml", "deep_learning"],
                    range=["#64748B", "#38BDF8", "#2DD4BF"],
                ),
                legend=alt.Legend(title="Family", orient="top"),
            ),
            tooltip=[
                alt.Tooltip("model:N", title="Model"),
                alt.Tooltip("family:N", title="Family"),
                alt.Tooltip("input_hours:Q", title="Input (h)"),
                alt.Tooltip(f"{metric}:Q", title=metric_title, format=".2f"),
                alt.Tooltip("training_seconds:Q", title="Fit Seconds", format=".2f"),
            ],
        )
        .properties(height=280)
    )
    return apply_cinematic_theme(chart)


def build_horizon_degradation_chart(df_metrics: pd.DataFrame) -> alt.Chart:
    """Build multi-horizon error curve (+1h to +24h) for key architectures."""
    if df_metrics.empty:
        return alt.Chart(pd.DataFrame({"h": [], "mae": []})).mark_line()

    subset = df_metrics[
        (df_metrics["input_hours"] == 24) | (df_metrics["family"] == "baseline")
    ].copy()

    chart = (
        alt.Chart(subset)
        .mark_line(point=alt.OverlayMarkDef(size=60), strokeWidth=2.4)
        .encode(
            x=alt.X(
                "horizon_hours:O",
                title="Forecast Horizon Ahead",
                axis=alt.Axis(labelExpr="'+' + datum.value + 'h'"),
            ),
            y=alt.Y("mae:Q", title="Validation MAE (µg/m³)", scale=alt.Scale(zero=False)),
            color=alt.Color(
                "model:N",
                scale=alt.Scale(scheme="tableau10"),
                legend=alt.Legend(title="Model (L=24h)", orient="right"),
            ),
            tooltip=[
                alt.Tooltip("model:N", title="Model"),
                alt.Tooltip("horizon_hours:O", title="Horizon"),
                alt.Tooltip("mae:Q", title="MAE", format=".2f"),
                alt.Tooltip("rmse:Q", title="RMSE", format=".2f"),
            ],
        )
        .properties(height=320)
    )
    return apply_cinematic_theme(chart)


def build_scatter_actual_vs_predicted(df_preds: pd.DataFrame) -> alt.Chart:
    """Build scatter plot of Predicted vs Actual PM2.5 with 1:1 diagonal."""
    if df_preds.empty:
        return alt.Chart(pd.DataFrame({"actual": [], "predicted": []})).mark_circle()

    sample_size = min(len(df_preds), 2500)
    df_sample = df_preds.sample(n=sample_size, random_state=42)
    max_val = max(df_sample["actual"].max(), df_sample["predicted"].max())

    points = (
        alt.Chart(df_sample)
        .mark_circle(size=24, opacity=0.45, color="#2DD4BF")
        .encode(
            x=alt.X("actual:Q", title="Ground Truth Actual PM2.5 (µg/m³)", scale=alt.Scale(domain=[0, max_val])),
            y=alt.Y("predicted:Q", title="Model Predicted PM2.5 (µg/m³)", scale=alt.Scale(domain=[0, max_val])),
            tooltip=[
                alt.Tooltip("target_timestamp:T", title="Time", format="%Y-%m-%d %H:%M"),
                alt.Tooltip("actual:Q", title="Actual", format=".1f"),
                alt.Tooltip("predicted:Q", title="Predicted", format=".1f"),
                alt.Tooltip("residual:Q", title="Error", format=".1f"),
            ],
        )
    )

    diag_df = pd.DataFrame({"x": [0, max_val], "y": [0, max_val]})
    diagonal = (
        alt.Chart(diag_df)
        .mark_line(color="#F43F5E", strokeDash=[4, 4], strokeWidth=1.8)
        .encode(x="x:Q", y="y:Q")
    )

    chart = (points + diagonal).properties(height=340).interactive()
    return apply_cinematic_theme(chart)


def build_error_by_pollution_tier(df_preds: pd.DataFrame) -> alt.Chart:
    """Build bar chart showing prediction error across pollution severity ranges."""
    if df_preds.empty or "actual" not in df_preds.columns:
        return alt.Chart(pd.DataFrame({"tier": [], "mae": []})).mark_bar()

    rows = []
    for tier in POLLUTION_TIERS:
        mask = (df_preds["actual"] >= tier["min"]) & (df_preds["actual"] < tier["max"])
        subset = df_preds[mask]
        if len(subset) > 0:
            tier_mae = (subset["predicted"] - subset["actual"]).abs().mean()
            rows.append({"Tier": tier["label"], "MAE": tier_mae, "Observations": len(subset)})

    df_tiers = pd.DataFrame(rows)
    if df_tiers.empty:
        return alt.Chart(pd.DataFrame({"Tier": [], "MAE": []})).mark_bar()

    chart = (
        alt.Chart(df_tiers)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X("MAE:Q", title="Mean Absolute Error (µg/m³)"),
            y=alt.Y("Tier:N", sort=None, title="Actual PM2.5 Severity Range"),
            color=alt.Color(
                "MAE:Q",
                scale=alt.Scale(scheme="tealblues"),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("Tier:N"),
                alt.Tooltip("MAE:Q", title="Tier MAE", format=".2f"),
                alt.Tooltip("Observations:Q", title="Observed Hours"),
            ],
        )
        .properties(height=240)
    )
    return apply_cinematic_theme(chart)


def build_feature_importance_chart(features: list[dict], max_features: int = 12) -> alt.Chart:
    """Build horizontal bar chart for top traditional ML feature importances."""
    if not features:
        return alt.Chart(pd.DataFrame({"feature": [], "importance": []})).mark_bar()

    df_fi = pd.DataFrame(features).head(max_features)
    val_col = "importance" if "importance" in df_fi.columns else "coefficient"

    chart = (
        alt.Chart(df_fi)
        .mark_bar(color="#38BDF8", cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X(f"{val_col}:Q", title="Feature Coefficient / Relative Weight"),
            y=alt.Y("feature:N", sort="-x", title="Autoregressive Lag Variable"),
            tooltip=[
                alt.Tooltip("feature:N", title="Feature"),
                alt.Tooltip(f"{val_col}:Q", title="Score", format=".4f"),
            ],
        )
        .properties(height=300)
    )
    return apply_cinematic_theme(chart)
