# Contributing to Factory Reference Notification API

## Running the check suite

```bash
uv sync --dev
uv run ruff check .
uv run pytest -q
uv run python scripts/check-event-compatibility.py
```

All 17 tests must pass. `ruff check` must exit 0. `check-event-compatibility.py` must exit 0.

## Rules for this repository

1. **Never remove an `eventType` value from `notification-requested.schema.json`.** Existing publishers depend on the current accepted types. This is a breaking change and will fail `check-event-compatibility.py` and the verifier.

2. **Never add a required field to the event schema** without a corresponding update to all existing fixtures in `contracts/events/fixtures/`. If the fixtures cannot be updated to satisfy the new required field, the change is backward-incompatible and must go through an explicit deprecation path.

3. **PII must not appear in logs.** Use `redact_dict()` before any log call that could contain user data. `tests/test_pii_redaction.py` covers this — do not weaken it.

4. **Delivery intent must persist before 202.** `persist_notification()` must be called before returning. Do not convert the endpoint to fire-and-forget without updating the outbox tests.

5. **Do not modify `.factory/repository-contract.yaml` and source code in the same PR.**

## Adding new event types

1. Add the value to the `enum` in `contracts/events/notification-requested.schema.json`
2. Add a fixture in `contracts/events/fixtures/` that uses the new type
3. Run `uv run python scripts/check-event-compatibility.py` — all fixtures must pass
4. Add a test in `tests/test_notifications.py` for the new type

## Adding new API endpoints

1. Add the route in `src/notifications/routes.py`
2. Add tests in `tests/`
3. If the endpoint receives or returns user data, apply `redact_dict()` before any logging

## Updating dependencies

```bash
uv add <package>          # adds to pyproject.toml and updates uv.lock
uv sync                   # apply changes
```

Commit both `pyproject.toml` and `uv.lock`. The CI uses `--frozen` and will fail if `uv.lock` is stale.

## Questions

Open a GitHub Discussion or an issue tagged `question`.
