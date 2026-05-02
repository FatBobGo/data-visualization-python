"""Data transformation service.

Provides column operations like renaming, type conversion, aggregation,
filtering, and null handling on parsed DataFrames.
"""

from __future__ import annotations

import pandas as pd

from dataviz.logger import get_logger
from dataviz.models.schemas import TransformOperation, TransformRequest

logger = get_logger(__name__)


def apply_transform(df: pd.DataFrame, request: TransformRequest) -> pd.DataFrame:
    """Apply a transformation operation to a DataFrame.

    Args:
        df: Source DataFrame (not mutated — returns a copy).
        request: Transformation specification.

    Returns:
        Transformed DataFrame copy.

    Raises:
        ValueError: If the operation or column is invalid.
    """
    result = df.copy()
    op = request.operation

    if op == TransformOperation.RENAME_COLUMN:
        if not request.column or not request.new_name:
            raise ValueError("rename_column requires 'column' and 'new_name'")
        if request.column not in result.columns:
            raise ValueError(f"Column '{request.column}' not found")
        result = result.rename(columns={request.column: request.new_name})
        logger.info("Renamed column '%s' -> '%s'", request.column, request.new_name)

    elif op == TransformOperation.CHANGE_TYPE:
        if not request.column or not request.target_type:
            raise ValueError("change_type requires 'column' and 'target_type'")
        if request.column not in result.columns:
            raise ValueError(f"Column '{request.column}' not found")
        result = _convert_column_type(result, request.column, request.target_type)

    elif op == TransformOperation.DROP_COLUMN:
        if not request.column:
            raise ValueError("drop_column requires 'column'")
        if request.column not in result.columns:
            raise ValueError(f"Column '{request.column}' not found")
        result = result.drop(columns=[request.column])
        logger.info("Dropped column '%s'", request.column)

    elif op == TransformOperation.FILL_NULLS:
        if not request.column:
            raise ValueError("fill_nulls requires 'column'")
        if request.column not in result.columns:
            raise ValueError(f"Column '{request.column}' not found")
        fill_val = request.fill_value if request.fill_value is not None else 0
        # Try numeric fill if column is numeric
        if pd.api.types.is_numeric_dtype(result[request.column]):
            try:
                fill_val = float(fill_val)
            except (ValueError, TypeError):
                pass
        result[request.column] = result[request.column].fillna(fill_val)
        logger.info("Filled nulls in '%s' with '%s'", request.column, fill_val)

    elif op == TransformOperation.DROP_NULLS:
        col = request.column
        if col:
            if col not in result.columns:
                raise ValueError(f"Column '{col}' not found")
            before = len(result)
            result = result.dropna(subset=[col])
            logger.info("Dropped %d null rows from '%s'", before - len(result), col)
        else:
            before = len(result)
            result = result.dropna()
            logger.info("Dropped %d rows with any null", before - len(result))

    elif op == TransformOperation.SORT:
        if not request.column:
            raise ValueError("sort requires 'column'")
        if request.column not in result.columns:
            raise ValueError(f"Column '{request.column}' not found")
        result = result.sort_values(
            by=request.column,
            ascending=request.sort_ascending,
        ).reset_index(drop=True)
        logger.info("Sorted by '%s' (%s)", request.column,
                     "asc" if request.sort_ascending else "desc")

    elif op == TransformOperation.FILTER:
        if not request.filter_condition:
            raise ValueError("filter requires 'filter_condition'")
        try:
            result = result.query(request.filter_condition)
            logger.info("Filtered with condition: %s (%d rows remaining)",
                        request.filter_condition, len(result))
        except Exception as exc:
            raise ValueError(f"Invalid filter condition: {exc}") from exc

    else:
        raise ValueError(f"Unknown operation: {op}")

    return result


def _convert_column_type(
    df: pd.DataFrame,
    column: str,
    target_type: str,
) -> pd.DataFrame:
    """Convert a column to a different data type.

    Args:
        df: DataFrame to modify.
        column: Column name.
        target_type: Target type string ('numeric', 'datetime', 'text').

    Returns:
        DataFrame with converted column.
    """
    if target_type == "numeric":
        df[column] = pd.to_numeric(df[column], errors="coerce")
        logger.info("Converted '%s' to numeric", column)
    elif target_type == "datetime":
        df[column] = pd.to_datetime(df[column], errors="coerce", format="mixed")
        logger.info("Converted '%s' to datetime", column)
    elif target_type == "text":
        df[column] = df[column].astype(str)
        logger.info("Converted '%s' to text", column)
    else:
        raise ValueError(f"Unsupported target type: {target_type}")
    return df
