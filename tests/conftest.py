"""Shared test fixtures for DataViz tests."""

import pandas as pd
import pytest


@pytest.fixture
def sample_csv_with_header() -> str:
    """CSV text with a header row."""
    return (
        "Name,Age,Score,Grade\n"
        "Alice,25,92,A\n"
        "Bob,30,85,B\n"
        "Carol,28,91,A\n"
        "David,35,68,C\n"
        "Eve,22,95,A\n"
    )


@pytest.fixture
def sample_csv_without_header() -> str:
    """CSV text without a header row (all numeric-ish)."""
    return (
        "1,100,200\n"
        "2,150,180\n"
        "3,120,220\n"
        "4,180,190\n"
        "5,160,210\n"
    )


@pytest.fixture
def sample_tsv_data() -> str:
    """Tab-delimited data with header."""
    return (
        "City\tPopulation\tArea\n"
        "New York\t8336817\t783.8\n"
        "Los Angeles\t3979576\t1213.9\n"
        "Chicago\t2693976\t589.0\n"
    )


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Pre-built DataFrame for chart engine tests."""
    return pd.DataFrame({
        "Category": ["A", "B", "C", "A", "B", "C"],
        "Value1": [10, 20, 30, 15, 25, 35],
        "Value2": [100, 200, 300, 150, 250, 350],
        "Date": pd.to_datetime([
            "2024-01-01", "2024-01-02", "2024-01-03",
            "2024-01-04", "2024-01-05", "2024-01-06",
        ]),
    })


@pytest.fixture
def numeric_only_dataframe() -> pd.DataFrame:
    """DataFrame with only numeric columns."""
    return pd.DataFrame({
        "X": [1, 2, 3, 4, 5],
        "Y": [10, 20, 15, 25, 30],
        "Z": [100, 80, 90, 110, 95],
    })
