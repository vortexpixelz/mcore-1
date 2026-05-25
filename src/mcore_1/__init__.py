"""MCORE-1 paper integration helpers (DNA carry scan + binary tree checker).

This subpackage is oriented toward the GJB2 / sonification paper repo; the core
metrical model remains in :mod:`mcore_py`.
"""

from __future__ import annotations

from mcore_1.check_tree import (
    CheckError,
    CheckResult,
    NodeResult,
    check_constituent,
    check_deletion,
    check_tree,
)
from mcore_1.encoder import EncodeStep, dna_to_trits, iter_encode_steps
from mcore_1.errors import ErrorKind
from mcore_1.tree import (
    build_binary_metrical_tree,
    build_frozen_after_deletion_trits,
    build_post_deletion_frozen_tree,
    descendant_orig_indices,
    frozen_weight_for_interval,
    orig_span,
    pool_original_trits_for_interval,
)

__all__ = [
    "EncodeStep",
    "ErrorKind",
    "CheckError",
    "CheckResult",
    "NodeResult",
    "check_tree",
    "check_constituent",
    "check_deletion",
    "dna_to_trits",
    "iter_encode_steps",
    "build_binary_metrical_tree",
    "build_frozen_after_deletion_trits",
    "build_post_deletion_frozen_tree",
    "descendant_orig_indices",
    "orig_span",
    "frozen_weight_for_interval",
    "pool_original_trits_for_interval",
]
