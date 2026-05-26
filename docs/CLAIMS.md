# MCORE-1 Epistemic Boundaries & Claims Registry

> **Purpose:** Every claim in the whitepaper and codebase must appear here
> with an explicit status tier. All contributors, reviewers, and automated
> agents (e.g., Cursor Cloud) must tag their outputs accordingly to prevent
> intellectual drift.
>
> **Status levels:** `[ESTABLISHED]` | `[PLAUSIBLE]` | `[CONJECTURAL]`

*Last updated: 2026-05-26 (Turn 3 pop-frame audit + astrophysical expansion)*

---

## `[ESTABLISHED]` — Bedrock

Backed by production-ready code, mathematical proofs, and reproducible
artifacts in this repository. Use direct language: "enforces,"
"implements," "verifies."

| Claim | Evidence |
|---|---|
| Ternary mora-pooling conservation invariant: `w(parent) = trit_add_seq(children)` under partial commutative semigroup `(T={S1,S2,S3}, +)` | `src/mcore_py/algebra.py`, `src/mcore_py/checker.py` |
| `check_tree` enforces CONSERVATION and OVERFLOW errors via O(N) post-order traversal | `src/mcore_1/check_tree.py`, `src/mcore_py/checker.py` |
| Five error kinds: OVERFLOW, CONSERVATION, BUDGET, TENSION_UNRESOLVED, EMPTY_CONSTITUENT | `src/mcore_py/checker.py` |
| TENSION_UNRESOLVED / POP_FRAME is a typed spec construct (Level.L4_SLOKA boundary trigger), not a metaphor | `src/mcore_py/checker.py` |
| Four algebra operations: addition (mora pooling), tension pairing, projection π_L, prastara completion * | `src/mcore_py/algebra.py` |
| Prastara completion generalizes Pingala's algorithm to ternary with polynomial-time budget pruning | `src/mcore_py/algebra.py` (`complete`, `enumerate_patterns`) |
| GJB2 sonification pipeline: 48 kHz, 40 ms Gabor clicks, 800/1600/3200 Hz, NM_004004.6 NCBI fetch | `gjb2-mcore-sonification/code/gjb2_sonification.py` |
| GJB2 WAV artifacts committed: wildtype, c.35delG, c.235delC | `gjb2-mcore-sonification/` repo root |
| Empirical σ_t × σ_f = 0.0907 (1.14× theoretical minimum) for GJB2 8 ms windows | `gjb2-mcore-sonification` analysis notebooks |
| `weights_for_check_tree` shift: signed {-1, 0, +1} -> unsigned {0, 1, 2} (S1/S2/S3) | `experimental/astro_ingestor/solar_ingestor.py` |
| `np.concatenate` integer-indexed Gabor render produces zero array-boundary bleeding | `gjb2_sonification.py`; all `experimental/astro_ingestor/` ingestors |

### What these mean in plain language

- The algebra is real, deterministic, and auditable. `check_tree` is not
  a heuristic — it is a formal verifier with typed error kinds.
- The GJB2 genomic sonification is reproducible from a fresh clone: fetch
  the gene from NCBI, run the script, get the same WAV every time.
- The Gabor render pipeline is artifact-free. The `np.concatenate` pattern
  is the locked standard for all future ingestors.

---

## `[PLAUSIBLE]` — Experimental Frontier

Supported by working code in `experimental/`. Demonstrates qualitative
agreement with physical motifs but awaits quantitative benchmarking
against external datasets. Use hedged language: "suggests," "is
consistent with," "analog to."

