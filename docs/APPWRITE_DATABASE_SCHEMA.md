# Appwrite TablesDB schema (MCORE + GJB2 + acoustic + quantum)

Use **TablesDB** (`appwrite.tables_db`). Create tables via `appwrite init tables` / Console, then `appwrite push tables`.

**Database `$id`:** `mcore_main`

**Row security:** `rowSecurity: true` on user data tables. Per-row permissions: `read("user:$userId")`, `create("user:$userId")`, `update("user:$userId")`, `delete("user:$userId")` (adjust for teams as needed).

## Canonical entity map

| Logical name | Table `$id` | Notes |
|--------------|-------------|--------|
| **Patterns** | `patterns` | Metrical trit strings + optional Base64-TME cache |
| **ConservationResults** | `conservation_results` | Cached full `CheckResult` summaries |
| **BisectionTrees** | `bisection_trees` | Topology metadata (immutable definition rows) |
| **Bisection tree runs** | `bisection_tree_runs` | One execution: weights + `NodeResult[]` JSON |
| **DNA_Carry_Encodings** | `dna_carry_encodings` | DNA + trits + optional encode log |
| **GJB2_Results** | `gjb2_results` | Deletion experiments linking encodings + runs |
| **GJB2 profiles** | `gjb2_profiles` | Named fixtures |
| **AcousticSonifications** | `acoustic_sonifications` | Trit stream + metrics + WAV **Storage** id |
| **PhononWavepackets** | `phonon_wavepackets` | Per-atom row (FK → sonifications) |
| **Quantum runs** | `quantum_scheduling_runs` | Fidelity list + validity + trajectory JSON |
| **Methylation runs** | `methylation_island_runs` | Betas + validity + trajectory JSON |
| **Overlay snapshots** | `overlay_snapshots` | Generic serialized overlay payloads |
| **Methylation profiles** | `methylation_profiles` | Reusable beta lists |
| **TME artifacts** | `tme_artifacts` | Base64-TME streams |
| **Sessions** | `mcore_sessions` | User workspace |
| **Realtime bridge** | `realtime_topics` | Optional mapping to Messaging topics |

Legacy alias: if you already shipped **`pattern_library`**, treat it as **Patterns** (same columns) until migrated.

---

## `mcore_sessions`

| Column | Type | Required | Index |
|--------|------|----------|-------|
| `user_id` | varchar(36) | yes | yes |
| `name` | varchar(255) | yes | no |
| `slug` | varchar(128) | no | unique (per user, enforce in app) |
| `settings` | mediumtext | no | no |

## `patterns` (Patterns)

| Column | Type | Required | Index |
|--------|------|----------|-------|
| `session_id` | varchar(36) | yes | yes |
| `title` | varchar(255) | yes | no |
| `pattern_digits` | varchar(1024) | yes | no |
| `pattern_classical` | text | no | no |
| `source` | enum | no | no |
| `base64tme_cache` | text | no | no |

## `conservation_results` (ConservationResults)

| Column | Type | Required | Index |
|--------|------|----------|-------|
| `session_id` | varchar(36) | yes | yes |
| `valid` | boolean | yes | yes |
| `error_count` | integer | yes | no |
| `errors_json` | mediumtext | no | no |

## `bisection_trees` (BisectionTrees)

| Column | Type | Required | Index |
|--------|------|----------|-------|
| `session_id` | varchar(36) | yes | yes |
| `leaf_count` | integer | yes | yes |
| `depth` | integer | yes | no |
| `topology_key` | varchar(64) | yes | yes |
| `notes` | text | no | no |

## `bisection_tree_runs`

| Column | Type | Required | Index |
|--------|------|----------|-------|
| `session_id` | varchar(36) | yes | yes |
| `bisection_tree_id` | varchar(36) | no | yes |
| `weights_json` | mediumtext | yes | no |
| `depth` | integer | no | no |
| `node_results_json` | mediumtext | yes | no |
| `all_valid` | boolean | yes | yes |

