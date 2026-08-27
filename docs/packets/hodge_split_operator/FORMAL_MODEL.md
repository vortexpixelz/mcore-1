# Formal Model v0: Unified State, Observer Split, and Discrete Dual

## 0. Status

This is a mathematical scaffold, not a field theory. Symbols are provisional until the coefficient algebra, dimension, orientation, metric, and operator domains are frozen.

## 1. Substrate

Let `K` be an oriented finite cell complex of dimension `n`, with dual complex `K*`.

MCORE trits require an explicit lift before signed orientation and linear combination are legal:

```text
lambda : T = {0,1,2} -> R
```

where `R` is a declared coefficient ring or real vector space. Candidate lifts must be compared rather than smuggled in. Examples include centered `{-1,0,+1}`, one-hot vectors, or constrained real embeddings.

Let:

```text
C^k(K; R)
```

be the `k`-cochains on `K` with coefficients in `R`.

## 2. Unified state

Define the candidate packaged state as a two-cochain:

```text
F_M in C^2(K; R)
```

The choice `k = 2` is motivated by the electromagnetic analogy, not yet by an internal MCORE theorem. Alternative degrees must remain admissible during ablation.

## 3. Metric and dual operator

Declare a weighted inner product or discrete metric `g_M`. A candidate discrete Hodge operator has type:

```text
*_M : C^k(K; R) -> C^(n-k)(K*; R)
```

For a matrix implementation, `*_M` should be constructed from primal/dual cell volumes, orientation, and the chosen coefficient representation.

Required operator receipts:

1. domain and codomain dimensions;
2. orientation convention;
3. metric weights;
4. invertibility conditions;
5. expected star-square law;
6. behavior on degenerate cells;
7. numerical tolerance.

A target identity is convention-dependent:

```text
*_M *_M omega = s(k,n,signature) omega
```

where `s` is a declared sign, not assumed to be `+1`.

## 4. Observer-relative split

Let `u` denote an observer, foliation, readout direction, or normalized time-like analogue. Define schematic projections:

```text
E_u = i_u F_M
B_u = -i_u (*_M F_M)
```

where `i_u` is contraction. Exact signs and coefficient factors must be derived from the selected conventions.

The central test is reconstruction:

```text
R_u(E_u, B_u) = F_M
```

for non-degenerate fixtures.

The object `F_M` should remain invariant while `E_u` and `B_u` change with `u`. This is the candidate answer to the current architectural question: views may mix under perspective change while the packaged state remains fixed.

## 5. Discrete conservation candidates

Let `delta` be the cochain coboundary operator:

```text
delta : C^k(K; R) -> C^(k+1)(K; R)
```

Candidate equations:

```text
delta F_M = 0
delta (*_M F_M) = J_M
```

with source/current cochain `J_M`.

Since `delta^2 = 0`, the second equation would imply a continuity condition:

```text
delta J_M = 0
```

provided all domains and mappings are valid.

## 6. Relationship to `check_tree()`

No equivalence is assumed.

`check_tree()` validates parent/child weight conservation on a tree. `delta F_M = 0` expresses closure on an oriented complex. The first formal task is to determine whether there exists a functor, embedding, or restricted construction connecting these structures.

Possible outcomes:

- a proof on a limited class of tree-derived complexes;
- a lossy correspondence useful for visualization;
- no meaningful correspondence.

The third outcome is acceptable and must not be hidden.

## 7. Perturbations

For a localized perturbation `Delta F_M`, record:

```text
Delta E_u = i_u Delta F_M
Delta B_u = -i_u (*_M Delta F_M)
```

and reconstruction residual:

```text
r_u = norm(R_u(E_u + Delta E_u, B_u + Delta B_u) - (F_M + Delta F_M))
```

This allows carry propagation, Jacobian sensitivity, and dual-view attribution to be evaluated without confusing them.

## 8. Jacobian relationship

The Jacobian lens is downstream:

```text
J_split = d(E_u, B_u) / dF_M
J_reconstruct = dR_u / d(E_u, B_u)
```

The Hodge-split layer defines the objects and maps. The Jacobian measures their local sensitivity. The lens was cute; this packet is checking whether there is a chassis beneath it.

## 9. Minimum theorem targets

1. **Reconstruction theorem:** state conditions under which `R_u` is exact.
2. **Star-square proposition:** derive the expected sign for the chosen complex and signature.
3. **Observer-change proposition:** show how channel views transform while `F_M` is fixed.
4. **Conservation compatibility result:** prove, bound, or reject a relationship between `check_tree()` and cochain closure.
5. **Null-separation result:** show that random complementary mappings fail the declared receipts.
