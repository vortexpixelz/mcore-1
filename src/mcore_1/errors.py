"""Error kinds for MCORE-1 tree validation (paper / GJB2 integration).

These mirror the validation categories used by :func:`mcore_1.check_tree.check_tree`
(which delegates to ``mcore_py.checker``).
"""

from __future__ import annotations

from enum import Enum, auto


class ErrorKind(Enum):
    """Structured error categories for metrical-tree checks."""

    CONSERVATION = auto()
    OVERFLOW = auto()
    EMPTY_CONSTITUENT = auto()
