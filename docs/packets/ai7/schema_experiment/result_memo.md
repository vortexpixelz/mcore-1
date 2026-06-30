---
experiment_id: AI7_SCHEMA_SELECTION_2026_06
schema_version: 0.1
status: complete
date_completed: 2026-06-30
---

# Result Memo

## Question

Which packet schema best preserves Bundle 1 as useful research memory while
producing a judgeable AI7 next action?

## Method

Backfilled Bundle 1 (MCORE-1 experimental lane, June 2026: NS-001 Gabor-Hölder
module, DIANEW Study A EVT protocol, schema factory scaffold) into all four
candidate schemas. Scored each on seven criteria (1–10) from scorecard.yaml.

## Results

| Schema | Total | Standout strength | Standout weakness |
|---|---|---|---|
| A: Minimal Grant | 49 | Reviewer-ready (9) | Claim discipline (5) |
| B: Research Ledger | **57** | Retrieval + reuse (9, 9) | Reviewer-ready (7) |
| C: Table Flip | 54 | Compression + claim discipline (9, 9) | Reviewer-ready (6) |
| D: Cockpit | 43 | Actionability / route steps (8) | Easy to fill (5) |

## Winner

**B: Research Ledger**

The observation → interpretation → hypothesis → evidence receipts → falsification
test → next action arc naturally enforces the claim upgrade ladder that MCORE
research requires. It produced the most specific and immediately executable next
action of the four schemas. Retrieval and reuse scores are the highest (both 9)
because the section labels are universal and the evidence receipts are directly
linkable.

## What the winning schema preserves

- The full epistemic progression from raw observation to falsifiable hypothesis.
- Specific, checkable evidence receipts (values, file paths, test counts).
- A concrete next action that names the data source (JHTDB), the method
  (structure-function exponent comparison), and the decision rule (if monotone
  decrease holds, upgrade to plausible; if not, falsify and record).
- Claim discipline without requiring domain-specific tier labels.

## What the winning schema breaks

- It is slightly less immediately legible to an NSF program officer than Schema A.
- The compression is good but does not force a one-liner the way Schema C's
  Sentence section does.

## Hybrid modifications

1. Add an optional **Sentence** field (from C) at the top of each B packet as a
   one-line retrieval hook that survives context loss.
2. Add an optional **Forbidden** field (from C) for experimental overlay packets
   where anti-claim guards are needed (e.g., NS-001 class modules).

## AI7 next action

Open **NS-002**: JHTDB calibration experiment.

Scope: one DNS snapshot → extract `omega_norm` time series → run `effective_alpha`
sweep → compare output trend to known Hölder/structure-function exponents from
the same snapshot.

Decision rule:
- If `alpha_eff` monotonically decreases as vorticity rises near dissipation scales:
  upgrade NS-001 conjecture to plausible; calibrate `lambda_omega` / `eta_phase`.
- If not: falsify the additive reduction model; record in the NS-001 claim-tier
  registry under ESTABLISHED (as a known falsification).

No NS proof claim regardless of outcome.
