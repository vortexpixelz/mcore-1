# VOR-117 — MCORE-1 repository audit

This document turns **Linear [VOR-117](https://linear.app/vortexpixel-solo-dev-env/issue/VOR-117/mcore-1-check)** from a vague “check the repo” beacon into a **repeatable audit**. The repo is a **layered research substrate**; the goal is **epistemic organization**, not more raw ideation.

**Use it as:** a sprint checklist in Linear (copy sections into sub-issues), or an internal pre-submission gate.

---

## Why an audit (not a todo)

| Old framing | Audit framing |
|-------------|----------------|
| “Is the repo cool?” | **What do we actually have** that survives adversarial compression? |
| Single theory | **Family of operators** — carry algebra, encodings, experiments, interpretation **separated** |
| Connect more domains | **Which parts** have invariants, nulls, and reproducible numbers? |

---

## Four buckets (partition the organism)

Everything in the tree should be **taggable** to one primary bucket. Cross-links are fine; **primary** bucket decides review standards.

| Bucket | Goal | Primary locations (this repo) |
|--------|------|----------------------------------|
| **Formal** | Precise operators, spec alignment, proof obligations | `src/mcore_py/`, `docs/MCORE-1-*.pdf`/spec, `tests/test_mcore.py` |
| **Experimental** | Synthetic tests, ablations, controlled comparisons | `s3_crystallization_analysis.py`, parts of `notebooks/*` |
| **Empirical** | Measured outcomes on real or standard data | SPARC notebooks, `S3_Winner_Subset_Characterization.ipynb`, `tests/GALATIC-ROTATION-CURVE-TEST.ipynb` |
| **Interpretive** | Cross-domain synthesis, metaphors, “why we care” | README narrative, `docs/*` essays, theory-forward notebook prose |

**Rule:** Interpretive text must not **silently upgrade** into Formal claims. See [notebooks/README.md](../notebooks/README.md) (OBSERVATION vs INTERPRETATION).

---

## Per-bucket audit criteria

For each **module, notebook, or doc section**, score or note:

1. **Invariant clarity** — What must hold? (types, conservation, BIC penalty, etc.)
2. **Falsifiability** — What observation would **kill** the claim?
3. **Baseline / control coverage** — Null model, shuffle, alternate parameterization, or alternate halo?
4. **Reproducibility** — One command or notebook path; pinned deps; data fetch documented?

Weak on (3) → **Experimental/Empirical** debt.  
Weak on (1)–(2) → **Formal** or **claim** debt.  
Strong on (1)–(3), heavy prose → keep in **Interpretive** or compress.

---

## Formal inventory (starter checklist)

- [ ] **Data model** — `Trit` / `Tension` / `Level` / `ProsodicUnit` / `Constituent` match spec §2.
- [ ] **Algebra** — `trit_add`, overflow, `tension_pair`, `complete` / `enumerate_patterns` match spec §3.
- [ ] **Checker** — `check_tree` error kinds match spec §10.1 intent.
- [ ] **Encoding** — TME-6, Base64-TME, MSS round-trips covered by tests.
- [ ] **Overlays** — Each overlay documents mapping to `{S1,S2,S3}` and conservation story.
- [ ] **Proof obligations** — Listed explicitly where “open in paper” (e.g. ε_T / T-bias optimality): **do not** assert in code comments as fact.

---

## Experimental & empirical inventory (starter checklist)

- [ ] **Notebook taxonomy** — Each notebook has category + top-cell template ([notebooks/README.md](../notebooks/README.md)).
- [ ] **SPARC / S3** — Adversarial controls documented (random anchor, permutation, alternate halo where implemented).
- [ ] **GJB2 / paper pipeline** — Lives primarily in [gjb2-mcore-sonification](https://github.com/vortexpixelz/gjb2-mcore-sonification); link from here, don’t duplicate fragile claims.
- [ ] **CI** — `pytest`, workflow on `main`; optional `[analysis]` extras for scripts.

---

## Interpretive layer — reviewer pressure map

These areas draw the **hardest** scrutiny; audit for **compression** (shorter claims, same evidence):

| Risk | Mitigation |
|------|------------|
| Ontology-heavy language | Move to `theory_notes`; keep API/README neutral. |
| Universal explanatory framing | Replace with “analogous constraints” + cite Formal layer. |
| Equivalence leaps across domains | Explicit “rhyme ≠ equivalence” sentence in paper/notebook. |
| Irreducibility / “binary cannot…” | Prefer “ternary gives native observability / reduced auxiliary state” where defensible. |
| ε_T / T-bias “inevitability” | State as **open** unless proved; link Linear discussion issue. |

---

## Publication candidate extraction

Ask: *Which artifacts could ship as a **methods** paper with minimal new work?*

Strong candidates usually bundle:

- Formal operator + encoding **definitions**
- One or two **empirical** pipelines with controls
- **Repro** (repo + tests + one flagship notebook executed cleanly)

Park cosmology / grand-unification prose for venues that expect it, or for Discussion with honest scope.

---

## Quick commands (reproducibility spot-check)

```bash
pip install -e ".[dev,analysis]"   # or .[dev] if analysis not needed
pytest
python -m mcore_py.cli smoke
python -m mcore_py.cli doctor
```

---

## Links

- Linear: [VOR-117 — mcore-1 check](https://linear.app/vortexpixel-solo-dev-env/issue/VOR-117/mcore-1-check)
- Notebook discipline: [notebooks/README.md](../notebooks/README.md)
- GitHub ↔ Linear workflow: [LINEAR.md](LINEAR.md)

When this audit is “done enough” for a milestone, **close or split VOR-117** into child issues per bucket so the beacon doesn’t stay a black hole.

**After governance changes:** run the **recompile → snapshot → deep-read** sequence ([RECOMPILE_AND_SNAPSHOT.md](RECOMPILE_AND_SNAPSHOT.md)) so artifacts and prose stay aligned.
