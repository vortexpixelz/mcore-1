# Real-Data Replacement for the Synthetic DSD–GJB2 Parallel

**Status:** analysis complete, awaiting review. No canonical claim file, notebook,
or pitch text has been modified.

**Reproduce:** `python analysis/dsd_real_data_substitution.py --gjb2-repo <path>`

**Headline:** the DSD↔GJB2 *equivalence* does not survive the substitution. The
step-function **shape** is real and exactly reproducible; the **propagation law**
that the notebook calls "identical mathematics" is an artifact of the forced
`p = 1` fixture. A second, independent problem surfaced: the encoder's carry
register is provably inert, so the observed geometry cannot be a carry cascade
at all.

---

## 1. Exact source and provenance of the real streams

| Field | Value |
|---|---|
| Repository | `vortexpixelz/gjb2-mcore-sonification` |
| Commit | `4edcd3f15c033886168a900298bb27ad04178c6c` |
| Reference file | `data/refseq/NM_004004.6.fasta` |
| FASTA header | `NM_004004.6\|GJB2\|CDS\|681bp` |
| Raw file SHA-256 | `1bdb7716f21e366d870754f6ea0a8dcae23d353c216a5f32ded805d16b2aa72c` |
| Normalized CDS SHA-256 | `4e200a0cd3e11879057fe0a2557e25de6925934e798e63ca4dc9235dec08907a` |
| Length / start codon | 681 bp / `ATG` ✔ |
| Base at c.35 / c.235 | `G` ✔ / `C` ✔ |
| Encoder | `gjb2_sonification.dna_to_mcore_trits`, vendored verbatim |
| Committed receipt compared against | `paper/figures/analysis_stats.tex` |

The loader is **fail-closed**: it aborts if the reference is absent, the wrong
length, lacks the `ATG` start, or does not carry `G` at c.35 and `C` at c.235.
No synthetic fallback path exists.

### Reproduction of the committed receipts — exact

| Variant | first diff | total diff | diff after | tail | **trit density** | DNA density |
|---|---|---|---|---|---|---|
| c.35delG | 35 | 391 | 390 | 645 | **0.6047** | 0.7519 |
| c.235delC | 236 | 273 | 273 | 445 | **0.6135** | 0.7551 |

Every integer matches `analysis_stats.tex` exactly; both densities match to three
decimals (`0.605`, `0.613`). The DNA-level ("plain") densities `0.752` / `0.755`
also reproduce. The streams used below are therefore the same objects the
committed receipts describe.

---

## 2. Methods

1. **Streams.** WT = verified CDS. Mutants built by deleting one base at c.35 and
   c.235. All three encoded with the vendored encoder, then compared
   **prefix-aligned** (same 1-based index, truncated to the shorter stream) —
   identical to `code/analysis.py::_carry_propagation_stats`.
2. **Mismatch vectors.** Exact 0/1 indicator per position. No smoothing, no
   windowing, no synthetic substitution anywhere in the observed lane.
3. **Carry audit.** The encoder is run with `log_carry=True` and every carry value
   is inspected.
4. **Structure tests.** The downstream tail is split into 10 equal blocks; a
   least-squares slope and lag-1 autocorrelation are computed. A *cumulative*
   process must show a rising slope; a *memoryless* one must be flat.
5. **Model comparison.** Observed block densities are fitted against two laws —
   memoryless `ρ(n) = p_obs` and the notebook's cumulative `ρ(n) = 1-(1-p)^n` —
   with the cumulative model's `p` calibrated to match the observed *first* block,
   the most generous possible fit for the cascade hypothesis.
6. **Synthetic controls.** Bernoulli(`p`) downstream, zero upstream, 200
   replicates per `p`, seed 42. Labelled as controlled idealisations throughout;
   never mixed with the observed lane.

---

## 3. Sensitivity table

Synthetic controls (idealisations) with the two observed streams on the same axes:

| p | mean density | block slope /base | lag-1 ac | n_max | DSD cumulative @ depth 3 | flat? |
|---|---|---|---|---|---|---|
| 0.500 | 0.4981 | −2.4e−06 | −0.0025 | 0 | 0.8750 | yes |
| 0.550 | 0.5502 | −2.2e−06 | −0.0012 | 0 | 0.9089 | yes |
| 0.600 | 0.6014 | +6.9e−06 | +0.0014 | 0 | 0.9360 | yes |
| **0.605** | 0.6079 | +7.9e−06 | −0.0021 | 0 | 0.9384 | yes |
| **0.613** | 0.6128 | +1.4e−05 | +0.0031 | 0 | 0.9420 | yes |
| 0.650 | 0.6491 | −7.6e−06 | −0.0003 | 0 | 0.9571 | yes |
| 0.750 | 0.7485 | −1.5e−06 | +0.0019 | 0 | 0.9844 | yes |
| 1.000 | 1.0000 | 0.0 | undefined | 0 | 1.0000 | yes |
| **OBSERVED c.35delG** | **0.6047** | +5.3e−06 | +0.0807 | 0 | 0.9382 | — |
| **OBSERVED c.235delC** | **0.6135** | −2.2e−04 | +0.0642 | 0 | 0.9423 | — |

