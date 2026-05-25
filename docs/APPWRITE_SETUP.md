# Appwrite setup (`appwrite init`)

Follow [Appwrite CLI](https://appwrite.io/docs/tooling/command-line/installation) installation, then:

## 1. Login

```bash
appwrite login
# Self-hosted:
# appwrite login --endpoint "https://your-instance.com/v1"
```

## 2. Initialize project config

From the repository root:

```bash
appwrite init project
```

This creates `appwrite.config.json`. Compare with `appwrite/appwrite.config.json.example` and merge the `tablesDB`, `tables`, `functions`, and `buckets` sections.

## 3. Create the database and tables

```bash
appwrite init tables
# Or define tables in appwrite.config.json and:
appwrite push tables --all --force
```

Use column types from [APPWRITE_DATABASE_SCHEMA.md](./APPWRITE_DATABASE_SCHEMA.md). Prefer **`varchar`** for indexed short strings and **`mediumtext`** for JSON payloads.

## 4. API keys

In Appwrite Console: **Settings → API keys**. Create a key with scopes:

- `tables.read`, `tables.write` (or legacy equivalent for your server role)
- `functions.read`, `functions.write` (if the MCP server triggers executions server-side)

Never expose the **admin key** to browser clients. For MCP on a developer machine, a **scoped server key** in `.env` is acceptable; rotate regularly.

## 5. Functions

```bash
appwrite init functions
```

Point the `path` field at `functions/check_tree` (see example config). Set:

- **Runtime:** `python-3.12` (or latest supported `python-*` in your region; run `appwrite functions list-runtimes`).
- **Entrypoint:** `src/main.py`
- **Build commands:** install dependencies; see `functions/check_tree/README.md` for vendoring `src/mcore_py` and `src/mcore_1`.

Deploy:

```bash
appwrite push functions --all --force
```

## 6. Local function run (optional)

```bash
appwrite run functions
```

## 7. Typed client generation (MCP-for-API synergy)

```bash
appwrite generate --language typescript --output ./clients/generated
```

Use the generated client in web apps; keep **this repo’s** `mcore-mcp` for LLM-facing domain tools.

## 8. PostHog (optional)

Set `POSTHOG_API_KEY` and `POSTHOG_HOST` in the environment where `mcore-mcp` or Functions run. See `.env.example`.
