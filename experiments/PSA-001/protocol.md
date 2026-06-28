# PSA-001 — Shard-Invariance Assay Protocol

**Protocol ID:** `PSA-001`  
**Version:** `0.1.0-draft`  
**Status:** Draft / pre-implementation  
**Scope:** MCORE-1 deterministic transform under two-shard execution  
**Primary question:** Does an explicitly partitioned execution reproduce the designated monolithic reference exactly when it uses an explicit, serializable boundary-state handoff?

---

## 1. Normative language

The terms **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative.

A run is **conformant** only when every REQUIRED assertion applicable to that run passes. A metric observation is not evidence of comparative value unless it satisfies the separate baseline and interpretation rules in this protocol.

---

## 2. Scope and non-claims

PSA-001 tests a bounded systems property:

```text
same planned transform + same input + explicit boundary handoff
    => exact equality between monolithic and recomposed two-shard execution
```

PSA-001 does **not** test or establish neon/plasma physics, universal sharding scalability, production distributed-systems resilience, AI interpretability, or LLM-failure prediction.

### 2.1 Topology guardrail

The current `check_tree()` implementation constructs a recursive midpoint-bisection tree from the **full input length**. For arbitrary split points, independently calling a local tree builder on `x[:b]` and `x[b:]` changes topology. Such a result is not automatically a carry failure.

Therefore, the transform under test (TUT) MUST execute against one shared, immutable **Execution Plan** that identifies the global input span and topology. A shard MUST NOT silently substitute a local-only bisection plan.

A future streaming or shard adapter MAY represent unfinished global tree work as a frontier, frame stack, or equivalent summary. The representation is implementation-defined, but its meaning and serialization are not.

---

## 3. Definitions

### 3.1 Fixture

`x` is the fixed PSA-001 synthetic input fixture.

- `len(x) == 128`
- every element of `x` MUST be in `{0, 1, 2}`
- fixture bytes and canonical JSON representation MUST be SHA-256 hashed
- the fixture identifier and hash MUST appear in every result manifest

### 3.2 Valid split point

A valid two-shard split point is an integer `b` such that:

```text
1 <= b <= 127
left  = x[0:b]
right = x[b:128]
```

Splits are indexed by the number of input trits in the left shard. Absolute input positions are zero-based in manifests unless a field explicitly ends in `_1`.

### 3.3 Execution Plan

`P` is an immutable, canonical plan shared by monolithic and sharded execution. It MUST include at least:

- `plan_schema` and `plan_version`
- `transform_id` and exact implementation version / git commit
- `input_length: 128`
- `root_span: [0, 127]`
- `topology_id` such as `recursive_bisection_midpoint_v1`
- any rule needed to determine parent formation, pooling, overflow behavior, and output ordering
- a canonical-plan SHA-256 hash

Two runs are comparable only when `plan_hash` is identical.

### 3.4 Monolithic reference execution

For an input `y` and plan `P`, define:

```text
M(y, P) = execute_monolithic(y, P)
```

`M(y, P)` MUST emit a canonical output manifest containing:

- output payload or a canonical output digest plus independently recomputable payload artifact
- terminal transform state
- ordered node/result records, if the TUT exposes them
- overflow/error records
- plan hash, input hash, runner version, and git commit

### 3.5 Sharded execution and boundary state

For a split `b`, define:

```text
L_b = execute_shard(x[0:b], P, entry_state)
R_b = execute_shard(x[b:128], P, L_b.boundary_state)
S_b = recompose(L_b, R_b, P)
```

`entry_state` is the declared initial state for `P`; it MUST be explicit and serializable. `L_b.boundary_state` is a `BoundaryState` conforming to the versioned schema defined by `src/mcore_1/sharding/boundary_state.py` or its successor.

Recomposition MUST consume only:

1. the immutable execution plan,
2. the two shard outputs,
3. their validated boundary-state manifests, and
4. declared deterministic recomposition code.

Recomposition MUST NOT read the full input, invoke the monolithic result, or access undeclared in-process state.

### 3.6 Exact equality

`EXACT_EQUAL(A, B)` is true only when all applicable components are equal after canonical normalization:

- `output_hash`
- canonical output payload
- ordered output/node records
- terminal transform state
- error / overflow classification and ordered records
- declared aggregate metrics that are part of the TUT output

Human-readable timestamps, wall-clock duration, host metadata, and artifact paths are non-semantic and MUST NOT enter the equality relation.

### 3.7 Canonical serialization

All protocol manifests MUST use UTF-8 JSON with:

- object keys sorted lexicographically,
- no insignificant whitespace,
- integers represented as JSON integers,
- no floating-point values in correctness-critical fields,
- no non-finite numeric values,
- no random IDs, timestamps, or host-specific paths in hashed semantic payloads.

The SHA-256 digest is computed over the UTF-8 bytes of this canonical JSON representation.

---

## 4. Determinism assertions

### A-DET-001 — Fixture validity

Before execution, the runner SHALL assert:

```text
len(x) == 128
all(t in {0, 1, 2} for t in x)
fixture_hash == sha256(canonical_fixture_json)
```

