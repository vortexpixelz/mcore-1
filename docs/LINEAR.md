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
| **Branch name** | `sym-42-add-cli-smoke` — use **Copy git branch name** on the issue (`Cmd/Ctrl+Shift+.`). |
| **PR title** | `SYM-42 Add CLI smoke test` |
| **PR description** | `Fixes SYM-42` or `Ref SYM-42` (closing vs non-closing magic words — [docs](https://linear.app/docs/github#link-through-pull-requests)). |

Replace **`SYM`** with your team’s **issue ID prefix** from Linear (e.g. `ENG`, `MCORE`).

## 4. GitHub Autolink (optional)

So `SYM-123` in PR bodies becomes a link:

- Repo **Settings → General → Autolink references** → add reference URL:  
  `https://linear.app/<your-workspace>/issue/SYM-<num>`  
  (Linear documents the exact pattern per team: [Autolink](https://linear.app/docs/github#enable-autolink).)

## 5. Suggested Linear structure (MCORE / research)

| Label / project | Use for |
|-----------------|--------|
| `spec` | MCORE-1 spec / encoding / conformance |
| `research` | SPARC, notebooks, falsifiable experiments |
| `ci` | Actions, packaging, ruff/pytest |
| `grant` | Narrative / supplements (no code) |

Tune to your real teams; this is a **starting convention**.

## 6. Branch naming with Cursor agents

Cloud/agent branches often look like `cursor/feature-8f62`. To still link Linear:

- Put **`SYM-123`** in the **PR title or description** even if the branch name does not include it.

## 7. What we cannot do from this repository

- Create your Linear workspace, teams, or API keys.
- Install the GitHub app (requires GitHub **admin** / org owner as appropriate).

If integration breaks, Linear’s FAQ recommends disconnecting on GitHub, visiting `https://linear.app/reset`, then reconnecting — see [GitHub integration FAQ](https://linear.app/docs/github#faq).
