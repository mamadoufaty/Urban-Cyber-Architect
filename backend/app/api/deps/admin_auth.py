"""Dépendance auth admin — placeholder jusqu'au branchement JWT/session backend.

TODO: brancher la vérification du token et la permission administration:read/write.
"""

from __future__ import annotations

from typing import Any


async def require_admin_access() -> Any | None:
    """Placeholder — n'applique aucune restriction pour ne pas casser les tests existants."""
    return None
