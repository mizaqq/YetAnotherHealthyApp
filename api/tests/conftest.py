"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def app():
    """Create FastAPI application for testing.

    Returns:
        FastAPI app instance
    """
    return create_app()


@pytest.fixture
def client(app):
    """Create test client.

    Args:
        app: FastAPI application

    Returns:
        Test client for making requests
    """
    return TestClient(app)
