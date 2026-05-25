# Notebooks — taxonomy and rigor

This folder (plus a few root-level `.ipynb` files) holds **research and demos**. The Python package under `src/mcore_py/` is the **formal core** (spec-backed, tested). These roles differ:

| Spine (`mcore_py`) | Notebooks |
|--------------------|-----------|
| Definitions, invariants, encodings | Hypotheses, plots, exploratory fits |
| `pytest` gates | Human judgment + figures |
| **Not** cosmology or clinical claims by itself | May cite external data; must separate **observation** from **interpretation** |

---

## Taxonomy (use names in Linear / PR descriptions)

| Category | Purpose | Typical contents |
|----------|---------|------------------|
| **`formalism/`** | Spec-aligned demos, algebra sanity | `mcore1_demo.ipynb`, quantum demos |
| **`experiments/`** | Empirical fits, real or synthetic data | SPARC rotation tests, Gabor analysis |
| **`controls/`** | Nulls, shuffles, ablations, baselines | Permutation tests, alternate halos |
| **`signal_processing/`** | Audio, spectrograms, uncertainty metrics | `gabor_analysis.ipynb` |
| **`genomics_proxies/`** | Encoding + divergence (often cross-repo) | Imputation / decay experiments |
| **`theory_notes/`** | Intuition only — **not** publication claims | Sketches; keep out of main paper line |

**Current layout:** most notebooks live in `notebooks/` at the repo root of this tree; a few live at repo root (`S3_*.ipynb`, `L7_*.ipynb`) for historical reasons. **Prefer new work under `notebooks/`** and the category subfolders as they grow.

### Inventory (this repo)

| Path | Suggested category |
|------|--------------------|
| `notebooks/mcore1_demo.ipynb` | formalism |
| `notebooks/mcore_q_demo.ipynb`, `mcore_q_decoherence.ipynb` | formalism / experiments |
| `notebooks/mcore_dsd_parallel.ipynb`, `mcore_drawdown_analysis.ipynb` | experiments |
| `notebooks/gabor_analysis.ipynb` | signal_processing |
| `notebooks/S3_Cosmological_Crystallization_Analysis.ipynb` | experiments + controls |
| `notebooks/L7_TNet_Imputation.ipynb`, `L7_Atomic_Decay_TNet_Imputation.ipynb` (if present) | genomics_proxies / experiments |
| `S3_Winner_Subset_Characterization.ipynb` | experiments + controls |
| `tests/GALATIC-ROTATION-CURVE-TEST.ipynb` | controls (mirror of SPARC test; CI path may vary) |

Related **paper + audio pipeline**: [gjb2-mcore-sonification](https://github.com/vortexpixelz/gjb2-mcore-sonification) (not this repo).

---

## Notebook template (copy into the top markdown cell)

Keep **Layer 1** (operators / code) aligned with `mcore_py` and the spec. Use this scaffold so **analogy ≠ equivalence** stays visible.

```markdown
## Meta
- **Linear:** VOR-___
- **Category:** (formalism | experiments | controls | …)
- **Spec / code refs:** e.g. MCORE-1 §…, `tests/test_mcore.py::…`

---

## DEFINITIONS
(State symbols, data source, preprocessing, and what “ternary / carry / S₃” means *in this notebook*.)

## CLAIM
(One falsifiable sentence, e.g. “Disk-anchored S₃ lowers BIC vs NFW-only for ≥X% of galaxies under …”)

## INVARIANT / CONSTRAINT
(What must hold: conservation, BIC penalty, bounds, etc.)

## NULL MODEL / BASELINE
(What “random” or simpler structure would look like; link control cells.)

## FAILURE CONDITIONS
(When you would abandon the claim: e.g. permutation null overlaps observed statistic.)

---

## OBSERVATION
(Figures, tables, numbers only — no cosmic or biological story here.)

## INTERPRETATION
(At most one short paragraph: “analogous constraints to …” — explicitly **not** “same mechanism as …”.)

## ADVERSARIAL CHECKLIST
- [ ] Random / shuffled control run
- [ ] Parameter-matched alternative (e.g. alternate halo / anchor)
- [ ] Scope stated: exploratory vs confirmatory
```

---

## “Publication fuel” vs “inspiration fuel”

- **Publication fuel:** bounded operator, declared null, reproducible numbers, control section, link to `pytest` / script entrypoints.
- **Inspiration fuel:** cross-domain metaphors, ontology — valuable in `theory_notes/`, not as substitutes for the sections above.

---

## Automation

- CLI smoke: `python -m mcore_py.cli notebook-smoke` (see root `README.md`).
- Prefer **nbconvert** or CI to execute `notebooks/*` only when dependencies and data paths are pinned.

For **Linear + PR linking**, see [docs/LINEAR.md](../docs/LINEAR.md) and the root [README](../README.md).
