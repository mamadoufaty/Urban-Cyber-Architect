"""Authentification JWT — API Wazuh Manager."""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from app.connectors.wazuh.errors import (
    WazuhAuthError,
    auth_error_from_status,
    classify_wazuh_exception,
)
from app.connectors.wazuh.models import WazuhConnectionConfig


@dataclass
class _TokenState:
    token: str
    expires_at: float


_authenticator_cache: dict[str, WazuhAuthenticator] = {}


def get_shared_authenticator(config: WazuhConnectionConfig) -> WazuhAuthenticator:
    """Authenticator partagé par configuration — évite un nouveau POST /authenticate par requête."""
    key = f"{config.normalized_base_url()}:{config.username.strip()}"
    auth = _authenticator_cache.get(key)
    if auth is None:
        auth = WazuhAuthenticator(config)
        _authenticator_cache[key] = auth
    return auth


def invalidate_shared_authenticators() -> None:
    _authenticator_cache.clear()


class WazuhAuthenticator:
    """Obtient et met en cache un jeton Bearer Wazuh (POST /security/user/authenticate?raw=true)."""

    def __init__(self, config: WazuhConnectionConfig):
        self._config = config
        self._state: _TokenState | None = None

    def _verify(self) -> bool:
        return bool(self._config.verify_ssl)

    async def get_token(self, client: httpx.AsyncClient | None = None) -> str:
        if self._state and self._state.expires_at > time.time():
            return self._state.token

        try:
            if client is not None:
                return await self._authenticate(client)
            async with httpx.AsyncClient(
                verify=self._verify(),
                timeout=httpx.Timeout(30.0),
            ) as owned:
                return await self._authenticate(owned)
        except WazuhAuthError:
            raise
        except httpx.HTTPError as exc:
            raise WazuhAuthError(classify_wazuh_exception(exc)) from exc

    async def _authenticate(self, client: httpx.AsyncClient) -> str:
        url = f"{self._config.normalized_base_url()}/security/user/authenticate?raw=true"
        response = await client.post(
            url,
            auth=(self._config.username, self._config.password),
        )
        if response.status_code != 200:
            body = response.text.strip()
            if body:
                raise WazuhAuthError(
                    f"Authentification Wazuh échouée (HTTP {response.status_code}): {body[:500]}"
                )
            raise WazuhAuthError(auth_error_from_status(response.status_code, body))

        token = response.text.strip()
        if not token:
            raise WazuhAuthError("Authentification invalide : jeton JWT absent dans la réponse Wazuh.")

        self._state = _TokenState(token=token, expires_at=time.time() + 840)
        return token

    def invalidate(self) -> None:
        self._state = None
