"""
Tests for task and purchase order API endpoints.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def clear_in_memory_stores():
    """Reset the in-memory task and PO stores so tests don't leak state into each other."""
    main.tasks.clear()
    main.purchase_orders.clear()
    yield
    main.tasks.clear()
    main.purchase_orders.clear()


@pytest.fixture
def po_payload():
    """Valid purchase order request for backlog item 1."""
    return {
        "backlog_item_id": "1",
        "supplier_name": "Acme Components",
        "quantity": 50,
        "unit_cost": 12.5,
        "expected_delivery_date": "2025-12-15",
        "notes": "Rush order",
    }


class TestTaskEndpoints:
    """Test suite for task-related endpoints."""

    def test_get_tasks_empty(self, client):
        """Test that no tasks exist before any are created."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """Test creating a task returns it as pending with a string id."""
        response = client.post(
            "/api/tasks",
            json={"title": "Audit stock", "priority": "high", "dueDate": "2025-11-20"},
        )
        assert response.status_code == 201

        task = response.json()
        assert task["id"] == "task-1"
        assert task["title"] == "Audit stock"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-11-20"
        assert task["status"] == "pending"

    def test_get_tasks_newest_first(self, client):
        """Test that tasks are listed newest first."""
        client.post("/api/tasks", json={"title": "First", "dueDate": "2025-11-20"})
        client.post("/api/tasks", json={"title": "Second", "dueDate": "2025-11-21"})

        data = client.get("/api/tasks").json()
        assert [t["title"] for t in data] == ["Second", "First"]

    def test_create_task_invalid_input(self, client):
        """Test that blank titles, bad priorities and bad dates are rejected."""
        bad_payloads = [
            {"title": "", "dueDate": "2025-11-20"},
            {"title": "X", "priority": "urgent", "dueDate": "2025-11-20"},
            {"title": "X", "dueDate": "not-a-date"},
            {"title": "X"},
        ]
        for payload in bad_payloads:
            assert client.post("/api/tasks", json=payload).status_code == 422

    def test_toggle_task(self, client):
        """Test toggling a task flips its status both ways."""
        task_id = client.post("/api/tasks", json={"title": "X", "dueDate": "2025-11-20"}).json()["id"]

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.json()["status"] == "pending"

    def test_delete_task(self, client):
        """Test deleting a task removes it from the list."""
        task_id = client.post("/api/tasks", json={"title": "X", "dueDate": "2025-11-20"}).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["id"] == task_id
        assert client.get("/api/tasks").json() == []

    def test_task_ids_not_reused_after_delete(self, client):
        """Test that a new task never reuses the id of a deleted one."""
        first = client.post("/api/tasks", json={"title": "A", "dueDate": "2025-11-20"}).json()["id"]
        client.delete(f"/api/tasks/{first}")
        second = client.post("/api/tasks", json={"title": "B", "dueDate": "2025-11-20"}).json()["id"]
        assert second != first

    def test_toggle_or_delete_nonexistent_task(self, client):
        """Test that unknown task ids return 404."""
        for response in (client.patch("/api/tasks/task-999"), client.delete("/api/tasks/task-999")):
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


class TestPurchaseOrderEndpoints:
    """Test suite for purchase order endpoints."""

    def test_create_purchase_order(self, client, po_payload):
        """Test creating a purchase order for a backlog item."""
        response = client.post("/api/purchase-orders", json=po_payload)
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("po-")
        assert po["backlog_item_id"] == "1"
        assert po["supplier_name"] == "Acme Components"
        assert po["quantity"] == 50
        assert abs(po["unit_cost"] - 12.5) < 0.01
        assert po["expected_delivery_date"] == "2025-12-15"
        assert po["status"] == "Pending"
        assert "-" in po["created_date"]
        assert po["notes"] == "Rush order"

    def test_get_purchase_order_by_backlog_item(self, client, po_payload):
        """Test fetching the PO for a backlog item after creating it."""
        created = client.post("/api/purchase-orders", json=po_payload).json()

        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_nonexistent_purchase_order(self, client):
        """Test that a backlog item without a PO returns 404."""
        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_purchase_order_unknown_backlog_item(self, client, po_payload):
        """Test that a PO for an unknown backlog item returns 404."""
        po_payload["backlog_item_id"] = "nonexistent-999"
        response = client.post("/api/purchase-orders", json=po_payload)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_duplicate_purchase_order(self, client, po_payload):
        """Test that a second PO for the same backlog item is rejected."""
        client.post("/api/purchase-orders", json=po_payload)
        response = client.post("/api/purchase-orders", json=po_payload)
        assert response.status_code == 409

    def test_create_purchase_order_invalid_input(self, client, po_payload):
        """Test that non-positive quantities/costs, blank suppliers and bad dates are rejected."""
        for field, value in [
            ("quantity", 0),
            ("unit_cost", -1),
            ("supplier_name", ""),
            ("expected_delivery_date", "soon"),
        ]:
            response = client.post("/api/purchase-orders", json={**po_payload, field: value})
            assert response.status_code == 422, field

    def test_backlog_exposes_purchase_order_id(self, client, po_payload):
        """Test that the backlog reflects the PO so the Dashboard shows View PO after reload."""
        po = client.post("/api/purchase-orders", json=po_payload).json()

        backlog = {item["id"]: item for item in client.get("/api/backlog").json()}
        assert backlog["1"]["purchase_order_id"] == po["id"]
        assert backlog["1"]["has_purchase_order"] is True
        assert backlog["2"]["purchase_order_id"] is None
        assert backlog["2"]["has_purchase_order"] is False
