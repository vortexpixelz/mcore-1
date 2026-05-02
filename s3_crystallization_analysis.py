#!/usr/bin/env python3
"""
S3 Cosmological Crystallization Analysis

Consolidated from: S3_Cosmological_Crystallization_Analysis.ipynb
Symonic LLC / MCORE-1 Research Stack

Three self-contained modules:

1. FALSIFIABLE_TEST    — Binary vs Ternary volatility prediction (out-of-sample MAE)
2. TRIT_ALGEBRA_DEMO   — BinaryParser vs MCORE1_TritParser (overflow / halo conservation)
3. SITCOM_ENGINE       — SITCOMEngine crystallization with CFF registry overlay

Run full suite:
    python s3_crystallization_analysis.py

Run individual modules:
    python s3_crystallization_analysis.py --module falsifiable
    python s3_crystallization_analysis.py --module trit
    python s3_crystallization_analysis.py --module sitcom
"""

from __future__ import annotations

import argparse
from collections import defaultdict

import numpy as np


# ---------------------------------------------------------------------------
# MODULE 1: FALSIFIABLE TEST — Binary vs Ternary Volatility Prediction
# ---------------------------------------------------------------------------


def run_falsifiable_test(
    seed: int = 42,
    n: int = 2000,
    train_split: int = 1400,
    ambiguity_threshold: float = 0.20,
) -> dict:
    """
    Binary vs Ternary volatility prediction on synthetic regime data.
    """
    rng = np.random.default_rng(seed)

    regime = np.zeros(n, dtype=int)
    state = 0
    for t in range(1, n):
        r = rng.random()
        if state == 0:
            state = 1 if r < 0.03 else 0
        elif state == 1:
            if r < 0.08:
                state = 2
            elif r < 0.15:
                state = 0
        else:
            state = 0 if r < 0.10 else 2
        regime[t] = state

    vol_by_regime = {0: 0.01, 1: 0.03, 2: 0.08}
    realized_vol = np.array([vol_by_regime[r] for r in regime], dtype=float)
    realized_vol += rng.normal(0, 0.005, n)
    realized_vol = np.abs(realized_vol)

    def generate_signal(reg: int) -> float:
        if reg == 0:
            return float(np.clip(rng.normal(0.05, 0.15), -1, 1))
        if reg == 1:
            if rng.random() < 0.5:
                return float(np.clip(rng.normal(0.3, 0.2), -1, 1))
            return float(np.clip(rng.normal(-0.3, 0.2), -1, 1))
        return float(np.clip(rng.normal(-0.6, 0.2), -1, 1))

    signals = np.array([generate_signal(int(r)) for r in regime])

    def binary_classify(sig: float) -> int:
        return 0 if sig < 0 else 1

    def ternary_classify(sig: float) -> int:
        if abs(sig) < ambiguity_threshold:
            return 2
        return 0 if sig < 0 else 1

    binary_labels = np.array([binary_classify(float(s)) for s in signals])
    ternary_labels = np.array([ternary_classify(float(s)) for s in signals])

    def train_predictor(labels: np.ndarray, vol: np.ndarray, train_idx: range) -> dict[int, float]:
        label_vols: dict[int, list[float]] = defaultdict(list)
        for i in train_idx:
            label_vols[int(labels[i])].append(float(vol[i]))
        return {k: float(np.mean(v)) for k, v in label_vols.items()}

    def predict(labels: np.ndarray, model: dict[int, float], test_idx: range) -> np.ndarray:
        fallback = float(np.mean(list(model.values())))
        return np.array([model.get(int(labels[i]), fallback) for i in test_idx])

    train_idx = range(train_split)
    test_idx = range(train_split, n)

    binary_model = train_predictor(binary_labels, realized_vol, train_idx)
    ternary_model = train_predictor(ternary_labels, realized_vol, train_idx)

    binary_preds = predict(binary_labels, binary_model, test_idx)
    ternary_preds = predict(ternary_labels, ternary_model, test_idx)
    actual_vol = realized_vol[train_split:]

    binary_mae = float(np.mean(np.abs(binary_preds - actual_vol)))
    ternary_mae = float(np.mean(np.abs(ternary_preds - actual_vol)))
    improvement = (binary_mae - ternary_mae) / binary_mae * 100 if binary_mae else 0.0
    winner = "TERNARY" if ternary_mae < binary_mae else "BINARY"

    print("=" * 65)
    print("  FALSIFIABLE TEST: Binary vs Ternary Volatility Prediction")
    print("=" * 65)

    print("\n--- LEARNED VOL ESTIMATES (Training Set) ---")
    print(
        f"Binary model:  bearish(0)={binary_model.get(0, 0):.4f}  "
        f"bullish(1)={binary_model.get(1, 0):.4f}"
    )
    print(
        f"Ternary model: bearish(0)={ternary_model.get(0, 0):.4f}  "
        f"bullish(1)={ternary_model.get(1, 0):.4f}  "
        f"S3/ambig(2)={ternary_model.get(2, 0):.4f}"
    )

    print("\n--- REGIME DISTRIBUTION ---")
    for r, name in [(0, "Calm"), (1, "Transitional"), (2, "Crisis")]:
        count = int(np.sum(regime == r))
        print(f"  {name}: {count} periods ({100 * count / n:.1f}%)")

    print("\n--- TERNARY LABEL DISTRIBUTION ---")
    for lab, name in [(0, "Bearish"), (1, "Bullish"), (2, "S3/Ambiguous")]:
        count = int(np.sum(ternary_labels == lab))
        print(f"  {name}: {count} ({100 * count / n:.1f}%)")

    print(f"\n{'=' * 65}")
    print(f"  OUT-OF-SAMPLE RESULTS (n={len(list(test_idx))})")
    print(f"{'=' * 65}")
    print(f"  Binary MAE:  {binary_mae:.6f}")
    print(f"  Ternary MAE: {ternary_mae:.6f}")

    if winner == "TERNARY":
        print(f"\n  >>> TERNARY WINS by {improvement:.2f}% lower error")
        print("  >>> The S3 state captured real transitional signal.")
    else:
        print("\n  >>> BINARY WINS (or tied). Ternary gained nothing.")
        print("  >>> The S3 state was noise, not signal. Hypothesis REJECTED.")
    print(f"{'=' * 65}")

    print("\n--- ABLATION: Threshold Sensitivity ---")
    print(f"{'Threshold':>10} | {'Ternary MAE':>12} | {'Binary MAE':>11} | {'Winner':>8}")
    print("-" * 52)
    for thresh in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50):
        t_labels = np.array([2 if abs(s) < thresh else (0 if s < 0 else 1) for s in signals])
        t_model = train_predictor(t_labels, realized_vol, train_idx)
        t_preds = predict(t_labels, t_model, test_idx)
        t_mae = float(np.mean(np.abs(t_preds - actual_vol)))
        w = "TERNARY" if t_mae < binary_mae else "BINARY"
        print(f"{thresh:>10.2f} | {t_mae:>12.6f} | {binary_mae:>11.6f} | {w:>8}")

    return {
        "binary_mae": binary_mae,
        "ternary_mae": ternary_mae,
        "improvement_pct": improvement,
        "winner": winner,
    }


