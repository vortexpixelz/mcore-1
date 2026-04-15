"""
Checker Algorithm (Spec Section 10.1)
======================================

Validates that a metrical tree satisfies mora conservation and all budget
constraints via post-order traversal.

The fundamental invariant: weight is a monoid homomorphism from the tree
structure to the trit algebra. For every internal node n with children
c1, ..., ck:

    w(n) = w(c1) + w(c2) + ... + w(ck)

Weight is neither created nor destroyed — only pooled.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from mcore_py.algebra import OVERFLOW, trit_add_seq
from mcore_py.model import Constituent, Level, ProsodicUnit, Trit


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------

class ErrorKind(Enum):
    """Categories of validation errors."""
    OVERFLOW = auto()           # Weight addition overflowed
    CONSERVATION = auto()       # Parent weight != sum of children
    BUDGET = auto()             # Budget constraint violated
    TENSION_UNRESOLVED = auto() # DEFER not resolved before POP_FRAME
    EMPTY_CONSTITUENT = auto()  # Constituent with no children


@dataclass(frozen=True)
class CheckError:
    """A single validation error in the metrical tree.

    Attributes
    ----------
    kind : ErrorKind
        The category of error.
    node_id : str
        The id of the ProsodicUnit where the error was detected.
    message : str
        Human-readable description.
    level : Level
        Hierarchy level where the error occurred.
    """
    kind: ErrorKind
    node_id: str
    message: str
    level: Level

    def __repr__(self) -> str:
        return f"CheckError({self.kind.name}: {self.message})"


@dataclass
class CheckResult:
    """Result of a tree validation.

    Attributes
    ----------
    valid : bool
        True if the tree is well-formed.
    errors : list[CheckError]
        All errors found (empty if valid).
    nodes_checked : int
        Total nodes visited during validation.
    """
    valid: bool
    errors: list[CheckError] = field(default_factory=list)
    nodes_checked: int = 0

    def __bool__(self) -> bool:
        return self.valid

    def __repr__(self) -> str:
        if self.valid:
            return f"CheckResult(valid=True, nodes={self.nodes_checked})"
        return (
            f"CheckResult(valid=False, errors={len(self.errors)}, "
            f"nodes={self.nodes_checked})"
        )


# ---------------------------------------------------------------------------
# Core checker
# ---------------------------------------------------------------------------

def check_tree(root: Constituent) -> CheckResult:
    """Validate a metrical tree for mora conservation and budget constraints.

    Uses post-order traversal: validates children before parent.

    Parameters
    ----------
    root : Constituent
        The root constituent of the metrical tree.

    Returns
    -------
    CheckResult
        Validation result with all errors found.

    Examples
    --------
    >>> from mcore_py.model import *
    >>> # Build a valid heavy-light foot (S2 = S1 + S1)
    >>> foot = Constituent(
    ...     parent=ProsodicUnit(weight=Trit.S2, level=Level.L2_GANA),
    ...     children=[
    ...         ProsodicUnit(weight=Trit.S1, level=Level.L0_MATRA),
    ...         ProsodicUnit(weight=Trit.S1, level=Level.L0_MATRA),
    ...     ],
    ... )
    >>> result = check_tree(foot)
    >>> result.valid
    True
    """
    errors: list[CheckError] = []
    nodes_checked = _check_node(root, errors)
    return CheckResult(
        valid=len(errors) == 0,
        errors=errors,
        nodes_checked=nodes_checked,
    )


def _check_node(node: Constituent, errors: list[CheckError]) -> int:
    """Recursively validate a node and its subtree. Returns nodes checked."""
    count = 1  # Count this node

    # Check for empty constituent
    if len(node.children) == 0:
        errors.append(CheckError(
            kind=ErrorKind.EMPTY_CONSTITUENT,
            node_id=node.parent.id,
            message=f"Constituent at {node.parent.level.name} has no children",
            level=node.parent.level,
        ))
        return count

    # Recurse into child constituents first (post-order)
    for child in node.children:
        if isinstance(child, Constituent):
            count += _check_node(child, errors)
        else:
            count += 1

    # Collect child weights
    child_weights: list[Trit] = node.child_weights()

    # Check mora conservation: w(parent) = w(c1) + w(c2) + ... + w(ck)
    pooled = trit_add_seq(child_weights)

    if pooled is OVERFLOW:
        errors.append(CheckError(
            kind=ErrorKind.OVERFLOW,
            node_id=node.parent.id,
            message=(
                f"Weight overflow at {node.parent.level.name}: "
                f"children {[w.name for w in child_weights]} exceed S3"
            ),
            level=node.parent.level,
        ))
    elif pooled != node.parent.weight:
        errors.append(CheckError(
            kind=ErrorKind.CONSERVATION,
            node_id=node.parent.id,
            message=(
                f"Conservation violated at {node.parent.level.name}: "
                f"parent weight {node.parent.weight.name} != "
                f"pooled children {pooled.name}"  # type: ignore[union-attr]
            ),
            level=node.parent.level,
        ))

    # Check budget constraint
    if node.budget is not None:
        total = sum(w.value for w in child_weights)
        if not node.budget.satisfied(total):
            errors.append(CheckError(
                kind=ErrorKind.BUDGET,
                node_id=node.parent.id,
                message=(
                    f"Budget violation at {node.parent.level.name}: "
                    f"total weight {total} outside "
                    f"[{node.budget.min_weight.value}, "
                    f"{node.budget.max_weight.value if node.budget.max_weight is not None else 'inf'}]"
                ),
                level=node.parent.level,
            ))

    # Check unresolved DEFERs (Spec §3.4 Option B)
    for tension, defer_level in node.defers:
        if node.parent.level >= Level.L4_SLOKA:
            # At top level, DEFERs must be resolved
            errors.append(CheckError(
                kind=ErrorKind.TENSION_UNRESOLVED,
                node_id=node.parent.id,
                message=(
                    f"Unresolved DEFER at {node.parent.level.name}: "
                    f"tension {tension.name} from {defer_level.name}"
                ),
                level=node.parent.level,
            ))
        # Otherwise, DEFERs propagate upward (handled by the caller)

    return count
