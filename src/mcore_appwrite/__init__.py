"""Thin Appwrite helpers for MCORE-1 (admin client + Function execution)."""

from __future__ import annotations

from mcore_appwrite.client import build_admin_client
from mcore_appwrite.config import AppwriteConfig, use_remote_check_tree
from mcore_appwrite.executor import execute_check_tree_function

__all__ = [
    "AppwriteConfig",
    "build_admin_client",
    "execute_check_tree_function",
    "use_remote_check_tree",
]
