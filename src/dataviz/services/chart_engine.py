"""Chart recommendation and configuration engine.

Analyzes column types to recommend appropriate chart types, then generates
Plotly.js-compatible JSON configurations for rendering in the frontend.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from dataviz.logger import get_logger
from dataviz.models.schemas import (
    ChartRecommendation,
    ChartRequest,
    ChartResponse,
    ChartType,
    ColumnType,
    DataProfile,
)

logger = get_logger(__name__)

COLOR_PALETTES = {
    "default": [
        "#6366f1", "#8b5cf6", "#a78bfa", "#c084fc",
        "#e879f9", "#f472b6", "#fb7185", "#f87171",
        "#fb923c", "#fbbf24", "#a3e635", "#34d399",
        "#22d3ee", "#60a5fa",
    ],
    "ocean": [
        "#0ea5e9", "#06b6d4", "#14b8a6", "#10b981",
        "#059669", "#047857", "#0284c7", "#0369a1",
    ],
    "sunset": [
        "#f97316", "#ef4444", "#ec4899", "#d946ef",
        "#a855f7", "#8b5cf6", "#f59e0b", "#eab308",
    ],
    "earth": [
        "#78716c", "#92400e", "#a16207", "#4d7c0f",
        "#15803d", "#0f766e", "#1e40af", "#6d28d9",
    ],
}

_BASE_LAYOUT: dict[str, Any] = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "Inter, system-ui, sans-serif", "color": "#e2e8f0", "size": 13},
    "margin": {"l": 60, "r": 30, "t": 50, "b": 60},
    "xaxis": {"gridcolor": "rgba(148,163,184,0.12)", "zerolinecolor": "rgba(148,163,184,0.2)"},
    "yaxis": {"gridcolor": "rgba(148,163,184,0.12)", "zerolinecolor": "rgba(148,163,184,0.2)"},
    "legend": {"bgcolor": "rgba(0,0,0,0)", "font": {"color": "#cbd5e1"}},
    "hoverlabel": {
        "bgcolor": "#1e293b",
        "font": {"color": "#f1f5f9", "family": "Inter, system-ui, sans-serif"},
        "bordercolor": "#475569",
    },
}


def _get_columns_by_type(profile: DataProfile) -> dict[ColumnType, list[str]]:
    grouped: dict[ColumnType, list[str]] = {t: [] for t in ColumnType}
    for col in profile.columns:
        grouped[col.dtype].append(col.name)
    return grouped


def _get_colors(palette: str = "default") -> list[str]:
    return COLOR_PALETTES.get(palette, COLOR_PALETTES["default"])


def recommend_charts(df: pd.DataFrame, profile: DataProfile) -> list[ChartRecommendation]:
    """Analyze data and recommend appropriate chart types sorted by relevance."""
    by_type = _get_columns_by_type(profile)
    num = by_type[ColumnType.NUMERIC]
    cat = by_type[ColumnType.CATEGORICAL]
    dt = by_type[ColumnType.DATETIME]
    recs: list[ChartRecommendation] = []

    for col in num[:3]:
        recs.append(ChartRecommendation(chart_type=ChartType.HISTOGRAM, title=f"Distribution of {col}",
            description=f"Histogram showing the distribution of {col}", x_column=col, columns=[col], score=0.8))
        recs.append(ChartRecommendation(chart_type=ChartType.BOX, title=f"Box Plot of {col}",
            description=f"Box plot showing the spread of {col}", y_column=col, columns=[col], score=0.6))

    if len(num) >= 2:
        x, y = num[0], num[1]
        recs.append(ChartRecommendation(chart_type=ChartType.SCATTER, title=f"{x} vs {y}",
            description=f"Scatter plot comparing {x} and {y}", x_column=x, y_column=y, columns=[x, y], score=0.9))
        recs.append(ChartRecommendation(chart_type=ChartType.LINE, title=f"{y} over {x}",
            description=f"Line chart showing {y} trend over {x}", x_column=x, y_column=y, columns=[x, y], score=0.7))

    if cat and num:
        c, n = cat[0], num[0]
        recs.append(ChartRecommendation(chart_type=ChartType.BAR, title=f"{n} by {c}",
            description=f"Bar chart of {n} grouped by {c}", x_column=c, y_column=n, columns=[c, n], score=0.95))
        if df[c].nunique() <= 12:
            recs.append(ChartRecommendation(chart_type=ChartType.PIE, title=f"{n} Distribution by {c}",
                description=f"Pie chart showing {n} proportions across {c}", x_column=c, y_column=n, columns=[c, n], score=0.85))

    if dt and num:
        d, n = dt[0], num[0]
        recs.append(ChartRecommendation(chart_type=ChartType.LINE, title=f"{n} over Time",
            description=f"Time series of {n} over {d}", x_column=d, y_column=n, columns=[d, n], score=0.95))
        recs.append(ChartRecommendation(chart_type=ChartType.AREA, title=f"{n} Area over Time",
            description=f"Area chart of {n} over {d}", x_column=d, y_column=n, columns=[d, n], score=0.8))

    if len(num) >= 3:
        recs.append(ChartRecommendation(chart_type=ChartType.HEATMAP, title="Correlation Matrix",
            description=f"Heatmap of correlations between {len(num)} numeric columns", columns=num, score=0.75))

    if cat and len(num) >= 2:
        c = cat[0]
        cols = num[:4]
        recs.append(ChartRecommendation(chart_type=ChartType.GROUPED_BAR, title=f"Comparison by {c}",
            description=f"Grouped bar comparing {len(cols)} metrics across {c}", x_column=c, columns=[c] + cols, score=0.85))

    recs.sort(key=lambda r: r.score, reverse=True)
    for rec in recs:
        rec.plotly_config = generate_plotly_config(df, rec)
    logger.info("Generated %d chart recommendations", len(recs))
    return recs


def generate_plotly_config(df: pd.DataFrame, rec: ChartRecommendation, palette: str = "default") -> dict[str, Any]:
    """Generate Plotly.js JSON config for a chart recommendation."""
    colors = _get_colors(palette)
    ct = rec.chart_type
    x_col, y_col = rec.x_column, rec.y_column
    data: list[dict[str, Any]] = []
    layout = {**_BASE_LAYOUT, "title": {"text": rec.title, "font": {"size": 16}}}

    if ct == ChartType.BAR:
        agg = df.groupby(x_col)[y_col].sum().reset_index()
        data.append({"type": "bar", "x": agg[x_col].tolist(), "y": agg[y_col].tolist(),
                      "marker": {"color": colors[0], "cornerradius": 4}})
        layout["xaxis"]["title"] = {"text": x_col}
        layout["yaxis"]["title"] = {"text": y_col}
    elif ct == ChartType.LINE:
        data.append({"type": "scatter", "mode": "lines+markers", "x": df[x_col].tolist(),
                      "y": df[y_col].tolist(), "line": {"color": colors[0], "width": 2.5},
                      "marker": {"size": 4, "color": colors[0]}})
        layout["xaxis"]["title"] = {"text": x_col}
        layout["yaxis"]["title"] = {"text": y_col}
    elif ct == ChartType.SCATTER:
        data.append({"type": "scatter", "mode": "markers", "x": df[x_col].tolist(),
                      "y": df[y_col].tolist(), "marker": {"color": colors[0], "size": 8, "opacity": 0.7,
                      "line": {"width": 1, "color": colors[1]}}})
        layout["xaxis"]["title"] = {"text": x_col}
        layout["yaxis"]["title"] = {"text": y_col}
    elif ct == ChartType.PIE:
        agg = df.groupby(x_col)[y_col].sum().reset_index()
        data.append({"type": "pie", "labels": agg[x_col].tolist(), "values": agg[y_col].tolist(),
                      "marker": {"colors": colors}, "hole": 0.4, "textinfo": "label+percent"})
    elif ct == ChartType.HISTOGRAM:
        data.append({"type": "histogram", "x": df[x_col].tolist(),
                      "marker": {"color": colors[0], "line": {"color": colors[1], "width": 1}}, "opacity": 0.85})
        layout["xaxis"]["title"] = {"text": x_col}
        layout["yaxis"]["title"] = {"text": "Count"}
    elif ct == ChartType.BOX:
        data.append({"type": "box", "y": df[y_col].tolist(), "name": y_col,
                      "marker": {"color": colors[0]}, "boxmean": "sd"})
    elif ct == ChartType.AREA:
        data.append({"type": "scatter", "mode": "lines", "x": df[x_col].tolist(),
                      "y": df[y_col].tolist(), "fill": "tozeroy",
                      "fillcolor": "rgba(99,102,241,0.15)", "line": {"color": colors[0], "width": 2}})
        layout["xaxis"]["title"] = {"text": x_col}
        layout["yaxis"]["title"] = {"text": y_col}
    elif ct == ChartType.HEATMAP:
        corr = df[rec.columns].apply(pd.to_numeric, errors="coerce").corr()
        data.append({"type": "heatmap", "x": corr.columns.tolist(), "y": corr.index.tolist(),
                      "z": corr.values.tolist(), "colorscale": [[0, "#312e81"], [0.5, "#1e293b"], [1, "#6366f1"]],
                      "zmin": -1, "zmax": 1})
    elif ct in (ChartType.GROUPED_BAR, ChartType.STACKED_BAR):
        cat_col = x_col
        num_cols = [c for c in rec.columns if c != cat_col]
        agg = df.groupby(cat_col)[num_cols].sum().reset_index()
        for i, nc in enumerate(num_cols):
            data.append({"type": "bar", "name": nc, "x": agg[cat_col].tolist(),
                          "y": agg[nc].tolist(), "marker": {"color": colors[i % len(colors)]}})
        layout["barmode"] = "stack" if ct == ChartType.STACKED_BAR else "group"
        layout["xaxis"]["title"] = {"text": cat_col}

    return {"data": data, "layout": layout}


def build_chart_from_request(df: pd.DataFrame, request: ChartRequest) -> ChartResponse:
    """Build a chart response from an explicit user request."""
    rec = ChartRecommendation(chart_type=request.chart_type, title=request.title or f"{request.chart_type.value} Chart",
        description="User-requested chart", x_column=request.x_column, y_column=request.y_column, columns=request.columns)
    palette = request.color_scheme or "default"
    config = generate_plotly_config(df, rec, palette=palette)
    layout = config["layout"]
    if request.title:
        layout["title"] = {"text": request.title, "font": {"size": 16}}
    if request.x_label:
        layout.setdefault("xaxis", {})["title"] = {"text": request.x_label}
    if request.y_label:
        layout.setdefault("yaxis", {})["title"] = {"text": request.y_label}
    if request.aggregation and request.x_column and request.y_column:
        if request.aggregation in ("sum", "mean", "count", "min", "max", "median"):
            agg_df = df.groupby(request.x_column)[request.y_column].agg(request.aggregation).reset_index()
            if config["data"]:
                config["data"][0]["x"] = agg_df[request.x_column].tolist()
                config["data"][0]["y"] = agg_df[request.y_column].tolist()
    return ChartResponse(chart_type=request.chart_type, plotly_data=config["data"], plotly_layout=config["layout"])
