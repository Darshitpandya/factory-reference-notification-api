# Security Policy — Factory Reference Notification API

## Reporting a vulnerability

**Do not open a public issue.**

Report privately via GitHub Security Advisories or contact the maintainer directly (see GitHub profile).

## PII handling

This service processes notification requests that may contain personal information. The key requirements are:

- **Logs** must never contain email addresses, phone numbers, names, or other PII — apply `redact_dict()` from `src/notifications/pii.py` before any log call
- **Retry payloads** stored in the outbox use the redacted version of the payload, not the original
- **Error messages** and stack traces must not include raw request body content
- **Audit exports** must apply the same redaction as logs

If you find a code path where PII can appear in logs, error traces, or the outbox table in unredacted form, report it via Security Advisories immediately.

## Event schema changes

Removing an `eventType` value breaks existing publishers. This is treated as a security-relevant change because it can silently drop notifications from production systems. Any PR removing an `eventType` value must go through explicit review regardless of CI status.

## Credential handling

- `DATABASE_URL` must be injected via environment variable; never committed
- No secret or token fields in `AGENTS.md`, work order files, or PR descriptions
- The `idempotencyKey` field is a client-generated identifier, not a secret — it must not be logged at debug level in combination with other identifying fields

## Supported versions

The `main` branch receives security patches. Older tagged releases are not actively maintained.
