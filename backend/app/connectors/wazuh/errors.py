"""Classification des erreurs connecteur Wazuh — messages utilisateur."""

from __future__ import annotations

import httpx


class WazuhAuthError(Exception):
    pass


class WazuhClientError(Exception):
    pass


def classify_wazuh_exception(exc: BaseException) -> str:
    if isinstance(exc, (WazuhAuthError, WazuhClientError)):
        return str(exc)

    if isinstance(exc, httpx.TimeoutException):
        return "Timeout : le manager Wazuh ne répond pas dans le délai imparti."

    if isinstance(exc, httpx.ConnectError):
        return _classify_connect_error(exc)

    if isinstance(exc, httpx.HTTPError):
        return f"Erreur réseau HTTP : {exc}"

    return f"Erreur inattendue : {exc}"


def _classify_connect_error(exc: httpx.ConnectError) -> str:
    message = str(exc).lower().replace("_", " ")
    cause = exc.__cause__
    cause_text = str(cause).lower().replace("_", " ") if cause else ""

    combined = f"{message} {cause_text}"

    if "certificate verify failed" in combined or "self-signed certificate" in combined:
        return (
            "Certificat invalide : le certificat SSL est auto-signé ou non reconnu. "
            "Décochez « Vérification SSL » dans les paramètres du connecteur."
        )
    if "ssl" in combined and ("cert" in combined or "tls" in combined):
        return (
            "Erreur SSL : impossible d'établir une connexion sécurisée. "
            "Vérifiez la configuration SSL ou désactivez « Vérification SSL »."
        )
    if "connection refused" in combined:
        return (
            "Manager inaccessible : connexion refusée. "
            "Vérifiez l'URL (ex. https://localhost:55000) et que l'API Wazuh est démarrée."
        )
    if "name or service not known" in combined or "getaddrinfo" in combined:
        return "Manager inaccessible : nom d'hôte introuvable. Vérifiez l'URL du manager."
    if "network is unreachable" in combined:
        return "Manager inaccessible : réseau injoignable."

    return f"Erreur réseau : impossible de joindre le manager Wazuh ({exc})."


def auth_error_from_status(status_code: int, body: str = "") -> str:
    if status_code in (401, 403):
        detail = _extract_wazuh_detail(body)
        if detail:
            return f"Authentification invalide : {detail}"
        return (
            "Authentification invalide : identifiants incorrects ou utilisateur sans droits API. "
            "Utilisez un compte API Wazuh (ex. wazuh-wui)."
        )
    if status_code == 404:
        return "Manager inaccessible : endpoint d'authentification introuvable. Vérifiez l'URL de l'API."
    return f"Authentification Wazuh échouée (HTTP {status_code})."


def _extract_wazuh_detail(body: str) -> str:
    text = body.strip()
    if not text:
        return ""
    try:
        import json

        payload = json.loads(text)
        if isinstance(payload, dict):
            return str(payload.get("detail") or payload.get("title") or "")
    except (ValueError, TypeError):
        pass
    return text[:200]
