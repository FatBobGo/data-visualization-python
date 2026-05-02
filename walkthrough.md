# DataViz — Implementation Walkthrough

## Summary

Built a complete **FastAPI + Plotly.js** data visualization web app that lets users upload CSV data (or paste text) and instantly generates interactive charts with smart recommendations. Designed as a fast alternative to Excel charting.

## What Was Built

### Backend (Python/FastAPI)

| Component | File | Purpose |
|-----------|------|---------|
| Config | [config.py](file:///Users/bob/dev/github/data-visualization-python/src/dataviz/config.py) | `pydantic-settings` with `.env` overrides |
| Logger | [logger.py](file:///Users/bob/dev/github/data-visualization-python/src/dataviz/logger.py) | Console + rotating file (10MB, 5 backups) |
| App Factory | [app.py](file:///Users/bob/dev/github/data-visualization-python/src/dataviz/app.py) | FastAPI with CORS, static files, lifespan |
| Schemas | [schemas.py](file:///Users/bob/dev/github/data-visualization-python/src/dataviz/models/schemas.py) | 15+ Pydantic models for API types |
| Data Parser | [data_parser.py](file:///Users/bob/dev/github/data-visualization-python/src/dataviz/services/data_parser.py) | Auto-detect headers, delimiters, column types |
| Chart Engine | [chart_engine.py](file:///Users/bob/dev/github/data-visualization-python/src/dataviz/services/chart_engine.py) | Smart chart recommendations + Plotly.js configs |
| Transformer | [data_transformer.py](file:///Users/bob/dev/github/data-visualization-python/src/dataviz/services/data_transformer.py) | Rename, convert, sort, filter, null handling |
| API Routes | [api.py](file:///Users/bob/dev/github/data-visualization-python/src/dataviz/routers/api.py) | 6 REST endpoints + in-memory session storage |

### Smart Features

- **Header auto-detection**: Heuristic — if first row is all strings but subsequent rows have numerics → header
- **Delimiter sniffing**: Uses `csv.Sniffer` + frequency analysis fallback (comma, tab, semicolon, pipe)
- **Type inference**: Classifies each column as `numeric`, `categorical`, `datetime`, or `text`
- **Chart recommendations**: Scored rules engine (e.g., 1 cat + 1 num → bar chart @ 0.95, 2 num → scatter @ 0.9)
- **10 chart types**: Bar, Line, Scatter, Pie, Histogram, Box, Area, Heatmap, Grouped Bar, Stacked Bar

### Frontend

- **Premium dark-mode UI** with glassmorphism panels and gradient backgrounds
- **Drag & drop** file upload with animated border
- **3 data input modes**: File upload, text paste, sample datasets
- **Data preview table** with column type badges (color-coded)
- **Chart gallery** with thumbnail previews (click to expand)
- **Chart workspace** with full control panel (chart type, columns, labels, colors, aggregation)
- **Interactive Plotly charts** with zoom, pan, hover tooltips, PNG export

### Infrastructure

- **Dockerfile**: Multi-stage (builder → runtime), non-root user, precompiled bytecode
- **README**: Installation, usage, Docker, API docs
- **`.env.example`**: All config vars documented

## Testing Results

```
69 tests passed ✅ (0.29s)
```

| Test File | Tests | Coverage |
|-----------|-------|----------|
| test_data_parser.py | 18 | Delimiters, headers, types, parsing, edge cases |
| test_chart_engine.py | 11 | Recommendations, Plotly config, user requests |
| test_data_transformer.py | 14 | Rename, convert, drop, nulls, sort, filter |
| test_api.py | 10 | Upload, paste, chart gen, transform, pages |

## How to Run

```bash
# Install
uv sync

# Dev server
uv run uvicorn dataviz.app:app --reload

# Tests
uv run pytest tests/ -v
```

Open [http://localhost:8000](http://localhost:8000) → try "Sales Data" sample → click a chart → customize with controls.

## Changes Made

```diff:pyproject.toml
[project]
name = "dataviz"
version = "0.1.0"
description = "Data Visualization Web App - Upload CSV data and generate interactive charts"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.136.1",
    "jinja2>=3.1.6",
    "pandas>=3.0.2",
    "pydantic-settings>=2.14.0",
    "python-dotenv>=1.2.2",
    "python-multipart>=0.0.27",
    "uvicorn>=0.46.0",
]

[dependency-groups]
dev = [
    "httpx>=0.28.1",
    "pytest>=9.0.3",
    "pytest-asyncio>=1.3.0",
]
===
[project]
name = "dataviz"
version = "0.1.0"
description = "Data Visualization Web App - Upload CSV data and generate interactive charts"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.136.1",
    "jinja2>=3.1.6",
    "pandas>=3.0.2",
    "pydantic-settings>=2.14.0",
    "python-dotenv>=1.2.2",
    "python-multipart>=0.0.27",
    "uvicorn>=0.46.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/dataviz"]

[dependency-groups]
dev = [
    "httpx>=0.28.1",
    "pytest>=9.0.3",
    "pytest-asyncio>=1.3.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```
