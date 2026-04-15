"""
MCORE-1 CLI Tool
=================

Command-line interface for parsing, validating, completing, and encoding
metrical structures.

Usage:
    mcore validate <pattern>        Validate a metrical pattern
    mcore complete <n> <budget>     Generate all valid patterns
    mcore encode <pattern>          Encode pattern as Base64-TME
    mcore decode <stream>           Decode Base64-TME stream
    mcore scansion <pattern>        Render plain-text scansion
    mcore info                      Show library version and conformance level
"""

from __future__ import annotations

import argparse
import json
import sys

from mcore_py.model import Budget, Constituent, Level, ProsodicUnit, Tension, Trit
from mcore_py.algebra import complete, enumerate_patterns, trit_add_seq, OVERFLOW
from mcore_py.checker import check_tree
from mcore_py.tme6 import Opcode, encode_tme6, opcodes_to_ints
from mcore_py.base64tme import to_base64tme, from_base64tme, annotate_stream
from mcore_py.mss import parse_mss, parse_mss_to_units, emit_mss
from mcore_py.renderers.terminal import render_scansion, render_line_flat


# ---------------------------------------------------------------------------
# Pattern parsing  (shorthand: "012" = S1 S2 S3, "-u-" = S2 S1 S2)
# ---------------------------------------------------------------------------

_CHAR_TO_TRIT: dict[str, Trit] = {
    "0": Trit.S1, "1": Trit.S2, "2": Trit.S3,
    "u": Trit.S1, "-": Trit.S2, "=": Trit.S3,
    "⏑": Trit.S1, "–": Trit.S2, "≡": Trit.S3,
}


def parse_pattern(s: str) -> list[Trit]:
    """Parse a metrical pattern string to a list of Trits.

    Accepts: digit notation (012), classical notation (-u-),
    or Unicode symbols (– ⏑ ≡). Spaces are ignored.
    """
    trits: list[Trit] = []
    for ch in s:
        if ch in _CHAR_TO_TRIT:
            trits.append(_CHAR_TO_TRIT[ch])
        elif ch in (" ", "|", "."):
            continue  # ignore separators
        else:
            raise ValueError(f"Unknown pattern character: {ch!r}")
    return trits


