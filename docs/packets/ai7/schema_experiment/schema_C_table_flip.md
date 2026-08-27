---
schema_id: C_table_flip
schema_version: 0.1
packet_version: 0.1
status: filled
source_bundle: Bundle 1
date_filled: 2026-06-23
---

# Schema C: Table Flip Packet

## Receipt

- `check_tree` — formal carry-cascade verifier; five typed error kinds; CI-passing tests in
  `src/mcore_py/checker.py`.
- GJB2 c.35delG WAV step-function — zero-to-near-100% mismatch; σ_t × σ_f = 0.0907; 100%
  lossless round-trip; all artifacts committed to repo.
- 0xparallax Run/Step trace gap — direct-fetched 2026-06-16; exists in repo.
- `mcore-cascade-eval` named in receipt ledger 2026-06-16 as concept only — NOT yet a repo file.

## Claim

MCORE carry-cascade diagnostics can detect pre-failure states in LLM reasoning trajectories,
and a Cascade Index derived from this approach is worth testing as a Trustworthy AI diagnostic.

## Ledger

### Observed

- MCORE `check_tree` is an implemented, formally verified carry-cascade verifier.
- GJB2 application produces measurable, reproducible cascade detection results.
- The Run/Step trace gap in 0xparallax is a documented structural analog to the cascade gap.

### Plausible

- LLM chain-of-thought traces contain carry-cascade-detectable structure analogous to GJB2.
- A Cascade Index computed on mid-trace steps would correlate with final-answer correctness.
- The 0xparallax Run/Step trace gap is a viable injection point for MCORE diagnostics.

### Speculative

- The Cascade Index outperforms perplexity and length baselines on reasoning benchmarks.
- MCORE error taxonomy (OVERFLOW, CONSERVATION, BUDGET) maps cleanly to LLM failure modes.
- This constitutes a novel reasoning-stability metric suitable for NSF Trustworthy AI.

### Forbidden for now

- Do not claim `mcore-cascade-eval` is implemented until a repo file is direct-fetched.
- Do not claim the Cascade Index predicts LLM failure without empirical benchmark data.
- Do not use GJB2 step-function as proof of LLM application; it is an analogy receipt only.
- Do not cite NSF submission or acceptance without a documented submission receipt.

## Sentence

The MCORE carry-cascade pattern is proven in GJB2; it is plausible but undemonstrated in
LLM trajectories; the next action is to create `mcore-cascade-eval` as a concrete repo file.

## Ask

Fund `mcore-cascade-eval` as a scoped pilot: one LLM family, two benchmarks, one baseline
comparison, reproducible harness committed to `vortexpixelz/mcore-1`.

