"""Tests for outbox pattern — idempotency and delivery guarantees."""

import uuid
from unittest.mock import MagicMock


def make_mock_conn(existing_id: str | None = None):
    """Create a mock database connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    # fetchone returns existing record if provided
    mock_cursor.fetchone.return_value = (existing_id,) if existing_id else None
    return mock_conn, mock_cursor


def test_persist_notification_inserts_new_record():
    """New notifications are inserted into the outbox."""
    from src.notifications.outbox import persist_notification

    conn, cursor = make_mock_conn(existing_id=None)
    result = persist_notification(
        conn,
        notification_id="notif-001",
        event_type="invoice.issued",
        payload={"entityId": "inv-001"},
        idempotency_key="idem-key-001",
    )

    # Should commit the insert
    conn.commit.assert_called_once()
    assert isinstance(result, str)
    assert len(result) > 0


def test_persist_notification_idempotent():
    """Duplicate idempotency_key returns existing record ID without inserting."""
    from src.notifications.outbox import persist_notification

    existing_id = str(uuid.uuid4())
    conn, cursor = make_mock_conn(existing_id=existing_id)

    result = persist_notification(
        conn,
        notification_id="notif-002",
        event_type="invoice.issued",
        payload={"entityId": "inv-002"},
        idempotency_key="same-key",
    )

    # Should return existing ID
    assert result == existing_id
    # Should NOT commit (no insert)
    conn.commit.assert_not_called()


def test_mark_delivered():
    """Delivered notifications are marked with DELIVERED status."""
    from src.notifications.outbox import mark_delivered

    conn, cursor = make_mock_conn()
    mark_delivered(conn, "outbox-id-001")

    conn.commit.assert_called_once()
    # Verify the UPDATE statement was called
    cursor.execute.assert_called_once()
    sql = cursor.execute.call_args[0][0]
    assert "DELIVERED" in sql


def test_mark_failed_increments_attempt():
    """Failed notifications increment the attempt counter."""
    from src.notifications.outbox import mark_failed

    conn, cursor = make_mock_conn()
    mark_failed(conn, "outbox-id-001", error="Connection refused")

    conn.commit.assert_called_once()
    sql = cursor.execute.call_args[0][0]
    assert "attempt_count" in sql
