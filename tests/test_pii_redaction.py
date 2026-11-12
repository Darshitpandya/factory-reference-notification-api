"""Tests for PII redaction — these must pass before any PR merges."""

from src.notifications.pii import REDACTED, redact_dict, redact_string


def test_redacts_email_in_string():
    result = redact_string("Contact user@example.com for details")
    assert "user@example.com" not in result
    assert REDACTED in result


def test_redacts_phone_number():
    result = redact_string("Call 555-123-4567 for support")
    assert "555-123-4567" not in result
    assert REDACTED in result


def test_redacts_ssn():
    result = redact_string("SSN: 123-45-6789")
    assert "123-45-6789" not in result
    assert REDACTED in result


def test_no_false_positive_on_normal_text():
    result = redact_string("Invoice amount: $100.00 for tenant-a")
    assert result == "Invoice amount: $100.00 for tenant-a"


def test_redact_dict_named_pii_fields():
    data = {
        "entityId": "inv-001",
        "email": "user@example.com",
        "recipientEmail": "other@example.com",
        "amount": 10000,
    }
    result = redact_dict(data, pii_fields={"email"})
    assert result["email"] == REDACTED
    assert result["entityId"] == "inv-001"
    assert result["amount"] == 10000


def test_redact_dict_nested():
    data = {
        "notification": {
            "email": "user@example.com",
            "metadata": {"ref": "INV-001"},
        }
    }
    result = redact_dict(data, pii_fields={"email"})
    assert result["notification"]["email"] == REDACTED
    assert result["notification"]["metadata"]["ref"] == "INV-001"


def test_redact_dict_preserves_non_pii():
    data = {"entityId": "inv-001", "tenantId": "tenant-a", "amount": 1000}
    result = redact_dict(data)
    assert result["entityId"] == "inv-001"
    assert result["tenantId"] == "tenant-a"
    assert result["amount"] == 1000


def test_redact_dict_handles_pii_in_string_values():
    data = {"message": "Invoice for user@company.com is ready"}
    result = redact_dict(data)
    assert "user@company.com" not in result["message"]
    assert REDACTED in result["message"]
