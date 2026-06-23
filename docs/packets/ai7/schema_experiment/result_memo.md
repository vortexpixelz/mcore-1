---
experiment_id: AI7_SCHEMA_SELECTION_2026_06
schema_version: 0.1
status: complete
date_completed: 2026-06-23
winner: B_research_ledger
---

# Result Memo

## Question

Which packet schema best preserves Bundle 1 as useful research memory while producing a
judgeable AI7 next action?

## Method

One source bundle (Bundle 1: early AI7 / MCORE-cascade-eval research notes) was backfilled
into all four schemas (A: Minimal Grant, B: Research Ledger, C: Table Flip, D: Cockpit).
Each schema was then scored 1–10 on seven criteria using the same rubric:
easy_to_fill, retrieval_quality, compression_quality, claim_discipline, actionability,
reviewer_readiness, reuse_potential. Scores and notes are in `scorecard.yaml`.

Claim-tier separation used throughout: ESTABLISHED / PLAUSIBLE / CONJECTURAL / FORBIDDEN.

## Results

| Schema | Avg Score | Standout | Weakness |
|--------|-----------|----------|----------|
| A: Minimal Grant | 7.0 | reviewer_readiness (8), actionability (8) | claim_discipline (5) |
| B: Research Ledger | 7.9 | claim_discipline (9), reuse_potential (9) | reviewer_readiness (6) |
| C: Table Flip | 7.4 | claim_discipline (10), retrieval_quality (8) | reviewer_readiness (5) |
| D: Cockpit | 6.4 | actionability (9) | reviewer_readiness (4), compression (6) |

No schema scored below 6 on any criterion. All four schemas produced a usable next action.
Schema B produced the highest average and the most balanced profile.

## Winner

**Schema B: Research Ledger Packet** is the provisional winner for Bundle 1 under this rubric.

Reasoning:
- Claim discipline (9) is the most important property for a pre-publication, funding-adjacent
  research bundle. Schema B's observation/interpretation/hypothesis triad enforces this
  structurally without requiring the reviewer to know the claim-tier terminology.
- Reuse potential (9) means the schema can absorb future bundles without modification.
- The explicit `next_action` and `falsification_test` fields produce one concrete, judgeable
  AI7 next action as required.
- Retrieval quality (8) means the packet can be re-read quickly weeks or months later.

This is not a claim that Schema B is objectively best. It is a claim that Schema B performed
best on Bundle 1 under this rubric.

## What the winning schema preserves

- The observation/interpretation split prevents plausible interpretations from silently
  entering the observation layer.
- Evidence receipts with tier labels preserve provenance and claim status.
- The falsification test preserves the scientific testability constraint.
- The next_action field preserves exactly one concrete, judgeable action.

## What the winning schema breaks

- Reviewer-readiness: Schema B's language is more research-internal than grant-abstract.
  An NSF or Manifund submission would require a translation step from B to A format.
- Schema B can become verbose for very small bundles where a single claim and ask are obvious.

## Hybrid modifications

Apply the following modifications to Schema B to form the recommended winner template:

1. Add a `summary` field at the top (one sentence, borrowed from Schema C's `sentence` field)
   for fast retrieval.
2. Add four-tier labels (ESTABLISHED, PLAUSIBLE, CONJECTURAL, FORBIDDEN) as a required
   convention within the `evidence_receipts` field (borrowing Schema C's claim discipline
   mechanism).
3. Keep the `next_action` field as the final field with a hard constraint: exactly one action.

## AI7 next action

Create `docs/mcore-cascade-eval-spec.md` in `vortexpixelz/mcore-1` with a minimum viable
harness specification: input trace format, error taxonomy mapping from LLM steps to MCORE
error kinds, and baseline comparison design (Cascade Index AUC vs. perplexity AUC on GSM8K
or ARC chain-of-thought traces). Commit the file. This single action moves `mcore-cascade-eval`
from `[SPEC FROM CHAT]` to `[ESTABLISHED AS REPO RECEIPT]` and unblocks the pilot study.

