"""Integration tests for the API endpoints."""

import pytest
from fastapi.testclient import TestClient

from dataviz.app import app


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_csv_content():
    """CSV content bytes for upload tests."""
    return (
        "Name,Age,Score,Grade\n"
        "Alice,25,92,A\n"
        "Bob,30,85,B\n"
        "Carol,28,91,A\n"
    ).encode("utf-8")


class TestSampleData:

    def test_list_samples(self, client):
        response = client.get("/api/sample-data")
        assert response.status_code == 200
        samples = response.json()
        assert len(samples) >= 3
        assert all("id" in s and "name" in s for s in samples)

    def test_load_sample(self, client):
        response = client.post("/api/sample-data/sales")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "profile" in data
        assert "recommendations" in data
        assert data["profile"]["row_count"] > 0

    def test_load_invalid_sample(self, client):
        response = client.post("/api/sample-data/nonexistent")
        assert response.status_code == 404


class TestUpload:

    def test_upload_csv(self, client, sample_csv_content):
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", sample_csv_content, "text/csv")},
            data={"has_header": "true"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["profile"]["row_count"] == 3
        assert len(data["profile"]["columns"]) == 4
        assert len(data["recommendations"]) > 0

    def test_upload_invalid_extension(self, client):
        response = client.post(
            "/api/upload",
            files={"file": ("test.json", b'{"key": "value"}', "application/json")},
        )
        assert response.status_code == 400

    def test_upload_auto_header(self, client, sample_csv_content):
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", sample_csv_content, "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["profile"]["has_header"] is True


class TestPaste:

    def test_paste_data(self, client):
        response = client.post(
            "/api/paste",
            data={"text": "Name,Age\nAlice,25\nBob,30"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["profile"]["row_count"] == 2

    def test_paste_empty(self, client):
        response = client.post(
            "/api/paste",
            data={"text": "   "},
        )
        assert response.status_code == 400


class TestChartGeneration:

    def test_generate_chart(self, client):
        # First load sample data
        resp = client.post("/api/sample-data/sales")
        session_id = resp.json()["session_id"]

        response = client.post(
            "/api/chart",
            data={
                "session_id": session_id,
                "chart_type": "bar",
                "x_column": "Month",
                "y_column": "Electronics",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chart_type"] == "bar"
        assert len(data["plotly_data"]) > 0

    def test_chart_invalid_session(self, client):
        response = client.post(
            "/api/chart",
            data={
                "session_id": "nonexistent",
                "chart_type": "bar",
            },
        )
        assert response.status_code == 404


class TestTransform:

    def test_rename_column(self, client):
        resp = client.post("/api/sample-data/students")
        session_id = resp.json()["session_id"]

        response = client.post(
            "/api/transform",
            data={
                "session_id": session_id,
                "operation": "rename_column",
                "column": "Name",
                "new_name": "Student",
            },
        )
        assert response.status_code == 200
        data = response.json()
        col_names = [c["name"] for c in data["profile"]["columns"]]
        assert "Student" in col_names
        assert "Name" not in col_names


class TestBatchRename:

    def test_batch_rename_success(self, client):
        """Batch rename all columns at once."""
        resp = client.post("/api/sample-data/students")
        session_id = resp.json()["session_id"]

        response = client.post(
            "/api/batch-rename",
            data={
                "session_id": session_id,
                "headers": "Student,Mathematics,Science,English,Letter",
            },
        )
        assert response.status_code == 200
        data = response.json()
        col_names = [c["name"] for c in data["profile"]["columns"]]
        assert col_names == ["Student", "Mathematics", "Science", "English", "Letter"]

    def test_batch_rename_count_mismatch(self, client):
        """Should fail when header count doesn't match column count."""
        resp = client.post("/api/sample-data/students")
        session_id = resp.json()["session_id"]

        response = client.post(
            "/api/batch-rename",
            data={
                "session_id": session_id,
                "headers": "A,B,C",
            },
        )
        assert response.status_code == 400
        assert "Expected" in response.json()["detail"]

    def test_batch_rename_empty_name(self, client):
        """Should fail when any column name is empty."""
        resp = client.post("/api/sample-data/students")
        session_id = resp.json()["session_id"]

        response = client.post(
            "/api/batch-rename",
            data={
                "session_id": session_id,
                "headers": "A,,C,D,E",
            },
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_batch_rename_duplicate_names(self, client):
        """Should fail when column names are not unique."""
        resp = client.post("/api/sample-data/students")
        session_id = resp.json()["session_id"]

        response = client.post(
            "/api/batch-rename",
            data={
                "session_id": session_id,
                "headers": "A,B,A,D,E",
            },
        )
        assert response.status_code == 400
        assert "unique" in response.json()["detail"].lower()

    def test_batch_rename_invalid_session(self, client):
        """Should fail with 404 for invalid session."""
        response = client.post(
            "/api/batch-rename",
            data={
                "session_id": "nonexistent",
                "headers": "A,B,C",
            },
        )
        assert response.status_code == 404


class TestPageRoutes:

    def test_index_page(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "DataViz" in response.text
