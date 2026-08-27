---
schema_id: A_minimal_grant
schema_version: 0.1
packet_version: 0.1
status: filled
source_bundle: Bundle 1
date_filled: 2026-06-23
---

# Schema A: Minimal Grant Packet

## Claim

Carry-cascade diagnostic structure — as implemented in MCORE and demonstrated on GJB2 genomic
data — can be adapted to detect pre-failure states in LLM reasoning trajectories, enabling a
measurable Trustworthy AI diagnostic.

## Problem

LLM reasoning failures are difficult to detect before they produce a wrong final answer.
Existing monitoring approaches rely on output-level signals. A trajectory-level diagnostic
based on cascade propagation structure would catch failures earlier and more formally.

## Evidence

- `check_tree` is an implemented, formally verified carry-cascade diagnostic with typed error
  kinds (OVERFLOW, CONSERVATION, BUDGET, TENSION_UNRESOLVED, EMPTY_CONSTITUENT); all covered
  by tests in `src/mcore_py/checker.py` and `tests/test_mcore.py`.
- The GJB2 c.35delG frameshift produces a measurable zero-to-near-100% mismatch step function
  visible in audio WAV files; σ_t × σ_f = 0.0907 (1.14× theoretical minimum); 100% lossless
  round-trip confirmed.
- `vortexpixelz/0xparallax` provides a documented Run/Step trace gap in an agent/orchestration
  substrate — a structural analog to the cascade gap under study.

## Experiment

`mcore-cascade-eval`: apply MCORE carry-cascade diagnostics to LLM reasoning trace data from
a public benchmark (e.g., GSM8K or ARC chain-of-thought completions). Measure whether
cascade-structure errors (OVERFLOW, CONSERVATION) in mid-trace steps predict final-answer
failure better than a simple length or perplexity baseline.

## Ask

Fund `mcore-cascade-eval` as a pilot study: scoped dataset, one model family, one baseline
comparison, reproducible eval harness in `vortexpixelz/mcore-1`.

