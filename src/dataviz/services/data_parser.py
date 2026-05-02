"""Data parsing service.

Handles CSV file and raw text parsing with automatic header detection,
delimiter inference, and column type classification.
"""

from __future__ import annotations

import csv
import io
from typing import Any

import pandas as pd

from dataviz.logger import get_logger
from dataviz.models.schemas import ColumnProfile, ColumnType, DataProfile

logger = get_logger(__name__)

# Maximum preview rows returned to the frontend
_PREVIEW_ROWS = 50
# Sample size for type inference heuristics
_SAMPLE_SIZE = 100


def detect_delimiter(text: str) -> str:
    """Detect the most likely delimiter in a text block.

    Uses Python's csv.Sniffer first, then falls back to frequency analysis.

    Args:
        text: Raw text content to analyze.

    Returns:
        Single character delimiter string.
    """
    # Try csv.Sniffer on a sample
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        logger.debug("Sniffer detected delimiter: %r", dialect.delimiter)
        return dialect.delimiter
    except csv.Error:
        pass

    # Fallback: count occurrences of common delimiters in the first few lines
    lines = sample.split("\n")[:10]
    candidates = {",": 0, "\t": 0, ";": 0, "|": 0}
    for line in lines:
        for delim in candidates:
            candidates[delim] += line.count(delim)

    best = max(candidates, key=candidates.get)
    if candidates[best] > 0:
        logger.debug("Frequency analysis detected delimiter: %r", best)
        return best

    logger.debug("No delimiter detected, defaulting to comma")
    return ","


def detect_header(df: pd.DataFrame) -> bool:
    """Heuristic to determine if the first row is a header.

    Strategy: If all values in the first row are strings but subsequent
    rows contain numeric or mixed types, the first row is likely a header.

    Args:
        df: DataFrame read WITHOUT header (header=None).

    Returns:
        True if the first row appears to be a header row.
    """
    if df.empty or len(df) < 2:
        return False

    first_row = df.iloc[0]
    rest = df.iloc[1:]

    # Check if all first-row values are string-like
    all_strings = all(
        isinstance(v, str) and not _is_numeric_string(v)
        for v in first_row
        if pd.notna(v)
    )

    if not all_strings:
        return False

    # Check if subsequent rows contain at least one numeric column
    has_numeric = False
    for col in rest.columns:
        try:
            pd.to_numeric(rest[col], errors="raise")
            has_numeric = True
            break
        except (ValueError, TypeError):
            continue

    return has_numeric


def _is_numeric_string(value: str) -> bool:
    """Check if a string represents a number."""
    try:
        float(value.replace(",", ""))
        return True
    except (ValueError, AttributeError):
        return False


def infer_column_type(series: pd.Series) -> ColumnType:
    """Classify a column's data type.

    Args:
        series: Pandas Series to classify.

    Returns:
        ColumnType enum value.
    """
    # Drop nulls for analysis
    non_null = series.dropna()
    if non_null.empty:
        return ColumnType.TEXT

    # Check if already numeric
    if pd.api.types.is_numeric_dtype(series):
        return ColumnType.NUMERIC

    # Try numeric conversion
    try:
        pd.to_numeric(non_null, errors="raise")
        return ColumnType.NUMERIC
    except (ValueError, TypeError):
        pass

    # Try datetime conversion
    try:
        pd.to_datetime(non_null, errors="raise", format="mixed")
        return ColumnType.DATETIME
    except (ValueError, TypeError):
        pass

    # Categorical vs text: if unique ratio is low, it's categorical
    unique_ratio = non_null.nunique() / len(non_null) if len(non_null) > 0 else 1.0
    if unique_ratio < 0.5 or non_null.nunique() <= 20:
        return ColumnType.CATEGORICAL

    return ColumnType.TEXT