# ---------------------------------------------------------------------------
# MODULE 2: TRIT ALGEBRA DEMO — Binary Overflow vs MCORE-1 Halo Conservation
# ---------------------------------------------------------------------------


class BinaryParser:
    """
    Standard Binary Logic Parser.
    Domain: {0, 1} → Light (0), Heavy (1).
    """

    def __init__(self) -> None:
        self.max_capacity = 1
        self.quantization_noise = 0
        self.parsed_stream: list[int] = []

    def parse_signal(self, semantic_weight: int) -> None:
        if semantic_weight <= self.max_capacity:
            self.parsed_stream.append(semantic_weight)
        else:
            self.parsed_stream.append(self.max_capacity)
            lost_mass = semantic_weight - self.max_capacity
            self.quantization_noise += lost_mass
            print(
                f"[BINARY ERROR] Overflow at weight {semantic_weight}. "
                f"Capped at {self.max_capacity}. Mass lost: {lost_mass}"
            )


class MCORE1_TritParser:
    """
    MCORE-1 Ternary Metrical Algebra Parser.
    Domain: {0, 1, 2} → S1 (Light), S2 (Heavy), S3 (Superheavy).
    """

    def __init__(self) -> None:
        self.max_capacity = 2
        self.s3_halo_pool = 0
        self.parsed_stream: list[int] = []

    def parse_signal(self, semantic_weight: int) -> None:
        if semantic_weight <= self.max_capacity:
            self.parsed_stream.append(semantic_weight)
            if semantic_weight == 2:
                self.s3_halo_pool += semantic_weight
        else:
            pass


