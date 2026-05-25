# Deploying the MCORE-1 MCP server on a VPS (Hetzner or similar)

This guide targets the **FastMCP** entrypoint in `src/mcore_mcp/server.py`: full Python environment, no Appwrite Open Runtime limits, and optional **hybrid** delegation to `mcore_check_tree` via env vars.

## What you are running

| Mode | Command | Typical use |
|------|-----------|-------------|
| **stdio** (default) | `python -m mcore_mcp.server` | Claude Desktop, Cursor, or any client that spawns a subprocess |
| **streamable-http** | `python -m mcore_mcp.server --transport streamable-http --host 127.0.0.1 --port 8765` | HTTP-aware MCP clients, reverse proxy, or Cloudflare Tunnel in front of localhost |

After `pip install -e ".[mcp]"`, the console script `mcore-mcp` is equivalent to `python -m mcore_mcp.server`.

## 1. Server setup (once per machine)

Use Python **3.10+** (project requires `>=3.10`; 3.11 or 3.12 is fine).

```bash
sudo mkdir -p /opt/mcore1 && sudo chown "$USER":"$USER" /opt/mcore1
cd /opt/mcore1
git clone https://github.com/vortexpixelz/mcore-1.git repo
cd repo
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip wheel
pip install -e ".[mcp]"
```

Confirm:

```bash
mcore-mcp --help
# or: python -m mcore_mcp.server --help
```

## 2. Environment file (secrets)

Create a root-only env file (adjust paths if not using `/opt/mcore1`):

```bash
sudo install -m 600 /dev/null /etc/mcore-mcp.env
sudo chown mcore:mcore /etc/mcore-mcp.env   # if you use a dedicated user
```

Populate from `.env.example` in the repo. Minimal **local-only** MCP (no Appwrite):

```bash
# optional analytics
# POSTHOG_API_KEY=
# POSTHOG_HOST=https://us.i.posthog.com
```

**Hybrid** (MCP on VPS, heavy `check_tree` ops hit Appwrite):

```bash
APPWRITE_ENDPOINT=https://<REGION>.cloud.appwrite.io/v1
APPWRITE_PROJECT_ID=...
APPWRITE_API_KEY=...          # server key — never expose to browsers
APPWRITE_FUNCTION_CHECK_TREE_ID=...
APPWRITE_USE_FUNCTIONS=true
```

When `APPWRITE_USE_FUNCTIONS` is unset or false, `mcore_check_tree_weights`, `mcore_check_tree_dna`, and `mcore_check_deletion` run **in-process** on the VPS (see `src/mcore_mcp/delegate.py`).

## 3. systemd (recommended for always-on)

Example unit: bind HTTP transport to **loopback** only; expose the internet via Tunnel or nginx, not by opening `8765` publicly.

`/etc/systemd/system/mcore-mcp.service`:

```ini
[Unit]
Description=MCORE-1 FastMCP (streamable-http on localhost)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=mcore
Group=mcore
WorkingDirectory=/opt/mcore1/repo
EnvironmentFile=-/etc/mcore-mcp.env
ExecStart=/opt/mcore1/repo/.venv/bin/python -m mcore_mcp.server \
  --transport streamable-http --host 127.0.0.1 --port 8765
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mcore-mcp.service
sudo systemctl status mcore-mcp.service
```

For **stdio** under systemd you normally do *not* use a long-running unit; instead the MCP client runs `ssh user@host /opt/mcore1/repo/.venv/bin/python -m mcore_mcp.server` (see below).

## 4. Expose HTTP safely

### Option A — Cloudflare Tunnel (no inbound ports on VPS)

Install `cloudflared` on the VPS. Point a private hostname at the local MCP port:

```yaml
# ~/.cloudflared/config.yml (illustrative)
tunnel: <your-tunnel-id>
credentials-file: /home/mcore/.cloudflared/<id>.json

ingress:
  - hostname: mcore-mcp.example.com
    service: http://127.0.0.1:8765
  - service: http_status:404
```

Add **Cloudflare Access** (or mTLS) so the MCP URL is not world-scannable. Your MCP client must support the same HTTP transport FastMCP advertises (`streamable-http`).

### Option B — nginx + TLS on the VPS

Terminate TLS in nginx and `proxy_pass http://127.0.0.1:8765;` with appropriate timeouts (MCP sessions can be long-lived). Keep `8765` firewalled from the public internet.

## 5. Connecting from Cursor (or other clients)

**stdio (simplest, no tunnel):** configure the MCP server as a subprocess. If the IDE runs on your laptop and the code runs on Hetzner, use SSH:

```json
{
  "mcpServers": {
    "mcore-1": {
      "command": "ssh",
      "args": [
        "-T",
        "mcore@YOUR_VPS_HOST",
        "/opt/mcore1/repo/.venv/bin/python",
        "-m",
        "mcore_mcp.server"
      ]
    }
  }
}
```

Use a **deploy key** or normal SSH key; prefer a dedicated `mcore` user with forced command or `Match User` restrictions if you harden further.

**streamable-http:** if your client supports remote MCP over HTTP, point it at your tunnel or nginx URL. Verify transport compatibility with your client version; when in doubt, use **stdio over SSH** first.

## 6. Docker (optional)

Minimal pattern: mount env file read-only, publish only if you must (prefer loopback + tunnel).

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e ".[mcp]"
EXPOSE 8765
CMD ["python", "-m", "mcore_mcp.server", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8765"]
```

Binding `0.0.0.0` is convenient in Docker but should sit **behind** a reverse proxy or host firewall, not directly on the raw internet.

## 7. Operations checklist

- [ ] `pip install -e ".[mcp]"` succeeds (pulls `fastmcp`, `appwrite`, `numpy`, optional `posthog`).
- [ ] Secrets only in `/etc/mcore-mcp.env` (mode `600`) or your secret manager.
- [ ] If using Appwrite delegation, `APPWRITE_FUNCTION_CHECK_TREE_ID` matches the deployed `mcore_check_tree` function.
- [ ] Health: `journalctl -u mcore-mcp -f` shows no crash loop; for HTTP, `curl -v http://127.0.0.1:8765/` may return a framework-specific response (404 on `/` is common; use client handshake paths per FastMCP / client docs).
- [ ] After git pulls, restart: `sudo systemctl restart mcore-mcp`.

## 8. Why this is faster than Appwrite-only

The same tool surface runs as a normal Python process: no deployment bundle vendoring, no Open Runtime response-body quirks, and straightforward logs. You can still call the Appwrite function from tools (`mcore_appwrite_exec_check_tree`) or transparent delegation when `APPWRITE_USE_FUNCTIONS=true`.
