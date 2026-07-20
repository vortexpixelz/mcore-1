# Experiment Plan: HODGE-SPLIT-001

## Question

Can a single discrete MCORE state produce observer-relative channel views and reconstruct itself while preserving explicit conservation receipts?

## Scope

This experiment is a toy-model gate. It is not a physics validation and should not use biological or electromagnetic data in its first pass.

## Proposed implementation lane

```text
experimental/hodge_split_operator/
  README.md
  fixtures.py
  operators.py
  run.py
  scorecard.yaml
  results/

tests/test_hodge_split_operator.py
```

Code should not be added until the assumptions in `FORMAL_MODEL.md` are frozen.

## Fixture A: minimal oriented complex

Use a small 2+1 dimensional cubical or simplicial complex with:

- explicit cell IDs;
- boundary matrices;
- primal and dual cells;
- orientation signs;
- a non-degenerate metric weight per cell;
- a baseline two-cochain `F_M`;
- a localized perturbation `Delta F_M`;
- at least three observer/readout directions.

## Coefficient-lift candidates

Test at least:

1. centered scalar lift: `0,1,2 -> -1,0,+1`;
2. one-hot lift into `R^3`;
3. constrained scalar lift preserving current MCORE ordering.

No lift is canonical until it wins a declared scorecard.

## Required tests

### T1. Reconstruction

For every valid observer `u`:

```text
R_u(E_u, B_u) ~= F_M
```

Record absolute and relative residuals.

### T2. Star-square behavior

Verify the expected sign law for the chosen dimension and signature. Fail if the implementation silently assumes involution.

### T3. Orientation reversal

Reverse the complex orientation and confirm that only predicted signs change.

### T4. Metric sensitivity

Modify cell weights while holding topology fixed. The dual should change in the predicted weighted manner.

### T5. Topology sensitivity

Modify incidence or boundary structure while holding metric weights fixed. Closure behavior should change independently of metric-only effects.

### T6. Conservation

Compute:

```text
closure_residual = ||delta F_M||
source_residual = ||delta (*_M F_M) - J_M||
continuity_residual = ||delta J_M||
```

These are separate from `check_tree()` receipts.

### T7. Observer change

Change `u`; confirm that channel views change while `F_M` is held fixed and reconstructable.

### T8. Perturbation attribution

Apply `Delta F_M`; record its trace across primal, dual, projected, and reconstructed views.

### T9. Null operators

Compare against:

- random permutation maps;
- shuffled dual-cell assignments;
- metric-free complement maps;
- orientation-erased maps.

A proposed dual is not interesting unless nulls fail at least reconstruction or conservation.

### T10. `check_tree()` bridge

Construct the smallest tree-derived complex candidate. Attempt to prove or falsify a relationship between parent/child weight conservation and cochain closure.

## Pathic table schema

| Field | Meaning |
|---|---|
| `path_id` | experiment trace |
| `cell_id` | primal cell |
| `cell_dimension` | degree |
| `orientation` | signed orientation |
| `observer_id` | selected split frame |
| `primal_state` | original MCORE state |
| `lifted_coefficient` | value after declared lift |
| `dual_cell_id` | complementary cell |
| `dual_state` | dual output |
| `spatial_projection` | observer-relative channel |
| `temporal_projection` | observer-relative channel |
| `boundary_residual` | closure error |
| `reconstruction_residual` | split/rebuild error |
| `carry_state` | optional downstream carry receipt |
| `claim_tier` | observed/plausible/speculative |
| `receipt_path` | file or result artifact |

## Acceptance gate

The experiment passes the formalization gate only if:

- all operator assumptions are explicit;
- reconstruction passes on non-degenerate fixtures;
- null operators fail;
- orientation and metric effects are separable;
- the coefficient lift is visible in every output;
- the relationship to `check_tree()` is proved, bounded, or explicitly rejected;
- results are reproducible from one command.

## Stop conditions

Stop and classify the bridge as analogy-only or rejected if:

- reconstruction requires observer-specific hidden state;
- the dual cannot be defined without arbitrary unreported choices;
- null operators perform equivalently;
- conservation holds only because fixtures were constructed to force it;
- ternary semantics are destroyed by the coefficient lift;
- the `check_tree()` relation collapses under the first counterexample.

## Output artifacts

- `results/run_manifest.json`
- `results/pathic_table.jsonl`
- `results/operator_matrices.json`
- `results/scorecard.yaml`
- `results/result_memo.md`
- plots only after the numeric receipts exist.