Failure classification: `PROTOCOL_PRECONDITION_FAILURE`.

### A-DET-002 — Plan identity

Before comparing any two results, the runner SHALL assert:

```text
monolithic.plan_hash == sharded.plan_hash
monolithic.input_hash == sharded.input_hash
monolithic.transform_id == sharded.transform_id
```

Failure classification: `PLAN_IDENTITY_FAILURE`.

### A-DET-003 — Monolithic repeatability

For every input condition `y`, two independent invocations of `M(y, P)` SHALL be exactly equal:

```text
EXACT_EQUAL(M(y, P, run=1), M(y, P, run=2))
```

Failure classification: `MONOLITHIC_NONDETERMINISM`.

A failure here blocks interpretation of all shard results for that input condition.

### A-DET-004 — Boundary serialization round trip

For every emitted boundary state `B`, the runner SHALL assert:

```text
B == deserialize(serialize(B))
sha256(serialize(B)) == B.manifest_hash
```

The comparison SHALL include all semantic fields and exclude no field other than explicitly non-semantic metadata defined by the boundary-state schema.

Failure classification: `BOUNDARY_SERIALIZATION_FAILURE`.

### A-DET-005 — No hidden-state recomposition

The recomposer SHALL run in an environment where undeclared access to the full fixture and monolithic-result artifact is unavailable or detectably prohibited.

Failure classification: `RECOMPOSITION_ISOLATION_FAILURE`.

---

## 5. Zero-perturbation shard-invariance assertions

For every split point `b in {1, ..., 127}`:

### A-ZERO-001 — Valid shard coverage

The left and right shard manifests SHALL declare contiguous, non-overlapping absolute spans whose union is `[0, 127]`:

```text
left.span  == [0, b - 1]
right.span == [b, 127]
left.span ∩ right.span == ∅
left.span ∪ right.span == [0, 127]
```

Failure classification: `SHARD_COVERAGE_FAILURE`.

### A-ZERO-002 — Boundary handoff continuity

The right shard SHALL accept exactly the boundary manifest emitted by the left shard:

```text
right.entry_boundary_hash == left.exit_boundary_hash
right.entry_state == deserialize(left.exit_boundary_manifest)
```

Failure classification: `BOUNDARY_CHAIN_FAILURE`.

### A-ZERO-003 — Exact recomposition

The recomposed sharded execution SHALL equal the monolithic reference:

```text
EXACT_EQUAL(S_b, M(x, P))
```

This is the primary PSA-001 zero-perturbation assertion.

Failure classification: `ZERO_PERTURBATION_SHARD_INVARIANCE_FAILURE`.

### A-ZERO-004 — Stable boundary manifest

Repeating the same shard execution with the same fixture, plan, and entry state SHALL yield an identical boundary manifest hash.

Failure classification: `BOUNDARY_NONDETERMINISM`.

### A-ZERO-005 — Topology preservation

If the TUT emits topology or node-span records, the recomposed execution SHALL use the same global topology identifier and ordered node-span sequence as the monolithic reference.

Failure classification: `TOPOLOGY_DIVERGENCE_FAILURE`.

---

## 6. Controlled perturbation assertions

### 6.1 Primary trit-flip operator

A ternary state has no unique binary-style “flip.” PSA-001 therefore freezes the primary operator as:

```text
flip_v1(0) = 1
flip_v1(1) = 2
flip_v1(2) = 0
```

For each zero-based position `i in {0, ..., 127}`:

```text
y_i = x with y_i[i] = flip_v1(x[i])
```

The exact operator identifier and pre-/post-flip trit values MUST be recorded in every perturbation manifest. A future bidirectional replacement sweep MAY be added as a separately versioned extension and MUST NOT be merged silently into `flip_v1` results.

### A-PERT-001 — Perturbed-input identity

For each `(i, b)`, the monolithic and sharded executions SHALL use byte-for-byte identical perturbed fixture content:

```text
M(y_i, P).input_hash == S_{i,b}.input_hash
```

Failure classification: `PERTURBED_INPUT_IDENTITY_FAILURE`.

### A-PERT-002 — Perturbed shard invariance

For every flip position `i` and every split point `b`:

```text
EXACT_EQUAL(S_{i,b}, M(y_i, P))
```

PSA-001 does **not** require `M(y_i, P)` to equal `M(x, P)`. A perturbation effect is expected to be measurable; only monolithic-versus-sharded equivalence is asserted.

Failure classification: `PERTURBED_SHARD_INVARIANCE_FAILURE`.

### A-PERT-003 — Perturbation provenance

Each result SHALL record:

- `operator_id: flip_v1`
- `flip_position`
- `original_trit`
- `mutated_trit`
- `split_point`
- fixture hash before and after mutation
- plan hash
- left and right boundary manifest hashes
- monolithic and recomposed output hashes

Failure classification: `PERTURBATION_PROVENANCE_FAILURE`.

### A-PERT-004 — Metric recording, not pattern assertion

The runner SHALL record MCORE-specific cascade or divergence metrics for every `(i, b)` pair. PSA-001 v0.1 makes **no** assertion about a required heatmap shape, locality gradient, or boundary-amplification pattern.

