"""REST API routes for data upload, chart generation, and transformation."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from dataviz.config import get_settings
from dataviz.logger import get_logger
from dataviz.models.schemas import (
    ChartRequest,
    ChartResponse,
    ChartType,
    TransformRequest,
    UploadResponse,
)
from dataviz.services.chart_engine import build_chart_from_request, recommend_charts
from dataviz.services.data_parser import parse_csv_file, parse_csv_text
from dataviz.services.data_transformer import apply_transform

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["api"])

# In-memory session storage for parsed data
# Key: session_id, Value: {"df": DataFrame, "profile": DataProfile}
_sessions: dict[str, dict[str, Any]] = {}

# Built-in sample datasets for quick demo
_SAMPLE_DATASETS = {
    "sales": {
        "name": "Sales Data",
        "description": "Monthly sales by product category",
        "data": (
            "Month,Electronics,Clothing,Food,Books\n"
            "Jan,12500,8200,15600,3200\nFeb,13100,7800,14200,3500\n"
            "Mar,14800,9100,16800,3100\nApr,15200,10500,15100,4200\n"
            "May,16700,11200,17300,3800\nJun,18100,12800,16500,4500\n"
            "Jul,17500,13500,18200,4100\nAug,19200,12100,17800,3900\n"
            "Sep,16800,10800,16100,4300\nOct,18500,11500,19200,4700\n"
            "Nov,21200,15200,22100,5800\nDec,24500,18500,25600,6200\n"
        ),
    },
    "students": {
        "name": "Student Performance",
        "description": "Student grades across subjects",
        "data": (
            "Name,Math,Science,English,Grade\n"
            "Alice,92,88,95,A\nBob,78,85,72,B\nCarol,95,92,89,A\n"
            "David,65,70,68,C\nEve,88,91,85,B\nFrank,72,68,75,C\n"
            "Grace,98,96,92,A\nHenry,82,79,88,B\nIvy,90,94,91,A\n"
            "Jack,55,60,58,D\nKate,87,83,90,B\nLiam,76,82,71,B\n"
        ),
    },
    "weather": {
        "name": "Weather Data",
        "description": "Daily temperature and rainfall",
        "data": (
            "Date,Temperature_C,Humidity_%,Rainfall_mm,Wind_Speed_kmh\n"
            "2024-01-01,5.2,78,12.5,15\n2024-01-02,3.8,82,8.2,22\n"
            "2024-01-03,6.1,71,0,10\n2024-01-04,7.5,65,0,8\n"
            "2024-01-05,4.2,88,25.1,30\n2024-01-06,2.1,91,18.7,28\n"
            "2024-01-07,1.5,85,5.3,18\n2024-01-08,3.9,79,0,12\n"
            "2024-01-09,8.2,62,0,6\n2024-01-10,9.5,58,0,5\n"
            "2024-01-11,7.8,70,3.2,14\n2024-01-12,5.1,76,10.8,20\n"
            "2024-01-13,4.3,80,15.4,25\n2024-01-14,6.7,68,0,9\n"
        ),
    },
}


def _store_session(df, profile) -> str:
    """Store parsed data in session and return session ID."""
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {"df": df, "profile": profile}
    # Limit stored sessions to prevent memory leaks
    if len(_sessions) > 100:
        oldest = next(iter(_sessions))
        del _sessions[oldest]
        logger.warning("Evicted oldest session %s (limit reached)", oldest)
    return session_id


def _get_session(session_id: str) -> dict[str, Any]:
    """Retrieve session data or raise 404."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please re-upload your data.")
    return _sessions[session_id]


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    has_header: str | None = Form(None),
):
    """Upload a CSV file for parsing and chart recommendation."""
    settings = get_settings()

    # Validate file extension
    if file.filename:
        ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in settings.allowed_extensions_list:
            raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed. Use: {settings.allowed_extensions}")

    # Read file content
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.max_upload_size_mb}MB limit")

    # Parse header override
    header_override = None
    if has_header == "true":
        header_override = True
    elif has_header == "false":
        header_override = False

    try:
        df, profile = parse_csv_file(content, file.filename or "upload.csv", has_header=header_override)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    session_id = _store_session(df, profile)
    recommendations = recommend_charts(df, profile)
    logger.info("File uploaded: %s -> session %s", file.filename, session_id)

    return UploadResponse(session_id=session_id, profile=profile, recommendations=recommendations)


