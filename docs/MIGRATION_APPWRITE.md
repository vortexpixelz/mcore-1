# Migrating local patterns and GJB2 trees to Appwrite

See **[APPWRITE_QUICKSTART.md](./APPWRITE_QUICKSTART.md)** for environment and
CLI shortcuts. This page is data-shape guidance only.

## Principles

1. **Library first** — reproduce outputs locally with `mcore_1` / `mcore_py`, then upsert rows so Appwrite is a **cache + collaboration** layer.
2. **Idempotent imports** — hash canonical inputs (`pattern_digits`, `weights_json`, `dna`) and store `content_sha256` (add column if desired) to skip duplicates.

## Pattern library (CLI → TablesDB)

1. For each saved pattern string from `mcore validate` / notebooks, parse to digits with `mcore_py.cli` parsing rules or your own exporter.
2. Create or select a `mcore_sessions` row for the user.
3. `tables_db.create_row(..., "pattern_library", ..., { "session_id", "title", "pattern_digits", ... })`.

## GJB2 bisection runs

1. Encode WT DNA: `dna_to_trits(dna)` → `trits`, `log`.
2. `rows = check_tree(trits)` (optional `depth=...`).
3. Insert `dna_carry_encodings` for WT; optionally mut DNA after deletion.
4. Insert `bisection_tree_runs` with `weights_json=json.dumps(trits)`, `node_results_json=json.dumps([asdict-like dict for each NodeResult])`.
5. Insert `gjb2_results` linking `deletion_pos_1`, encoding IDs, and `tree_run_id`.

### `NodeResult` JSON shape

```json
{
  "node_id": "…",
  "leaf_lo": 1,
  "leaf_hi": 4,
  "valid": true,
  "errors": []
}
```

Use `dataclasses.asdict` in Python when building payloads.

## Realtime collaboration

After each successful `update_row` from an editor, emit a client-side event or rely on **TablesDB realtime** subscriptions so peers refresh the same `session_id` partition.

## Rollback

Keep immutable exports (JSON files in git or object storage) of critical runs before bulk migration. Appwrite supports **backups** on enterprise tiers; self-hosted operators should snapshot MariaDB/Redis per Appwrite ops guides.
