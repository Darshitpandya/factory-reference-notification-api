"""Tests for notification API routes."""

from fastapi.testclient import TestClient

from src.notifications.app import app

client = TestClient(app)


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_create_notification_accepted():
    """Valid notification is accepted (202) and returns a notification ID."""
    res = client.post("/v1/notifications", json={
        "eventType": "invoice.issued",
        "recipientId": "user-001",
        "payload": {
            "entityId": "inv-001",
            "tenantId": "tenant-a",
            "timestamp": "2026-01-01T00:00:00Z",
        },
        "idempotencyKey": "test-idempotency-key-001",
    })
    assert res.status_code == 202
    body = res.json()
    assert "notificationId" in body
    assert body["status"] == "ACCEPTED"
    assert body["idempotencyKey"] == "test-idempotency-key-001"


def test_invalid_event_type_rejected():
    """Unknown event type is rejected with 422."""
    res = client.post("/v1/notifications", json={
        "eventType": "unknown.event.type.not.in.schema",
        "recipientId": "user-001",
        "payload": {"entityId": "e-001", "tenantId": "tenant-a", "timestamp": "2026-01-01T00:00:00Z"},
        "idempotencyKey": "test-key-002",
    })
    assert res.status_code == 422


def test_idempotency_key_too_short():
    """Idempotency key shorter than 8 chars is rejected."""
    res = client.post("/v1/notifications", json={
        "eventType": "invoice.issued",
        "recipientId": "user-001",
        "payload": {},
        "idempotencyKey": "short",
    })
    assert res.status_code == 422


def test_missing_required_fields():
    """Request without eventType is rejected."""
    res = client.post("/v1/notifications", json={
        "recipientId": "user-001",
        "payload": {},
        "idempotencyKey": "test-key-003",
    })
    assert res.status_code == 422
