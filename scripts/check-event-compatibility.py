#!/usr/bin/env python3
"""
check-event-compatibility.py

Validates that all fixture files in contracts/events/fixtures/ conform to
the current event schema. Exits 1 if any fixture fails.

Usage: uv run python scripts/check-event-compatibility.py
"""

import json
import sys
from pathlib import Path
import jsonschema

SCHEMA_PATH = Path("contracts/events/notification-requested.schema.json")
FIXTURES_DIR = Path("contracts/events/fixtures")


def main() -> int:
    if not SCHEMA_PATH.exists():
        print(f"✗ Schema not found: {SCHEMA_PATH}")
        return 1

    schema = json.loads(SCHEMA_PATH.read_text())
    fixtures = list(FIXTURES_DIR.glob("*.json"))

    if not fixtures:
        print(f"⚠  No fixtures found in {FIXTURES_DIR}")
        return 0

    failures = 0
    for fixture_path in sorted(fixtures):
        fixture = json.loads(fixture_path.read_text())
        try:
            jsonschema.validate(fixture, schema)
            print(f"✓  {fixture_path.name}")
        except jsonschema.ValidationError as e:
            print(f"✗  {fixture_path.name}: {e.message}")
            failures += 1

    print(f"\n{len(fixtures) - failures}/{len(fixtures)} fixtures passed")

    if failures > 0:
        print("✗ Schema compatibility check FAILED — do not merge breaking event schema changes")
        return 1

    print("✓ All fixtures compatible with current schema")
    return 0


if __name__ == "__main__":
    sys.exit(main())
