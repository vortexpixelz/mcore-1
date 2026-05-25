"""Post-order metrical tree validation (delegates to ``mcore_py``)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcore_py.checker import CheckError, CheckResult, check_tree as _check_tree_postorder

if TYPE_CHECKING:
    from mcore_py.model import Constituent


def check_tree(root: Constituent) -> CheckResult:
    """Validate *root* in post-order (children before parent).

    This is the same algorithm as ``mcore_py.checker.check_tree``:
    mora pooling / conservation, overflow, budget, empty-constituent, etc.
    """
    return _check_tree_postorder(root)


__all__ = ["check_tree", "CheckResult", "CheckError"]
