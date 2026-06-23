---
schema_id: B_research_ledger
schema_version: 0.1
packet_version: 0.1
status: filled
source_bundle: Bundle 1
date_filled: 2026-06-23
---

# Schema B: Research Ledger Packet

## Observation

- `check_tree` is a formal, tested carry-cascade verifier with typed error kinds implemented in
  `src/mcore_py/checker.py`; all five error kinds are covered by CI-passing tests.
- The GJB2 c.35delG frameshift produces a zero-to-near-100% mismatch step function in audio WAV
  files; σ_t × σ_f = 0.0907 (1.14× theoretical minimum); 100% lossless round-trip confirmed by
  FFT decoder on all 681 trits.
- `vortexpixelz/0xparallax` contains an agent/orchestration substrate with a documented Run/Step
  trace gap; confirmed in the 2026-06-16 receipt ledger by direct-fetch.
- `mcore-cascade-eval` was named in the 2026-06-16 receipt ledger with status
  `[SPEC FROM CHAT / NOT YET DIRECT-FETCHED AS REPO FILE]` — a concept, not yet a repo artifact.

## Interpretation

The carry-cascade diagnostic demonstrates that a formally specified propagation structure can be
made detectable and measurable in a real-world biological domain (GJB2). The Run/Step trace gap
in 0xparallax suggests a structural homolog: an LLM reasoning step transition also has an
observable trace gap where cascade errors could be injected or detected. If LLM trajectories can
be encoded as carry sequences, then MCORE's error taxonomy may apply directly.

## Hypothesis

A Cascade Index derived from MCORE carry-cascade diagnostics applied to LLM mid-trace steps
predicts final-answer failure on standard reasoning benchmarks better than simple length or
perplexity baselines.

Falsification condition: if Cascade Index AUC is not distinguishable from a random baseline on
≥ 3 diverse LLM families and ≥ 2 benchmarks, the hypothesis is disconfirmed for this domain.

## Evidence Receipts

- [ESTABLISHED] `check_tree` carry-cascade verifier — `src/mcore_py/checker.py`, CI-passing tests.
- [ESTABLISHED] GJB2 step-function result — WAV files + σ_t × σ_f measurement in repo.
- [ESTABLISHED] 0xparallax Run/Step trace gap — direct-fetched 2026-06-16.
- [PLAUSIBLE] LLM reasoning trajectories contain cascade-detectable structure.
- [CONJECTURAL] Cascade Index predicts LLM failure better than simple baselines.
- [NOT YET A RECEIPT] `mcore-cascade-eval` as a repo file or eval harness.

## Falsification Test

Create a minimal `mcore-cascade-eval` harness. Apply it to chain-of-thought traces from GSM8K
or ARC on one model family. Compare Cascade Index AUC vs. perplexity AUC. If AUC does not
exceed random baseline (0.5) by a meaningful margin (e.g., 0.05) on at least two benchmark
subsets, the Cascade Index hypothesis is disconfirmed.

## Next Action

Create `mcore-cascade-eval` as a repo file in `vortexpixelz/mcore-1` with a minimal test harness
spec: input format, error taxonomy mapping, baseline comparison design. Direct-fetch the file
to promote from [SPEC FROM CHAT] to [ESTABLISHED AS REPO RECEIPT] before any external pitch.

