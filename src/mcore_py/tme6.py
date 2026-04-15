"""
TME-6 Binary Encoding (Spec Section 6)
========================================

6-bit packed binary format. Each opcode is exactly 6 bits (values 0-63),
enabling compact encoding and direct mapping to the 64-character Base64-TME
alphabet.

State model: a TME-6 interpreter maintains a state vector with current
weight, tension, hierarchy level, protocol version, a frame stack, and
a defer stack.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

from mcore_py.model import Level, ProsodicUnit, Tension, Trit


# ---------------------------------------------------------------------------
# 6.1  Opcode Table
# ---------------------------------------------------------------------------

class Opcode(IntEnum):
    """TME-6 opcodes (Spec §6.1). Each value is 0-63 (6 bits)."""

    # Weight / Tension / Hierarchy  (0-10)
    SET_WEIGHT_S1 = 0
    SET_WEIGHT_S2 = 1
    SET_WEIGHT_S3 = 2
    SET_TENSION_DEBT = 3
    SET_TENSION_NEUTRAL = 4
    SET_TENSION_SURPLUS = 5
    SET_LEVEL_0 = 6
    SET_LEVEL_1 = 7
    SET_LEVEL_2 = 8
    SET_LEVEL_3 = 9
    SET_LEVEL_4 = 10

    # Control  (11-14)
    PUSH_FRAME = 11
    POP_FRAME = 12
    RESET_ALL = 13
    VERSION_TAG = 14

    # Trit-pair states  (15-23)
    TP_S1_N = 15   # (S1, neutral)
    TP_S1_D = 16   # (S1, debt)
    TP_S1_S = 17   # (S1, surplus)
    TP_S2_N = 18   # (S2, neutral)
    TP_S2_D = 19   # (S2, debt)
    TP_S2_S = 20   # (S2, surplus)
    TP_S3_N = 21   # (S3, neutral)
    TP_S3_D = 22   # (S3, debt)
    TP_S3_S = 23   # (S3, surplus)

    # Syncopation pairs  (24-26)
    PAIR_CHORIAMBIC = 24
    PAIR_IONIC = 25
    PAIR_GLYCONIC = 26

    # Reserved pair relationships  (27-35)
    PAIR_RESERVED_27 = 27
    PAIR_RESERVED_28 = 28
    PAIR_RESERVED_29 = 29
    PAIR_RESERVED_30 = 30
    PAIR_RESERVED_31 = 31
    PAIR_RESERVED_32 = 32
    PAIR_RESERVED_33 = 33
    PAIR_RESERVED_34 = 34
    PAIR_RESERVED_35 = 35

    # Budget  (36-47)
    BUDGET_SET = 36
    BUDGET_CHECK = 37
    BUDGET_OVERFLOW = 38
    DEFER_OPEN = 39
    DEFER_RESOLVE = 40
    BUDGET_RESERVED_41 = 41
    BUDGET_RESERVED_42 = 42
    BUDGET_RESERVED_43 = 43
    BUDGET_RESERVED_44 = 44
    BUDGET_RESERVED_45 = 45
    BUDGET_RESERVED_46 = 46
    BUDGET_RESERVED_47 = 47

    # QuantitativeMetrics overlay  (48-55)
    QM_RESOLUTION = 48
    QM_CAESURA = 49
    QM_BRIDGE = 50
    QM_ANCEPS = 51
    QM_BIL = 52         # brevis in longo
    QM_CATALEXIS = 53
    QM_RESERVED_54 = 54
    QM_RESERVED_55 = 55

    # TonoMetrics overlay  (56-59)
    TM_PING = 56
    TM_ZE = 57
    TM_DUI = 58
    TM_RESERVED_59 = 59

    # User-defined  (60-63)
    USER_0 = 60
    USER_1 = 61
    USER_2 = 62
    USER_3 = 63


# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------

# Map trit-pair opcodes to (Trit, Tension)
_TP_DECODE: dict[Opcode, tuple[Trit, Tension]] = {
    Opcode.TP_S1_N: (Trit.S1, Tension.NEUTRAL),
    Opcode.TP_S1_D: (Trit.S1, Tension.DEBT),
    Opcode.TP_S1_S: (Trit.S1, Tension.SURPLUS),
    Opcode.TP_S2_N: (Trit.S2, Tension.NEUTRAL),
    Opcode.TP_S2_D: (Trit.S2, Tension.DEBT),
    Opcode.TP_S2_S: (Trit.S2, Tension.SURPLUS),
    Opcode.TP_S3_N: (Trit.S3, Tension.NEUTRAL),
    Opcode.TP_S3_D: (Trit.S3, Tension.DEBT),
    Opcode.TP_S3_S: (Trit.S3, Tension.SURPLUS),
}

# Reverse: (Trit, Tension) -> trit-pair opcode
_TP_ENCODE: dict[tuple[Trit, Tension], Opcode] = {v: k for k, v in _TP_DECODE.items()}


# ---------------------------------------------------------------------------
# 6.2  State Model
# ---------------------------------------------------------------------------

@dataclass
class TME6Frame:
    """A single frame on the validation stack."""
    units: list[ProsodicUnit] = field(default_factory=list)
    defers: list[tuple[Tension, Level]] = field(default_factory=list)
    level: Level = Level.L0_MATRA


@dataclass
class TME6State:
    """Interpreter state for a TME-6 stream (Spec §6.2).

    Each opcode modifies one channel; state persists until
    explicitly changed or reset.
    """
    weight: Trit = Trit.S1
    tension: Tension = Tension.NEUTRAL
    level: Level = Level.L0_MATRA
    version: int = 1
    frame_stack: list[TME6Frame] = field(default_factory=list)
    units: list[ProsodicUnit] = field(default_factory=list)

    def reset(self) -> None:
        """Reset all channels to defaults (RESET_ALL)."""
        self.weight = Trit.S1
        self.tension = Tension.NEUTRAL
        self.level = Level.L0_MATRA

    def current_unit(self) -> ProsodicUnit:
        """Snapshot the current state as a ProsodicUnit."""
        return ProsodicUnit(
            weight=self.weight,
            tension=self.tension,
            level=self.level,
        )


# ---------------------------------------------------------------------------
# Encoder: ProsodicUnit sequence -> opcode stream
# ---------------------------------------------------------------------------

def encode_tme6(units: list[ProsodicUnit]) -> list[Opcode]:
    """Encode a sequence of ProsodicUnits as a TME-6 opcode stream.

    Uses trit-pair opcodes for compact encoding when possible.

    Parameters
    ----------
    units : list[ProsodicUnit]
        Units to encode.

    Returns
    -------
    list[Opcode]
        TME-6 opcode sequence.
    """
    opcodes: list[Opcode] = []

    for unit in units:
        # Try trit-pair encoding first (most compact)
        tp_key = (unit.weight, unit.tension)
        if tp_key in _TP_ENCODE:
            opcodes.append(_TP_ENCODE[tp_key])
        else:
            # Fall back to separate weight + tension opcodes
            opcodes.append(Opcode(unit.weight.value))  # SET_WEIGHT_S{1,2,3}
            opcodes.append(Opcode(3 + unit.tension.value + 1))  # SET_TENSION_{D,N,S}

        # Always emit level if not L0 (default)
        if unit.level != Level.L0_MATRA:
            opcodes.append(Opcode(6 + unit.level.value))  # SET_LEVEL_{0-4}

    return opcodes


# ---------------------------------------------------------------------------
# Decoder: opcode stream -> ProsodicUnit sequence
# ---------------------------------------------------------------------------

def decode_tme6(opcodes: list[int | Opcode]) -> list[ProsodicUnit]:
    """Decode a TME-6 opcode stream into ProsodicUnits.

    Parameters
    ----------
    opcodes : list[int | Opcode]
        TME-6 opcode values (0-63).

    Returns
    -------
    list[ProsodicUnit]
        Decoded prosodic units.

    Raises
    ------
    ValueError
        On opcode out of range or invalid stream structure.
    """
    state = TME6State()
    units: list[ProsodicUnit] = []
    i = 0

    while i < len(opcodes):
        raw = int(opcodes[i])
        if raw < 0 or raw > 63:
            raise ValueError(f"Opcode out of range at position {i}: {raw}")

        op = Opcode(raw)

        # Weight
        if op in (Opcode.SET_WEIGHT_S1, Opcode.SET_WEIGHT_S2, Opcode.SET_WEIGHT_S3):
            state.weight = Trit(op.value)

        # Tension
        elif op == Opcode.SET_TENSION_DEBT:
            state.tension = Tension.DEBT
        elif op == Opcode.SET_TENSION_NEUTRAL:
            state.tension = Tension.NEUTRAL
        elif op == Opcode.SET_TENSION_SURPLUS:
            state.tension = Tension.SURPLUS

        # Level
        elif Opcode.SET_LEVEL_0 <= op <= Opcode.SET_LEVEL_4:
            state.level = Level(op.value - 6)

        # Control
        elif op == Opcode.PUSH_FRAME:
            state.frame_stack.append(TME6Frame(level=state.level))
        elif op == Opcode.POP_FRAME:
            if state.frame_stack:
                state.frame_stack.pop()
        elif op == Opcode.RESET_ALL:
            state.reset()
        elif op == Opcode.VERSION_TAG:
            i += 1
            if i < len(opcodes):
                state.version = int(opcodes[i])

        # Trit-pair states (compact weight+tension)
        elif op in _TP_DECODE:
            state.weight, state.tension = _TP_DECODE[op]
            units.append(state.current_unit())
            i += 1
            continue  # unit already emitted

        # DEFER
        elif op == Opcode.DEFER_OPEN:
            if state.frame_stack:
                state.frame_stack[-1].defers.append((state.tension, state.level))
        elif op == Opcode.DEFER_RESOLVE:
            if state.frame_stack and state.frame_stack[-1].defers:
                state.frame_stack[-1].defers.pop()

        # Budget, syncopation, overlay, user — currently pass-through
        else:
            pass

        i += 1

    return units


# ---------------------------------------------------------------------------
# Raw opcode stream utilities
# ---------------------------------------------------------------------------

def opcodes_to_ints(opcodes: list[Opcode]) -> list[int]:
    """Convert Opcode list to raw integer list."""
    return [op.value for op in opcodes]


def ints_to_opcodes(values: list[int]) -> list[Opcode]:
    """Convert raw integer list to Opcode list."""
    return [Opcode(v) for v in values]
