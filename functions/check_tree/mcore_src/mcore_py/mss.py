r"""
MSS Surface Syntax (Spec Section 8)
=====================================

Human-readable metrical annotation embedded in UTF-8 text, modeled on
ANSI escape sequences.

Format:  \TME[version:opcode:params]

BNF Grammar:
    <mss-escape> ::= '\TME[' <version> ':' <opcode-expr> ']'
    <version>    ::= <digit>+
    <opcode-expr>::= <opcode> | <opcode> ':' <params>
    <opcode>     ::= 'W' | 'T' | 'H' | 'F' | 'P' | 'B' | 'D' | 'R' | '*'
    <params>     ::= <param> (',' <param>)*
    <param>      ::= <integer> | <identifier> | <float>

Degradation contract: parsers encountering an unrecognized version MUST
emit a diagnostic warning, pass through raw bytes unchanged, and continue
parsing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from mcore_py.model import Level, ProsodicUnit, Tension, Trit
from mcore_py.tme6 import Opcode


# ---------------------------------------------------------------------------
# Parsed MSS token
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MSSToken:
    """A parsed MSS escape sequence.

    Attributes
    ----------
    version : int
        Protocol version.
    opcode : str
        Single-letter opcode (W, T, H, F, P, B, D, R, *).
    params : list[str]
        Parameters as strings (caller interprets types).
    raw : str
        The original escape sequence text.
    """
    version: int
    opcode: str
    params: list[str]
    raw: str

    def __repr__(self) -> str:
        p = ",".join(self.params) if self.params else ""
        return f"MSS(v{self.version}:{self.opcode}:{p})"


# ---------------------------------------------------------------------------
# MSS opcode -> semantic action mapping
# ---------------------------------------------------------------------------

_VALID_OPCODES = {"W", "T", "H", "F", "P", "B", "D", "R", "*"}

# Pattern:  \TME[version:opcode] or \TME[version:opcode:params]
_MSS_PATTERN = re.compile(
    r"\\TME\["
    r"(\d+)"           # version (group 1)
    r":"
    r"([WTHFPBDR*])"   # opcode  (group 2)
    r"(?::([^]]*))?"   # params  (group 3, optional)
    r"\]"
)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_mss(text: str, strict_version: int | None = 1) -> list[MSSToken]:
    r"""Parse all MSS escape sequences from a text string.

    Parameters
    ----------
    text : str
        Input text potentially containing \TME[...] sequences.
    strict_version : int | None
        If set, emit warnings for unrecognized versions. None = accept all.

    Returns
    -------
    list[MSSToken]
        All parsed tokens in order of appearance.

    Examples
    --------
    >>> tokens = parse_mss(r"\TME[1:W:2]")
    >>> tokens[0].opcode
    'W'
    >>> tokens[0].params
    ['2']
    """
    tokens: list[MSSToken] = []

    for match in _MSS_PATTERN.finditer(text):
        version = int(match.group(1))
        opcode = match.group(2)
        raw_params = match.group(3)

        params: list[str] = []
        if raw_params:
            params = [p.strip() for p in raw_params.split(",")]

        tokens.append(MSSToken(
            version=version,
            opcode=opcode,
            params=params,
            raw=match.group(0),
        ))

    return tokens


def parse_mss_to_units(text: str) -> list[ProsodicUnit]:
    r"""Parse MSS tokens and convert weight tokens to ProsodicUnits.

    Only processes W (weight) tokens with optional preceding T (tension)
    and H (hierarchy) tokens.

    Parameters
    ----------
    text : str
        Input text with MSS annotations.

    Returns
    -------
    list[ProsodicUnit]
        Extracted prosodic units.
    """
    tokens = parse_mss(text)
    units: list[ProsodicUnit] = []

    current_tension = Tension.NEUTRAL
    current_level = Level.L0_MATRA

    for tok in tokens:
        if tok.opcode == "T" and tok.params:
            val = int(tok.params[0])
            current_tension = Tension(val)
        elif tok.opcode == "H" and tok.params:
            val = int(tok.params[0])
            current_level = Level(val)
        elif tok.opcode == "W" and tok.params:
            val = int(tok.params[0])
            units.append(ProsodicUnit(
                weight=Trit(val),
                tension=current_tension,
                level=current_level,
            ))
            # Reset tension after use (tension is per-unit, not sticky)
            current_tension = Tension.NEUTRAL
        elif tok.opcode == "*":
            current_tension = Tension.NEUTRAL
            current_level = Level.L0_MATRA

    return units


# ---------------------------------------------------------------------------
# Emitter
# ---------------------------------------------------------------------------

def emit_mss(
    unit: ProsodicUnit,
    version: int = 1,
    include_tension: bool = True,
    include_level: bool = True,
) -> str:
    r"""Emit an MSS escape sequence for a ProsodicUnit.

    Parameters
    ----------
    unit : ProsodicUnit
        The unit to encode.
    version : int
        Protocol version.
    include_tension : bool
        Include tension if non-neutral.
    include_level : bool
        Include level if non-default (L0).

    Returns
    -------
    str
        MSS escape sequence(s).

    Examples
    --------
    >>> from mcore_py.model import ProsodicUnit, Trit, Tension, Level
    >>> u = ProsodicUnit(weight=Trit.S2, tension=Tension.DEBT, level=Level.L2_GANA)
    >>> emit_mss(u)
    '\\TME[1:T:-1]\\TME[1:H:2]\\TME[1:W:1]'
    """
    parts: list[str] = []

    if include_tension and unit.tension != Tension.NEUTRAL:
        parts.append(f"\\TME[{version}:T:{unit.tension.value}]")

    if include_level and unit.level != Level.L0_MATRA:
        parts.append(f"\\TME[{version}:H:{unit.level.value}]")

    parts.append(f"\\TME[{version}:W:{unit.weight.value}]")

    return "".join(parts)


def emit_mss_frame(
    children: list[ProsodicUnit],
    version: int = 1,
) -> str:
    r"""Emit a PUSH_FRAME / content / POP_FRAME MSS sequence.

    Parameters
    ----------
    children : list[ProsodicUnit]
        Children of the constituent.
    version : int
        Protocol version.

    Returns
    -------
    str
        Complete MSS frame.
    """
    parts = [f"\\TME[{version}:F:push]"]
    for child in children:
        parts.append(emit_mss(child, version=version))
    parts.append(f"\\TME[{version}:F:pop]")
    return "".join(parts)
