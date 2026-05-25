"""
Base64-TME Serialization (Spec Section 7)
==========================================

Maps TME-6 values (0-63) to a 64-character alphabet for text-safe
serialization in UTF-8 streams.

Key visual property: Trit-pair states (opcodes 15-23) encode as F through N,
making metrical content immediately recognizable in a Base64-TME stream.

Alphabet:
    00-09: 0 1 2 3 4 5 6 7 8 9
    10-35: A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
    36-47: a b c d e f g h i j k l
    48-63: m n o p q r s t u v w x y z . _
"""

from __future__ import annotations

from mcore_py.tme6 import Opcode


# ---------------------------------------------------------------------------
# Alphabet definition (Spec §7)
# ---------------------------------------------------------------------------

_B64TME_CHARS = (
    "0123456789"                    # 00-09: digits
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"    # 10-35: uppercase
    "abcdefghijkl"                  # 36-47: lowercase a-l
    "mnopqrstuvwxyz._"              # 48-63: lowercase m-z + . + _
)

assert len(_B64TME_CHARS) == 64, f"Alphabet must be exactly 64 chars, got {len(_B64TME_CHARS)}"

# Build reverse lookup: char -> int
_CHAR_TO_INT: dict[str, int] = {ch: i for i, ch in enumerate(_B64TME_CHARS)}


# ---------------------------------------------------------------------------
# Encode / Decode
# ---------------------------------------------------------------------------

def to_base64tme(opcodes: list[int | Opcode]) -> str:
    """Encode a TME-6 opcode stream as a Base64-TME string.

    Parameters
    ----------
    opcodes : list[int | Opcode]
        TME-6 values (0-63).

    Returns
    -------
    str
        Base64-TME encoded string.

    Raises
    ------
    ValueError
        If any value is outside 0-63.

    Examples
    --------
    >>> # Heavy-light foot: PUSH_FRAME SET_LEVEL_2 SET_WEIGHT_S2 SET_WEIGHT_S1 POP_FRAME
    >>> to_base64tme([11, 8, 1, 0, 12])
    'B810C'
    """
    chars: list[str] = []
    for op in opcodes:
        val = int(op)
        if val < 0 or val > 63:
            raise ValueError(f"TME-6 value out of range: {val}")
        chars.append(_B64TME_CHARS[val])
    return "".join(chars)


def from_base64tme(stream: str) -> list[int]:
    """Decode a Base64-TME string to TME-6 opcode values.

    Parameters
    ----------
    stream : str
        Base64-TME encoded string.

    Returns
    -------
    list[int]
        TME-6 opcode values (0-63).

    Raises
    ------
    ValueError
        If any character is not in the Base64-TME alphabet.

    Examples
    --------
    >>> from_base64tme("B810C")
    [11, 8, 1, 0, 12]
    """
    values: list[int] = []
    for i, ch in enumerate(stream):
        if ch not in _CHAR_TO_INT:
            raise ValueError(
                f"Invalid Base64-TME character at position {i}: {ch!r}"
            )
        values.append(_CHAR_TO_INT[ch])
    return values


# ---------------------------------------------------------------------------
# Visual inspection helpers
# ---------------------------------------------------------------------------

def annotate_stream(stream: str) -> list[tuple[str, int, str]]:
    """Annotate each character in a Base64-TME stream with its opcode name.

    Returns a list of (char, opcode_value, opcode_name) tuples.

    Examples
    --------
    >>> annotate_stream("B810C")
    [('B', 11, 'PUSH_FRAME'), ('8', 8, 'SET_LEVEL_2'), ('1', 1, 'SET_WEIGHT_S2'), ('0', 0, 'SET_WEIGHT_S1'), ('C', 12, 'POP_FRAME')]
    """
    result: list[tuple[str, int, str]] = []
    for ch in stream:
        val = _CHAR_TO_INT.get(ch)
        if val is None:
            result.append((ch, -1, "UNKNOWN"))
        else:
            try:
                name = Opcode(val).name
            except ValueError:
                name = f"RAW_{val}"
            result.append((ch, val, name))
    return result


def is_metrical_content(stream: str) -> bool:
    """Check if a Base64-TME stream contains trit-pair metrical content.

    Trit-pair states (opcodes 15-23) encode as F through N.
    """
    return any(ch in "FGHIJKLMN" for ch in stream)
