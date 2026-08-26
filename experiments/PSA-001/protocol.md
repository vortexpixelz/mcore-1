# PSA-001A Protocol — Current DNA Encoder Bounded Null

Parent: #39  
Child: #49  
Base commit: `21cf94b0f2aa5c9cb62e5d19d1c76f51ab665d7f`

## Decision-gate outcome

Use outcome 1 from #49: assay the current public DNA encoder
`mcore_1.encoder.dna_to_trits` without changing its value map or injecting an
artificial carry.  On valid DNA input, carry `0` is the sole reachable boundary
state.  The assay therefore measures a bounded null/baseline result.

The atomic-decay T-Net notebook, including Attempt 4, is **not** the
transform-under-test.  It is a separate synthetic STFT-imputation application
whose sequence context and learned hidden state would require a distinct
sharding protocol.

## Frozen inputs

- Input domain: uppercase DNA over `{A,C,G,T}`.
- Fixture: `fixtures/dna_128.txt`.
- Fixture length: 128 symbols.
- Fixture SHA-256 after stripping the terminal newline:
  `ec4fec99482dc489f8006c8c2544bc5b25ee610aaa930a862b2f8ae59566e4a5`.
- Perturbation: deterministic cyclic base substitution
  `A→C, C→G, G→T, T→A` at exactly one position.
- Boundaries: every two-shard split `1..127`.

## Boundary contract

`src/mcore_1/psa001_sharding.py` exposes the equivalent interface:

```text
run_dna_shard(input, start_state) -> (output, end_state, trace)
```

The canonical state contains:

- `schema_version = psa001-boundary-v1`
- `transform_id = mcore_1.encoder.dna_to_trits`
- `carry = 0`

Canonical JSON uses sorted keys and compact separators; its UTF-8 bytes are
hashed with SHA-256.  Unknown schema/transform identifiers and nonzero carry
fail closed.

## Matrix

The focused test performs:

- 127 unperturbed monolithic-versus-two-shard comparisons;
- 128 perturbation positions × 127 boundaries = 16,256 comparisons;
- 16,383 total comparisons.

For every comparison it requires exact output equality, terminal-state
equality, boundary-state hash equality, and equality with naive chunking.
Naive chunking is included only as a conventional baseline and is expected to
match because the boundary state is degenerate.

## Run

```bash
python -m pytest tests/test_psa001_shard_invariance.py -q
```

The repository's existing pull-request CI also executes the full test suite in
Python 3.11 and in the Docker image.

## Claim boundary

A passing result establishes only that the current carry-inert DNA encoder is
exactly invariant under the tested two-shard decomposition for this fixture and
perturbation matrix.  It is not evidence for nontrivial carry propagation,
sharding superiority, the Atomic Decay T-Net, physics claims, AI
interpretability, or generalized distributed-system resilience.
