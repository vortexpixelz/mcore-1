"""
Terminal Renderer (Spec Section 9 — MRP)
==========================================

Renders MCORE-1 metrical structures using ANSI terminal formatting:
  - S1 = dim text
  - S2 = normal text
  - S3 = bold + underline
  - debt = red background
  - surplus = green background
  - Hierarchy = Level × 2 indent
"""

from __future__ import annotations

from mcore_py.model import Constituent, Level, ProsodicUnit, Tension, Trit


# ---------------------------------------------------------------------------
# ANSI escape codes
# ---------------------------------------------------------------------------

class _Ansi:
    RESET = "\033[0m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    FG_WHITE = "\033[97m"


# Weight -> ANSI formatting
_WEIGHT_FORMAT: dict[Trit, str] = {
    Trit.S1: _Ansi.DIM,
    Trit.S2: "",  # normal (no modifier)
    Trit.S3: _Ansi.BOLD + _Ansi.UNDERLINE,
}

# Tension -> ANSI background
_TENSION_FORMAT: dict[Tension, str] = {
    Tension.DEBT: _Ansi.BG_RED + _Ansi.FG_WHITE,
    Tension.NEUTRAL: "",
    Tension.SURPLUS: _Ansi.BG_GREEN,
}

# Classical metrical symbols
_WEIGHT_SYMBOL: dict[Trit, str] = {
    Trit.S1: "u",   # breve (light)
    Trit.S2: "–",   # macron (heavy)
    Trit.S3: "≡",   # triple bar (superheavy)
}

_TENSION_SYMBOL: dict[Tension, str] = {
    Tension.DEBT: "↓",
    Tension.NEUTRAL: "",
    Tension.SURPLUS: "↑",
}


# ---------------------------------------------------------------------------
# Rendering functions
# ---------------------------------------------------------------------------

def render_unit(unit: ProsodicUnit, use_ansi: bool = True) -> str:
    """Render a single ProsodicUnit as a formatted string.

    Parameters
    ----------
    unit : ProsodicUnit
        Unit to render.
    use_ansi : bool
        If True, include ANSI escape codes. If False, plain symbols.
    """
    symbol = _WEIGHT_SYMBOL[unit.weight]
    t_sym = _TENSION_SYMBOL[unit.tension]
    label = unit.label or ""

    if not use_ansi:
        return f"{symbol}{t_sym}" + (f"({label})" if label else "")

    w_fmt = _WEIGHT_FORMAT[unit.weight]
    t_fmt = _TENSION_FORMAT[unit.tension]
    content = f"{symbol}{t_sym}" + (f" {label}" if label else "")

    return f"{w_fmt}{t_fmt}{content}{_Ansi.RESET}"


def render_terminal(
    node: Constituent | ProsodicUnit,
    use_ansi: bool = True,
    indent: int = 0,
) -> str:
    """Render a metrical tree for terminal display.

    Parameters
    ----------
    node : Constituent | ProsodicUnit
        Root of the tree to render.
    use_ansi : bool
        Include ANSI escape codes.
    indent : int
        Current indentation level.

    Returns
    -------
    str
        Multi-line string representation.
    """
    if isinstance(node, ProsodicUnit):
        prefix = "  " * indent
        return f"{prefix}{render_unit(node, use_ansi)}"

    lines: list[str] = []
    prefix = "  " * indent
    level_name = node.parent.level.name

    # Header for this constituent
    w_sym = _WEIGHT_SYMBOL[node.parent.weight]
    header = f"{prefix}[{level_name} {w_sym}]"
    if use_ansi:
        w_fmt = _WEIGHT_FORMAT[node.parent.weight]
        header = f"{prefix}{w_fmt}[{level_name} {w_sym}]{_Ansi.RESET}"
    lines.append(header)

    # Children
    for child in node.children:
        child_indent = indent + node.parent.level.value + 1
        lines.append(render_terminal(child, use_ansi, child_indent))

    return "\n".join(lines)


def render_line_flat(units: list[ProsodicUnit], use_ansi: bool = True) -> str:
    """Render a flat sequence of units as a single line of metrical notation.

    Parameters
    ----------
    units : list[ProsodicUnit]
        The metrical positions.
    use_ansi : bool
        Include ANSI formatting.

    Returns
    -------
    str
        Single line like "– u – u | – u –"
    """
    parts = [render_unit(u, use_ansi) for u in units]
    return " ".join(parts)


def render_scansion(units: list[ProsodicUnit]) -> str:
    """Render a plain-text scansion line (no ANSI).

    Returns a string like: – u – – u – u –

    Parameters
    ----------
    units : list[ProsodicUnit]
        Metrical positions.
    """
    return " ".join(
        _WEIGHT_SYMBOL[u.weight] + _TENSION_SYMBOL[u.tension]
        for u in units
    )
