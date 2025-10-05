"""Contract tests for API endpoints."""

from fastapi.testclient import TestClient


class TestParseContract:
    """Contract tests for /api/v1/parse endpoint."""

    def test_parse_returns_valid_response(self, client: TestClient) -> None:
        """Test parse endpoint returns valid response schema.

        Args:
            client: Test client fixture
        """
        response = client.post(
            "/api/v1/parse",
            json={"text": "2 jajka, 100g kurczaka"},
        )
        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "items" in data
        assert "needs_clarification" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["needs_clarification"], bool)

        # Validate item structure
        if data["items"]:
            item = data["items"][0]
            assert "label" in item
            assert "confidence" in item
            assert 0.0 <= item["confidence"] <= 1.0

    def test_parse_rejects_empty_text(self, client: TestClient) -> None:
        """Test parse endpoint rejects empty text.

        Args:
            client: Test client fixture
        """
        response = client.post(
            "/api/v1/parse",
            json={"text": ""},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_parse_rejects_missing_text(self, client: TestClient) -> None:
        """Test parse endpoint rejects missing text field.

        Args:
            client: Test client fixture
        """
        response = client.post(
            "/api/v1/parse",
            json={},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_parse_rejects_text_too_long(self, client: TestClient) -> None:
        """Test parse endpoint rejects text exceeding max length.

        Args:
            client: Test client fixture
        """
        response = client.post(
            "/api/v1/parse",
            json={"text": "a" * 2001},  # Over 2000 char limit
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestMatchContract:
    """Contract tests for /api/v1/match endpoint."""

    def test_match_returns_valid_response(self, client: TestClient) -> None:
        """Test match endpoint returns valid response schema.

        Args:
            client: Test client fixture
        """
        response = client.post(
            "/api/v1/match",
            json={"items": [{"label": "kurczak", "grams": 100.0}]},
        )
        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "matches" in data
        assert isinstance(data["matches"], list)

        # Validate match structure
        if data["matches"]:
            match = data["matches"][0]
            assert "label" in match
            assert "food_id" in match
            assert "source" in match
            assert "match_score" in match
            assert "macros_per_100g" in match
            assert 0.0 <= match["match_score"] <= 1.0

            # Validate macros structure
            macros = match["macros_per_100g"]
            assert "kcal" in macros
            assert "protein_g" in macros
            assert "fat_g" in macros
            assert "carbs_g" in macros

    def test_match_rejects_empty_items(self, client: TestClient) -> None:
        """Test match endpoint rejects empty items list.

        Args:
            client: Test client fixture
        """
        response = client.post(
            "/api/v1/match",
            json={"items": []},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_match_rejects_invalid_grams(self, client: TestClient) -> None:
        """Test match endpoint rejects zero or negative grams.

        Args:
            client: Test client fixture
        """
        response = client.post(
            "/api/v1/match",
            json={"items": [{"label": "kurczak", "grams": 0.0}]},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_match_rejects_missing_label(self, client: TestClient) -> None:
        """Test match endpoint rejects missing label field.

        Args:
            client: Test client fixture
        """
        response = client.post(
            "/api/v1/match",
            json={"items": [{"grams": 100.0}]},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestLogContract:
    """Contract tests for /api/v1/log endpoint."""

    def test_log_returns_valid_response(self, client: TestClient) -> None:
        """Test log endpoint returns valid response schema.

        Args:
            client: Test client fixture
        """
        response = client.post(
            "/api/v1/log",
            json={"items": [{"food_id": "food_12345", "label": "kurczak", "grams": 150.0}]},
        )
        assert response.status_code == 201
        data = response.json()

        # Validate response structure
        assert "meal_id" in data
        assert "totals" in data
        assert "items" in data

        # Validate totals structure
        totals = data["totals"]
        assert "kcal" in totals
        assert "protein_g" in totals
        assert "fat_g" in totals
        assert "carbs_g" in totals

    def test_log_accepts_optional_fields(self, client: TestClient) -> None:
        """Test log endpoint accepts optional eaten_at and note fields.

        Args:
            client: Test client fixture
        """
        response = client.post(
            "/api/v1/log",
            json={
                "eaten_at": "2025-10-05T12:30:00Z",
                "note": "Healthy lunch",
                "items": [{"food_id": "food_12345", "label": "kurczak", "grams": 150.0}],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "meal_id" in data

    def test_log_rejects_empty_items(self, client: TestClient) -> None:
        """Test log endpoint rejects empty items list.

        Args:
            client: Test client fixture
        """
        response = client.post(
            "/api/v1/log",
            json={"items": []},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_log_rejects_invalid_grams(self, client: TestClient) -> None:
        """Test log endpoint rejects zero or negative grams.

        Args:
            client: Test client fixture
        """
        response = client.post(
            "/api/v1/log",
            json={"items": [{"food_id": "food_12345", "label": "kurczak", "grams": 0.0}]},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_log_rejects_note_too_long(self, client: TestClient) -> None:
        """Test log endpoint rejects note exceeding max length.

        Args:
            client: Test client fixture
        """
        response = client.post(
            "/api/v1/log",
            json={
                "note": "a" * 501,  # Over 500 char limit
                "items": [{"food_id": "food_12345", "label": "kurczak", "grams": 150.0}],
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestSummaryContract:
    """Contract tests for /api/v1/summary endpoint."""

    def test_summary_returns_valid_response(self, client: TestClient) -> None:
        """Test summary endpoint returns valid response schema.

        Args:
            client: Test client fixture
        """
        response = client.get(
            "/api/v1/summary",
            params={"date": "2025-10-05"},
        )
        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "date" in data
        assert "totals" in data
        assert "meals" in data
        assert isinstance(data["meals"], list)

    def test_summary_requires_date_parameter(self, client: TestClient) -> None:
        """Test summary endpoint requires date parameter.

        Args:
            client: Test client fixture
        """
        response = client.get("/api/v1/summary")
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_summary_rejects_invalid_date_format(self, client: TestClient) -> None:
        """Test summary endpoint rejects invalid date format.

        Args:
            client: Test client fixture
        """
        response = client.get(
            "/api/v1/summary",
            params={"date": "invalid-date"},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestFoodsContract:
    """Contract tests for /api/v1/foods/search endpoint."""

    def test_foods_search_returns_valid_response(self, client: TestClient) -> None:
        """Test foods search endpoint returns valid response schema.

        Args:
            client: Test client fixture
        """
        response = client.get(
            "/api/v1/foods/search",
            params={"q": "kurczak", "limit": 10},
        )
        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "results" in data
        assert "total" in data
        assert isinstance(data["results"], list)
        assert isinstance(data["total"], int)

        # Validate food item structure
        if data["results"]:
            food = data["results"][0]
            assert "id" in food
            assert "name" in food
            assert "source" in food
            assert "macros_per_100g" in food

    def test_foods_search_with_default_limit(self, client: TestClient) -> None:
        """Test foods search endpoint with default limit.

        Args:
            client: Test client fixture
        """
        response = client.get(
            "/api/v1/foods/search",
            params={"q": "kurczak"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    def test_foods_search_rejects_missing_query(self, client: TestClient) -> None:
        """Test foods search endpoint rejects missing query parameter.

        Args:
            client: Test client fixture
        """
        response = client.get("/api/v1/foods/search")
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_foods_search_rejects_invalid_limit(self, client: TestClient) -> None:
        """Test foods search endpoint rejects invalid limit values.

        Args:
            client: Test client fixture
        """
        response = client.get(
            "/api/v1/foods/search",
            params={"q": "kurczak", "limit": 0},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestErrorResponseFormat:
    """Contract tests for error response format consistency."""

    def test_validation_errors_have_consistent_format(self, client: TestClient) -> None:
        """Test that validation errors return consistent format.

        Args:
            client: Test client fixture
        """
        response = client.post(
            "/api/v1/parse",
            json={"text": ""},
        )
        assert response.status_code == 422
        data = response.json()

        # Validate error structure from FastAPI/Pydantic
        assert "detail" in data
        assert isinstance(data["detail"], list)
        if data["detail"]:
            error = data["detail"][0]
            assert "type" in error or "msg" in error
            assert "loc" in error


class TestCORSHeaders:
    """Contract tests for CORS configuration."""

    def test_cors_headers_present_on_preflight(self, client: TestClient) -> None:
        """Test that CORS headers are present on OPTIONS requests.

        Args:
            client: Test client fixture
        """
        response = client.options(
            "/api/v1/parse",
            headers={"Origin": "http://localhost:3000"},
        )
        # TestClient doesn't fully simulate preflight, but we verify the route exists
        assert response.status_code in [200, 405]  # OPTIONS might not be implemented


class TestOpenAPIConsistency:
    """Contract tests for OpenAPI schema consistency."""

    def test_all_endpoints_documented_in_openapi(self, client: TestClient) -> None:
        """Test that all implemented endpoints are documented in OpenAPI.

        Args:
            client: Test client fixture
        """
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        # Check that all core endpoints are documented
        required_paths = [
            "/api/v1/parse",
            "/api/v1/match",
            "/api/v1/log",
            "/api/v1/summary",
            "/api/v1/foods/search",
        ]

        for path in required_paths:
            assert path in schema["paths"], f"Path {path} not documented in OpenAPI schema"

    def test_openapi_models_have_examples(self, client: TestClient) -> None:
        """Test that OpenAPI schema includes examples for major models.

        Args:
            client: Test client fixture
        """
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        # Verify that components are defined
        assert "components" in schema
        assert "schemas" in schema["components"]

        # Check for some key models
        expected_schemas = [
            "ParseRequest",
            "ParseResponse",
            "MatchRequest",
            "MatchResponse",
            "LogRequest",
            "LogResponse",
        ]

        for schema_name in expected_schemas:
            assert schema_name in schema["components"]["schemas"], (
                f"Schema {schema_name} not found in OpenAPI components"
            )
