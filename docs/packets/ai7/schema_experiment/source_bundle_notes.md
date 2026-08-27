---
packet_id: AI7-BUNDLE-1-SOURCE
schema_version: 0.1
packet_version: 0.1
status: filled
source_bundle: Bundle 1
date_created: 2026-06-23
date_filled: 2026-06-23
---

# Source Bundle Notes

## Raw source inventory

Bundle 1 is the early AI7 research bundle assembled from the following directly-verified sources:

- `receipts/2026-06-16-symonic-receipt-ledger.md` — dated receipt ledger with claim tiers
- `docs/CLAIMS.md` — MCORE-1 epistemic boundaries and claims registry
- `docs/experiments/schema_selection_ai7_packet.md` — experiment design spec
- `docs/VOR-117_REPOSITORY_AUDIT.md` — repository audit structure and bucket framework
- `docs/packets/ai7/schema_experiment/CLAIM_TIERS.md` — claim tier definitions
- Repo: `vortexpixelz/mcore-1`, branch `main` (all files above direct-fetched)

Bundle 1 focus: Can the MCORE carry-cascade diagnostic pattern be adapted to detect
pre-failure states in LLM reasoning trajectories? Can this motivate an NSF Trustworthy AI ask?

## Receipts

Observed facts, files, test outputs, citations, repo links, measurements.

- `check_tree` implements a formal carry-cascade verifier with typed error kinds (OVERFLOW,
  CONSERVATION, BUDGET, TENSION_UNRESOLVED, EMPTY_CONSTITUENT); proven by `src/mcore_py/checker.py`
  and `tests/test_mcore.py`.
- GJB2 c.35delG frameshift produces a zero-to-near-100% mismatch step function visible in audio
  WAV files; directly measured, σ_t × σ_f = 0.0907 (1.14× theoretical minimum).
- `vortexpixelz/0xparallax` exists, provides agent/orchestration substrate with documented
  Run/Step trace gap; confirmed in receipt ledger 2026-06-16.
- The MCORE/GJB2 trajectory-divergence diagnostic is implemented and produces auditable results
  from a fresh repo clone.
- `mcore-cascade-eval` was named as a concept in the 2026-06-16 receipt ledger; status at time
  of capture: `[SPEC FROM CHAT / NOT YET DIRECT-FETCHED AS REPO FILE]`.
- NSF Trustworthy AI program exists as a funding target; no acceptance or submission receipt in hand.
- The receipt ledger explicitly separates ESTABLISHED / PLAUSIBLE / CONJECTURAL / FORBIDDEN tiers
  and enforces "no phantom receipts" as operating doctrine.

## Claims already present in the bundle

Claims the bundle appears to make. Do not upgrade them yet.

- [ESTABLISHED] MCORE/GJB2 gives an implemented trajectory-divergence diagnostic pattern.
- [ESTABLISHED] 0xparallax gives an agent/orchestration substrate with a documented Run/Step trace gap.
- [PLAUSIBLE] The carry-cascade diagnostic pattern can be adapted to observable LLM reasoning trajectories.
- [CONJECTURAL] A Cascade Index derived from MCORE predicts LLM final-answer failure better than simple baselines.
- [ASK] Fund `mcore-cascade-eval`: apply MCORE carry-cascade diagnostics to LLM reasoning trace data.

## Open questions

- Does the MCORE trace gap in 0xparallax map structurally to the kind of gap that precedes LLM failure?
- What LLM reasoning trace format would `mcore-cascade-eval` need as input?
- Is NSF Trustworthy AI the right funding vehicle or should this target a different mechanism?
- What is the minimal falsification test for the Cascade Index claim?

## Possible AI7 / NSF fit

- NSF Trustworthy AI: reasoning stability as a measurable, falsifiable property is well-aligned.
- The carry-cascade framing provides a formal diagnostic structure that is not just vibes.
- The GJB2 step-function result is a concrete existence proof that cascade structure is detectable
  in a different domain; it makes the hypothesis more credible than a pure LLM-only pitch.
- A minimal eval harness (`mcore-cascade-eval`) could be scoped as a pilot study.

## Notes that should not become claims yet

- Do not claim `mcore-cascade-eval` is implemented until a repo file is direct-fetched.
- Do not claim the Cascade Index predicts LLM failure without benchmark data.
- Do not cite the GJB2 step-function result as proof of LLM application; it is an analogy receipt only.
- Do not claim NSF submission or funding without a submission receipt.
