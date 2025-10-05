"""Tests for main application and health endpoint."""

import json
from pathlib import Path

from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint.

    Args:
        client: Test client fixture
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_openapi_schema(client: TestClient) -> None:
    """Test OpenAPI schema is accessible and complete.

    Args:
        client: Test client fixture
    """
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    # Validate basic OpenAPI structure
    assert schema["openapi"] == "3.1.0"
    assert schema["info"]["title"] == "Calorie Intake Logger API"
    assert schema["info"]["version"] == "0.1.0"
    assert "description" in schema["info"]
    assert "contact" in schema["info"]
    assert "license" in schema["info"]

    # Validate paths exist
    assert "paths" in schema
    assert "/api/v1/parse" in schema["paths"]
    assert "/api/v1/match" in schema["paths"]
    assert "/api/v1/log" in schema["paths"]
    assert "/api/v1/summary" in schema["paths"]
    assert "/api/v1/foods/search" in schema["paths"]
    assert "/health" in schema["paths"]

    # Validate tags metadata
    assert "tags" in schema
    tag_names = {tag["name"] for tag in schema["tags"]}
    assert tag_names == {"parse", "match", "log", "summary", "foods", "health"}

    # Validate components/schemas exist
    assert "components" in schema
    assert "schemas" in schema["components"]


def test_openapi_schema_in_sync(client: TestClient) -> None:
    """Test that docs/openapi.json is in sync with the application schema.

    This ensures that 'make openapi' has been run after any schema changes.

    Args:
        client: Test client fixture
    """
    # Get the current schema from the running app
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    current_schema = response.json()

    # Load the exported schema file
    exported_schema_path = Path(__file__).parent.parent.parent / "docs" / "openapi.json"

    if not exported_schema_path.exists():
        # If the file doesn't exist, this is a CI failure
        # Developer should run: make openapi
        raise AssertionError("docs/openapi.json not found. Run 'make openapi' to generate it.")

    with open(exported_schema_path, encoding="utf-8") as f:
        exported_schema = json.load(f)

    # Compare the schemas
    # Note: We compare the JSON representations to ensure they're identical
    assert current_schema == exported_schema, (
        "OpenAPI schema is out of sync. Run 'make openapi' to update docs/openapi.json"
    )