An observed pattern is an exploratory result, not a pass condition, unless a later protocol version preregisters the pattern and its decision rule.

---

## 7. Baseline assertions and interpretation limits

For every perturbed condition, the result manifest SHALL include:

- Hamming distance between `x` and `y_i`
- Levenshtein/edit distance between `x` and `y_i`
- SHA-256 equality / inequality result
- outcome of naïve chunking with no boundary carry handoff
- optional rolling checksum or Merkle-style chunk-integrity result

### A-BASE-001 — Baseline provenance

Every baseline implementation SHALL identify its version, configuration, and input/output hashes.

Failure classification: `BASELINE_PROVENANCE_FAILURE`.

### A-BASE-002 — No superiority claim from constant baselines

For a single equal-length substitution, Hamming distance and ordinary edit distance will generally be `1`, while SHA-256 will generally report inequality. These are bookkeeping controls, not by themselves a discriminative benchmark.

Therefore, PSA-001 v0.1 SHALL NOT claim that MCORE-1 outperforms these baselines merely because MCORE-specific metrics vary while these controls are constant. A comparative-value claim requires a separately preregistered target, data partition, evaluation measure, and held-out decision rule.

### A-BASE-003 — Naïve no-handoff comparator

The no-boundary-handoff run SHALL be labeled a deliberately incomplete comparator. It MAY demonstrate that declared boundary state matters, but it SHALL NOT be treated as a realistic production baseline or evidence of scalability.

---

## 8. Failure handling and reproducers

Any failed REQUIRED assertion SHALL emit a minimized reproducer directory containing:

```text
fixture.json
execution_plan.json
perturbation.json
left_shard_manifest.json
right_shard_manifest.json
boundary_state.json
monolithic_manifest.json
recomposed_manifest.json
comparison.json
runner_environment.json
README.md
```

`comparison.json` SHALL name the first failing assertion, enumerate semantic fields that differ, and include each artifact hash.

Failure categories are:

| Category | Meaning |
|---|---|
| `PROTOCOL_PRECONDITION_FAILURE` | fixture, configuration, or plan was invalid |
| `PLAN_IDENTITY_FAILURE` | compared executions used different plans or identities |
| `MONOLITHIC_NONDETERMINISM` | reference execution was not repeatable |
| `BOUNDARY_SERIALIZATION_FAILURE` | state changed or became invalid across serialization |
| `RECOMPOSITION_ISOLATION_FAILURE` | recomposition accessed undeclared information |
| `ZERO_PERTURBATION_SHARD_INVARIANCE_FAILURE` | unperturbed recomposition differed from monolithic reference |
| `PERTURBED_SHARD_INVARIANCE_FAILURE` | perturbed recomposition differed from corresponding monolithic reference |
| `TOPOLOGY_DIVERGENCE_FAILURE` | shard execution used a non-equivalent global topology |
| `BASELINE_PROVENANCE_FAILURE` | a comparator could not be reproduced |

---

## 9. Required result matrix

| Condition | Inputs | Splits | Primary assertion |
|---|---:|---:|---|
| Unperturbed | 1 | 127 | `EXACT_EQUAL(S_b, M(x, P))` |
| `flip_v1` at every position | 128 | 127 each | `EXACT_EQUAL(S_{i,b}, M(y_i, P))` |

Minimum number of sharded comparison rows:

```text
127 + (128 × 127) = 16,383
```

The result set MUST explicitly record pass, fail, or invalid for every row. Missing rows are invalid, not implicit passes.

---

## 10. Release, hold, and revise decision rules

### Release a bounded claim only when

All conditions below are met:

1. All 127 zero-perturbation comparisons pass.
2. All boundary manifests validate and round-trip canonically.
3. Required baseline results and provenance are present.
4. The runner, fixed fixture, plan, commit, configs, hashes, and reproduction instructions are committed and independently runnable.
5. Failures, if any, are either resolved or separately classified as invalid protocol runs and are not omitted from the results manifest.

### Hold when

- any zero-perturbation comparison fails;
- the global plan/topology differs between monolithic and shard runs;
- a boundary manifest cannot be independently validated;
- results lack baseline provenance or a reproducible runner;
- an interpretation attempts to exceed the bounded systems property tested here.

“Neon” remains limited to visualization or observability language unless an independent dataset, hypothesis, protocol, and result set are created.

### Revise or retire when

- the boundary contract cannot be made exact without hidden full-input or monolithic-result access;
- the transform’s global topology cannot be represented by a declared shard-compatible execution plan;
- MCORE-specific metrics add no preregistered, independently evaluated diagnostic value in a later comparative assay;
- a simpler prespecified baseline fully accounts for the observed diagnostic behavior.

---

## 11. Bounded public sentence after a passing release gate

> MCORE-1 was tested for deterministic equivalence between monolithic and two-shard execution on a fixed synthetic 128-trit fixture, using an explicit serialized boundary-state handoff and conventional integrity controls.

No stronger statement is authorized by PSA-001 alone.
