# SDK

The **Appwrite integration** for this repo is the Python package
**`mcore_appwrite`** under **`src/mcore_appwrite/`** (installed with the rest of
`mcore-py` from `src/`).

| Module | Role |
|--------|------|
| `mcore_appwrite.config` | `AppwriteConfig.from_env()`, `use_remote_check_tree()` |
| `mcore_appwrite.client` | `build_admin_client()` |
| `mcore_appwrite.executor` | `execute_check_tree_function()` |

There is no separate npm/TypeScript SDK in this repository; use
`appwrite generate` for typed web clients against your TablesDB schema
(**`docs/APPWRITE_DATABASE_SCHEMA.md`**).
