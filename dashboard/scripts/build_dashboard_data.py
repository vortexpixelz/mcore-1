#!/usr/bin/env python3
"""Build Symonic Trust Dashboard JSON from repo-local artifacts.

This script is intentionally stdlib-only so it can run in Codespaces, CI,
local shells, and low-friction agent environments.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "dashboard" / "data"
CLAIMS_PATHS = [ROOT / "docs" / "CLAIMS.md", ROOT / "CLAIMS.md"]
RECEIPTS_DIR = ROOT / "receipts"

CLAIM_TIERS = ["ESTABLISHED", "PLAUSIBLE", "CONJECTURAL", "ORNAMENTAL", "ASK"]
OVERCLAIM_WORDS = ["prove", "proves", "proven", "demonstrates", "guarantees", "solves"]


@dataclass
class RepoState:
    head_sha: str | None
    branch: str | None
    dirty: bool
    generated_at: str


def run(cmd: list[str]) -> str | None:
    try:
        return subprocess.check_output(cmd, cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def count_claim_tiers(text: str) -> dict[str, int]:
    counts = {tier: 0 for tier in CLAIM_TIERS}
    for tier in CLAIM_TIERS:
        # Match [ESTABLISHED], **ESTABLISHED**, plain headings, and tier labels.
        counts[tier] = len(re.findall(rf"(?i)(?:\[|\b){re.escape(tier)}(?:\]|\b)", text))
    return counts


def collect_receipts() -> dict[str, Any]:
    receipts: list[dict[str, Any]] = []
    if RECEIPTS_DIR.exists():
        for path in sorted(RECEIPTS_DIR.glob("*.md")):
            stat = path.stat()
            text = read_text(path)
            receipts.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "name": path.name,
                    "bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                    "tier_counts": count_claim_tiers(text),
                    "direct_fetch_mentions": len(re.findall(r"(?i)direct[- ]fetch|sha|receipt", text)),
                }
            )
    latest = max((r["modified_at"] for r in receipts), default=None)
    return {"count": len(receipts), "latest_modified_at": latest, "items": receipts}


def lint_claim_language(text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        lower = line.lower()
        if any(f"[{tier.lower()}]" in lower for tier in ("ESTABLISHED",)):
            continue
        for word in OVERCLAIM_WORDS:
            if re.search(rf"\b{re.escape(word)}\b", lower):
                findings.append(
                    {
                        "line": line_no,
                        "word": word,
                        "text": line[:240],
                        "severity": "review",
                    }
                )
    return findings


def repo_state() -> RepoState:
    head_sha = run(["git", "rev-parse", "HEAD"])
    branch = run(["git", "branch", "--show-current"])
    dirty = bool(run(["git", "status", "--porcelain"]))
    return RepoState(
        head_sha=head_sha,
        branch=branch,
        dirty=dirty,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def discover_tests() -> dict[str, Any]:
    tests_dir = ROOT / "tests"
    if not tests_dir.exists():
        return {"tests_dir_exists": False, "python_test_files": 0}
    files = sorted(tests_dir.glob("test_*.py"))
    return {
        "tests_dir_exists": True,
        "python_test_files": len(files),
        "sample": [str(p.relative_to(ROOT)) for p in files[:12]],
    }


def build() -> dict[str, Any]:
    claims_path = first_existing(CLAIMS_PATHS)
    claims_text = read_text(claims_path) if claims_path else ""
    claim_counts = count_claim_tiers(claims_text)
    lint_findings = lint_claim_language(claims_text)
    receipts = collect_receipts()
    state = asdict(repo_state())
    tests = discover_tests()

    total_claims = sum(claim_counts.values())
    established = claim_counts.get("ESTABLISHED", 0)
    trust_score = 0
    if total_claims:
        trust_score += min(40, round(40 * established / max(total_claims, 1)))
    trust_score += 20 if receipts["count"] else 0
    trust_score += 20 if tests.get("python_test_files", 0) else 0
    trust_score += 10 if not lint_findings else max(0, 10 - len(lint_findings))
    trust_score += 10 if not state["dirty"] else 0

    return {
        "schema_version": "symonic.trust.v0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": state,
        "claims": {
            "source_path": str(claims_path.relative_to(ROOT)) if claims_path else None,
            "tier_counts": claim_counts,
            "total": total_claims,
            "overclaim_lint_findings": lint_findings,
        },
        "receipts": receipts,
        "tests": tests,
        "trust_score": {
            "score": trust_score,
            "max_score": 100,
            "label": "early scaffold",
            "components": {
                "established_claim_ratio": "up to 40",
                "receipt_presence": "20",
                "test_presence": "20",
                "overclaim_lint_cleanliness": "10",
                "clean_worktree": "10",
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DATA_DIR / "trust_state.json")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = build()
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
