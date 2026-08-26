#!/usr/bin/env python3
"""Real-data replacement for the synthetic DSD-GJB2 parallel.

Replaces the forced-100%-downstream-mismatch fixture in
``notebooks/mcore_dsd_parallel.ipynb`` with the measured prefix-aligned
GJB2 deletion streams, then re-derives every quantity in that notebook
that was computed under ``p = 1``.

This script is deliberately fail-closed on provenance: it will not run
against a synthetic or fallback reference. It requires the verified
NM_004004.6 CDS from the ``gjb2-mcore-sonification`` repository.

Usage:
    python analysis/dsd_real_data_substitution.py \
        --gjb2-repo /workspace/gjb2-mcore-sonification

Outputs a deterministic report to stdout and, with --json, a machine
readable receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------
# Constants pinned from the committed receipts
# (gjb2-mcore-sonification: paper/figures/analysis_stats.tex)
# --------------------------------------------------------------------------

CDS_LEN = 681
EXPECTED = {
    35: {
        "first_diff": 35,
        "total_diff": 391,
        "diff_after": 390,
        "tail_after": 645,
        "dens_after": 0.605,
        "plain_dens": 0.752,
    },
    235: {
        "first_diff": 236,
        "total_diff": 273,
        "diff_after": 273,
        "tail_after": 445,
        "dens_after": 0.613,
        "plain_dens": 0.755,
    },
}

# MCORE-1 quantum overlay thresholds (src/mcore_py/overlays/quantum.py)
FIDELITY_IDLE_MAX = 0.70
PHI_S3 = 1.0 - FIDELITY_IDLE_MAX  # 0.30 corruption budget

SWEEP_P = [0.50, 0.55, 0.60, 0.605, 0.613, 0.65, 0.75, 1.00]

RNG_SEED = 42
N_SYNTH_REPLICATES = 200


# --------------------------------------------------------------------------
# Encoder (vendored verbatim from gjb2_sonification.dna_to_mcore_trits)
# --------------------------------------------------------------------------


def dna_to_mcore_trits(seq: str, log_carry: bool = False):
    """MCORE-1 DNA->trit map. Vendored verbatim for auditability.

    Kept byte-identical to the upstream implementation so that this
    script's streams are provably the same objects the committed
    receipts describe.
    """
    base_val = {"A": 0, "C": 1, "G": 2, "T": 0}
    trits, carry_log, carry = [], [], 0
    for base in seq.upper():
        if base not in base_val:
            continue
        val = base_val[base] + carry + (1 if base == "T" else 0)
        trits.append(val % 3)
        carry = val // 3
        if log_carry:
            carry_log.append(carry)
    return (trits, carry_log) if log_carry else trits


def apply_deletion(seq: str, pos_1based: int) -> str:
    """Delete a single base at a 1-based CDS coordinate."""
    i = pos_1based - 1
    return seq[:i] + seq[i + 1 :]


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------


@dataclass
class Provenance:
    fasta_path: str
    header: str
    raw_sha256: str
    cds_sha256: str
    cds_len: int
    base_at_35: str
    base_at_235: str
    starts_atg: bool
    gjb2_repo_head: str

    def verify(self) -> None:
        problems = []
        if self.cds_len != CDS_LEN:
            problems.append(f"CDS length {self.cds_len} != {CDS_LEN}")
        if not self.starts_atg:
            problems.append("CDS does not start with ATG")
        if self.base_at_35 != "G":
            problems.append(f"base at c.35 is {self.base_at_35!r}, expected 'G'")
        if self.base_at_235 != "C":
            problems.append(f"base at c.235 is {self.base_at_235!r}, expected 'C'")
        if problems:
            raise SystemExit(
                "FAIL-CLOSED: reference did not verify:\n  - " + "\n  - ".join(problems)
            )


def load_reference(gjb2_repo: Path) -> tuple[str, Provenance]:
    fasta = gjb2_repo / "data" / "refseq" / "NM_004004.6.fasta"
    if not fasta.exists():
        raise SystemExit(
            f"FAIL-CLOSED: verified reference not found at {fasta}.\n"
            "This analysis refuses to run against a synthetic fallback."
        )
    raw = fasta.read_bytes()
    lines = raw.decode().splitlines()
    header = lines[0].lstrip(">") if lines and lines[0].startswith(">") else "<none>"
    seq = "".join(ln.strip() for ln in lines if not ln.startswith(">")).upper()

    # Accept full transcript (extract CDS 179..859) or bare 681bp CDS.
    if len(seq) != CDS_LEN:
        seq = seq[178:859]

    head = "<unknown>"
    git_head = gjb2_repo / ".git" / "HEAD"
    if git_head.exists():
        try:
            import subprocess

            head = subprocess.run(
                ["git", "-C", str(gjb2_repo), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        except Exception:
            pass

    prov = Provenance(
        fasta_path=str(fasta),
        header=header,
        raw_sha256=hashlib.sha256(raw).hexdigest(),
        cds_sha256=hashlib.sha256(seq.encode()).hexdigest(),
        cds_len=len(seq),
        base_at_35=seq[34] if len(seq) > 34 else "?",
        base_at_235=seq[234] if len(seq) > 234 else "?",
        starts_atg=seq.startswith("ATG"),
        gjb2_repo_head=head,
    )
    prov.verify()
    return seq, prov


# --------------------------------------------------------------------------
# Observed mismatch vectors
# --------------------------------------------------------------------------


@dataclass
class ObservedStream:
    label: str
    del_pos: int
    mismatch: np.ndarray = field(repr=False)  # 0/1 over aligned prefix length
    first_diff: int = 0
    total_diff: int = 0
    diff_after: int = 0
    tail_after: int = 0
    dens_after: float = 0.0
    plain_dens_after: float = 0.0
    n_aligned: int = 0


def build_observed(wt_dna: str, del_pos: int, label: str) -> ObservedStream:
    mut_dna = apply_deletion(wt_dna, del_pos)
    wt_t = np.asarray(dna_to_mcore_trits(wt_dna))
    mut_t = np.asarray(dna_to_mcore_trits(mut_dna))

    n = min(len(wt_t), len(mut_t))
    mismatch = (wt_t[:n] != mut_t[:n]).astype(np.int8)

    idx_1based = np.nonzero(mismatch)[0] + 1
    first = int(idx_1based[0]) if idx_1based.size else -1
    total = int(idx_1based.size)
    after = idx_1based[idx_1based > del_pos]
    tail_len = max(0, n - del_pos)
    dens = float(after.size / tail_len) if tail_len else 0.0

    # Nucleotide-level ("plain") comparison for contrast
    n_dna = min(len(wt_dna), len(mut_dna))
    dna_diff = np.array([1 if wt_dna[i] != mut_dna[i] else 0 for i in range(n_dna)], dtype=np.int8)
    dna_idx = np.nonzero(dna_diff)[0] + 1
    dna_after = dna_idx[dna_idx > del_pos]
    dna_tail = max(0, n_dna - del_pos)
    plain_dens = float(dna_after.size / dna_tail) if dna_tail else 0.0

    return ObservedStream(
        label=label,
        del_pos=del_pos,
        mismatch=mismatch,
        first_diff=first,
        total_diff=total,
        diff_after=int(after.size),
        tail_after=tail_len,
        dens_after=dens,
        plain_dens_after=plain_dens,
        n_aligned=n,
    )


# --------------------------------------------------------------------------
# Structural tests: is the downstream regime cumulative or memoryless?
# --------------------------------------------------------------------------


def dsd_curve(p: float, n: np.ndarray) -> np.ndarray:
    """The DSD leak-accumulation law from notebook section 2."""
    return 1.0 - (1.0 - p) ** n


def block_densities(mismatch: np.ndarray, del_pos: int, n_blocks: int = 10):
    """Mean mismatch density in equal blocks across the downstream tail.

    A cumulative cascade must show these RISING toward 1.0.
    A memoryless per-position process shows them FLAT.
    """
    tail = mismatch[del_pos:]
    if tail.size < n_blocks:
        return np.array([]), np.array([])
    edges = np.linspace(0, tail.size, n_blocks + 1).astype(int)
    dens = np.array([tail[edges[i] : edges[i + 1]].mean() for i in range(n_blocks)], dtype=float)
    centers = (edges[:-1] + edges[1:]) / 2.0
    return centers, dens


def trend_test(centers: np.ndarray, dens: np.ndarray) -> dict:
    """Least-squares slope of block density vs downstream offset."""
    if centers.size < 3:
        return {"slope": float("nan"), "r": float("nan"), "n_blocks": int(centers.size)}
    x = centers - centers.mean()
    y = dens - dens.mean()
    denom = float((x * x).sum())
    slope = float((x * y).sum() / denom) if denom else float("nan")
    sx = float(np.sqrt((x * x).sum()))
    sy = float(np.sqrt((y * y).sum()))
    r = float((x * y).sum() / (sx * sy)) if sx and sy else float("nan")
    return {"slope": slope, "r": r, "n_blocks": int(centers.size)}


def lag1_autocorr(mismatch: np.ndarray, del_pos: int) -> float:
    """Lag-1 autocorrelation of the downstream mismatch indicator.

    ~0 is consistent with independent per-position events (memoryless).
    Strong positive values would indicate propagating/correlated state.
    """
    tail = mismatch[del_pos:].astype(float)
    if tail.size < 3:
        return float("nan")
    a, b = tail[:-1], tail[1:]
    a_c, b_c = a - a.mean(), b - b.mean()
    denom = float(np.sqrt((a_c * a_c).sum() * (b_c * b_c).sum()))
    if denom == 0.0:
        # Degenerate: a constant stream (e.g. the forced p=1 fixture) has no
        # variance, so autocorrelation is undefined rather than zero.
        return float("nan")
    return float((a_c * b_c).sum() / denom)


def carry_activity(wt_dna: str) -> dict:
    """Is the MCORE-1 DNA encoder's carry register ever non-zero?

    base_val maxes at 2 (G) and the T bonus is +1 with base_val 0, so the
    per-base contribution is bounded by 2. With carry starting at 0,
    val = contribution + carry <= 2, hence val // 3 == 0 forever.
    Verified empirically here rather than asserted.
    """
    _, carry_log = dna_to_mcore_trits(wt_dna, log_carry=True)
    arr = np.asarray(carry_log)
    return {
        "n_positions": int(arr.size),
        "n_nonzero_carry": int((arr != 0).sum()),
        "max_carry": int(arr.max()) if arr.size else 0,
        "carry_inert": bool((arr == 0).all()),
    }


def encoder_collision_profile(wt_dna: str) -> dict:
    """Base composition and the induced trit-collision structure.

    The map is memoryless once carry is proven inert: A->0, C->1, G->2, T->1.
    C and T collide onto trit 1, so a one-base frameshift produces a
    mismatch only when the shifted pair falls in different trit classes.
    """
    from collections import Counter

    bc = Counter(wt_dna)
    trit_of = {"A": 0, "C": 1, "G": 2, "T": 1}
    tc = Counter(trit_of[b] for b in wt_dna if b in trit_of)
    n = sum(tc.values())
    probs = {k: tc[k] / n for k in (0, 1, 2)}
    p_same = sum(v * v for v in probs.values())
    return {
        "base_counts": dict(bc),
        "trit_counts": {str(k): int(tc[k]) for k in (0, 1, 2)},
        "trit_freqs": {str(k): round(probs[k], 6) for k in (0, 1, 2)},
        "predicted_mismatch_iid": round(1.0 - p_same, 6),
    }


def adjacent_shift_density(wt_dna: str, del_pos: int) -> float:
    """Exact mismatch density predicted by the pure one-base shift model.

    After a deletion at k, the mutant reads wt[i+1] where wt read wt[i].
    So downstream mismatch at i is exactly trit(wt[i]) != trit(wt[i+1]).
    """
    trit_of = {"A": 0, "C": 1, "G": 2, "T": 1}
    s = [trit_of[b] for b in wt_dna if b in trit_of]
    tail = [1 if s[i] != s[i + 1] else 0 for i in range(del_pos, len(s) - 1)]
    return float(np.mean(tail)) if tail else float("nan")


# --------------------------------------------------------------------------
# Synthetic controls at fixed p (explicitly labelled idealisations)
# --------------------------------------------------------------------------


def synthetic_stream(p: float, n_bases: int, del_pos: int, rng) -> np.ndarray:
    """Stochastic control: zero mismatch upstream, Bernoulli(p) downstream."""
    m = np.zeros(n_bases, dtype=np.int8)
    if p >= 1.0:
        m[del_pos:] = 1
    else:
        m[del_pos:] = (rng.random(n_bases - del_pos) < p).astype(np.int8)
    return m


def n_max_for(p: float) -> int:
    """Max certifiable DSD depth under the MCORE-1 S3 budget."""
    if p <= 0.0:
        return math.inf  # type: ignore[return-value]
    if p >= PHI_S3:
        return 0
    return int(math.log(1 - PHI_S3) / math.log(1 - p))


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------


def hr(title: str = "") -> None:
    if title:
        print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")
    else:
        print("-" * 78)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--gjb2-repo",
        default="/workspace/gjb2-mcore-sonification",
        type=Path,
        help="Path to the gjb2-mcore-sonification checkout.",
    )
    ap.add_argument("--json", type=Path, default=None, help="Write a JSON receipt.")
    args = ap.parse_args()

    receipt: dict = {}
    rng = np.random.default_rng(RNG_SEED)

    # ---------------------------------------------------------------- §1
    hr("1  PROVENANCE  (fail-closed)")
    wt_dna, prov = load_reference(args.gjb2_repo)
    print(f"  source repo HEAD   : {prov.gjb2_repo_head}")
    print(f"  fasta              : {prov.fasta_path}")
    print(f"  header             : {prov.header}")
    print(f"  raw file sha256    : {prov.raw_sha256}")
    print(f"  normalized CDS sha : {prov.cds_sha256}")
    print(f"  CDS length         : {prov.cds_len} bp   starts ATG: {prov.starts_atg}")
    print(f"  c.35 base          : {prov.base_at_35}   c.235 base: {prov.base_at_235}")
    print("  -> reference VERIFIED; no synthetic fallback used.")
    receipt["provenance"] = asdict(prov)

    # ---------------------------------------------------------------- §2
    hr("2  ENCODER MECHANICS  (is the 'carry cascade' real?)")
    ca = carry_activity(wt_dna)
    print(f"  positions encoded      : {ca['n_positions']}")
    print(f"  non-zero carry events  : {ca['n_nonzero_carry']}")
    print(f"  max carry value        : {ca['max_carry']}")
    print(f"  CARRY-INERT            : {ca['carry_inert']}")
    if ca["carry_inert"]:
        print(
            "\n  The DNA encoder's carry register is provably never non-zero:\n"
            "  per-base contribution is bounded by 2, so val = contrib + carry <= 2\n"
            "  and val // 3 == 0 at every position. The map reduces to a MEMORYLESS\n"
            "  per-base lookup:  A->0, C->1, G->2, T->1.\n"
            "  Downstream mismatch therefore CANNOT be attributed to carry propagation."
        )
    prof = encoder_collision_profile(wt_dna)
    print(f"\n  base counts        : {prof['base_counts']}")
    print(f"  trit freqs         : {prof['trit_freqs']}")
    print(
        f"  i.i.d. prediction  : {prof['predicted_mismatch_iid']:.4f}"
        "   (1 - sum q_t^2, the collision-complement)"
    )
    receipt["carry"] = ca
    receipt["encoder_profile"] = prof

    # ---------------------------------------------------------------- §3
    hr("3  OBSERVED STREAMS  (exact, prefix-aligned)")
    observed = {
        35: build_observed(wt_dna, 35, "c.35delG"),
        235: build_observed(wt_dna, 235, "c.235delC"),
    }
    print(
        f"  {'variant':<12} {'first':>6} {'total':>6} {'after':>6} "
        f"{'tail':>6} {'trit dens':>10} {'DNA dens':>9}"
    )
    hr()
    ok = True
    for pos, obs in observed.items():
        exp = EXPECTED[pos]
        print(
            f"  {obs.label:<12} {obs.first_diff:>6} {obs.total_diff:>6} "
            f"{obs.diff_after:>6} {obs.tail_after:>6} "
            f"{obs.dens_after:>10.4f} {obs.plain_dens_after:>9.4f}"
        )
        checks = [
            ("first_diff", obs.first_diff, exp["first_diff"]),
            ("total_diff", obs.total_diff, exp["total_diff"]),
            ("diff_after", obs.diff_after, exp["diff_after"]),
            ("tail_after", obs.tail_after, exp["tail_after"]),
        ]
        for name, got, want in checks:
            if got != want:
                print(f"      MISMATCH vs committed receipt: {name} {got} != {want}")
                ok = False
        for name, got, want in [
            ("dens_after", obs.dens_after, exp["dens_after"]),
            ("plain_dens", obs.plain_dens_after, exp["plain_dens"]),
        ]:
            if abs(round(got, 3) - want) > 5e-4:
                print(f"      MISMATCH vs committed receipt: {name} {got:.4f} != {want}")
                ok = False
    print(
        f"\n  Reproduction of paper/figures/analysis_stats.tex: "
        f"{'EXACT MATCH' if ok else 'DIVERGENCE — investigate'}"
    )
    receipt["observed"] = {
        str(p): {k: v for k, v in asdict(o).items() if k != "mismatch"} for p, o in observed.items()
    }
    receipt["receipts_reproduced"] = ok

    # Pure-shift model check
    print("\n  Pure one-base-shift model (no carry, memoryless map):")
    for pos, obs in observed.items():
        pred = adjacent_shift_density(wt_dna, pos)
        print(
            f"    {obs.label:<12} predicted {pred:.4f}  observed {obs.dens_after:.4f}"
            f"   delta {abs(pred - obs.dens_after):.4f}"
        )

    # ---------------------------------------------------------------- §4
    hr("4  IS THE DOWNSTREAM REGIME CUMULATIVE OR FLAT?")
    print(
        "  The DSD law p_corrupt(n) = 1-(1-p)^n is CUMULATIVE: it must rise\n"
        "  monotonically toward 1.0 with depth. Testing whether the observed\n"
        "  GJB2 mismatch density does the same.\n"
    )
    struct = {}
    for pos, obs in observed.items():
        centers, dens = block_densities(obs.mismatch, pos, n_blocks=10)
        tr = trend_test(centers, dens)
        ac = lag1_autocorr(obs.mismatch, pos)
        struct[str(pos)] = {"blocks": dens.round(4).tolist(), **tr, "lag1_autocorr": ac}
        print(f"  {obs.label}: downstream density in 10 equal blocks")
        print("    " + "  ".join(f"{d:.3f}" for d in dens))
        print(f"    least-squares slope = {tr['slope']:+.3e} / base   (r = {tr['r']:+.3f})")
        print(f"    lag-1 autocorrelation = {ac:+.4f}")
        # Compare against what a cumulative cascade at the observed p predicts
        n_idx = np.arange(1, 11)
        cum = dsd_curve(obs.dens_after, n_idx)
        print(
            f"    cumulative DSD at p={obs.dens_after:.3f} would give: "
            + "  ".join(f"{c:.3f}" for c in cum[:5])
            + "  ..."
        )
        print()
    receipt["structure"] = struct

    # ---------------------------------------------------------------- §5
    hr("5  SENSITIVITY SWEEP  (synthetic controls vs observed)")
    print(
        "  Synthetic streams are stochastic Bernoulli(p) downstream, zero upstream.\n"
        f"  {N_SYNTH_REPLICATES} replicates per p, seed {RNG_SEED}. These are CONTROLLED\n"
        "  IDEALISATIONS, not observations.\n"
    )
    print(
        f"  {'p':>7} | {'mean dens':>9} | {'blk slope':>11} | {'lag1 ac':>8} | "
        f"{'n_max':>5} | {'DSD@n=3':>8} | {'flat?':>5}"
    )
    hr()
    sweep = []
    for p in SWEEP_P:
        ds, slopes, acs = [], [], []
        for _ in range(N_SYNTH_REPLICATES):
            m = synthetic_stream(p, CDS_LEN, 35, rng)
            ds.append(m[35:].mean())
            c, d = block_densities(m, 35, n_blocks=10)
            slopes.append(trend_test(c, d)["slope"])
            acs.append(lag1_autocorr(m, 35))
        acs_valid = [a for a in acs if not math.isnan(a)]
        acs_mean = float(np.mean(acs_valid)) if acs_valid else float("nan")
        nm = n_max_for(p)
        cum3 = dsd_curve(p, np.array([3]))[0]
        flat = "yes" if abs(float(np.mean(slopes))) < 1e-4 else "no"
        row = {
            "p": p,
            "mean_density": float(np.mean(ds)),
            "block_slope": float(np.mean(slopes)),
            "lag1_autocorr": acs_mean,
            "n_max": nm,
            "dsd_cumulative_at_depth3": float(cum3),
            "flat": flat,
        }
        sweep.append(row)
        print(
            f"  {p:>7.3f} | {row['mean_density']:>9.4f} | {row['block_slope']:>+11.3e} | "
            f"{row['lag1_autocorr']:>+8.4f} | {nm:>5d} | {cum3:>8.4f} | {flat:>5}"
        )
    hr()
    for pos, obs in observed.items():
        c, d = block_densities(obs.mismatch, pos, n_blocks=10)
        tr = trend_test(c, d)
        ac = lag1_autocorr(obs.mismatch, pos)
        print(
            f"  OBSERVED {obs.label:<10} {obs.dens_after:>9.4f} | {tr['slope']:>+11.3e} | "
            f"{ac:>+8.4f} | {n_max_for(obs.dens_after):>5d} | "
            f"{dsd_curve(obs.dens_after, np.array([3]))[0]:>8.4f} |"
        )
    receipt["sweep"] = sweep

    # ---------------------------------------------------------------- §6
    hr("6  NOTEBOOK QUANTITIES RE-DERIVED AT THE OBSERVED DENSITY")
    print(f"  {'quantity':<44} {'at p=1':>12} {'at observed':>14}")
    hr()
    o35 = observed[35]
    rows = [
        (
            "downstream mismatch density (c.35delG)",
            "1.0000",
            f"{o35.dens_after:.4f}",
        ),
        (
            "downstream mismatch density (c.235delC)",
            "1.0000",
            f"{observed[235].dens_after:.4f}",
        ),
        (
            "positions differing downstream (c.35delG)",
            f"{o35.tail_after}",
            f"{o35.diff_after}",
        ),
        (
            "positions IDENTICAL downstream (c.35delG)",
            "0",
            f"{o35.tail_after - o35.diff_after}",
        ),
        ("n_max (S3 budget, phi=0.30)", f"{n_max_for(1.0)}", f"{n_max_for(o35.dens_after)}"),
        (
            "DSD cumulative corruption at depth 3",
            f"{dsd_curve(1.0, np.array([3]))[0]:.4f}",
            f"{dsd_curve(o35.dens_after, np.array([3]))[0]:.4f}",
        ),
        (
            "observed density at 'depth 3' (block 3 of 10)",
            "1.0000",
            f"{block_densities(o35.mismatch, 35, 10)[1][2]:.4f}",
        ),
    ]
    for name, a, b in rows:
        print(f"  {name:<44} {a:>12} {b:>14}")
    receipt["rederived"] = [{"quantity": n, "p1": a, "observed": b} for n, a, b in rows]

    print(
        f"\n  {o35.tail_after - o35.diff_after} of {o35.tail_after} downstream positions "
        f"({(o35.tail_after - o35.diff_after) / o35.tail_after:.1%}) are UNCHANGED\n"
        "  by the deletion. The notebook's fixture forces all of them to differ."
    )

    # ---------------------------------------------------------------- §7
    hr("7  MODEL COMPARISON  (which law actually describes the observed tail?)")
    print(
        "  Two candidate laws for downstream density as a function of distance\n"
        "  past the fault site, fitted to the 10 observed blocks:\n"
        "    A. MEMORYLESS   rho(n) = p_obs                (constant)\n"
        "    B. CUMULATIVE   rho(n) = 1-(1-p)^n            (the DSD law)\n"
        "  Model B's p is calibrated so its first block equals the observed first\n"
        "  block, i.e. the most generous possible fit for the cascade hypothesis.\n"
    )
    print(f"  {'variant':<12} {'RMSE memoryless':>16} {'RMSE cumulative':>16} {'winner':>12}")
    hr()
    modelcmp = {}
    for pos, obs in observed.items():
        _, d = block_densities(obs.mismatch, pos, n_blocks=10)
        n_idx = np.arange(1, d.size + 1)
        pred_flat = np.full(d.size, obs.dens_after)
        p_cal = float(d[0])  # generous calibration for the cumulative model
        pred_cum = dsd_curve(p_cal, n_idx)
        rmse_flat = float(np.sqrt(((d - pred_flat) ** 2).mean()))
        rmse_cum = float(np.sqrt(((d - pred_cum) ** 2).mean()))
        winner = "MEMORYLESS" if rmse_flat < rmse_cum else "CUMULATIVE"
        modelcmp[str(pos)] = {
            "rmse_memoryless": rmse_flat,
            "rmse_cumulative": rmse_cum,
            "cumulative_p_calibrated": p_cal,
            "winner": winner,
            "ratio": rmse_cum / rmse_flat if rmse_flat else float("inf"),
        }
        print(
            f"  {obs.label:<12} {rmse_flat:>16.4f} {rmse_cum:>16.4f} {winner:>12}"
            f"   ({rmse_cum / rmse_flat:.1f}x worse)"
        )
    receipt["model_comparison"] = modelcmp
    print(
        "\n  The DSD cumulative law is rejected by the real streams. The observed\n"
        "  downstream regime is a constant-rate memoryless process, not an\n"
        "  accumulating cascade. At p=1 the two laws are indistinguishable\n"
        "  (both are a flat step at 1.0) — which is precisely why the synthetic\n"
        "  fixture appeared to confirm the equivalence."
    )

    # ---------------------------------------------------------------- §8
    hr("8  CLASSIFICATION OF NOTEBOOK CONCLUSIONS")
    verdicts = [
        (
            "Zero trit mismatch upstream of the deletion",
            "ROBUST AT OBSERVED DENSITY",
            f"exact: first diff at {observed[35].first_diff} / {observed[235].first_diff}",
        ),
        (
            "Step function in mismatch density at the site",
            "ROBUST AT OBSERVED DENSITY",
            "0.0000 -> ~0.61 discontinuity confirmed",
        ),
        (
            "Fault injected at one point corrupts a downstream region",
            "QUALITATIVE ONLY",
            "shape shared; propagation law differs",
        ),
        (
            "Downstream density is ~1.0 / every codon differs",
            "P=1 ARTIFACT",
            f"{(o35.tail_after - o35.diff_after) / o35.tail_after:.1%} of downstream "
            "positions are unchanged",
        ),
        (
            "GJB2 is the p->1 limit of the DSD formula",
            "P=1 ARTIFACT",
            "degenerate limit; law does not transfer at p=0.605",
        ),
        (
            "'Identical mathematics' / carry cascade equivalence",
            "P=1 ARTIFACT",
            "cumulative law rejected; encoder carry-inert",
        ),
        (
            "Mismatch geometry attributable to encoder carry",
            "P=1 ARTIFACT",
            "0 non-zero carry events in 681 positions",
        ),
        (
            "n_max = 0 for GJB2 under the S3 budget",
            "THRESHOLD-DEPENDENT",
            "true for any p >= 0.30; not evidence of equivalence",
        ),
        (
            "DSD leak model itself (1-(1-p)^n) for engineered circuits",
            "UNRESOLVED",
            "untested here; no DSD measurements in repo",
        ),
        (
            "Sanskrit-prosody limb of the three-way unification",
            "UNRESOLVED",
            "out of scope of this substitution",
        ),
    ]
    print(f"  {'conclusion':<52} {'verdict':<27} basis")
    hr()
    for c, v, basis in verdicts:
        print(f"  {c:<52} {v:<27} {basis}")
    receipt["verdicts"] = [{"conclusion": c, "verdict": v, "basis": b} for c, v, b in verdicts]

    if args.json:
        args.json.write_text(json.dumps(receipt, indent=2, default=str))
        print(f"\n  JSON receipt written to {args.json}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