def build_column_profile(series: pd.Series, col_type: ColumnType) -> ColumnProfile:
    """Build a detailed profile for a single column.

    Args:
        series: The column data.
        col_type: Pre-determined column type.

    Returns:
        ColumnProfile with stats and sample values.
    """
    non_null = series.dropna()
    profile = ColumnProfile(
        name=str(series.name),
        dtype=col_type,
        sample_values=non_null.head(5).tolist(),
        unique_count=int(non_null.nunique()),
        null_count=int(series.isna().sum()),
    )

    if col_type == ColumnType.NUMERIC:
        numeric = pd.to_numeric(non_null, errors="coerce").dropna()
        if not numeric.empty:
            profile.min_val = float(numeric.min())
            profile.max_val = float(numeric.max())
            profile.mean_val = round(float(numeric.mean()), 4)
            profile.median_val = float(numeric.median())

    return profile


def parse_csv_text(
    text: str,
    has_header: bool | None = None,
    delimiter: str | None = None,
) -> tuple[pd.DataFrame, DataProfile]:
    """Parse raw CSV/TSV text into a DataFrame and data profile.

    Args:
        text: Raw text content.
        has_header: Override header detection. None = auto-detect.
        delimiter: Override delimiter. None = auto-detect.

    Returns:
        Tuple of (parsed DataFrame, DataProfile).
    """
    text = text.strip()
    if not text:
        raise ValueError("Empty data provided")

    # Detect delimiter
    if delimiter is None:
        delimiter = detect_delimiter(text)
    logger.info("Using delimiter: %r", delimiter)

    # First pass: read without header to inspect
    df_raw = pd.read_csv(
        io.StringIO(text),
        sep=delimiter,
        header=None,
        dtype=str,
        skip_blank_lines=True,
        on_bad_lines="skip",
    )

    if df_raw.empty:
        raise ValueError("No data could be parsed from input")

    # Detect or apply header setting
    if has_header is None:
        has_header = detect_header(df_raw)
    logger.info("Header detected: %s", has_header)

    # Re-read with proper header setting
    if has_header:
        df = pd.read_csv(
            io.StringIO(text),
            sep=delimiter,
            header=0,
            skip_blank_lines=True,
            on_bad_lines="skip",
        )
    else:
        df = df_raw.copy()
        df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]

    # Convert numeric-looking columns
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col], errors="raise")
        except (ValueError, TypeError):
            pass

    # Build column profiles
    columns: list[ColumnProfile] = []
    for col in df.columns:
        col_type = infer_column_type(df[col])
        profile = build_column_profile(df[col], col_type)
        columns.append(profile)

    # Build preview
    preview_df = df.head(_PREVIEW_ROWS)
    preview_rows = preview_df.where(preview_df.notna(), None).to_dict(orient="records")

    data_profile = DataProfile(
        columns=columns,
        row_count=len(df),
        has_header=has_header,
        delimiter=delimiter,
        preview_rows=preview_rows,
    )

    logger.info(
        "Parsed data: %d rows x %d columns (header=%s)",
        len(df),
        len(df.columns),
        has_header,
    )

    return df, data_profile


def parse_csv_file(
    file_content: bytes,
    filename: str,
    has_header: bool | None = None,
) -> tuple[pd.DataFrame, DataProfile]:
    """Parse an uploaded CSV file.

    Args:
        file_content: Raw file bytes.
        filename: Original filename for extension detection.
        has_header: Override header detection.

    Returns:
        Tuple of (parsed DataFrame, DataProfile).
    """
    # Attempt UTF-8 decode, fallback to latin-1
    try:
        text = file_content.decode("utf-8")
    except UnicodeDecodeError:
        logger.warning("UTF-8 decode failed for %s, trying latin-1", filename)
        text = file_content.decode("latin-1")

    # Use tab delimiter for TSV files
    delimiter = None
    if filename.lower().endswith(".tsv"):
        delimiter = "\t"

    return parse_csv_text(text, has_header=has_header, delimiter=delimiter)
