"""Typed configuration for Appwrite + optional Function delegation."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppwriteConfig:
    """Server-side Appwrite settings (API key — never ship to browsers)."""

    endpoint: str
    project_id: str
    api_key: str
    check_tree_function_id: str | None = None

    @classmethod
    def from_env(cls) -> AppwriteConfig | None:
        endpoint = os.environ.get("APPWRITE_ENDPOINT", "").rstrip("/")
        project = os.environ.get("APPWRITE_PROJECT_ID", "")
        key = os.environ.get("APPWRITE_API_KEY", "")
        if not (endpoint and project and key):
            return None
        fid = os.environ.get("APPWRITE_FUNCTION_CHECK_TREE_ID") or None
        return cls(
            endpoint=endpoint,
            project_id=project,
            api_key=key,
            check_tree_function_id=fid,
        )


def use_remote_check_tree() -> bool:
    """When true, MCP / gateways may delegate ``check_tree`` to Appwrite Functions."""
    return os.environ.get("APPWRITE_USE_FUNCTIONS", "").lower() in ("1", "true", "yes")
