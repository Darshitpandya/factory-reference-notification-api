"""
Transactional outbox pattern.

Delivery intent is persisted before acknowledging a request.
This guarantees at-least-once delivery even if the process crashes
between acknowledgment and actual delivery.
"""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection(database_url: str):
    return psycopg2.connect(database_url)


def persist_notification(
    conn,
    notification_id: str,
    event_type: str,
    payload: dict[str, Any],
    idempotency_key: str,
) -> str:
    """
    Persist notification to the outbox table BEFORE acknowledging the request.
    Returns the outbox record ID.

    Idempotency: if idempotency_key already exists, returns the existing record ID
    without inserting a duplicate.
    """
    with conn.cursor() as cur:
        # Check for existing record (idempotency)
        cur.execute(
            "SELECT id FROM notification_outbox WHERE idempotency_key = %s",
            (idempotency_key,)
        )
        existing = cur.fetchone()
        if existing:
            return existing[0]

        # Insert new outbox record
        outbox_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO notification_outbox
              (id, notification_id, event_type, payload, idempotency_key,
               status, attempt_count, created_at)
            VALUES (%s, %s, %s, %s, %s, 'PENDING', 0, %s)
            """,
            (
                outbox_id,
                notification_id,
                event_type,
                json.dumps(payload),
                idempotency_key,
                datetime.now(UTC),
            ),
        )
        conn.commit()
        return outbox_id


def mark_delivered(conn, outbox_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE notification_outbox SET status = 'DELIVERED', delivered_at = %s WHERE id = %s",
            (datetime.now(UTC), outbox_id),
        )
        conn.commit()


def mark_failed(conn, outbox_id: str, error: str, increment_attempt: bool = True) -> None:
    with conn.cursor() as cur:
        if increment_attempt:
            cur.execute(
                """
                UPDATE notification_outbox
                SET status = 'FAILED', last_error = %s,
                    attempt_count = attempt_count + 1, updated_at = %s
                WHERE id = %s
                """,
                (error[:500], datetime.now(UTC), outbox_id),
            )
        else:
            cur.execute(
                "UPDATE notification_outbox SET last_error = %s WHERE id = %s",
                (error[:500], outbox_id),
            )
        conn.commit()


def get_pending_notifications(conn, limit: int = 50) -> list[dict[str, Any]]:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, notification_id, event_type, payload, attempt_count
            FROM notification_outbox
            WHERE status = 'PENDING' AND attempt_count < 5
            ORDER BY created_at ASC
            LIMIT %s
            FOR UPDATE SKIP LOCKED
            """,
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]
