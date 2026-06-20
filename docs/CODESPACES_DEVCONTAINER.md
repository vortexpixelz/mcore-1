# GitHub Codespaces and Dev Containers

The repo includes **`.devcontainer/devcontainer.json`**, which works in:

1. **GitHub Codespaces** (cloud dev environment)
2. **VS Code or Cursor** with the **Dev Containers** extension (local Docker)

## GitHub Codespaces

1. Open the repository on GitHub.
2. Click **Code** → **Codespaces** → **Create codespace on main** (or your branch).
3. Wait for the container to build. The **`postCreateCommand`** installs the package in editable mode with MCP and dev extras: `pip install -e ".[mcp,dev]"`.

**Optional Appwrite / analytics:** create a `.env` in the repo root (gitignored) or set Codespace **secrets** and export them in your shell profile — see `.env.example`.

### MCP inside a Codespace

- **stdio (typical for Cursor / Claude-style clients):** run the server as a subprocess from the client, with the working directory set to the repository root, for example:

  ```bash
  python -m mcore_mcp.server
  ```

  In Cursor, use an MCP config entry with `command` + `args` (and optionally `cwd` pointing at your Codespace checkout if the client runs outside the container).

- **streamable-http:** in a terminal inside the Codespace:

  ```bash
  python -m mcore_mcp.server --transport streamable-http --host 127.0.0.1 --port 8765
  ```

  Port **8765** is listed in `forwardPorts`; when the server starts, use the **Ports** tab to open or copy the forwarded URL. Your MCP client must support the same HTTP transport as FastMCP.

## Local machine: Dev Containers extension

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or another OCI runtime Dev Containers can use).
2. Install the **Dev Containers** extension (`ms-vscode-remote.remote-containers`) in VS Code or Cursor.
3. **Clone** the repository locally and open the folder.
4. Command Palette (**F1**) → **Dev Containers: Reopen in Container**.
5. After build, the same `pip install` runs as in Codespaces.

The optional **Docker** extension in `devcontainer.json` is for browsing images/containers from inside the dev environment; it is not required for the container to run.

## Troubleshooting

- **`pip install` fails in postCreate:** open a terminal in the container and run  
  `python -m pip install -e ".[mcp,dev]"`  
  manually and read the error (network, compiler for a rare wheel build, etc.).
- **Wrong Python:** the image pins Python 3.12; the interpreter path is `/usr/local/bin/python` (see `customizations` in `devcontainer.json`).
