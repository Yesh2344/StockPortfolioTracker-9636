"""
Integration tests for the Flask API using the test client.
"""

import json
import pytest
from app import app


@pytest.fixture
def client():
    """Flask test client fixture."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_portfolio_success(client, monkeypatch):
    """Test successful portfolio calculation with mocked API calls."""

    # Mock utils.fetch_latest_price to avoid real network calls
    def mock_fetch_latest_price(symbol):
        return {"AAPL": 150.0, "MSFT": 250.0}.get(symbol, 100.0)

    monkeypatch.setattr("utils.fetch_latest_price", mock_fetch_latest_price)

    holdings = [{"symbol": "AAPL", "shares": 2}, {"symbol": "MSFT", "shares": 1}]
    response = client.get(
        "/api/portfolio",
        query_string={"holdings": json.dumps(holdings)},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "portfolio" in data
    assert data["total_value"] == pytest.approx(150.0 * 2 + 250.0 * 1, 0.01)
    for entry in data["portfolio"]:
        assert entry["price"] is not None
        assert entry["value"] is not None


def test_portfolio_missing_param(client):
    """Ensure a 400 error when the holdings parameter is absent."""
    response = client.get("/api/portfolio")
    assert response.status_code == 400
    assert response.get_json()["error"] == "Missing 'holdings' query parameter."