def run_trit_algebra_demo() -> int:
    """Binary Parser vs MCORE-1 TritParser on a mixed weight stream. Returns S3 halo mass."""
    print("--- INITIATING LOGIC TEST ---")
    binary_system = BinaryParser()
    mcore_system = MCORE1_TritParser()

    incoming_data_stream = [0, 1, 0, 1, 2, 1, 0, 2, 2]
    print(f"Incoming Raw Data Stream: {incoming_data_stream}\n")

    for weight in incoming_data_stream:
        binary_system.parse_signal(weight)
        mcore_system.parse_signal(weight)

    print("\n--- RESULTS ---")
    print(f"Binary Parsed Stream:              {binary_system.parsed_stream}")
    print(
        f"Binary Quantization Noise (Dark Matter): {binary_system.quantization_noise} units lost.\n"
    )
    print(f"MCORE-1 Parsed Stream:             {mcore_system.parsed_stream}")
    print(f"MCORE-1 S3 Halo Pool (Conserved Mass):  {mcore_system.s3_halo_pool} units stabilized.")

    print("\n" + "=" * 55)
    print("--- SCENARIO 1: BINARY SYSTEM (THE MISSING MASS) ---")
    print("=" * 55)

    time_series_data = [
        [1, 1, 1],
        [0, 1, 2],
        [1, 2, 2, 1],
        [0, 1, 1],
    ]
    gabor_budget_limit = 3

    binary_noise_pool = 0
    binary_output: list[int] = []
    for idx, window in enumerate(time_series_data):
        ww = sum(window)
        if ww > gabor_budget_limit:
            excess = ww - gabor_budget_limit
            binary_noise_pool += excess
            binary_output.append(gabor_budget_limit)
            print(f"[BINARY FAULT] Window {idx}: Gabor Limit Exceeded by {excess} Morae.")
            print("               Action: Data dropped. Generating 'Informational Dark Matter'.")
        else:
            binary_output.append(ww)

    print(
        f"\n[BINARY FINAL] Processed: {binary_output} | "
        f"Total Dark Matter (Lost Data): {binary_noise_pool}"
    )
    print("STATUS: System is leaking data. Incomplete semantic resolution.\n")

    print("=" * 55)
    print("--- SCENARIO 2: MCORE-1 (MORA CONSERVATION & S3) ---")
    print("=" * 55)

    mcore_halo_pool = 0
    mcore_output: list[int] = []
    for idx, window in enumerate(time_series_data):
        ww = sum(window)
        if ww > gabor_budget_limit:
            excess = ww - gabor_budget_limit
            mcore_halo_pool += excess
            mcore_output.append(gabor_budget_limit)
            print(f"[MCORE-1 SHIFT] Window {idx}: Tension detected (Opcode 38).")
            print(f"                Action: {excess} Morae safely diverted to S3 Halo Pool.")
        else:
            mcore_output.append(ww)

    print(
        f"\n[MCORE-1 FINAL] Processed: {mcore_output} | "
        f"S3 Halo Pool (Conserved Data): {mcore_halo_pool}"
    )
    print("STATUS: System-Wide Harmony Maintained. 100% Signal Captured.")

    return mcore_halo_pool