## `dna_carry_encodings` (DNA_Carry_Encodings)

| Column | Type | Required | Index |
|--------|------|----------|-------|
| `session_id` | varchar(36) | yes | yes |
| `dna` | mediumtext | yes | prefix |
| `trits_json` | mediumtext | yes | no |
| `encode_log_json` | longtext | no | no |

## `gjb2_profiles`

| Column | Type | Required | Index |
|--------|------|----------|-------|
| `session_id` | varchar(36) | yes | yes |
| `name` | varchar(255) | yes | no |
| `description` | text | no | no |

## `gjb2_results` (GJB2_Results)

| Column | Type | Required | Index |
|--------|------|----------|-------|
| `session_id` | varchar(36) | yes | yes |
| `profile_id` | varchar(36) | no | yes |
| `deletion_pos_1` | integer | yes | yes |
| `wt_encoding_id` | varchar(36) | no | yes |
| `mut_encoding_id` | varchar(36) | no | yes |
| `tree_run_id` | varchar(36) | no | yes |
| `summary` | text | no | no |

## `acoustic_sonifications` (AcousticSonifications)

| Column | Type | Required | Index |
|--------|------|----------|-------|
| `session_id` | varchar(36) | yes | yes |
| `title` | varchar(255) | yes | no |
| `trits_json` | mediumtext | yes | no |
| `sample_rate_hz` | integer | yes | no |
| `normalised` | boolean | yes | no |
| `metrics_json` | mediumtext | no | no |
| `wav_file_id` | varchar(36) | no | yes |

## `phonon_wavepackets` (PhononWavepackets)

| Column | Type | Required | Index |
|--------|------|----------|-------|
| `sonification_id` | varchar(36) | yes | yes |
| `atom_index` | integer | yes | yes |
| `trit` | integer | yes | no |
| `carrier_hz` | float | yes | no |
| `feature_json` | text | no | no |

## `quantum_scheduling_runs`

| Column | Type | Required | Index |
|--------|------|----------|-------|
| `session_id` | varchar(36) | yes | yes |
| `fidelities_json` | mediumtext | yes | no |
| `valid` | boolean | yes | yes |
| `trajectory_json` | mediumtext | no | no |

## `methylation_island_runs`

| Column | Type | Required | Index |
|--------|------|----------|-------|
| `session_id` | varchar(36) | yes | yes |
| `betas_json` | mediumtext | yes | no |
| `valid` | boolean | yes | yes |
| `trajectory_json` | mediumtext | no | no |

## `overlay_snapshots`

| Column | Type | Required | Index |
|--------|------|----------|-------|
| `session_id` | varchar(36) | yes | yes |
| `overlay_kind` | enum | yes | yes |
| `payload_json` | mediumtext | yes | no |

## `methylation_profiles`

| Column | Type | Required | Index |
|--------|------|----------|-------|
| `session_id` | varchar(36) | yes | yes |
| `label` | varchar(255) | yes | no |
| `beta_list_json` | mediumtext | yes | no |

## `tme_artifacts`

| Column | Type | Required | Index |
|--------|------|----------|-------|
| `session_id` | varchar(36) | yes | yes |
| `stream` | mediumtext | yes | no |
| `storage_file_id` | varchar(36) | no | no |

## `realtime_topics`

| Column | Type | Required | Index |
|--------|------|----------|-------|
| `session_id` | varchar(36) | yes | yes |
| `appwrite_topic_id` | varchar(255) | yes | no |
| `purpose` | varchar(128) | no | no |

## Indexes and Realtime

- Add composite keys on `(session_id, $createdAt)` for list UIs.
- Use **Realtime** subscriptions filtered by `session_id` (never subscribe unfiltered to large tables).

## Permissions (snippet)

```text
read("user:$userId")
create("user:$userId")
update("user:$userId")
delete("user:$userId")
```
