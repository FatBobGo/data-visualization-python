"""Tests for the data transformer service."""

import pandas as pd
import pytest

from dataviz.models.schemas import TransformOperation, TransformRequest
from dataviz.services.data_transformer import apply_transform


@pytest.fixture
def test_df():
    """DataFrame for transform tests."""
    return pd.DataFrame({
        "Name": ["Alice", "Bob", "Carol", None, "Eve"],
        "Age": [25, 30, 28, 35, 22],
        "Score": [92.0, 85.0, None, 68.0, 95.0],
    })


class TestRenameColumn:

    def test_rename_success(self, test_df):
        req = TransformRequest(operation=TransformOperation.RENAME_COLUMN, column="Name", new_name="Student")
        result = apply_transform(test_df, req)
        assert "Student" in result.columns
        assert "Name" not in result.columns

    def test_rename_missing_column(self, test_df):
        req = TransformRequest(operation=TransformOperation.RENAME_COLUMN, column="Missing", new_name="New")
        with pytest.raises(ValueError, match="not found"):
            apply_transform(test_df, req)

    def test_rename_no_new_name(self, test_df):
        req = TransformRequest(operation=TransformOperation.RENAME_COLUMN, column="Name")
        with pytest.raises(ValueError, match="new_name"):
            apply_transform(test_df, req)


class TestChangeType:

    def test_to_numeric(self):
        df = pd.DataFrame({"Value": ["10", "20", "30"]})
        req = TransformRequest(operation=TransformOperation.CHANGE_TYPE, column="Value", target_type="numeric")
        result = apply_transform(df, req)
        assert pd.api.types.is_numeric_dtype(result["Value"])

    def test_to_text(self, test_df):
        req = TransformRequest(operation=TransformOperation.CHANGE_TYPE, column="Age", target_type="text")
        result = apply_transform(test_df, req)
        assert pd.api.types.is_string_dtype(result["Age"])

    def test_unsupported_type(self, test_df):
        req = TransformRequest(operation=TransformOperation.CHANGE_TYPE, column="Age", target_type="boolean")
        with pytest.raises(ValueError, match="Unsupported"):
            apply_transform(test_df, req)


class TestDropColumn:

    def test_drop_success(self, test_df):
        req = TransformRequest(operation=TransformOperation.DROP_COLUMN, column="Score")
        result = apply_transform(test_df, req)
        assert "Score" not in result.columns
        assert len(result.columns) == 2

    def test_drop_missing(self, test_df):
        req = TransformRequest(operation=TransformOperation.DROP_COLUMN, column="Missing")
        with pytest.raises(ValueError, match="not found"):
            apply_transform(test_df, req)


class TestFillNulls:

    def test_fill_numeric(self, test_df):
        req = TransformRequest(operation=TransformOperation.FILL_NULLS, column="Score", fill_value="0")
        result = apply_transform(test_df, req)
        assert result["Score"].isna().sum() == 0

    def test_fill_string(self, test_df):
        req = TransformRequest(operation=TransformOperation.FILL_NULLS, column="Name", fill_value="Unknown")
        result = apply_transform(test_df, req)
        assert result["Name"].isna().sum() == 0
        assert "Unknown" in result["Name"].values


class TestDropNulls:

    def test_drop_from_column(self, test_df):
        req = TransformRequest(operation=TransformOperation.DROP_NULLS, column="Name")
        result = apply_transform(test_df, req)
        assert len(result) == 4

    def test_drop_any(self, test_df):
        req = TransformRequest(operation=TransformOperation.DROP_NULLS)
        result = apply_transform(test_df, req)
        assert len(result) == 3  # rows with any null removed


class TestSort:

    def test_sort_ascending(self, test_df):
        req = TransformRequest(operation=TransformOperation.SORT, column="Age", sort_ascending=True)
        result = apply_transform(test_df, req)
        assert result["Age"].tolist() == sorted(result["Age"].tolist())

    def test_sort_descending(self, test_df):
        req = TransformRequest(operation=TransformOperation.SORT, column="Age", sort_ascending=False)
        result = apply_transform(test_df, req)
        assert result["Age"].tolist() == sorted(result["Age"].tolist(), reverse=True)


class TestFilter:

    def test_filter_expression(self, test_df):
        req = TransformRequest(operation=TransformOperation.FILTER, filter_condition="Age > 25")
        result = apply_transform(test_df, req)
        assert all(result["Age"] > 25)

    def test_invalid_filter(self, test_df):
        req = TransformRequest(operation=TransformOperation.FILTER, filter_condition="INVALID EXPR !!!")
        with pytest.raises(ValueError, match="Invalid filter"):
            apply_transform(test_df, req)


class TestOriginalUnmutated:
    """Ensure transforms don't mutate the original DataFrame."""

    def test_no_mutation(self, test_df):
        original_cols = list(test_df.columns)
        req = TransformRequest(operation=TransformOperation.DROP_COLUMN, column="Score")
        apply_transform(test_df, req)
        assert list(test_df.columns) == original_cols
