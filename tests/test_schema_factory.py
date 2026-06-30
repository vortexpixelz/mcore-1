"""
test_schema_factory.py
Red-green test for the schema_factory registry.
Intentionally fails until schema_registry.yaml exists with required fields.
"""

from pathlib import Path

import pytest

REGISTRY_PATH = Path("experimental/schema_factory/schema_registry.yaml")
REQUIRED_FIELDS = {"schema_id", "schema_version", "fields"}


def test_candidate_schema_registry_exists_and_has_required_fields():
    assert REGISTRY_PATH.exists(), (
        f"schema_factory needs {REGISTRY_PATH} — "
        "create it with candidate schema entries and required fields"
    )
    import yaml  # noqa: PLC0415

    registry = yaml.safe_load(REGISTRY_PATH.read_text())
    schemas = registry.get("schemas", [])
    assert schemas, "registry must contain at least one schema entry"
    for entry in schemas:
        missing = REQUIRED_FIELDS - set(entry.keys())
        assert not missing, (
            f"schema entry {entry.get('schema_id', '?')} is missing fields: {missing}"
        )
        assert isinstance(entry["fields"], list) and entry["fields"], (
            f"schema {entry['schema_id']} must have a non-empty fields list"
        )
