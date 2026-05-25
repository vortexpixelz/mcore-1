# Appwrite TablesDB schema (MCORE + GJB2)

Use **TablesDB** (`appwrite.tables_db`) for new projects. Replace placeholder IDs (`mcore`, `patterns`, …) with your own via `appwrite init tables` or the Console, then `appwrite push tables`.

**Database:** `mcore_main` (suggested `$id`: `mcore_main`)

**Row security:** set `rowSecurity: true` on every user-owned table. Grant `create`, `read`, `update`, `delete` with `Permission.*(Role.user("$userId"))` on rows from authenticated clients.

## Entity overview

| Table `$id` | Purpose |
|-------------|---------|
| `mcore_sessions` | User-scoped workspace / lab session |
| `pattern_library` | Saved metrical patterns (trit strings, labels) |
| `conservation_results` | Cached `CheckResult`-like summaries from `check_constituent` |
| `bisection_tree_runs` | Inputs + serialized `NodeResult[]` from weight-stream `check_tree` |
| `dna_carry_encodings` | DNA string, `trits` JSON, optional `encode_log` JSON |
| `gjb2_profiles` | Named GJB2 study profiles (metadata, default DNA fixtures) |
| `gjb2_results` | Deletion site, links to WT/mut encodings, tree run IDs |
| `overlay_snapshots` | Methylation / quantum / generic overlay payloads (JSON) |
| `methylation_profiles` | Island labels + beta lists (mediumtext JSON) |
| `tme_artifacts` | Base64-TME streams, file refs to Storage |
| `realtime_topics` | Optional mapping to Appwrite **Topics** for push (see Messaging docs) |

## Table: `mcore_sessions`

| Column | Type | Required | Index | Notes |
|--------|------|----------|-------|-------|
| `user_id` | varchar(36) | yes | yes | Denormalized owner for queries |
| `name` | varchar(255) | yes | no | |
| `slug` | varchar(128) | no | unique (user scoped) | Optional URL slug |
| `settings` | mediumtext | no | no | JSON: UI prefs, feature flags |

## Table: `pattern_library`

| Column | Type | Required | Index | Notes |
|--------|------|----------|-------|-------|
| `session_id` | varchar(36) | yes | yes | Relationship → `mcore_sessions` |
| `title` | varchar(255) | yes | no | |
| `pattern_digits` | varchar(1024) | yes | no | `012` style |
| `pattern_classical` | text | no | no | Optional `-u-` rendering |
| `source` | enum | no | no | `manual`, `import_cli`, `mcp` |

## Table: `conservation_results`

| Column | Type | Required | Index | Notes |
|--------|------|----------|-------|-------|
| `session_id` | varchar(36) | yes | yes | |
| `valid` | boolean | yes | yes | |
| `error_count` | integer | yes | no | |
| `errors_json` | mediumtext | no | no | Redacted checker messages |

## Table: `bisection_tree_runs`

| Column | Type | Required | Index | Notes |
|--------|------|----------|-------|-------|
| `session_id` | varchar(36) | yes | yes | |
| `weights_json` | mediumtext | yes | no | list[int] 0..2 |
| `depth` | integer | no | no | Optional asserted depth |
| `node_results_json` | mediumtext | yes | no | Serialized `NodeResult` |
| `all_valid` | boolean | yes | yes | |

## Table: `dna_carry_encodings`

| Column | Type | Required | Index | Notes |
|--------|------|----------|-------|-------|
| `session_id` | varchar(36) | yes | yes | |
| `dna` | mediumtext | yes | prefix | May be large amplicons |
| `trits_json` | mediumtext | yes | no | |
| `encode_log_json` | longtext | no | no | Optional full `EncodeStep` trace |

## Table: `gjb2_profiles`

| Column | Type | Required | Index | Notes |
|--------|------|----------|-------|-------|
| `session_id` | varchar(36) | yes | yes | |
| `name` | varchar(255) | yes | no | |
| `description` | text | no | no | |

## Table: `gjb2_results`

| Column | Type | Required | Index | Notes |
|--------|------|----------|-------|-------|
| `session_id` | varchar(36) | yes | yes | |
| `profile_id` | varchar(36) | no | yes | |
| `deletion_pos_1` | integer | yes | yes | |
| `wt_encoding_id` | varchar(36) | no | yes | → `dna_carry_encodings` |
| `mut_encoding_id` | varchar(36) | no | yes | → `dna_carry_encodings` |
| `tree_run_id` | varchar(36) | no | yes | → `bisection_tree_runs` |
| `summary` | text | no | no | Human-readable |

## Table: `overlay_snapshots`

| Column | Type | Required | Index | Notes |
|--------|------|----------|-------|-------|
| `session_id` | varchar(36) | yes | yes | |
| `overlay_kind` | enum | yes | yes | `methylation`, `quantum`, `generic` |
| `payload_json` | mediumtext | yes | no | |

## Table: `methylation_profiles`

| Column | Type | Required | Index | Notes |
|--------|------|----------|-------|-------|
| `session_id` | varchar(36) | yes | yes | |
| `label` | varchar(255) | yes | no | |
| `beta_list_json` | mediumtext | yes | no | |

## Table: `tme_artifacts`

| Column | Type | Required | Index | Notes |
|--------|------|----------|-------|-------|
| `session_id` | varchar(36) | yes | yes | |
| `stream` | mediumtext | yes | no | Base64-TME |
| `storage_file_id` | varchar(36) | no | no | Optional large blobs in Storage |

## Suggested indexes

- Composite: `(session_id, $createdAt)` on high-churn tables for dashboards.
- Full index on `pattern_library.title` only if `varchar` size ≤ 768 (Appwrite prefix rules).

## Realtime

Subscribe to table channels in client SDKs when **Realtime** is enabled for the database. Use narrow `Query.equal("session_id", ...)` in list subscriptions to avoid leaking other labs’ rows.

## Permissions snippet (conceptual)

```text
read("user:$userId")
create("user:$userId")
update("user:$userId")
delete("user:$userId")
```

For team/shared libraries, add `read("team:TEAM_ID")` on specific rows or use Appwrite **Teams** memberships.
