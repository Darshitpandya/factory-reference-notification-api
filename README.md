# Factory Reference Notification API

Python/FastAPI reference consumer for the [AI Software Factory Contract](https://github.com/Darshitpandya/ai-software-factory-contract).

Proves **Build Once, Reuse** — the same factory release `1.4.0` that runs against the TypeScript billing API works equally against this Python service with its own schema, PII, and reliability acceptance.

## Related Repositories

| Repository | Role |
|---|---|
| [ai-software-factory-contract](https://github.com/Darshitpandya/ai-software-factory-contract) | Factory engine |
| [ai-factory-trusted-verifier](https://github.com/Darshitpandya/ai-factory-trusted-verifier) | Independent verifier |
| [factory-reference-billing-api](https://github.com/Darshitpandya/factory-reference-billing-api) | TypeScript billing API (same factory, different domain) |
| **This repo** | Python notification API — event compatibility, PII controls |

## Commands

```bash
uv sync --dev
uv run ruff check .
uv run pytest -q        # 17 tests: notifications, PII redaction, outbox
uv run python scripts/check-event-compatibility.py
```

## Key Patterns

- **Outbox pattern** — delivery intent persisted before 202 response
- **PII redaction** — email, phone, SSN stripped before logging or retry
- **Event schema validation** — `contracts/events/notification-requested.schema.json`
- **Idempotency** — duplicate `idempotencyKey` returns existing record ID

## Consumes Factory Release

```yaml
# .factory/repository-contract.yaml
consumedRelease: "1.4.0"   # same release as billing API
acceptance:
  requiredChecks:
    - factory-contract/acceptance
  compatibilityBaselinePath: contracts/events/notification-requested.schema.json
  piiPolicies:
    - pii-must-be-redacted-in-logs
```
