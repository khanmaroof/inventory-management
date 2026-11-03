"""
Tests for restocking order API endpoints.
"""
from datetime import date, timedelta

import pytest

import main


@pytest.fixture(autouse=True)
def clear_restocking_orders():
    """Reset the in-memory order store so tests don't leak state into each other."""
    main.restocking_orders.clear()
    yield
    main.restocking_orders.clear()


class TestRestockingEndpoints:
    """Test suite for restocking-related endpoints."""

    def test_demand_forecasts_include_cost_and_lead_time(self, client):
        """Test that demand forecasts expose pricing and lead time for restocking."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for forecast in data:
            assert isinstance(forecast["unit_cost"], (int, float))
            assert isinstance(forecast["lead_time_days"], int)
            assert forecast["unit_cost"] > 0
            assert forecast["lead_time_days"] > 0

    def test_get_restocking_orders_empty(self, client):
        """Test that no restocking orders exist before any are submitted."""
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_restocking_order(self, client):
        """Test submitting a restocking order computes totals and lead time."""
        forecasts = {f["item_sku"]: f for f in client.get("/api/demand").json()}
        lines = [{"sku": "WDG-001", "quantity": 10}, {"sku": "MTR-304", "quantity": 2}]

        response = client.post("/api/restocking-orders", json={"budget": 100000, "items": lines})
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"] == "RST-0001"
        assert order["status"] == "Submitted"
        assert len(order["items"]) == 2

        expected_total = sum(l["quantity"] * forecasts[l["sku"]]["unit_cost"] for l in lines)
        assert abs(order["total_cost"] - expected_total) < 0.01

        expected_lead = max(forecasts[l["sku"]]["lead_time_days"] for l in lines)
        assert order["lead_time_days"] == expected_lead
        assert order["submitted_date"] == date.today().isoformat()
        assert order["expected_delivery"] == (date.today() + timedelta(days=expected_lead)).isoformat()

    def test_created_order_appears_in_list(self, client):
        """Test that submitted orders are returned newest first."""
        client.post("/api/restocking-orders", json={"budget": 10000, "items": [{"sku": "GSK-203", "quantity": 5}]})
        client.post("/api/restocking-orders", json={"budget": 10000, "items": [{"sku": "FLT-405", "quantity": 5}]})

        response = client.get("/api/restocking-orders")
        assert response.status_code == 200

        data = response.json()
        assert [o["order_number"] for o in data] == ["RST-0002", "RST-0001"]

    def test_create_restocking_order_over_budget(self, client):
        """Test that an order exceeding the budget is rejected."""
        response = client.post("/api/restocking-orders", json={"budget": 100, "items": [{"sku": "MTR-304", "quantity": 1}]})
        assert response.status_code == 400
        assert "exceeds budget" in response.json()["detail"]
        assert main.restocking_orders == []

    def test_create_restocking_order_unknown_sku(self, client):
        """Test that an unknown SKU returns 404."""
        response = client.post("/api/restocking-orders", json={"budget": 1000, "items": [{"sku": "NOPE-999", "quantity": 1}]})
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        assert main.restocking_orders == []

    def test_create_restocking_order_exact_budget(self, client):
        """Test that an order costing exactly the budget is accepted."""
        # GSK-203 costs 8.20/unit, so 10 units is exactly 82.00
        response = client.post("/api/restocking-orders", json={"budget": 82.0, "items": [{"sku": "GSK-203", "quantity": 10}]})
        assert response.status_code == 201
        assert response.json()["total_cost"] == 82.0

    def test_create_restocking_order_negative_budget(self, client):
        """Test that a negative budget is a validation error."""
        response = client.post("/api/restocking-orders", json={"budget": -1, "items": [{"sku": "WDG-001", "quantity": 1}]})
        assert response.status_code == 422

    def test_create_restocking_order_empty_items(self, client):
        """Test that an order with no items is a validation error."""
        response = client.post("/api/restocking-orders", json={"budget": 1000, "items": []})
        assert response.status_code == 422

    def test_create_restocking_order_zero_quantity(self, client):
        """Test that a non-positive quantity is a validation error."""
        response = client.post("/api/restocking-orders", json={"budget": 1000, "items": [{"sku": "WDG-001", "quantity": 0}]})
        assert response.status_code == 422
