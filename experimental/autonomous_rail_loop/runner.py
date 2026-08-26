"""Bounded autonomous-loop experiment for MCORE-1.

The experiment deliberately begins with a bad proposal and lets a deterministic
agent revise one violation per turn. The rail uses the existing MCORE-1
``check_tree`` invariant for claim/evidence conservation, plus explicit policy
checks for secret-bearing files, transform allow-lists, and promotion state.

This is an experiment, not a claim that MCORE-1 already provides a complete
agent-control plane.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Literal

from mcore_py.checker import check_tree
from mcore_py.model import Constituent, Level, ProsodicUnit, Trit

Decision = Literal["ALLOW", "REVISE", "BLOCK"]
PromotionState = Literal["DEV", "INFORM", "PORTAL"]

ALLOWED_TRANSFORMS = {"bounded-copy-v1", "evidence-summarize-v1"}
SECRET_NAME_RE = re.compile(r"(?i)(?:api[_-]?key|token|secret|password|private[_-]?key)")
ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
PLACEHOLDERS = {"", "changeme", "example", "placeholder", "replace-me", "<redacted>"}


@dataclass(frozen=True)
class Evidence:
    label: str
    strength: Trit
    source_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "strength": self.strength.name,
            "source_hash": self.source_hash,
        }


@dataclass(frozen=True)
class Proposal:
    iteration: int
    claim: str
    claim_strength: Trit
    evidence: tuple[Evidence, ...]
    changed_files: tuple[tuple[str, str], ...]
    transform_id: str
    requested_state: PromotionState

    def files(self) -> dict[str, str]:
        return dict(self.changed_files)

    def to_dict(self, *, redact: bool = True) -> dict[str, Any]:
        files: dict[str, str] = {}
        for path, content in self.changed_files:
            files[path] = redact_content(content) if redact else content
        return {
            "iteration": self.iteration,
            "claim": self.claim,
            "claim_strength": self.claim_strength.name,
            "evidence": [item.to_dict() for item in self.evidence],
            "changed_files": files,
            "transform_id": self.transform_id,
            "requested_state": self.requested_state,
        }


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Literal["INFO", "REVISE", "BLOCK"]
    message: str
    artifact: str | None = None
    fingerprint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "artifact": self.artifact,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True)
class Receipt:
    iteration: int
    parent_receipt_hash: str | None
    proposal_hash: str
    decision: Decision
    requested_state: PromotionState
    permitted_state: PromotionState | None
    findings: tuple[Finding, ...]
    receipt_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "iteration": self.iteration,
            "parent_receipt_hash": self.parent_receipt_hash,
            "proposal_hash": self.proposal_hash,
            "decision": self.decision,
            "requested_state": self.requested_state,
            "permitted_state": self.permitted_state,
            "findings": [finding.to_dict() for finding in self.findings],
            "receipt_hash": self.receipt_hash,
        }


@dataclass(frozen=True)
class LoopResult:
    proposals: tuple[Proposal, ...]
    receipts: tuple[Receipt, ...]

    @property
    def final_receipt(self) -> Receipt:
        return self.receipts[-1]


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def redact_content(content: str) -> str:
    redacted_lines: list[str] = []
    for line in content.splitlines():
        match = ASSIGNMENT_RE.match(line)
        if match and SECRET_NAME_RE.search(match.group(1)):
            redacted_lines.append(f"{match.group(1)}=<redacted>")
        else:
            redacted_lines.append(line)
    return "\n".join(redacted_lines)


def _is_protected_env_path(path: str) -> bool:
    name = Path(path).name
    return name == ".env" or (name.startswith(".env.") and name != ".env.example")


def _secret_findings(path: str, content: str) -> list[Finding]:
    findings: list[Finding] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        match = ASSIGNMENT_RE.match(line)
        if not match:
            continue
        variable, value = match.groups()
        normalized_value = value.strip().strip("'\"").lower()
        if SECRET_NAME_RE.search(variable) and normalized_value not in PLACEHOLDERS:
            findings.append(
                Finding(
                    code="SECRET_VALUE_PRESENT",
                    severity="BLOCK",
                    message=f"Secret-like value assigned at line {line_number}; value omitted.",
                    artifact=path,
                    fingerprint=canonical_hash({"path": path, "line": line_number, "value": value}),
                )
            )
    return findings


def _claim_conservation_findings(proposal: Proposal) -> list[Finding]:
    if not proposal.evidence:
        return [
            Finding(
                code="EVIDENCE_MISSING",
                severity="BLOCK",
                message="The claim has no evidence children and cannot be checked for conservation.",
            )
        ]

    tree = Constituent(
        parent=ProsodicUnit(
            weight=proposal.claim_strength,
            level=Level.L2_GANA,
            label="claim",
        ),
        children=[
            ProsodicUnit(
                weight=evidence.strength,
                level=Level.L1_AKSARA,
                label=evidence.label,
            )
            for evidence in proposal.evidence
        ],
    )
    result = check_tree(tree)
    if result.valid:
        return []

    return [
        Finding(
            code=f"MCORE_{error.kind.name}",
            severity="REVISE",
            message=error.message,
            artifact="claim/evidence tree",
        )
        for error in result.errors
    ]


def _promotion_findings(proposal: Proposal) -> list[Finding]:
    if proposal.requested_state != "PORTAL":
        return []

    distinct_sources = {evidence.source_hash for evidence in proposal.evidence}
    if proposal.claim_strength == Trit.S3 and len(distinct_sources) >= 2:
        return []

    return [
        Finding(
            code="PORTAL_EVIDENCE_GATE",
            severity="REVISE",
            message="PORTAL requires an S3 claim backed by at least two distinct evidence sources.",
        )
    ]


def evaluate(proposal: Proposal, parent_receipt_hash: str | None) -> Receipt:
    findings: list[Finding] = []

    for path, content in proposal.changed_files:
        if _is_protected_env_path(path):
            findings.append(
                Finding(
                    code="PROTECTED_ENV_PATH",
                    severity="BLOCK",
                    message="Runtime environment files cannot enter an agent-authored change set.",
                    artifact=path,
                )
            )
        findings.extend(_secret_findings(path, content))

    if proposal.transform_id not in ALLOWED_TRANSFORMS:
        findings.append(
            Finding(
                code="UNSUPPORTED_TRANSFORM_ID",
                severity="BLOCK",
                message=f"Transform {proposal.transform_id!r} is not in the bounded allow-list.",
            )
        )

    findings.extend(_claim_conservation_findings(proposal))
    findings.extend(_promotion_findings(proposal))

    severities = {finding.severity for finding in findings}
    if "BLOCK" in severities:
        decision: Decision = "BLOCK"
        permitted_state: PromotionState | None = None
    elif "REVISE" in severities:
        decision = "REVISE"
        permitted_state = "DEV"
    else:
        decision = "ALLOW"
        permitted_state = proposal.requested_state

    proposal_hash = canonical_hash(proposal.to_dict(redact=True))
    receipt_body = {
        "iteration": proposal.iteration,
        "parent_receipt_hash": parent_receipt_hash,
        "proposal_hash": proposal_hash,
        "decision": decision,
        "requested_state": proposal.requested_state,
        "permitted_state": permitted_state,
        "findings": [finding.to_dict() for finding in findings],
    }
    return Receipt(
        iteration=proposal.iteration,
        parent_receipt_hash=parent_receipt_hash,
        proposal_hash=proposal_hash,
        decision=decision,
        requested_state=proposal.requested_state,
        permitted_state=permitted_state,
        findings=tuple(findings),
        receipt_hash=canonical_hash(receipt_body),
    )


class BoundedAgent:
    """Deterministic agent that fixes exactly one receipt class per iteration."""

    def initial_proposal(self) -> Proposal:
        evidence = Evidence(
            label="one deterministic local fixture",
            strength=Trit.S1,
            source_hash=canonical_hash("fixture-001"),
        )
        return Proposal(
            iteration=1,
            claim="MCORE-1 proves autonomous AI work is safe.",
            claim_strength=Trit.S3,
            evidence=(evidence,),
            changed_files=((".env", "OPENAI_API_KEY=demo-secret-not-real"),),
            transform_id="freeform-agent-v9",
            requested_state="PORTAL",
        )

    def revise(self, proposal: Proposal, receipt: Receipt) -> Proposal:
        codes = {finding.code for finding in receipt.findings}
        next_iteration = proposal.iteration + 1

        if "PROTECTED_ENV_PATH" in codes or "SECRET_VALUE_PRESENT" in codes:
            return replace(
                proposal,
                iteration=next_iteration,
                changed_files=((".env.example", "OPENAI_API_KEY=<redacted>"),),
            )

        if "UNSUPPORTED_TRANSFORM_ID" in codes:
            return replace(
                proposal,
                iteration=next_iteration,
                transform_id="bounded-copy-v1",
            )

        if any(code.startswith("MCORE_") or code == "EVIDENCE_MISSING" for code in codes):
            return replace(
                proposal,
                iteration=next_iteration,
                claim="One deterministic fixture completed the bounded MCORE rail loop.",
                claim_strength=Trit.S1,
            )

        if "PORTAL_EVIDENCE_GATE" in codes:
            return replace(
                proposal,
                iteration=next_iteration,
                requested_state="INFORM",
            )

        return replace(proposal, iteration=next_iteration)


def run_autonomous_loop(max_loops: int = 6) -> LoopResult:
    if max_loops < 1:
        raise ValueError("max_loops must be at least 1")

    agent = BoundedAgent()
    proposal = agent.initial_proposal()
    proposals: list[Proposal] = []
    receipts: list[Receipt] = []
    parent_hash: str | None = None

    for _ in range(max_loops):
        receipt = evaluate(proposal, parent_hash)
        proposals.append(proposal)
        receipts.append(receipt)
        if receipt.decision == "ALLOW":
            break
        parent_hash = receipt.receipt_hash
        proposal = agent.revise(proposal, receipt)

    return LoopResult(tuple(proposals), tuple(receipts))


def verify_receipt_chain(receipts: Iterable[Receipt]) -> bool:
    previous: str | None = None
    for receipt in receipts:
        if receipt.parent_receipt_hash != previous:
            return False
        body = {
            "iteration": receipt.iteration,
            "parent_receipt_hash": receipt.parent_receipt_hash,
            "proposal_hash": receipt.proposal_hash,
            "decision": receipt.decision,
            "requested_state": receipt.requested_state,
            "permitted_state": receipt.permitted_state,
            "findings": [finding.to_dict() for finding in receipt.findings],
        }
        if receipt.receipt_hash != canonical_hash(body):
            return False
        previous = receipt.receipt_hash
    return True


def write_artifacts(result: LoopResult, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    with (output_dir / "receipts.jsonl").open("w", encoding="utf-8") as handle:
        for proposal, receipt in zip(result.proposals, result.receipts):
            handle.write(
                json.dumps(
                    {"proposal": proposal.to_dict(redact=True), "receipt": receipt.to_dict()},
                    sort_keys=True,
                    ensure_ascii=False,
                )
                + "\n"
            )

    lines = [
        "# MCORE-1 autonomous rail loop v0",
        "",
        f"Loops executed: {len(result.receipts)}",
        f"Receipt chain valid: {verify_receipt_chain(result.receipts)}",
        f"Final decision: {result.final_receipt.decision}",
        f"Final permitted state: {result.final_receipt.permitted_state}",
        "",
        "| Loop | Decision | Requested | Permitted | Findings |",
        "|---:|---|---|---|---|",
    ]
    for receipt in result.receipts:
        finding_codes = ", ".join(finding.code for finding in receipt.findings) or "none"
        lines.append(
            f"| {receipt.iteration} | {receipt.decision} | {receipt.requested_state} | "
            f"{receipt.permitted_state or 'none'} | {finding_codes} |"
        )
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "This run demonstrates a bounded, deterministic control loop using the existing ",
            "MCORE-1 tree checker as one rail. It does not establish safety, general autonomy, ",
            "or semantic truth checking.",
            "",
        ]
    )
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-loops", type=int, default=6)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/autonomous-rail-loop"))
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = run_autonomous_loop(max_loops=args.max_loops)
    write_artifacts(result, args.output_dir)
    print((args.output_dir / "summary.md").read_text(encoding="utf-8"))
    return 0 if result.final_receipt.decision == "ALLOW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
