"""Appwrite admin client factory (server SDK)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcore_appwrite.config import AppwriteConfig

if TYPE_CHECKING:
    from appwrite.client import Client


def build_admin_client(cfg: AppwriteConfig) -> Client:
    from appwrite.client import Client

    ep = cfg.endpoint if cfg.endpoint.endswith("/v1") else f"{cfg.endpoint}/v1"
    return Client().set_endpoint(ep).set_project(cfg.project_id).set_key(cfg.api_key)
