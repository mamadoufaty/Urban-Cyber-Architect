"""Registre des points d'extension GRC — module EBIOS RM."""

from __future__ import annotations

from app.metamodel.ebios import EXTENSION_MODULES, INTEGRATION_HOOKS, list_ebios_metamodel


def get_extension_registry() -> dict:
    return {
        "metamodel": list_ebios_metamodel(),
        "future_modules": EXTENSION_MODULES,
        "integrations": INTEGRATION_HOOKS,
    }


def is_hook_available(hook_id: str) -> bool:
    for hook in INTEGRATION_HOOKS:
        if hook["id"] == hook_id:
            return hook.get("status") == "available"
    return False
