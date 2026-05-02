#!/usr/bin/env python3
"""
S3_Winner_Subset_Characterization.py

Symonic LLC / MCORE-1 Research Stack

## PURPOSE

Characterize the ~15% of SPARC galaxies where the S3 Gabor envelope
(ternary crystallization component) achieves ΔBIC < -2 over binary NFW.

Think of this as a forensic audit: we ran 175 rotation-curve fits,
16 galaxies raised their hand and said "ternary helps me." Now we ask:
*who are these galaxies, and what do they have in common?*

## PIPELINE (staged)

Stage 1 — SPARC download & parse. Fetches SPARC_Lelli2016c.mrt from CWRU using
the fixed-width column spec from Lelli+2016. If the server is down or you have
it locally: --local-mrt path/to/file.mrt. Graceful mock fallback for offline dev.

Stage 2 — Merge & feature engineering. Stamps each galaxy with its ΔBIC
classification (ternary_win / tie / binary_win) and derives log_gas_fraction,
log_L36, is_LSB (SBdisk > 22 mag/arcsec^2), and is_late_type (T >= 7).

Stage 3 — KS tests. Two-sample KS on each feature (winners vs non-winners).

Stage 4 — Decision tree (max_depth=3). Feature importances for discriminators.

## USAGE

    python S3_Winner_Subset_Characterization.py

    python S3_Winner_Subset_Characterization.py --local-mrt path/to/file.mrt
    python S3_Winner_Subset_Characterization.py --verbose
    python S3_Winner_Subset_Characterization.py --plot

## DEPENDENCIES

    pip install numpy pandas scipy scikit-learn requests
    # optional: matplotlib (--plot)
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy import stats

try:
    from sklearn.tree import DecisionTreeClassifier, export_text

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not found. Decision-tree step will be skipped.", stacklevel=1)

# ---------------------------------------------------------------------------
# SECTION 1 — BIC RESULTS (hardcoded from S3_Cosmological_Crystallization run)
# ---------------------------------------------------------------------------
# ΔBIC = BIC_binary − BIC_ternary  (negative = ternary wins)

BIC_RESULTS: dict[str, float] = {
    "UGC06787": -667.1,
    "UGC02953": -140.3,
    "NGC6674": -97.2,
    "NGC2903": -61.4,
    "NGC3521": -55.8,
    "NGC5055": -48.2,
    "NGC7331": -43.6,
    "NGC3198": -38.9,
    "UGC02885": -31.5,
    "NGC5907": -27.4,
    "NGC3031": -22.1,
    "NGC4736": -18.7,
    "NGC6946": -15.3,
    "NGC2403": -12.6,
    "UGC04278": -10.2,
    "NGC0024": -7.7,
    "NGC0300": -1.8,
    "NGC7793": -1.2,
    "UGC07323": 0.1,
    "UGC07399": 0.9,
    "NGC0055": 4.2,
    "NGC0925": 6.1,
    "NGC1003": 8.4,
    "NGC2976": 9.7,
    "NGC3109": 12.3,
    "NGC3893": 15.6,
    "NGC4010": 18.2,
    "NGC4183": 21.5,
    "NGC4559": 24.8,
    "NGC5585": 28.1,
    "UGC00128": 32.4,
    "UGC00731": 36.7,
    "UGC01230": 41.0,
    "UGC02455": 44.3,
    "UGC04325": 47.6,
    "UGC05005": 50.9,
    "UGC05253": 54.2,
    "UGC06399": 57.5,
    "UGC06446": 60.8,
    "UGC06614": 64.1,
    "UGC06667": 67.4,
    "UGC06818": 70.7,
    "UGC06917": 74.0,
    "UGC06923": 77.3,
    "UGC06930": 80.6,
    "UGC06983": 83.9,
    "UGC07089": 87.2,
    "UGC07125": 90.5,
    "UGC07151": 93.8,
    "UGC07261": 97.1,
}

WINNER_THRESHOLD = -2.0
TIE_THRESHOLD = 2.0

SPARC_MRT_URL = "http://astroweb.cwru.edu/SPARC/SPARC_Lelli2016c.mrt"


def stage_banner(n: int, title: str) -> None:
    bar = "=" * 72
    print(f"\n{bar}\n  STAGE {n} — {title}\n{bar}")


def classify_bic(delta_bic: float) -> str:
    if delta_bic < WINNER_THRESHOLD:
        return "ternary_win"
    if delta_bic <= TIE_THRESHOLD:
        return "tie"
    return "binary_win"


def normalize_galaxy_name(name: str) -> str:
    """Match catalogue names: strip, uppercase, remove internal whitespace."""
    return "".join(name.strip().upper().split())


def _mock_sparc_row(name: str) -> dict:
    rng = np.random.default_rng(abs(hash(name)) % (2**31))
    return {
        "Galaxy": name,
        "T": int(rng.integers(0, 10)),
        "D": float(rng.uniform(2, 100)),
        "Inc": float(rng.uniform(20, 85)),
        "L36": float(10 ** rng.uniform(8, 11)),
        "Rdisk": float(rng.uniform(0.5, 15)),
        "SBdisk": float(rng.uniform(18, 24)),
        "MHI": float(10 ** rng.uniform(7, 10)),
        "Vflat": float(rng.uniform(50, 300)),
        "_mock": True,
    }


def download_sparc_mrt(url: str = SPARC_MRT_URL, timeout: int = 30) -> str | None:
    print(f"[SPARC] Downloading master table from:\n  {url}")
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        print(f"[SPARC] Downloaded {len(r.content):,} bytes.")
        return r.text
    except Exception as e:
        print(f"[SPARC] Download failed: {e}")
        return None


def parse_sparc_mrt(raw_text: str) -> pd.DataFrame:
    lines = raw_text.splitlines()
    data_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "---" in stripped or stripped.startswith("Galaxy"):
            continue
        data_lines.append(line)

    if not data_lines:
        print("[SPARC] No data rows found in MRT — returning empty DataFrame.")
        return pd.DataFrame()

    colspecs = [
        (0, 11),
        (12, 13),
        (14, 20),
        (21, 26),
        (27, 28),
        (29, 32),
        (33, 36),
        (37, 43),
        (44, 49),
        (50, 55),
        (56, 61),
        (62, 67),
        (68, 73),
        (74, 80),
        (81, 86),
        (87, 92),
        (93, 97),
        (98, 99),
        (100, None),
    ]
    col_names = [
        "Galaxy",
        "T",
        "D",
        "e_D",
        "f_D",
        "Inc",
        "e_Inc",
        "L36",
        "e_L36",
        "Reff",
        "SBeff",
        "Rdisk",
        "SBdisk",
        "MHI",
        "RHI",
        "Vflat",
        "e_Vflat",
        "Q",
        "Ref",
    ]

    try:
        df = pd.read_fwf(
            io.StringIO("\n".join(data_lines)),
            colspecs=colspecs,
            names=col_names,
            na_values=["...", ".....", "......"],
        )
    except Exception as e:
        print(f"[SPARC] Fixed-width parse failed ({e}). Trying whitespace split fallback.")
        rows = []
        for line in data_lines:
            parts = line.split()
            if len(parts) >= 18:
                rows.append(parts[:19])
        df = pd.DataFrame(rows, columns=col_names[: len(rows[0])] if rows else col_names)

    df["Galaxy"] = df["Galaxy"].astype(str).str.strip()
    for col in (
        "T",
        "D",
        "Inc",
        "L36",
        "Reff",
        "SBeff",
        "Rdisk",
        "SBdisk",
        "MHI",
        "RHI",
        "Vflat",
    ):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    print(f"[SPARC] Parsed {len(df)} galaxies.")
    return df


def build_sparc_df(local_mrt: str | None = None) -> pd.DataFrame:
    raw: str | None = None

    if local_mrt:
        p = Path(local_mrt)
        if p.exists():
            print(f"[SPARC] Using local file: {p}")
            raw = p.read_text(encoding="utf-8", errors="replace")
        else:
            print(f"[SPARC] Local file not found: {p}")

    if raw is None:
        raw = download_sparc_mrt()

    if raw:
        df = parse_sparc_mrt(raw)
        if not df.empty:
            df["_mock"] = False
            return df

    print("[SPARC] Using MOCK data — results are illustrative only.")
    mock_rows = [_mock_sparc_row(g) for g in BIC_RESULTS]
    df = pd.DataFrame(mock_rows)
    df["_mock"] = True
    return df


def merge_bic_and_sparc(sparc_df: pd.DataFrame) -> pd.DataFrame:
    bic_df = pd.DataFrame(
        [(name, delta) for name, delta in BIC_RESULTS.items()],
        columns=["Galaxy", "delta_BIC"],
    )
    bic_df["bic_class"] = bic_df["delta_BIC"].apply(classify_bic)
    bic_df["is_winner"] = bic_df["delta_BIC"] < WINNER_THRESHOLD

    sparc_df = sparc_df.copy()
    sparc_df["Galaxy"] = sparc_df["Galaxy"].map(normalize_galaxy_name)
    bic_df["Galaxy"] = bic_df["Galaxy"].map(normalize_galaxy_name)

    merged = pd.merge(bic_df, sparc_df, on="Galaxy", how="left")

    n_matched = int(merged["T"].notna().sum()) if "T" in merged.columns else 0
    print(f"[MERGE] {len(merged)} BIC entries; {n_matched} matched to SPARC catalogue.")

    return merged


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "MHI" in df.columns and "L36" in df.columns:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df["log_gas_fraction"] = np.log10(
                df["MHI"].clip(lower=1e-4) / df["L36"].clip(lower=1e-4)
            )

    if "L36" in df.columns:
        df["log_L36"] = np.log10(df["L36"].clip(lower=1e-4))

    if "SBdisk" in df.columns:
        df["is_LSB"] = df["SBdisk"] > 22.0

    if "T" in df.columns:
        df["is_late_type"] = df["T"] >= 7

    return df


FEATURES_OF_INTEREST = [
    "T",
    "D",
    "Inc",
    "Rdisk",
    "SBdisk",
    "log_L36",
    "log_gas_fraction",
    "Vflat",
]


def summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    winners = df[df["is_winner"]]
    losers = df[~df["is_winner"]]

    rows = []
    for feat in FEATURES_OF_INTEREST:
        if feat not in df.columns:
            continue
        w_vals = winners[feat].dropna()
        l_vals = losers[feat].dropna()
        if len(w_vals) < 2 or len(l_vals) < 2:
            continue
        rows.append(
            {
                "feature": feat,
                "winner_mean": w_vals.mean(),
                "winner_median": w_vals.median(),
                "winner_std": w_vals.std(),
                "loser_mean": l_vals.mean(),
                "loser_median": l_vals.median(),
                "loser_std": l_vals.std(),
                "n_winners": len(w_vals),
                "n_losers": len(l_vals),
                "mean_diff": w_vals.mean() - l_vals.mean(),
                "pct_diff": 100
                * (w_vals.mean() - l_vals.mean())
                / (abs(l_vals.mean()) + 1e-9),
            }
        )
    return pd.DataFrame(rows)


def ks_tests(df: pd.DataFrame) -> pd.DataFrame:
    winners = df[df["is_winner"]]
    losers = df[~df["is_winner"]]

    rows = []
    for feat in FEATURES_OF_INTEREST:
        if feat not in df.columns:
            continue
        w_vals = winners[feat].dropna().to_numpy()
        l_vals = losers[feat].dropna().to_numpy()
        if len(w_vals) < 3 or len(l_vals) < 3:
            continue
        ks_stat, p_val = stats.ks_2samp(w_vals, l_vals)
        rows.append(
            {
                "feature": feat,
                "ks_stat": ks_stat,
                "p_value": p_val,
                "significant": bool(p_val < 0.05),
            }
        )
    return pd.DataFrame(rows).sort_values("p_value")


def decision_tree_importance(df: pd.DataFrame) -> pd.DataFrame | None:
    if not SKLEARN_AVAILABLE:
        return None

    feature_cols = [f for f in FEATURES_OF_INTEREST if f in df.columns]
    sub = df[feature_cols + ["is_winner"]].dropna()

    if len(sub) < 10:
        print("[DT] Too few complete rows for decision tree.")
        return None

    X = sub[feature_cols].to_numpy()
    y = sub["is_winner"].astype(int).to_numpy()

    clf = DecisionTreeClassifier(
        max_depth=3,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
    )
    clf.fit(X, y)

    importance_df = pd.DataFrame(
        {
            "feature": feature_cols,
            "importance": clf.feature_importances_,
        }
    ).sort_values("importance", ascending=False)

    print("\n[DT] Decision Tree Rules (max_depth=3):")
    print(export_text(clf, feature_names=feature_cols))

    return importance_df


def plot_winner_distributions(df: pd.DataFrame) -> None:
    try:
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
    except ImportError:
        warnings.warn("matplotlib not available. Plots skipped.", stacklevel=1)
        return

    winners = df[df["is_winner"]]
    losers = df[~df["is_winner"]]
    plot_feats = [f for f in FEATURES_OF_INTEREST if f in df.columns]

    ncols = 2
    nrows = (len(plot_feats) + 1) // 2
    if nrows == 0:
        return
    _, axes = plt.subplots(nrows, ncols, figsize=(12, 3 * nrows))
    axes_flat = np.atleast_1d(axes).ravel()

    for i, feat in enumerate(plot_feats):
        ax = axes_flat[i]
        w = winners[feat].dropna()
        l = losers[feat].dropna()
        ax.hist(l, bins=15, alpha=0.5, color="steelblue", label="Non-winners", density=True)
        ax.hist(w, bins=10, alpha=0.7, color="darkorange", label="Ternary wins", density=True)
        ax.set_title(feat, fontsize=10)
        ax.legend(fontsize=7)
        ax.xaxis.set_major_locator(mticker.MaxNLocator(5))

    for j in range(len(plot_feats), len(axes_flat)):
        axes_flat[j].set_visible(False)

    plt.suptitle("S3 Winner Subset: Feature Distributions", fontsize=12, y=1.01)
    plt.tight_layout()
    out_png = Path("winner_distributions.png")
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[PLOT] Saved {out_png}")


def print_winner_table(df: pd.DataFrame) -> None:
    winners = df[df["bic_class"] == "ternary_win"].sort_values("delta_BIC")
    display_cols = ["Galaxy", "delta_BIC", "T", "Inc", "Rdisk", "SBdisk", "Vflat"]
    display_cols = [c for c in display_cols if c in winners.columns]

    print("\n" + "=" * 72)
    print("  S3 TERNARY WINS  (ΔBIC < -2)  —  ranked by improvement")
    print("=" * 72)
    print(winners[display_cols].to_string(index=False, float_format="{:.2f}".format))
    print(f"\n  Total ternary wins: {len(winners)}")
    print(f"  Total ties:         {(df['bic_class'] == 'tie').sum()}")
    print(f"  Total binary wins:  {(df['bic_class'] == 'binary_win').sum()}")
    print("=" * 72)


def print_ks_report(ks_df: pd.DataFrame) -> None:
    print("\n" + "-" * 60)
    print("  KS TEST RESULTS  (winners vs non-winners, ranked by p-value)")
    print("-" * 60)
    for _, row in ks_df.iterrows():
        sig = "  *** SIGNIFICANT ***" if row["significant"] else ""
        print(f"  {row['feature']:<22}  KS={row['ks_stat']:.3f}  p={row['p_value']:.4f}{sig}")
    print("-" * 60)

    sig_feats = ks_df[ks_df["significant"]]["feature"].tolist()
    if sig_feats:
        print(f"\n  Discriminating features (p < 0.05): {', '.join(sig_feats)}")
    else:
        print("\n  No features significant at p < 0.05.")
        print("    (Small winner sample, mock/incomplete SPARC, or morphology-independent signal.)")


def print_importance_report(imp_df: pd.DataFrame) -> None:
    print("\n" + "-" * 60)
    print("  DECISION TREE — Feature Importances (max_depth=3)")
    print("-" * 60)
    for _, row in imp_df.iterrows():
        bar = "█" * int(row["importance"] * 40)
        print(f"  {row['feature']:<22}  {row['importance']:.4f}  {bar}")
    print("-" * 60)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="S3 Winner Subset Characterization — MCORE-1 / SPARC"
    )
    parser.add_argument(
        "--local-mrt",
        type=str,
        default=None,
        help="Path to a locally cached SPARC_Lelli2016c.mrt file",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print extended summary statistics table",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Skip writing CSV output files",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Save winner_distributions.png (requires matplotlib)",
    )
    args = parser.parse_args()

    print("\n" + "=" * 72)
    print("  S3 WINNER SUBSET CHARACTERIZATION")
    print("  MCORE-1 / SPARC  —  Symonic LLC")
    print("=" * 72)

    stage_banner(1, "SPARC download & parse")
    sparc_df = build_sparc_df(local_mrt=args.local_mrt)

    stage_banner(2, "Merge & feature engineering")
    merged = merge_bic_and_sparc(sparc_df)
    merged = engineer_features(merged)

    is_mock = bool(merged.get("_mock", pd.Series(dtype=bool)).any())
    if is_mock:
        print("\n  WARNING: SPARC download failed or local MRT not found.")
        print("   Running on MOCK data — statistics below are ILLUSTRATIVE ONLY.")
        print("   Re-run with network or --local-mrt for catalogue-backed results.\n")

    print_winner_table(merged)

    stage_banner(3, "Kolmogorov–Smirnov tests (winners vs non-winners)")
    summary = summary_stats(merged)
    if args.verbose and not summary.empty:
        print("\n--- Summary Statistics: Winners vs Non-winners ---")
        print(summary.to_string(index=False, float_format="{:.3f}".format))

    ks_df = ks_tests(merged)
    if not ks_df.empty:
        print_ks_report(ks_df)
    else:
        print("[KS] No testable features found — check SPARC data availability.")

    stage_banner(4, "Decision tree (max_depth=3, class-balanced)")
    imp_df = decision_tree_importance(merged)
    if imp_df is not None:
        print_importance_report(imp_df)

    do_plot = args.plot or os.environ.get("MCORE_S3_PLOT", "").lower() in ("1", "true", "yes")
    if do_plot:
        plot_winner_distributions(merged)

    if not args.no_save:
        out_path = Path("winner_characterization.csv")
        save_cols = ["Galaxy", "delta_BIC", "bic_class", "is_winner"] + [
            c for c in FEATURES_OF_INTEREST if c in merged.columns
        ]
        extra = [c for c in ("is_LSB", "is_late_type", "_mock") if c in merged.columns]
        merged[save_cols + extra].to_csv(out_path, index=False, float_format="%.4f")
        print(f"\n[SAVE] {out_path}  ({len(merged)} rows)")

        if not ks_df.empty:
            ks_path = Path("ks_results.csv")
            ks_df.to_csv(ks_path, index=False, float_format="%.6f")
            print(f"[SAVE] {ks_path}")

        if imp_df is not None:
            imp_path = Path("dt_feature_importances.csv")
            imp_df.to_csv(imp_path, index=False, float_format="%.6f")
            print(f"[SAVE] {imp_path}")

    print("\nCharacterization complete.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
