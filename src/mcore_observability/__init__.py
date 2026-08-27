"""Experiment and observability adapters for MCORE-1.

This package is intentionally outside :mod:`mcore_1`: the core checker remains
pure while batch workflows gain structured, serializable run records.
"""

from .mutation_batch import BatchFailure, MutationBatchProcessor

__all__ = ["BatchFailure", "MutationBatchProcessor"]
