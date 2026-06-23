---
schema_id: D_cockpit
schema_version: 0.1
packet_version: 0.1
status: filled
source_bundle: Bundle 1
date_filled: 2026-06-23
---

# Schema D: Cockpit Packet

## Destination

A funded, reproducible `mcore-cascade-eval` pilot study that demonstrates whether MCORE
carry-cascade diagnostics detect pre-failure states in LLM reasoning trajectories, generating
enough data to produce or disconfirm a Trustworthy AI grant application.

## Current Position

- MCORE `check_tree` is implemented and formally verified (ESTABLISHED).
- GJB2 step-function cascade result is measured and committed (ESTABLISHED).
- 0xparallax Run/Step trace gap is documented (ESTABLISHED).
- `mcore-cascade-eval` is a concept only; no repo file exists yet (SPEC FROM CHAT).
- NSF Trustworthy AI is identified as a target; no submission in hand.

## Signal

The GJB2 carry-cascade step function (zero-to-near-100% mismatch after c.35delG) is the
strongest signal in hand. It shows cascade detection works in a biological domain. The
structural homolog in LLM traces (Run/Step gap in 0xparallax) is the next signal to validate.
Cascade Index AUC on a reasoning benchmark will be the decision gate for the NSF pitch.

## Uncertainty

- Unknown: whether LLM chain-of-thought traces encode enough carry-cascade structure for
  MCORE diagnostics to fire meaningfully (vs. random noise).
- Unknown: whether Cascade Index AUC exceeds perplexity baseline on reasoning benchmarks.
- Unknown: whether NSF Trustworthy AI is the right mechanism or if another vehicle fits better.
- Known unknown: `mcore-cascade-eval` harness design choices will affect results; not yet specified.

## Route

1. Create `mcore-cascade-eval` as a repo spec file with input format, error taxonomy mapping,
   and baseline comparison design.
2. Direct-fetch the file to promote from [SPEC FROM CHAT] to [ESTABLISHED AS REPO RECEIPT].
3. Implement minimal harness: encode chain-of-thought steps as carry sequences; apply `check_tree`.
4. Run on GSM8K or ARC chain-of-thought traces for one model family.
5. Compare Cascade Index AUC vs. perplexity baseline.
6. If AUC > random + 0.05 on ≥ 2 subsets: draft NSF Trustworthy AI pitch.
7. If AUC is at noise level: document as disconfirmation and revise hypothesis.

## Artifact

Current artifacts in hand:
- `src/mcore_py/checker.py` — the verifier.
- `gjb2-mcore-sonification/` — step-function result.
- `vortexpixelz/0xparallax` — Run/Step trace documentation.

Next artifact to create:
- `docs/mcore-cascade-eval-spec.md` — pilot study specification.

## Dismount

Create `docs/mcore-cascade-eval-spec.md` in `vortexpixelz/mcore-1` with a minimum viable
harness spec. Commit and direct-fetch. That single action moves the Cascade Index from
[SPEC FROM CHAT] to [ESTABLISHED AS REPO RECEIPT] and unblocks the pilot study.

