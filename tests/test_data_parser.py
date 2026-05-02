"""Tests for the data parser service."""

import pytest

from dataviz.services.data_parser import (
    detect_delimiter,
    detect_header,
    infer_column_type,
    parse_csv_text,
    parse_csv_file,
)
from dataviz.models.schemas import ColumnType
import pandas as pd


class TestDetectDelimiter:
    """Tests for delimiter detection."""

    def test_comma_delimiter(self):
        text = "a,b,c\n1,2,3\n4,5,6"
        assert detect_delimiter(text) == ","

    def test_tab_delimiter(self):
        text = "a\tb\tc\n1\t2\t3\n4\t5\t6"
        assert detect_delimiter(text) == "\t"

    def test_semicolon_delimiter(self):
        text = "a;b;c\n1;2;3\n4;5;6"
        assert detect_delimiter(text) == ";"

    def test_pipe_delimiter(self):
        text = "a|b|c\n1|2|3\n4|5|6"
        assert detect_delimiter(text) == "|"

    def test_fallback_to_comma(self):
        text = "single_value"
        assert detect_delimiter(text) == ","


class TestDetectHeader:
    """Tests for header detection."""

    def test_detects_header_row(self):
        df = pd.DataFrame([
            ["Name", "Age", "Score"],
            ["Alice", "25", "92"],
            ["Bob", "30", "85"],
        ])
        assert detect_header(df) is True

    def test_no_header_all_numeric(self):
        df = pd.DataFrame([
            ["1", "100", "200"],
            ["2", "150", "180"],
            ["3", "120", "220"],
        ])
        assert detect_header(df) is False

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        assert detect_header(df) is False

    def test_single_row(self):
        df = pd.DataFrame([["Name", "Age"]])
        assert detect_header(df) is False


class TestInferColumnType:
    """Tests for column type inference."""

    def test_numeric_integers(self):
        series = pd.Series([1, 2, 3, 4, 5])
        assert infer_column_type(series) == ColumnType.NUMERIC

    def test_numeric_floats(self):
        series = pd.Series([1.5, 2.3, 3.7])
        assert infer_column_type(series) == ColumnType.NUMERIC

    def test_numeric_strings(self):
        series = pd.Series(["100", "200", "300"])
        assert infer_column_type(series) == ColumnType.NUMERIC

    def test_categorical(self):
        series = pd.Series(["A", "B", "A", "C", "B", "A"])
        assert infer_column_type(series) == ColumnType.CATEGORICAL

    def test_datetime(self):
        series = pd.Series(["2024-01-01", "2024-01-02", "2024-01-03"])
        assert infer_column_type(series) == ColumnType.DATETIME

    def test_text_high_cardinality(self):
        series = pd.Series([f"unique_text_{i}" for i in range(50)])
        assert infer_column_type(series) == ColumnType.TEXT

    def test_empty_series(self):
        series = pd.Series([None, None, None])
        assert infer_column_type(series) == ColumnType.TEXT


class TestParseCsvText:
    """Tests for CSV text parsing."""

    def test_parse_with_header(self, sample_csv_with_header):
        df, profile = parse_csv_text(sample_csv_with_header, has_header=True)
        assert len(df) == 5
        assert "Name" in df.columns
        assert profile.has_header is True
        assert profile.row_count == 5

    def test_parse_without_header(self, sample_csv_without_header):
        df, profile = parse_csv_text(sample_csv_without_header, has_header=False)
        assert len(df) == 5
        assert "Column_1" in df.columns
        assert profile.has_header is False

    def test_auto_detect_header(self, sample_csv_with_header):
        df, profile = parse_csv_text(sample_csv_with_header)
        assert profile.has_header is True
        assert "Name" in df.columns

    def test_auto_detect_no_header(self, sample_csv_without_header):
        df, profile = parse_csv_text(sample_csv_without_header)
        assert profile.has_header is False

    def test_column_profiling(self, sample_csv_with_header):
        df, profile = parse_csv_text(sample_csv_with_header)
        col_names = [c.name for c in profile.columns]
        assert "Name" in col_names
        assert "Age" in col_names

        # Find numeric column profile
        age_col = next(c for c in profile.columns if c.name == "Age")
        assert age_col.dtype == ColumnType.NUMERIC
        assert age_col.null_count == 0

    def test_preview_rows(self, sample_csv_with_header):
        df, profile = parse_csv_text(sample_csv_with_header)
        assert len(profile.preview_rows) == 5
        assert profile.preview_rows[0]["Name"] == "Alice"

    def test_empty_data_raises(self):
        with pytest.raises(ValueError, match="Empty data"):
            parse_csv_text("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="Empty data"):
            parse_csv_text("   \n  \n  ")

    def test_tab_delimiter_data(self, sample_tsv_data):
        df, profile = parse_csv_text(sample_tsv_data)
        assert profile.delimiter == "\t"
        assert "City" in df.columns
        assert len(df) == 3


class TestParseCsvFile:
    """Tests for CSV file parsing."""

    def test_parse_utf8_file(self, sample_csv_with_header):
        content = sample_csv_with_header.encode("utf-8")
        df, profile = parse_csv_file(content, "test.csv")
        assert len(df) == 5
        assert profile.has_header is True

    def test_parse_latin1_file(self):
        text = "Name,City\nAlice,São Paulo\nBob,Zürich"
        content = text.encode("latin-1")
        df, profile = parse_csv_file(content, "test.csv", has_header=True)
        assert len(df) == 2

    def test_tsv_extension(self, sample_tsv_data):
        content = sample_tsv_data.encode("utf-8")
        df, profile = parse_csv_file(content, "data.tsv")
        assert profile.delimiter == "\t"
