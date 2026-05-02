"""Pydantic models for API request/response schemas."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# --- Enums ---

class ColumnType(str, Enum):
    """Detected data type for a column."""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    TEXT = "text"


class ChartType(str, Enum):
    """Supported chart types."""
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    PIE = "pie"
    HISTOGRAM = "histogram"
    BOX = "box"
    HEATMAP = "heatmap"
    AREA = "area"
    GROUPED_BAR = "grouped_bar"
    STACKED_BAR = "stacked_bar"


# --- Column & Data Profile ---

class ColumnProfile(BaseModel):
    """Profile information for a single column."""
    name: str
    dtype: ColumnType
    sample_values: list[Any] = Field(default_factory=list)
    unique_count: int = 0
    null_count: int = 0
    # Numeric stats (optional)
    min_val: float | None = None
    max_val: float | None = None
    mean_val: float | None = None
    median_val: float | None = None


class DataProfile(BaseModel):
    """Full profile of a parsed dataset."""
    columns: list[ColumnProfile]
    row_count: int
    has_header: bool
    delimiter: str
    preview_rows: list[dict[str, Any]] = Field(default_factory=list)


# --- Chart ---

class ChartRecommendation(BaseModel):
    """A recommended chart with its Plotly configuration."""
    chart_type: ChartType
    title: str
    description: str
    x_column: str | None = None
    y_column: str | None = None
    columns: list[str] = Field(default_factory=list)
    plotly_config: dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0  # Relevance score for sorting


class ChartRequest(BaseModel):
    """Request to generate a specific chart."""
    chart_type: ChartType
    x_column: str | None = None
    y_column: str | None = None
    columns: list[str] = Field(default_factory=list)
    title: str | None = None
    x_label: str | None = None
    y_label: str | None = None
    color_scheme: str | None = None
    aggregation: str | None = None  # sum, mean, count, etc.


class ChartResponse(BaseModel):
    """Response containing Plotly chart configuration."""
    chart_type: ChartType
    plotly_data: list[dict[str, Any]]
    plotly_layout: dict[str, Any]


# --- Data Transform ---

class TransformOperation(str, Enum):
    """Available data transformation operations."""
    RENAME_COLUMN = "rename_column"
    CHANGE_TYPE = "change_type"
    DROP_COLUMN = "drop_column"
    FILL_NULLS = "fill_nulls"
    DROP_NULLS = "drop_nulls"
    SORT = "sort"
    FILTER = "filter"


class TransformRequest(BaseModel):
    """Request to apply a data transformation."""
    operation: TransformOperation
    column: str | None = None
    new_name: str | None = None
    target_type: str | None = None
    fill_value: str | None = None
    sort_ascending: bool = True
    filter_condition: str | None = None


# --- API Responses ---

class UploadResponse(BaseModel):
    """Response after uploading/pasting data."""
    session_id: str
    profile: DataProfile
    recommendations: list[ChartRecommendation]


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: str | None = None
