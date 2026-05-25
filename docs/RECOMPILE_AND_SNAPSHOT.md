# Recompile, snapshot, then deep-read

After **governance / taxonomy / audit** changes, “recompile” is not only `pip install`. It means **re-synchronizing artifacts** so figures, exports, PDFs, and READMEs do not encode **pre-membrane** semantics (overstrong claims, mixed layers).

Use this sequence **in order** (adapt paths to your machine):

1. **Recompile** — rebuild install + tests + any generated outputs you ship  
2. **Snapshot** — tag or archive a **release candidate** so citations and reviews anchor  
3. **Audit outputs** — spot-check generated files against current docs  
4. **Theorem / README alignment** — terminology matches softened claims  
5. **Null-model coverage** — controls still run; notebook cells not stale  
6. **Notation** — `Trit` / `Tension` / “S₃” used consistently across layers  
7. **Deep read** — paper + notebooks + audio narrative **only after** 1–6  

---

## 1. Recompile — **this repo (`mcore-1` / `mcore-py`)**

```bash
cd /path/to/mcore-1
python -m pip install -e ".[dev,analysis]"
python -m pytest
python -m mcore_py.cli doctor
python -m mcore_py.cli smoke
```

Optional (if you execute notebooks in CI or before release):

```bash
python -m jupyter nbconvert --execute --inplace notebooks/mcore1_demo.ipynb  # example
```

Optional lint:

```bash
python -m ruff check src tests
```

**Regenerate deliberately:**

| Artifact | How |
|----------|-----|
| Package metadata / wheel | `python -m pip install -e .` then `python -m build` if you publish wheels |
| Notebook outputs (cleared cells) | nbconvert `--execute` or clear outputs + re-run where policy requires clean diffs |
| Figures committed from notebooks | Re-run the cells that write `*.png` under `notebooks/` |
| Spec / theorem **PDF** | Built from your LaTeX source wherever it lives (often **not** this repo alone) |

This repo does **not** have a single `make paper` target; wire your paper build in the repo that holds `main.tex` (e.g. **gjb2-mcore-sonification** `paper/`).

---

## 2. Snapshot — **freeze semantic state**

After a good recompile pass:

```bash
git tag -a mcore-1-v0.2-review-candidate -m "RC: post governance + audit docs; pytest green"
git push origin mcore-1-v0.2-review-candidate
```

Or use **`submission-baseline`** / date-stamped tag — whatever your venue wants for “reproducibility anchor.”

**Why:** avoids infinite morph where the **paper**, **README**, **figures**, and **audio layer** drift from each other.

---

## 3–6. Audit checklist (quick)

- [ ] **Outputs:** Open regenerated figures; captions match OBSERVATION vs INTERPRETATION rules ([notebooks/README.md](notebooks/README.md)).  
- [ ] **README / audit docs:** No resurrected “irreducible” / “binary cannot” phrasing unless intentionally restored.  
- [ ] **Nulls:** SPARC / S3 control scripts still referenced; permutation / random-anchor cells unchanged or re-run.  
- [ ] **Sonification repo:** Rebuild WAV / analysis there with **projection ≠ proof** language in README/paper ([gjb2-mcore-sonification](https://github.com/vortexpixelz/gjb2-mcore-sonification)).  

---

## 7. Deep read

Only after the snapshot exists: read paper + key notebooks + Linear (**[VOR-117](https://linear.app/vortexpixel-solo-dev-env/issue/VOR-117/mcore-1-check)**) against **tagged tree**, not moving `main`.

---

## Related docs

- [VOR-117 repository audit](VOR-117_REPOSITORY_AUDIT.md)  
- [Notebook taxonomy & template](notebooks/README.md)  
- [Linear ↔ GitHub](LINEAR.md)
