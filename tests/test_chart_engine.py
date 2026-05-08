"""Tests for the chart recommendation engine."""

import pandas as pd
import pytest

from dataviz.models.schemas import (
    ChartRequest,
    ChartType,
    ColumnProfile,
    ColumnType,
    DataProfile,
)
from dataviz.services.chart_engine import (
    build_chart_from_request,
    generate_plotly_config,
    recommend_charts,
    ChartRecommendation,
)


def _build_profile(columns: list[ColumnProfile], row_count: int = 6) -> DataProfile:
    """Helper to build a DataProfile for testing."""
    return DataProfile(
        columns=columns,
        row_count=row_count,
        has_header=True,
        delimiter=",",
    )


class TestRecommendCharts:
    """Tests for chart recommendations based on column types."""

    def test_categorical_and_numeric(self, sample_dataframe):
        profile = _build_profile([
            ColumnProfile(name="Category", dtype=ColumnType.CATEGORICAL, unique_count=3),
            ColumnProfile(name="Value1", dtype=ColumnType.NUMERIC),
            ColumnProfile(name="Value2", dtype=ColumnType.NUMERIC),
            ColumnProfile(name="Date", dtype=ColumnType.DATETIME),
        ])
        recs = recommend_charts(sample_dataframe, profile)
        types = [r.chart_type for r in recs]
        assert ChartType.BAR in types
        assert ChartType.PIE in types
        assert len(recs) > 0

    def test_numeric_only(self, numeric_only_dataframe):
        profile = _build_profile([
            ColumnProfile(name="X", dtype=ColumnType.NUMERIC),
            ColumnProfile(name="Y", dtype=ColumnType.NUMERIC),
            ColumnProfile(name="Z", dtype=ColumnType.NUMERIC),
        ], row_count=5)
        recs = recommend_charts(numeric_only_dataframe, profile)
        types = [r.chart_type for r in recs]
        assert ChartType.SCATTER in types
        assert ChartType.HISTOGRAM in types
        assert ChartType.HEATMAP in types

    def test_single_numeric_column(self):
        df = pd.DataFrame({"Value": [10, 20, 30, 40, 50]})
        profile = _build_profile([
            ColumnProfile(name="Value", dtype=ColumnType.NUMERIC),
        ], row_count=5)
        recs = recommend_charts(df, profile)
        types = [r.chart_type for r in recs]
        assert ChartType.HISTOGRAM in types
        assert ChartType.BOX in types

    def test_datetime_and_numeric(self):
        df = pd.DataFrame({
            "Date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "Sales": [100, 200, 150],
        })
        profile = _build_profile([
            ColumnProfile(name="Date", dtype=ColumnType.DATETIME),
            ColumnProfile(name="Sales", dtype=ColumnType.NUMERIC),
        ], row_count=3)
        recs = recommend_charts(df, profile)
        types = [r.chart_type for r in recs]
        assert ChartType.LINE in types

    def test_categorical_and_multi_numeric_recommends_line(self):
        """Line chart should be recommended for categorical + multi-numeric data."""
        df = pd.DataFrame({
            "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "Electronics": [12500, 13100, 14800, 15200, 16700, 18100],
            "Clothing": [8200, 7800, 9100, 10500, 11200, 12800],
            "Food": [15600, 14200, 16800, 15100, 17300, 16500],
        })
        profile = _build_profile([
            ColumnProfile(name="Month", dtype=ColumnType.CATEGORICAL, unique_count=6),
            ColumnProfile(name="Electronics", dtype=ColumnType.NUMERIC),
            ColumnProfile(name="Clothing", dtype=ColumnType.NUMERIC),
            ColumnProfile(name="Food", dtype=ColumnType.NUMERIC),
        ])
        recs = recommend_charts(df, profile)
        types = [r.chart_type for r in recs]
        assert ChartType.LINE in types
        # Find the line chart with categorical x-axis
        line_recs = [r for r in recs if r.chart_type == ChartType.LINE and r.x_column == "Month"]
        assert len(line_recs) >= 1
        # Should have multi-Y columns
        assert len(line_recs[0].columns) > 2  # x_col + at least 2 y_cols

    def test_sorted_by_score(self, sample_dataframe):
        profile = _build_profile([
            ColumnProfile(name="Category", dtype=ColumnType.CATEGORICAL, unique_count=3),
            ColumnProfile(name="Value1", dtype=ColumnType.NUMERIC),
        ])
        recs = recommend_charts(sample_dataframe, profile)
        scores = [r.score for r in recs]
        assert scores == sorted(scores, reverse=True)


class TestGeneratePlotlyConfig:
    """Tests for Plotly configuration generation."""

    def test_bar_chart_config(self, sample_dataframe):
        rec = ChartRecommendation(
            chart_type=ChartType.BAR,
            title="Test Bar",
            description="Test",
            x_column="Category",
            y_column="Value1",
            columns=["Category", "Value1"],
        )
        config = generate_plotly_config(sample_dataframe, rec)
        assert "data" in config
        assert "layout" in config
        assert len(config["data"]) > 0
        assert config["data"][0]["type"] == "bar"

    def test_scatter_chart_config(self, numeric_only_dataframe):
        rec = ChartRecommendation(
            chart_type=ChartType.SCATTER,
            title="Test Scatter",
            description="Test",
            x_column="X",
            y_column="Y",
            columns=["X", "Y"],
        )
        config = generate_plotly_config(numeric_only_dataframe, rec)
        assert config["data"][0]["type"] == "scatter"
        assert config["data"][0]["mode"] == "markers"

    def test_heatmap_config(self, numeric_only_dataframe):
        rec = ChartRecommendation(
            chart_type=ChartType.HEATMAP,
            title="Correlation",
            description="Test",
            columns=["X", "Y", "Z"],
        )
        config = generate_plotly_config(numeric_only_dataframe, rec)
        assert config["data"][0]["type"] == "heatmap"


class TestBuildChartFromRequest:
    """Tests for user-requested chart generation."""

    def test_basic_request(self, sample_dataframe):
        request = ChartRequest(
            chart_type=ChartType.BAR,
            x_column="Category",
            y_column="Value1",
            columns=["Category", "Value1"],
        )
        response = build_chart_from_request(sample_dataframe, request)
        assert response.chart_type == ChartType.BAR
        assert len(response.plotly_data) > 0

    def test_with_title_override(self, sample_dataframe):
        request = ChartRequest(
            chart_type=ChartType.BAR,
            x_column="Category",
            y_column="Value1",
            columns=["Category", "Value1"],
            title="Custom Title",
        )
        response = build_chart_from_request(sample_dataframe, request)
        assert response.plotly_layout["title"]["text"] == "Custom Title"

    def test_with_axis_labels(self, sample_dataframe):
        request = ChartRequest(
            chart_type=ChartType.BAR,
            x_column="Category",
            y_column="Value1",
            columns=["Category", "Value1"],
            x_label="Categories",
            y_label="Values",
        )
        response = build_chart_from_request(sample_dataframe, request)
        assert response.plotly_layout["xaxis"]["title"]["text"] == "Categories"

    def test_with_aggregation(self, sample_dataframe):
        request = ChartRequest(
            chart_type=ChartType.BAR,
            x_column="Category",
            y_column="Value1",
            columns=["Category", "Value1"],
            aggregation="mean",
        )
        response = build_chart_from_request(sample_dataframe, request)
        assert len(response.plotly_data) > 0