Observed downstream density in 10 equal blocks:

```
c.35delG   0.531  0.646  0.609  0.631  0.672  0.585  0.531  0.615  0.656  0.569
c.235delC  0.682  0.689  0.614  0.600  0.523  0.622  0.614  0.644  0.636  0.511
```

What a cumulative cascade at the *same* starting rate predicts instead:

```
p=0.605    0.605  0.844  0.938  0.976  0.990  0.996  0.998  0.999  1.000  1.000
```

### Model comparison — the decisive test

| Variant | RMSE memoryless | RMSE cumulative | Winner |
|---|---|---|---|
| c.35delG | **0.0471** | 0.3354 | memoryless — cumulative is 7.1× worse |
| c.235delC | **0.0555** | 0.3653 | memoryless — cumulative is 6.6× worse |

The observed tail is a **constant-rate memoryless process**, not an accumulating
cascade. At `p = 1` the two laws are indistinguishable (both are a flat step at
1.0) — which is exactly why the synthetic fixture appeared to confirm the
equivalence.

---

## 4. Which existing conclusions survive

| Conclusion | Verdict | Basis |
|---|---|---|
| Zero trit mismatch upstream of the deletion | **ROBUST AT OBSERVED DENSITY** | exact; first diff at 35 / 236 |
| Step function in mismatch density at the site | **ROBUST AT OBSERVED DENSITY** | 0.0000 → ~0.61 discontinuity confirmed |
| A point fault corrupts an extended downstream region | **QUALITATIVE ONLY** | shape shared; propagation law differs |
| `n_max = 0` for GJB2 under the S3 budget | **THRESHOLD-DEPENDENT** | true for *any* p ≥ 0.30, so it carries no evidential weight |

The upstream-silence and step-discontinuity results are genuinely strong: the
first differing position is at the deletion site to the base, with exactly zero
mismatch before it. That is a real, exactly reproducible structural finding.

---

## 5. Which conclusions fail or weaken

| Conclusion | Verdict | Basis |
|---|---|---|
| Downstream density ≈ 1.0 / "every downstream codon differs" | **P=1 ARTIFACT** | 255 of 645 downstream positions (39.5%) are **unchanged** |
| "The GJB2 case is the p→1 limit of the DSD formula" | **P=1 ARTIFACT** | degenerate limit; the law does not transfer at p = 0.605 |
| "Identical mathematics" / carry-cascade equivalence | **P=1 ARTIFACT** | cumulative law rejected at 6.6–7.1× worse RMSE |
| Mismatch geometry attributable to encoder carry | **P=1 ARTIFACT** | 0 non-zero carry events in 681 positions |
| DSD leak model itself for engineered circuits | **UNRESOLVED** | untested; no DSD measurements exist in either repo |
| Sanskrit-prosody limb of the three-way unification | **UNRESOLVED** | out of scope of this substitution |

### 5a. The carry register is inert — an independent problem

`base_val = {A:0, C:1, G:2, T:0}` with a `+1` bonus for `T`. The per-base
contribution is therefore bounded by 2, so `val = contribution + carry ≤ 2` and
`carry = val // 3 == 0` at **every** position. Measured: **0 non-zero carry
events across all 681 positions.**

The encoder is a memoryless per-base lookup — `A→0, C→1, G→2, T→1` — with no
state and no propagation. Three consequences:

- The notebook's §3 statement that "each codon (3-base group) maps to a trit
  value" and "the carry from one codon propagates to the next" is **incorrect
  on both counts**. The map is per-base, not per-codon, and nothing propagates.
- "Carry cascade" cannot describe the GJB2 geometry. What actually happens is a
  **frame shift in the sequence**, read through a stateless map.
- The variable named `carry_density_after_site` in `code/analysis.py` is a
  misnomer. It is a trit-level density; no carry is involved.

### 5b. The observed density is fully explained without any cascade

After a deletion at position *k*, the mutant reads `wt[i+1]` where WT reads
`wt[i]`. So downstream mismatch at *i* is exactly `trit(wt[i]) != trit(wt[i+1])`
— a pure one-base shift through a stateless map. That model predicts:

| Variant | Predicted | Observed | Δ |
|---|---|---|---|
| c.35delG | 0.6047 | 0.6047 | **0.0000** |
| c.235delC | 0.6135 | 0.6135 | **0.0000** |

Zero residual. There is no unexplained variance left for a cascade mechanism to
account for. The i.i.d. estimate from base composition alone (1 − Σq²= 0.6233)
already lands within 0.02 of both observations — because `C` and `T` both map to
trit 1, roughly 3/8 of shifted pairs collide and produce no mismatch. **The ~60%
figure is a property of GJB2's base composition under a 2-to-1 encoding, not
evidence of fault propagation.**

