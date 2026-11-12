# Notification API — Engineering Instructions

Owner: notifications-domain. Language: Python. Runtime: FastAPI.
Canonical events: `contracts/events/*.schema.json`. Database: Postgres outbox.

## Commands
- `uv sync --frozen`
- `uv run ruff check .`
- `uv run pytest -q`
- `uv run python scripts/check-event-compatibility.py`

## Boundaries
- Preserve already accepted notification event payloads and consumers.
- Redact PII in logs, traces, exceptions, retries and audit exports.
- Persist delivery intent before acknowledging a request.
- Enforce idempotency and bounded retry/backoff without duplicate delivery.
- No secret/token fields in agent-readable task prompts or PR files.
- Do not edit protected security policy or verifier implementation.

## Artifacts and acceptance
- Python source under `src/notifications/`; tests under `tests/`.
- Accepted event fixtures under `contracts/events/fixtures/`.
- Trusted required check is `factory-contract/acceptance`.
- Proof requires event compatibility, PII redaction, reliability and deployment.

## Stop conditions
If a change invalidates an accepted event fixture or exposes PII, stop.
If the delivery target cannot be reached after bounded retries, preserve error.
This file gives working context only; it is not an authorization policy.
