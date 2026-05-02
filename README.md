# DataViz — Interactive Data Visualization

Upload CSV data and instantly generate beautiful interactive charts. A fast alternative to Excel charting.

## Features

- **Drag & drop CSV upload** or paste data directly
- **Auto-detect headers** — works with or without header rows
- **Smart delimiter detection** — CSV, TSV, semicolon, pipe
- **Column type inference** — numeric, categorical, datetime, text
- **Smart chart recommendations** — suggests the best visualizations for your data
- **10 chart types** — Bar, Line, Scatter, Pie, Histogram, Box, Area, Heatmap, Grouped Bar, Stacked Bar
- **Interactive charts** — zoom, pan, hover tooltips, export PNG
- **Chart controls** — change columns, chart type, labels, colors, aggregation
- **Sample datasets** — try the app instantly with built-in data
- **Premium dark-mode UI** — glassmorphism design with smooth animations

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd data-visualization-python

# Install dependencies
uv sync

# Copy environment config
cp .env.example .env
```

### Run Locally

```bash
uv run uvicorn dataviz.app:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Run with Docker

```bash
# Build
docker build -t dataviz .

# Run
docker run -p 8000:8000 dataviz
```

## Testing

```bash
uv run pytest tests/ -v
```

## Architecture

```
src/dataviz/
├── app.py                  # FastAPI application factory
├── config.py               # Settings from .env
├── logger.py               # Console + rotating file logger
├── routers/
│   ├── api.py              # REST API endpoints
│   └── pages.py            # HTML page routes
├── services/
│   ├── data_parser.py      # CSV parsing, header detection, type inference
│   ├── chart_engine.py     # Chart recommendation + Plotly config
│   └── data_transformer.py # Column operations & aggregation
├── models/
│   └── schemas.py          # Pydantic request/response models
├── static/                 # CSS + JavaScript
└── templates/              # Jinja2 HTML templates
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/upload` | Upload CSV file |
| `POST` | `/api/paste` | Parse pasted text |
| `POST` | `/api/chart` | Generate specific chart |
| `POST` | `/api/transform` | Apply data transformation |
| `GET`  | `/api/sample-data` | List sample datasets |
| `POST` | `/api/sample-data/{id}` | Load sample dataset |

## License

MIT