This also explains why the trit density (0.605) sits *below* the DNA density
(0.752): encoder collisions absorb about a fifth of the nucleotide differences.

---

## 6. Recommended repository changes

Ordered by urgency. None are applied.

**A. `notebooks/mcore_dsd_parallel.ipynb` — retitle and re-scope (required
before the equivalence is cited anywhere).**
- Title: "Carry Cascade Equivalence" → **"Structural Parallel"**. The word
  *equivalence* is not supported.
- §3 prose: remove "each codon (3-base group) maps to a trit value" and "the
  carry from one codon propagates to the next". Replace with the per-base
  stateless map and state that the carry register is provably inert.
- §4 table row "Jumps to ~1.0 and stays" → "Jumps to ~0.61 and stays flat".
  Remove "immediate 100% corruption".
- §9 "The GJB2 case is the p→1 limit of the DSD formula" — remove. Replace with
  the measured contrast: DSD accumulates, GJB2 does not.
- §6 item 4 "GJB2 as worst case (p=1)" — remove or relabel explicitly as a
  hypothetical upper bound, never as observed.
- Final cell: `'GJB2 c.35delG: p=100% (frameshift), n_max=0'` → report the
  measured 0.605 and note `n_max = 0` holds for any p ≥ 0.30.
- Keep the synthetic fixture, relabelled **"controlled idealisation — limiting
  case only, not GJB2 evidence."**

**B. `code/analysis.py` (sonification repo) — rename `carry_*` keys** to
`trit_*` (e.g. `carry_density_after_site` → `trit_density_after_site`), with a
compatibility alias if the TeX macros depend on the old names. The current name
asserts a mechanism the encoder does not have.

**C. Add this analysis** (`analysis/dsd_real_data_substitution.py` +
`analysis/DSD_REAL_DATA_FINDINGS.md`) as the standing receipt for the real-data
lane.

**D. Check for the same language elsewhere.** `docs/CLAIMS.md`, `README.md`, and
`docs/MCORE-1-Acoustic-Quantum-Extension-Spec-v0.2.md` all carry mismatch claims;
PR #46 corrected the *numbers* but the *carry-cascade mechanism* wording was not
in scope and should be re-audited against §5a.

---

## 7. Exact pitch-safe wording

Use verbatim. Every number is reproducible from the script.

> **Safe — the structural result:**
>
> "Encoding the verified GJB2 reference (NM_004004.6, 681 bp CDS) into MCORE-1
> trits and applying the two most common pathogenic deletions produces an exact
> step function: zero trit mismatch upstream of the deletion site, and a
> sustained downstream mismatch density of 0.605 for c.35delG and 0.613 for
> c.235delC. The first differing position falls at the deletion site to the base.
> Independent audio-derived estimates from the sonified streams agree at 0.598
> and 0.602, and the DNA-derived and audio-decoded trit streams agree exactly."

> **Safe — the analogy, correctly bounded:**
>
> "This has the same *shape* as leak accumulation in DNA strand-displacement
> circuits: a fault injected at one point, silence before it, degradation after.
> We are describing a shared structural motif, not a quantitative equivalence —
> the DSD leak model accumulates with circuit depth, whereas the observed GJB2
> mismatch density is flat downstream. Whether a deeper correspondence exists is
> open."

> **If asked what drives the ~60%:**
>
> "It is a one-base frame shift read through the trit map. Because the encoding
> sends both C and T to the same trit, roughly a third of shifted positions
> collide and produce no mismatch — which is why the trit density (0.605) sits
> below the nucleotide density (0.752). A pure shift model reproduces both
> measured densities to four decimal places with zero residual."

> **If asked about carry propagation — answer this, not the notebook:**
>
> "The DNA encoder's carry register is provably inert on this alphabet: we
> measured zero non-zero carry events across all 681 positions. The map is a
> stateless per-base lookup. The frameshift geometry is real; attributing it to
> carry propagation would be wrong, and we corrected that."

### Do not say

- ❌ "identical mathematics" / "proves the equivalence" / "isomorphic"
- ❌ "p = 1" or "100% downstream mismatch" as anything observed
- ❌ "carry cascade" as the mechanism for the GJB2 result
- ❌ "every downstream codon differs" — 39.5% of them do not
- ❌ "validated" on the strength of two deletions in one gene — say
  "reproduced exactly for the two most common pathogenic deletions"

---

## 8. Diff preview

Branch `claude/mcore-1-assessment-gcu9fn` at `21cf94b`. **Nothing committed,
nothing pushed.** Two new files, no modifications to any existing file:

```
 analysis/DSD_REAL_DATA_FINDINGS.md      | new, 288 lines
 analysis/dsd_real_data_substitution.py  | new, 726 lines
```

`git status --short`:

```
?? analysis/
```

The existing notebooks, `docs/CLAIMS.md`, `README.md`, and the spec document are
untouched, as required. Section 6 lists what would change next, pending review.
