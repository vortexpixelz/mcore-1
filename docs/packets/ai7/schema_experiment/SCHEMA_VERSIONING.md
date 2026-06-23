# Schema Versioning Note

Use two versions:

```yaml
schema_version: 0.1
packet_version: 0.1
```

## Meaning

- `schema_version` tracks the mold.
- `packet_version` tracks the packet inside the mold.

## Example

```yaml
packet_id: AI7-BUNDLE-1
schema_version: 0.1
packet_version: 0.2
status: structured_backfill
source_bundle: Bundle 1
```

## Rule

Changing fields or required structure increments `schema_version`.

Improving one packet's content increments `packet_version`.