@router.post("/paste", response_model=UploadResponse)
async def paste_data(
    text: str = Form(...),
    has_header: str | None = Form(None),
):
    """Parse pasted text data for chart recommendation."""
    if not text.strip():
        raise HTTPException(status_code=400, detail="No data provided")

    header_override = None
    if has_header == "true":
        header_override = True
    elif has_header == "false":
        header_override = False

    try:
        df, profile = parse_csv_text(text, has_header=header_override)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    session_id = _store_session(df, profile)
    recommendations = recommend_charts(df, profile)
    logger.info("Text pasted -> session %s (%d rows)", session_id, len(df))

    return UploadResponse(session_id=session_id, profile=profile, recommendations=recommendations)


@router.post("/chart", response_model=ChartResponse)
async def generate_chart(
    session_id: str = Form(...),
    chart_type: str = Form(...),
    x_column: str | None = Form(None),
    y_column: str | None = Form(None),
    columns: str | None = Form(None),
    title: str | None = Form(None),
    x_label: str | None = Form(None),
    y_label: str | None = Form(None),
    color_scheme: str | None = Form(None),
    aggregation: str | None = Form(None),
):
    """Generate a specific chart from user selections."""
    session = _get_session(session_id)
    df = session["df"]

    cols = [c.strip() for c in columns.split(",") if c.strip()] if columns else []
    request = ChartRequest(
        chart_type=ChartType(chart_type),
        x_column=x_column,
        y_column=y_column,
        columns=cols,
        title=title,
        x_label=x_label,
        y_label=y_label,
        color_scheme=color_scheme,
        aggregation=aggregation,
    )

    try:
        return build_chart_from_request(df, request)
    except Exception as exc:
        logger.error("Chart generation failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/transform")
async def transform_data(
    session_id: str = Form(...),
    operation: str = Form(...),
    column: str | None = Form(None),
    new_name: str | None = Form(None),
    target_type: str | None = Form(None),
    fill_value: str | None = Form(None),
    sort_ascending: bool = Form(True),
    filter_condition: str | None = Form(None),
):
    """Apply a data transformation and return updated profile + charts."""
    session = _get_session(session_id)
    df = session["df"]

    request = TransformRequest(
        operation=operation,
        column=column,
        new_name=new_name,
        target_type=target_type,
        fill_value=fill_value,
        sort_ascending=sort_ascending,
        filter_condition=filter_condition,
    )

    try:
        new_df = apply_transform(df, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Re-parse profile from transformed data
    from dataviz.services.data_parser import parse_csv_text
    csv_text = new_df.to_csv(index=False)
    _, new_profile = parse_csv_text(csv_text, has_header=True)

    # Update session
    _sessions[session_id] = {"df": new_df, "profile": new_profile}
    recommendations = recommend_charts(new_df, new_profile)

    return UploadResponse(session_id=session_id, profile=new_profile, recommendations=recommendations)


@router.get("/sample-data")
async def list_sample_data():
    """List available sample datasets."""
    return [
        {"id": k, "name": v["name"], "description": v["description"]}
        for k, v in _SAMPLE_DATASETS.items()
    ]


@router.post("/sample-data/{dataset_id}", response_model=UploadResponse)
async def load_sample_data(dataset_id: str):
    """Load a built-in sample dataset."""
    if dataset_id not in _SAMPLE_DATASETS:
        raise HTTPException(status_code=404, detail=f"Sample dataset '{dataset_id}' not found")

    text = _SAMPLE_DATASETS[dataset_id]["data"]
    df, profile = parse_csv_text(text, has_header=True)
    session_id = _store_session(df, profile)
    recommendations = recommend_charts(df, profile)
    logger.info("Loaded sample dataset: %s -> session %s", dataset_id, session_id)

    return UploadResponse(session_id=session_id, profile=profile, recommendations=recommendations)
