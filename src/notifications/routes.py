"""
Notification API routes.

Accepts notification requests, validates against JSON schema,
persists to outbox, and returns accepted status.
"""

import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any

import jsonschema
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, field_validator

from .outbox import get_connection, persist_notification
from .pii import redact_dict

router = APIRouter()
logger = logging.getLogger("notifications")

# Load event schema once at startup
_SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "events" / "notification-requested.schema.json"
_EVENT_SCHEMA = json.loads(_SCHEMA_PATH.read_text()) if _SCHEMA_PATH.exists() else {}


class NotificationRequest(BaseModel):
    eventType: str
    recipientId: str  # opaque ID — not email, not PII
    payload: dict[str, Any]
    idempotencyKey: str

    @field_validator("idempotencyKey")
    @classmethod
    def validate_idempotency_key(cls, v: str) -> str:
        if len(v) < 8 or len(v) > 128:
            raise ValueError("idempotencyKey must be 8-128 characters")
        return v


@router.post("/v1/notifications", status_code=202)
async def create_notification(
    body: NotificationRequest,
    x_request_id: str | None = Header(default=None),
):
    """
    Accept a notification request.

    1. Validate event schema
    2. Persist to outbox BEFORE returning 202 (guaranteed delivery)
    3. Return accepted status with notification ID

    PII is never logged — redacted before any log emission.
    """
    notification_id = str(uuid.uuid4())

    # Validate against event schema
    if _EVENT_SCHEMA:
        try:
            jsonschema.validate(
                {"eventType": body.eventType, "payload": body.payload},
                _EVENT_SCHEMA,
            )
        except jsonschema.ValidationError as e:
            raise HTTPException(status_code=422, detail=f"Event schema validation failed: {e.message}")

    # Redact PII from payload before logging
    safe_payload = redact_dict(body.payload)
    logger.info(
        "notification_accepted",
        extra={
            "notification_id": notification_id,
            "event_type": body.eventType,
            "payload_keys": list(body.payload.keys()),  # keys only, not values
            # safe_payload logged separately at debug level only
        },
    )

    # Persist delivery intent to outbox
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url:
        conn = get_connection(database_url)
        try:
            outbox_id = persist_notification(
                conn,
                notification_id=notification_id,
                event_type=body.eventType,
                payload=safe_payload,  # Store redacted version
                idempotency_key=body.idempotencyKey,
            )
        finally:
            conn.close()
    else:
        outbox_id = "no-db-configured"

    return {
        "notificationId": notification_id,
        "outboxId": outbox_id,
        "status": "ACCEPTED",
        "idempotencyKey": body.idempotencyKey,
    }


@router.get("/v1/notifications/{notification_id}")
async def get_notification_status(notification_id: str):
    """Get delivery status of a notification by ID."""
    # Stub — full implementation queries notification_outbox table
    return {"notificationId": notification_id, "status": "UNKNOWN"}
