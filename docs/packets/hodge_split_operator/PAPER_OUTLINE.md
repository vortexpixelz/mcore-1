# Paper Outline

## Title candidates

1. **Observer-Relative Decomposition in MCORE-1: A Discrete Dual Operator for Coupled Spatial-Temporal State**
2. **Package First, Split Second: A Hodge-Inspired Reconstruction Layer for Ternary Conservation Systems**
3. **Dual Views of a Conserved State: Discrete Hodge Structure and Observer Dependence in MCORE-1**

## Abstract contract

The abstract must state:

- the architectural gap;
- the proposed discrete dual/split construction;
- the exact test fixtures;
- reconstruction and conservation results;
- null-model performance;
- explicit rejection of any unsupported spacetime-unification claim.

## 1. Introduction

- MCORE-1 links a ternary conservation grammar across multiple overlays.
- The repository contains sequential propagation, time-frequency localization, and geometric representations.
- These views are not yet generated from one explicit metric-aware state object.
- Contribution: a falsifiable observer-relative reconstruction layer inspired by differential forms and discrete Hodge theory.

## 2. Background

### 2.1 MCORE-1

- ternary algebra;
- `check_tree()` conservation;
- carry propagation;
- existing experimental and claim-tier governance.

### 2.2 Unified electromagnetic field and observer decomposition

- electromagnetic two-form `F`;
- observer-relative electric and magnetic views;
- role of metric, orientation, and Hodge star;
- why the source clip is an intake signal rather than a proof.

### 2.3 Discrete exterior calculus

- oriented cell complexes;
- primal and dual cochains;
- coboundary operator;
- discrete Hodge matrices;
- reconstruction and sign conventions.

## 3. Problem statement

Can one MCORE state object generate consistent spatial and temporal projections relative to a declared observer, then reconstruct itself while preserving independently checkable conservation receipts?

## 4. Formal setup

### 4.1 Oriented finite complex `K`
### 4.2 Trit lift `lambda : T -> R`
### 4.3 Unified state `F_M`
### 4.4 Metric or weighted inner product `g_M`
### 4.5 Candidate dual operator `*_M`
### 4.6 Observer variable `u`
### 4.7 Split and reconstruction maps

## 5. Conservation compatibility

### 5.1 Cochain closure
### 5.2 Source/current cochain
### 5.3 Continuity from `delta^2 = 0`
### 5.4 Relationship to tree conservation
### 5.5 Counterexamples and non-equivalence cases

## 6. Implementation

### 6.1 Minimal 2+1 dimensional fixture
### 6.2 Oriented cubical versus simplicial representation
### 6.3 Sparse matrix form of `*_M`
### 6.4 Pathic table output
### 6.5 Reproducible command and receipts

## 7. Experiments

1. exact reconstruction;
2. star-square sign test;
3. orientation reversal;
4. controlled metric changes;
5. observer-change consistency;
6. perturbation attribution;
7. carry/Jacobian downstream analysis;
8. shuffled and random dual nulls;
9. coefficient-lift ablation;
10. cell-complex ablation.

## 8. Results

Report:

- reconstruction residual distributions;
- closure and source residuals;
- pass/fail matrix by observer and fixture;
- null separation;
- sensitivity to metric and orientation;
- claim-tier changes.

No result section may replace a failed fixture with a prettier visualization.

## 9. Discussion

- what the operator adds to MCORE-1;
- whether it belongs in core, an overlay, or only a visualization layer;
- whether pathic tables become a useful audit surface;
- how the Jacobian lane attaches after the structure is defined;
- where the electromagnetic analogy ends.

## 10. Limitations

- no physical identification of MCORE states with electromagnetic fields;
- no claim of spacetime unification;
- no automatic equivalence between `check_tree()` and cochain closure;
- dependence on coefficient lift, metric, orientation, and topology;
- toy-complex results may not generalize.

## 11. Conclusion

The conclusion must choose one outcome: coherent formal layer, useful analogy only, or rejected construction.

## Appendix plan

- A. notation and conventions;
- B. discrete star matrices;
- C. fixture definitions;
- D. pathic-table schema;
- E. null operators;
- F. claim register and receipt manifest.
