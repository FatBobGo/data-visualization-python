# ============================================
# DataViz — Multi-stage Production Dockerfile
# ============================================

# --- Stage 1: Builder ---
FROM python:3.12-slim AS builder

LABEL maintainer="dataviz"
LABEL description="DataViz - Interactive Data Visualization Web App"
LABEL version="0.1.0"

WORKDIR /build

# Install uv for dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev deps in production)
RUN uv pip install --system --no-cache-dir -r pyproject.toml

# Copy source code
COPY src/ src/

# Precompile bytecode for faster cold starts
RUN python -m compileall -b src/


# --- Stage 2: Runtime ---
FROM python:3.12-slim AS runtime

LABEL maintainer="dataviz"
LABEL description="DataViz - Interactive Data Visualization Web App"
LABEL version="0.1.0"

# Python optimization flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONOPTIMIZE=2

WORKDIR /app

# Create non-root user for security hardening
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /build/src src/

# Create log directory
RUN mkdir -p logs && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "dataviz.app:app", "--host", "0.0.0.0", "--port", "8000"]
