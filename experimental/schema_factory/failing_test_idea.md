# Intentional Failing Test Idea

This is not yet a committed pytest failure. It is a design note for a red test.

## Purpose

Create one test that fails until the schema factory can load candidate schemas and confirm required fields.

## Proposed failing test

```python
from pathlib import Path

REQUIRED_FIELDS = {"schema_id", "schema_version", "fields"}


def test_candidate_schema_registry_exists_and_has_required_fields():
    registry = Path("experimental/schema_factory/schema_registry.yaml")
    assert registry.exists(), "schema factory needs a schema_registry.yaml"
```

## Why this should fail first

There is no `schema_registry.yaml` yet. The failure is useful because it forces the next implementation step to be concrete.

## Then make it pass

Create:

```text
experimental/schema_factory/schema_registry.yaml
```

with candidate schema entries and required fields.
