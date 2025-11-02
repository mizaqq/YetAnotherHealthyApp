from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_application


@pytest.fixture(scope="session")
def app() -> FastAPI:
    """Create a FastAPI application instance for integration tests."""

    return create_application()


@pytest.fixture()
def test_client(app: FastAPI) -> Iterator[TestClient]:
    """Provide a test client for interacting with the API."""

    with TestClient(app) as client:
        yield client
