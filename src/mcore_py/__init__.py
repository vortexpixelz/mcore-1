"""
MCORE-1: Metrical Core Representation
======================================

Language-agnostic data model for representing metrical (prosodic) structure
as hierarchical trees with weighted nodes, a ternary weight algebra, 6-bit
binary encoding (TME-6), text-safe serialization (Base64-TME), human-readable
surface syntax (MSS), and rendering protocol (MRP).

Specification v0.1 — March 2026
"""

__version__ = "0.1.0"

from mcore_py.model import (
    Budget,
    Constituent,
    EdgeLicense,
    HierarchyMap,
    Level,
    ProsodicUnit,
    Tension,
    Trit,
)
from mcore_py.algebra import (
    trit_add,
    trit_add_seq,
    tension_pair,
    project,
    complete,
    OVERFLOW,
)
from mcore_py.checker import check_tree, CheckError, CheckResult
from mcore_py.tme6 import Opcode, encode_tme6, decode_tme6
from mcore_py.base64tme import to_base64tme, from_base64tme
from mcore_py.mss import parse_mss, emit_mss

__all__ = [
    # Model
    "Trit", "Tension", "Level", "ProsodicUnit", "Constituent",
    "Budget", "EdgeLicense", "HierarchyMap",
    # Algebra
    "trit_add", "trit_add_seq", "tension_pair", "project", "complete", "OVERFLOW",
    # Checker
    "check_tree", "CheckError", "CheckResult",
    # TME-6
    "Opcode", "encode_tme6", "decode_tme6",
    # Base64-TME
    "to_base64tme", "from_base64tme",
    # MSS
    "parse_mss", "emit_mss",
]