def trits_to_str(trits: list[Trit], style: str = "classical") -> str:
    """Convert a list of Trits to a display string."""
    if style == "digit":
        return "".join(str(t.value) for t in trits)
    elif style == "classical":
        _map = {Trit.S1: "u", Trit.S2: "–", Trit.S3: "≡"}
        return " ".join(_map[t] for t in trits)
    else:
        return " ".join(t.name for t in trits)


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a metrical pattern."""
    trits = parse_pattern(args.pattern)

    # Build a simple constituent
    children = [ProsodicUnit(weight=t) for t in trits]
    pooled = trit_add_seq(trits)

    if pooled is OVERFLOW:
        print(f"INVALID: weight overflow for pattern {trits_to_str(trits)}")
        return 1

    parent = ProsodicUnit(weight=pooled, level=Level.L2_GANA)
    foot = Constituent(parent=parent, children=children)

    result = check_tree(foot)
    if result.valid:
        print(f"VALID: {trits_to_str(trits)}  (total weight: {pooled.name})")
        return 0
    else:
        print(f"INVALID: {trits_to_str(trits)}")
        for err in result.errors:
            print(f"  {err.kind.name}: {err.message}")
        return 1


def cmd_complete(args: argparse.Namespace) -> int:
    """Generate all valid metrical patterns."""
    n = args.positions
    budget_val = args.budget

    budget = Budget(
        min_weight=Trit(budget_val),
        max_weight=Trit(budget_val),
        unit=Level.L0_MATRA,
        exact=True,
    )

    patterns = enumerate_patterns(n, budget)

    if args.json:
        data = [[t.value for t in p] for p in patterns]
        print(json.dumps(data))
    else:
        print(f"Patterns: {n} positions, budget={Trit(budget_val).name}")
        print(f"Found: {len(patterns)}")
        print()
        for p in patterns:
            print(f"  {trits_to_str(p)}")

    return 0


def cmd_encode(args: argparse.Namespace) -> int:
    """Encode a pattern as Base64-TME."""
    trits = parse_pattern(args.pattern)
    units = [ProsodicUnit(weight=t) for t in trits]

    opcodes = encode_tme6(units)
    ints = opcodes_to_ints(opcodes)
    b64 = to_base64tme(ints)

    if args.annotate:
        annotations = annotate_stream(b64)
        for ch, val, name in annotations:
            print(f"  {ch}  ({val:2d})  {name}")
    else:
        print(b64)

    return 0


def cmd_decode(args: argparse.Namespace) -> int:
    """Decode a Base64-TME stream."""
    values = from_base64tme(args.stream)

    if args.annotate:
        annotations = annotate_stream(args.stream)
        for ch, val, name in annotations:
            print(f"  {ch}  ({val:2d})  {name}")
    else:
        print(f"TME-6 values: {values}")
        try:
            opcodes_list = [Opcode(v) for v in values]
            print(f"Opcodes: {[op.name for op in opcodes_list]}")
        except ValueError:
            print("(some values are not valid opcodes)")

    return 0


def cmd_scansion(args: argparse.Namespace) -> int:
    """Render a plain-text scansion."""
    trits = parse_pattern(args.pattern)
    units = [ProsodicUnit(weight=t) for t in trits]
    print(render_scansion(units))
    return 0


def cmd_info(_args: argparse.Namespace) -> int:
    """Show library info."""
    import mcore_py
    print(f"mcore-py v{mcore_py.__version__}")
    print(f"MCORE-1 Specification v0.1 (March 2026)")
    print()
    print("Conformance levels implemented:")
    print("  Level 1 (Core):       ✓  data model, trit algebra, checker")
    print("  Level 2 (Encoding):   ✓  TME-6, Base64-TME, MSS parsing")
    print("  Level 3 (Generation): ✓  completion + QuantitativeMetrics overlay")
    print("  Level 4 (Full):       ◐  terminal renderer + token stream (audio TBD)")
    return 0


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mcore",
        description="MCORE-1 Metrical Core Representation — CLI tool",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # validate
    p_val = sub.add_parser("validate", help="Validate a metrical pattern")
    p_val.add_argument("pattern", help="Pattern string (e.g., '-u-u' or '0101')")

    # complete
    p_comp = sub.add_parser("complete", help="Generate all valid patterns")
    p_comp.add_argument("positions", type=int, help="Number of positions")
    p_comp.add_argument("budget", type=int, choices=[0, 1, 2],
                        help="Target total weight (0=S1, 1=S2, 2=S3)")
    p_comp.add_argument("--json", action="store_true", help="Output as JSON")

    # encode
    p_enc = sub.add_parser("encode", help="Encode pattern as Base64-TME")
    p_enc.add_argument("pattern", help="Pattern string")
    p_enc.add_argument("--annotate", "-a", action="store_true",
                       help="Show annotated opcodes")

    # decode
    p_dec = sub.add_parser("decode", help="Decode Base64-TME stream")
    p_dec.add_argument("stream", help="Base64-TME string")
    p_dec.add_argument("--annotate", "-a", action="store_true",
                       help="Show annotated opcodes")

    # scansion
    p_scan = sub.add_parser("scansion", help="Render plain-text scansion")
    p_scan.add_argument("pattern", help="Pattern string")

    # info
    sub.add_parser("info", help="Show version and conformance info")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    dispatch = {
        "validate": cmd_validate,
        "complete": cmd_complete,
        "encode": cmd_encode,
        "decode": cmd_decode,
        "scansion": cmd_scansion,
        "info": cmd_info,
    }

    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
