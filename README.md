# Factory Reference Notification API

[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)
[![CI](https://img.shields.io/badge/CI%2017%20tests-passing-brightgreen?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/Darshitpandya/factory-reference-notification-api/actions)
[![GitHub Stars](https://img.shields.io/github/stars/Darshitpandya/factory-reference-notification-api?style=flat-square&logo=github)](https://github.com/Darshitpandya/factory-reference-notification-api/stargazers)
[![Factory Release](https://img.shields.io/badge/Factory%20Release-1.4.0-brightgreen?style=flat-square)](.factory/repository-contract.yaml)
[![Python](https://img.shields.io/badge/Python-FastAPI-3776AB?style=flat-square&logo=python&logoColor=white)](src/notifications/app.py)
[![PII Redacted](https://img.shields.io/badge/PII-redacted-orange?style=flat-square)](src/notifications/pii.py)
[![check](https://img.shields.io/badge/required%20check-factory--contract%2Facceptance-blue?style=flat-square&logo=github)](.factory/repository-contract.yaml)

**Python reference consumer proving factory reuse across different languages, schemas, and domains.**

This service consumes the same factory release (`1.4.0`) as the TypeScript billing API, with its own schema, PII requirements, and delivery reliability acceptance — without copying any orchestration logic.

> **Reuse proof:** `run-notification-reuse-001` FactoryRun in Port — 5 stages ACCEPTED using factory release 1.4.0, same as billing API, different language/domain/policies.

Works with **Claude Code** · **GitHub Actions** · **Port** · **FastAPI** · **PostgreSQL**

[The reuse proof](#the-reuse-proof) · [Quick start](#quick-start) · [API reference](#api-reference) · [Design patterns](#design-patterns) · [Tests](#tests) · [Factory contract](#factory-contract-integration) · [Contributing](CONTRIBUTING.md)

---

## Related repositories

| Repo | Role |
|---|---|
| [`ai-software-factory-contract`](https://github.com/Darshitpandya/ai-software-factory-contract) | Factory engine — same release that runs against this repo |
| [`ai-factory-trusted-verifier`](https://github.com/Darshitpandya/ai-factory-trusted-verifier) | Posts `factory-contract/acceptance` for event schema compatibility |
| [`factory-reference-billing-api`](https://github.com/Darshitpandya/factory-reference-billing-api) | TypeScript billing API — the other reference consumer |
| **This repo** | Python notification API — reuse proof, event compatibility, PII controls |

---

## The reuse proof

The AI Software Factory Contract claims **Build Once** means reusable production machinery, not a copy-pasted workflow. This repository is the proof.

| Property | Billing API | Notification API |
|---|---|---|
| Language | TypeScript | Python |
| Framework | Fastify | FastAPI |
| Compatibility check | OpenAPI (`oasdiff breaking`) | JSON Schema (fixture validation) |
| Security constraint | Tenant isolation | PII redaction |
| Delivery contract | API reliability | Outbox, idempotency, retry |
| **Factory release** | **1.4.0** | **1.4.0** |
| Orchestration code copied | — | None |

The factory's five stages run against this repo using the same coordinator, the same Claude executor, and the same SKILL.md procedures. The only difference is the `RepositoryContract` in `.factory/repository-contract.yaml`, which declares this repo's own build commands, compatibility path, and PII policies.

---

## Quick Start

**Prerequisites:** Python ≥ 3.12, `uv` ([install](https://docs.astral.sh/uv/getting-started/installation/)), Docker (optional, for PostgreSQL)

### 1. Clone and install

```bash
git clone https://github.com/Darshitpandya/factory-reference-notification-api.git
cd factory-reference-notification-api
uv sync --dev
```

### 2. Run the tests

```bash
uv run pytest -q
# 17 tests: notifications, PII redaction, outbox pattern
```

### 3. Check event compatibility

```bash
uv run python scripts/check-event-compatibility.py
# Validates all fixtures in contracts/events/fixtures/ against the current schema
```

### 4. Lint

```bash
uv run ruff check .
```

### 5. Run the server

```bash
export DATABASE_URL=postgresql://notifications:notifications@localhost:5432/notifications
uv run python -m src.notifications.app
# FastAPI on :3003; docs at http://localhost:3003/docs
```

Or with Docker Compose:

```bash
docker compose -f deploy/docker-compose.yaml up -d
```

---

## API Reference

### `POST /v1/notifications`

Accept a notification request. Returns `202 Accepted` immediately; delivery is handled asynchronously via the outbox.

```bash
curl -X POST http://localhost:3003/v1/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "invoice.issued",
    "recipientId": "user-001",
    "payload": {
      "entityId": "inv-001",
      "tenantId": "tenant-a",
      "timestamp": "2026-01-01T00:00:00Z",
      "metadata": {"amount_cents": 10000, "currency": "USD"}
    },
    "idempotencyKey": "unique-key-per-request-min-8-chars"
  }'
```

Response:
```json
{
  "notificationId": "uuid",
  "outboxId": "uuid",
  "status": "ACCEPTED",
  "idempotencyKey": "unique-key-per-request-min-8-chars"
}
```

**Idempotency:** Submitting the same `idempotencyKey` twice returns the existing `outboxId` without creating a duplicate. Delivery intent is persisted before the 202 response.

**Supported `eventType` values:** `invoice.issued`, `invoice.overdue`, `invoice.paid`, `account.created`, `account.suspended`

**PII:** `recipientId` is an opaque ID, not an email address or phone number. The `payload` is redacted before logging.

### `GET /v1/notifications/{notification_id}`

Returns delivery status for a notification by ID.

### `GET /health`

```json
{"status": "ok", "version": "1.0.0"}
```

---

## Design Patterns

### Outbox pattern

Delivery intent is written to the `notification_outbox` table **before** the 202 response is sent. This guarantees at-least-once delivery even if the process crashes between acknowledgment and actual delivery.

```
Request → validate → persist to outbox → 202 response
                          │
                     background worker
                          │
                     deliver → mark DELIVERED
                     (or) retry up to 5× → mark FAILED
```

### PII redaction

`src/notifications/pii.py` applies redaction before any logging, error tracing, retry payload, or audit export:

```python
from src.notifications.pii import redact_dict

safe = redact_dict(payload)
logger.info("notification_accepted", extra={"payload_keys": list(payload.keys())})
# NOT: logger.info("notification", extra={"payload": payload})
```

Fields named `email`, `phone`, `address`, `ssn`, `creditCard`, `password`, `token`, `secret`, `apiKey` are always redacted. Email, phone, and SSN patterns in string values are also redacted.

### Event schema validation

`contracts/events/notification-requested.schema.json` is the canonical event contract. Any PR that removes an `eventType` value or adds a required field is a breaking change and will be caught by `scripts/check-event-compatibility.py` and the trusted verifier.

---

## Tests

```bash
uv run pytest -q              # all 17 tests
uv run pytest tests/test_pii_redaction.py -v   # PII tests only
uv run pytest tests/test_outbox.py -v          # outbox pattern tests
```

| File | What it covers |
|---|---|
| `tests/test_notifications.py` | Health, valid notification accepted, invalid event type, idempotency key validation |
| `tests/test_pii_redaction.py` | Email redaction, phone redaction, SSN redaction, dict traversal, no false positives |
| `tests/test_outbox.py` | New record insertion, idempotency (no duplicate), mark delivered, mark failed + attempt increment |

---

## Factory Contract Integration

```yaml
# .factory/repository-contract.yaml
consumedRelease: "1.4.0"   # same as billing API
acceptance:
  requiredChecks:
    - factory-contract/acceptance
  compatibilityBaselinePath: contracts/events/notification-requested.schema.json
  piiPolicies:
    - pii-must-be-redacted-in-logs
    - no-pii-in-retry-payloads
```

The trusted verifier uses `notification-requested.schema.json` at the base SHA to detect breaking schema changes — equivalent to what `oasdiff` does for the billing API's OpenAPI spec.

### Event schema compatibility

```bash
# Check all fixtures pass the current schema
uv run python scripts/check-event-compatibility.py

# Adding a new eventType value is non-breaking (backward compatible)
# Removing an eventType value is breaking (existing publishers break)
# Adding a required field is breaking
# Adding an optional field is non-breaking
```

---

## Security

- PII must not appear in logs, traces, exceptions, retries, or audit exports — `src/notifications/pii.py` is the enforcement point
- Delivery intent persisted before 202 response (no silent drops)
- No secret or token fields in AGENTS.md, work order files, or PR descriptions
- See [SECURITY.md](SECURITY.md)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](LICENSE).
