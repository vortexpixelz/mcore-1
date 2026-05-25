# `mcore_appwrite`

Small **server-side** helpers for Appwrite (admin API key). Used by the MCP
server when delegating to Functions or when you add persistence in your own
gateway.

- `AppwriteConfig.from_env()` — reads `APPWRITE_ENDPOINT`, `APPWRITE_PROJECT_ID`, `APPWRITE_API_KEY`, optional `APPWRITE_FUNCTION_CHECK_TREE_ID`
- `build_admin_client(cfg)` — `Client` with endpoint `/v1`
- `execute_check_tree_function(cfg, payload)` — `Functions.create_execution` + JSON parse of `responseBody`

Do **not** ship the API key to browsers; use session clients in SSR per Appwrite docs.
