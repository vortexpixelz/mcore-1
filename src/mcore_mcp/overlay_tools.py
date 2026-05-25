"""Pure helpers for MCP tools (overlays + acoustic + TME)."""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from typing import Any

from mcore_py.base64tme import to_base64tme
from mcore_py.checker import check_tree as check_constituent_tree
from mcore_py.cli import parse_pattern
from mcore_py.model import ProsodicUnit
from mcore_py.overlays import MethylationMetrics, QuantumResourceMetrics
from mcore_py.tme6 import encode_tme6, opcodes_to_ints


def _enum_matrix(rows: Sequence[Sequence[Enum]]) -> list[list[str]]:
    return [[x.name for x in row] for row in rows]


def methylation_island_check(
    betas: list[float],
    *,
    labels: list[str] | None = None,
    island_label: str = "mcp_island",
) -> dict[str, Any]:
    """Build a CpG island from beta values and run ``check_tree``."""
    island = MethylationMetrics.from_beta_list(
        betas,
        labels=labels,
        island_label=island_label,
    )
    result = check_constituent_tree(island)
    return {
        "valid": result.valid,
        "n_sites": len(betas),
        "errors": [{"kind": e.kind.name, "message": e.message} for e in result.errors],
    }


def quantum_frame_check(
    fidelities: list[float],
    *,
    labels: list[str] | None = None,
    frame_label: str | None = "mcp_frame",
) -> dict[str, Any]:
    """Build a quantum scheduling frame from fidelities and run ``check_tree``."""
    frame = QuantumResourceMetrics.from_fidelity_list(
        fidelities,
        labels=labels,
        frame_label=frame_label,
    )
    result = check_constituent_tree(frame)
    return {
        "valid": result.valid,
        "n_qubits": len(fidelities),
        "errors": [{"kind": e.kind.name, "message": e.message} for e in result.errors],
    }


def quantum_decoherence_trajectory(
    fidelities: list[float],
    *,
    steps: int = 5,
    decay_rate: float = 0.05,
) -> dict[str, Any]:
    """Qubit state trajectory under fidelity decay (ternary classification per step)."""
    traj = QuantumResourceMetrics.decoherence_trajectory(
        fidelities, decay_rate=decay_rate, steps=steps
    )
    return {
        "steps": steps,
        "decay_rate": decay_rate,
        "trajectories": _enum_matrix(traj),
    }


def methylation_decoherence_trajectory(
    betas: list[float],
    *,
    steps: int = 5,
    drift_rate: float = 0.05,
) -> dict[str, Any]:
    """Methylation state trajectory under beta drift (ternary classification per step)."""
    traj = MethylationMetrics.decoherence_trajectory(
        betas, drift_rate=drift_rate, steps=steps
    )
    return {
        "steps": steps,
        "drift_rate": drift_rate,
        "trajectories": _enum_matrix(traj),
    }


def pattern_to_base64tme(pattern: str) -> dict[str, Any]:
    """Encode a metrical pattern string to Base64-TME (spec §7)."""
    trits = parse_pattern(pattern)
    units = [ProsodicUnit(weight=t) for t in trits]
    opcodes = encode_tme6(units)
    ints = opcodes_to_ints(opcodes)
    stream = to_base64tme(ints)
    return {"pattern": pattern, "base64tme": stream, "n_opcodes": len(ints)}


def acoustic_phonon_synthesis_summary(
    trits: list[int],
    *,
    normalise: bool = True,
    max_atoms: int = 512,
) -> dict[str, Any]:
    """Summarise Gaussian phonon synthesis (no raw waveform — use Storage for WAV)."""
    import numpy as np

    from mcore_py.audio import ATOM_SAMPLES, SR, synthesise

    if len(trits) > max_atoms:
        raise ValueError(f"max {max_atoms} trits for this summary tool; got {len(trits)}")
    audio = synthesise(trits, normalise=normalise)
    peak = float(np.max(np.abs(audio))) if len(audio) else 0.0
    rms = float(np.sqrt(np.mean(np.square(audio)))) if len(audio) else 0.0
    return {
        "sample_rate_hz": SR,
        "atom_samples": ATOM_SAMPLES,
        "n_atoms": len(trits),
        "n_samples": int(len(audio)),
        "duration_s": float(len(audio) / SR),
        "peak_abs": peak,
        "rms": rms,
        "carrier_freqs_hz": {0: 800.0, 1: 1600.0, 2: 3200.0},
    }


def acoustic_atom_roundtrip_fft(trits: list[int], *, max_atoms: int = 64) -> dict[str, Any]:
    """Synthesise each atom and decode via FFT (lossless for ideal atoms)."""
    from mcore_py.audio import decode_atom_fft, make_atom

    if len(trits) > max_atoms:
        raise ValueError(f"max {max_atoms} trits; got {len(trits)}")
    decoded: list[int] = []
    for t in trits:
        atom = make_atom(int(t))
        decoded.append(decode_atom_fft(atom))
    matches = sum(1 for a, b in zip(trits, decoded, strict=True) if int(a) == int(b))
    return {"input": list(trits), "decoded": decoded, "matches": matches, "len": len(trits)}