| Claim | What would promote to `[ESTABLISHED]` |
|---|---|
| Solar trit sequences (PIL slices) will surface CONSERVATION errors in `check_tree` comparable to GJB2 | Run `solar_conservation_audit.py` on real HMI FITS data; confirm `pil_density > global_density` on ≥ 1 published active-region dataset |
| Astrophysical ingestors (galactic / neutrino / pulsar / GW) produce algebraically consistent carry-cascade errors | Feed ingestor output to deployed Appwrite `check_tree`; record pass/fail rate across event types |
| Orbital inspiral cascade (primary → secondary → tertiary → coalesce) maps qualitatively to multi-scale tearing-mode hierarchy | Compare depth distribution of cascade events to published plasmoid statistics (Loureiro 2007, Bhattacharjee 2009) |
| Fractal stress equation captures qualitative hierarchical tearing motif from tearing-mode literature (FKR 1963) | Compare depth distribution of cascade events to published plasmoid statistics |
| Internal thermodynamic ledger closure ΔE ≈ 0 maps metaphorically to MHD flux conservation | Formal mapping argument from ledger variables to MHD energy terms |
| Domain-agnostic quantisation Q(F) successfully discretises continuous telemetry into valid trit sequences | Benchmark noise-floor thresholds against known physical signal-to-noise ratios for each domain |

### What these mean in plain language

- The astrophysical ingestors are real, running code that produces real
  WAV files. The claim is not that they model plasma physics — it is
  that the algebra *reacts* to physical data structure in a consistent way.
- "Evocative computational analogy" and "structural bookkeeping layer"
  are the correct register. Not "physically faithful plasma simulator."

---

## `[CONJECTURAL]` — Open Research Hypotheses

Ultimate validation targets. Must not appear in abstracts or grant
applications without an explicit limitation statement. Use: "we
hypothesize," "remains future work," "motivates investigation."

| Claim | Validation path |
|---|---|
| Solar fractal sonification is physically faithful to reconnection dynamics | Quantitative benchmark: run same active region through MHD simulation + MCORE-1; compare event distributions |
| Multi-messenger universality: same kernel applies uniformly across all astrophysical domains | Domain-by-domain benchmark for each new data type before claiming universality |
| Physical energy parity: MCORE-1 internal thermal ledger maps linearly to joule/erg dissipation in real reconnection events | Correlation study against RHESSI / GOES X-ray flux for known flare events |
| Universal structural equivalence: DNA frameshift mutation and solar polarity inversion tear share a fundamental cross-scale topological law | Formal topological proof + independent experimental confirmation |
| Real-time predictive capability: MCORE-1 processes live FITS data fast enough to predict secondary flare coordinates before standard models | Live benchmark on SDO data stream with lead-time measurement |
| MCORE-1 acoustic output is perceptually optimal for scientific sonification | User study / psychoacoustic evaluation |

---

## Engineering Guardrails

1. All multi-modal astrophysical ingestion code **must remain isolated**
   in `experimental/astro_ingestor/` until externally benchmarked.
2. All audio rendering pipelines **must use** the `np.concatenate`
   integer-indexing pattern. Floating-point `t_offset` sliding windows
   are deprecated.
3. Automated agents **must tag** every output paragraph with
   `[ESTABLISHED]`, `[PLAUSIBLE]`, or `[CONJECTURAL]`.
4. **Promotion criteria** (no exceptions):
   - `[PLAUSIBLE]` → `[ESTABLISHED]`: reproducible code path + at least
     one external dataset validation.
   - `[CONJECTURAL]` → `[PLAUSIBLE]`: formal argument or peer-reviewed
     publication supporting the mechanism.

---

## Whitepaper Language Rules

1. Every prose paragraph must be internally tagged in draft comments
   before final copy.
2. `[CONJECTURAL]` claims use hedged language: "suggests," "motivates,"
   "is consistent with," "remains future work."
3. `[ESTABLISHED]` claims use direct language: "enforces," "implements,"
   "verifies."
4. Never use `[CONJECTURAL]` language in an abstract without a
   corresponding limitation statement.
5. "The universe speaks MCORE-1" is outreach/rhetorical language only
   — never in a methods section.

---

*Registry maintained by Jacob Walker / Symonic / ArchēLab.*
