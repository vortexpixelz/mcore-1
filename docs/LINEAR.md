# Linear ↔ GitHub workflow (Symonic / MCORE)

This repo does **not** configure Linear automatically. Use this doc as the **checklist** for whoever admins the Linear workspace and the `vortexpixelz` GitHub org.

## 1. Connect GitHub (org or repo admin)

1. In Linear: **Settings → Integrations → [GitHub](https://linear.app/settings/integrations/github)** → **Enable**.
2. Choose the GitHub org and repositories (include **`mcore-1`** and any related repos).
3. Each developer: **Settings → Connected accounts** → connect personal GitHub so PRs map to the right person.

Official reference: [Linear — GitHub](https://linear.app/docs/github).

## 2. Optional: commit linking (webhook)

If you want **commits** (not only PRs) to move issues:

1. In Linear’s GitHub integration page, turn on **Link commits to issues with magic words**.
2. In GitHub **Settings → Webhooks**, add the payload URL and secret Linear provides; enable **Push events**.

## 3. Link issues to PRs (daily workflow)

Pick **one** of these (Linear recognizes them):

| Method | Example |
|--------|---------|
| **Branch name** | `vor-117-mcore-1-check` — use **Copy git branch name** on the issue (`Cmd/Ctrl+Shift+.`). |
| **PR title** | `VOR-117 Add notebook taxonomy` |
| **PR description** | `Fixes VOR-117` or `Ref VOR-117` (closing vs non-closing magic words — [docs](https://linear.app/docs/github#link-through-pull-requests)). |

Use your team’s real **issue ID prefix** (Symonic solo dev env uses **`VOR`**).

## 4. GitHub Autolink (optional)

So `VOR-123` in PR bodies becomes a link:

- Repo **Settings → General → Autolink references** → add reference URL:  
  `https://linear.app/vortexpixel-solo-dev-env/issue/VOR-<num>/`  
  ([Autolink](https://linear.app/docs/github#enable-autolink); adjust the workspace slug if you rename it.)

## 5. Suggested Linear structure (MCORE / research)

| Label / project | Use for |
|-----------------|--------|
| `spec` | MCORE-1 spec / encoding / conformance |
| `research` | SPARC, notebooks, falsifiable experiments |
| `ci` | Actions, packaging, ruff/pytest |
| `grant` | Narrative / supplements (no code) |

Tune to your real teams; this is a **starting convention**.

## 6. Branch naming with Cursor agents

Cloud/agent branches often look like `cursor/feature-8f62`. Linear will not see the issue ID in the branch unless you paste it — put **`VOR-___`** in the **PR title or description** (see §3).

## 7. Paper / repo checklist (Linear)

Track submission engineering and cross-repo checks as **Linear issues**, not only in chat.

- **VOR-117 — mcore-1 check** — [open in Linear](https://linear.app/vortexpixel-solo-dev-env/issue/VOR-117/mcore-1-check). In-repo companion: **[VOR-117 repository audit](VOR-117_REPOSITORY_AUDIT.md)** (four-bucket sprint: Formal / Experimental / Empirical / Interpretive).
- Notebook discipline (taxonomy, observation vs interpretation): [notebooks/README.md](../notebooks/README.md)

## 8. What we cannot do from this repository

- Create your Linear workspace, teams, or API keys.
- Install the GitHub app (requires GitHub **admin** / org owner as appropriate).

If integration breaks, Linear’s FAQ recommends disconnecting on GitHub, visiting `https://linear.app/reset`, then reconnecting — see [GitHub integration FAQ](https://linear.app/docs/github#faq).
