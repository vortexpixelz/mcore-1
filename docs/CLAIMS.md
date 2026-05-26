# MCORE-1 Claims Registry

Every claim in the whitepaper and codebase must appear here with status.
Status levels: **[ESTABLISHED]** | **[PLAUSIBLE]** | **[CONJECTURAL]**

Last updated: May 2026 (Turn 3 pop-frame audit)

---

## [ESTABLISHED] — Supported by committed code and artifacts

| Claim | Evidence |
|---|---|
| Ternary mora-pooling conservation invariant: `w(parent) = trit_add_seq(children)` under partial commutative semigroup `(T={S1,S2,S3}, +)` | `src/mcore_py/algebra.py`, `src/mcore_py/checker.py` |
| `check_tree` enforces CONSERVATION and OVERFLOW errors via O(N) post-order traversal | `src/mcore_1/check_tree.py`, `src/mcore_py/checker.py` |
| Five error kinds: OVERFLOW, CONSERVATION, BUDGET, TENSION_UNRESOLVED, EMPTY_CONSTITUENT | `src/mcore_py/checker.py` |
| TENSION_UNRESOLVED / POP_FRAME is a typed spec construct (Level.L4_SLOKA boundary trigger), not a metaphor | `src/mcore_py/checker.py` |
| Four algebra operations: addition (mora pooling), tension pairing, projection π_L, prastara completion \* | `src/mcore_py/algebra.py` |
| Prastara completion generalizes Pingala's algorithm to ternary with polynomial-time budget pruning | `src/mcore_py/algebra.py` (`complete`, `enumerate_patterns`) |
| GJB2 sonification pipeline: 48 kHz, 40 ms Gabor clicks, 800/1600/3200 Hz, NM_004004.6 NCBI fetch | `gjb2-mcore-sonification/code/gjb2_sonification.py` |
| GJB2 WAV artifacts committed: wildtype, c.35delG, c.235delC | `gjb2-mcore-sonification/` repo root |
| Empirical σ_t × σ_f = 0.0907 (1.14× theoretical minimum) for GJB2 8ms windows | `gjb2-mcore-sonification` analysis notebooks |

---

## [PLAUSIBLE] — Consistent with established core; cross-domain validation pending

| Claim | What would promote to ESTABLISHED |
|---|---|
| Solar trit sequences (PIL slices) will surface CONSERVATION errors in `check_tree` comparable to GJB2 | Run check_tree on HMI-derived trit sequences; measure error density vs. flare magnitude |
| Astrophysical trit sequences (galactic/neutrino/pulsar) will surface algebraically consistent carry-cascade errors | Feed ingestor output to deployed Appwrite check_tree function; record pass/fail rate |
| Fractal stress equation captures qualitative hierarchical tearing motif from tearing-mode literature (FKR 1963, Loureiro 2007) | Compare depth distribution of cascade events to published plasmoid statistics |
| Internal thermodynamic ledger closure ΔE ≈ 0 maps metaphorically to MHD flux conservation | Formal mapping argument from ledger variables to MHD energy terms |

---

## [CONJECTURAL] — Research program; not validated

| Claim | Validation path |
|---|---|
| Solar fractal sonification is "physically faithful" to reconnection dynamics | Quantitative benchmark: run same AR on MHD simulation + MCORE-1; compare event distributions |
| Multi-messenger universality: same kernel applies uniformly across all astrophysical domains | Domain-by-domain benchmark for each new data type before claiming universality |
| MCORE-1 acoustic output is perceptually optimal for scientific sonification | User study / psychoacoustic evaluation |
| "The universe speaks MCORE-1" | Not a scientific claim; rhetorical / outreach language only |

---

## Whitepaper Language Rules

1. Every prose paragraph must be internally tagged [ESTABLISHED], [PLAUSIBLE], or [CONJECTURAL] in comments/drafts before final copy.
2. [CONJECTURAL] claims must use hedged language: "suggests," "motivates," "is consistent with," "remains future work."
3. [ESTABLISHED] claims may use direct language: "enforces," "implements," "verifies."
4. Never use [CONJECTURAL] language in an abstract without a corresponding limitation statement.