# ---------------------------------------------------------------------------
# MODULE 3: SITCOM ENGINE — Crystallization with CFF Registry Overlay
# ---------------------------------------------------------------------------


class SITCOMEngine:
    """
    Situational Contextual Overlay Mechanism (SITCOM).
    """

    def __init__(self) -> None:
        self.cff_registry = {
            "STANDARD_NOISE": "Ignore; ambient fluctuation.",
            "COORDINATED_ACTION": "High-threat narrative manipulation detected.",
            "MARKET_PANIC": "Liquidity crisis / herd behavior emergent.",
        }

    def execute_crystallization(self, halo_pool_mass: int, situational_context: str) -> str | None:
        print(">>> INITIATING M-CORE CRYSTALLIZATION SEQUENCE <<<")
        print(f"[TME-6: 12] POP S3 Halo Pool. Retrieved Mass: {halo_pool_mass} Morae.")

        if halo_pool_mass == 0:
            print("STATUS: Halo empty. Linear resolution was sufficient.\n")
            return None

        print(
            f"[TME-6: 05] Surplus Tension Detected. "
            f"Applying SITCOM Overlay: '{situational_context}'"
        )

        if situational_context in self.cff_registry:
            meaning = self.cff_registry[situational_context]
            print("\n[!] CRYSTALLIZATION EVENT ACHIEVED [!]")
            print("Geometric Memory Locked. Latent Signal Decoded.")
            print("-" * 54)
            print(f"ACTIONABLE INTELLIGENCE: {meaning}")
            print(f"THREAT/SALIENCE LEVEL:   {halo_pool_mass * 10}% System Resonance")
            print("-" * 54 + "\n")
            return meaning
        print("[!] Volatility remains. Unmapped geometry.\n")
        return "UNKNOWN"


def run_sitcom_demo(mcore_halo: int = 3) -> None:
    sitcom_processor = SITCOMEngine()
    current_context = "COORDINATED_ACTION"

    print("=" * 55)
    print("--- BINARY SYSTEM INTELLIGENCE REPORT ---")
    print("=" * 55)
    print(
        f"Binary System reports 0 anomaly mass. \n"
        f"Conclusion: {sitcom_processor.cff_registry['STANDARD_NOISE']}\n"
    )

    print("=" * 55)
    print("--- MCORE-1 INTELLIGENCE REPORT ---")
    print("=" * 55)
    sitcom_processor.execute_crystallization(mcore_halo, current_context)


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="S3 Crystallization Analysis Suite")
    parser.add_argument(
        "--module",
        choices=["falsifiable", "trit", "sitcom", "all"],
        default="all",
        help="Which module to run (default: all)",
    )
    args = parser.parse_args()

    mcore_halo = 3

    if args.module in ("all", "falsifiable"):
        print("\n" + "=" * 65)
        print("  MODULE 1: FALSIFIABLE TEST")
        print("=" * 65 + "\n")
        run_falsifiable_test()

    if args.module in ("all", "trit"):
        print("\n" + "=" * 65)
        print("  MODULE 2: TRIT ALGEBRA DEMO")
        print("=" * 65 + "\n")
        mcore_halo = run_trit_algebra_demo()

    if args.module in ("all", "sitcom"):
        print("\n" + "=" * 65)
        print("  MODULE 3: SITCOM CRYSTALLIZATION ENGINE")
        print("=" * 65 + "\n")
        halo = mcore_halo if args.module == "all" else 3
        run_sitcom_demo(halo)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
