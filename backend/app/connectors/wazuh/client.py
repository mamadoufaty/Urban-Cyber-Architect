"""Client HTTP — API Wazuh Manager et Indexer (lecture seule)."""



from __future__ import annotations



import logging

from typing import Any

from urllib.parse import quote



import httpx



from app.connectors.wazuh.auth import WazuhAuthenticator, get_shared_authenticator

from app.connectors.wazuh.errors import (

    WazuhAuthError,

    WazuhClientError,

    auth_error_from_status,

    classify_wazuh_exception,

)

from app.connectors.wazuh.models import WazuhAgent, WazuhAlert, WazuhConnectionConfig



logger = logging.getLogger(__name__)





class WazuhClient:

    """Client lecture seule pour l'API Wazuh Manager (55000) et l'API Indexer (9200)."""



    def __init__(self, config: WazuhConnectionConfig):

        self._config = config

        self._auth: WazuhAuthenticator = get_shared_authenticator(config)



    def _verify(self) -> bool:

        return bool(self._config.verify_ssl)



    def _manager_client(self) -> httpx.AsyncClient:

        return httpx.AsyncClient(

            verify=self._verify(),

            timeout=httpx.Timeout(30.0),

        )



    async def _manager_get(self, path: str, *, params: dict | None = None) -> dict[str, Any]:

        try:

            async with self._manager_client() as client:

                token = await self._auth.get_token(client)

                url = f"{self._config.normalized_base_url()}{path}"

                response = await client.get(

                    url,

                    params=params,

                    headers={"Authorization": f"Bearer {token}"},

                )

                if response.status_code == 401:

                    self._auth.invalidate()

                    token = await self._auth.get_token(client)

                    response = await client.get(

                        url,

                        params=params,

                        headers={"Authorization": f"Bearer {token}"},

                    )

                if response.status_code in (401, 403):

                    raise WazuhClientError(

                        auth_error_from_status(response.status_code, response.text)

                    )

                if response.status_code != 200:

                    raise WazuhClientError(

                        f"Wazuh API {path} → {response.status_code}: {response.text[:300]}"

                    )

                return response.json()

        except WazuhAuthError as exc:

            raise WazuhClientError(str(exc)) from exc

        except httpx.HTTPError as exc:

            raise WazuhClientError(classify_wazuh_exception(exc)) from exc



    async def _indexer_request(

        self,

        method: str,

        path: str,

        *,

        json: dict | None = None,

    ) -> httpx.Response:

        """Requête indexer — réutilise le client manager et le JWT en cache (pas de nouvel authenticate dédié)."""

        indexer_url = self._config.resolved_indexer_url()

        url = f"{indexer_url}{path}"

        try:

            async with self._manager_client() as client:

                token = await self._auth.get_token(client)

                logger.info(

                    "Wazuh indexer %s %s — étape 1/2 : Bearer JWT manager (cache partagé)",

                    method,

                    url,

                )

                response = await client.request(

                    method,

                    url,

                    json=json,

                    headers={

                        "Authorization": f"Bearer {token}",

                        "Content-Type": "application/json",

                    },

                )

                if response.status_code not in (401, 403):

                    return response



                logger.warning(

                    "Wazuh indexer %s %s — étape 1/2 refusée (HTTP %s) : %s",

                    method,

                    url,

                    response.status_code,

                    response.text[:200],

                )



                indexer_user, indexer_pwd = self._config.credentials_for_indexer()

                logger.info(

                    "Wazuh indexer %s %s — étape 2/2 : Basic auth (utilisateur %s)",

                    method,

                    url,

                    indexer_user,

                )

                response = await client.request(

                    method,

                    url,

                    json=json,

                    auth=(indexer_user, indexer_pwd),

                    headers={"Content-Type": "application/json"},

                )

                if response.status_code in (401, 403):

                    logger.error(

                        "Wazuh indexer %s %s — étape 2/2 refusée (HTTP %s) : %s",

                        method,

                        url,

                        response.status_code,

                        response.text[:200],

                    )

                return response

        except httpx.HTTPError as exc:

            raise WazuhClientError(classify_wazuh_exception(exc)) from exc



    async def get_api_info(self) -> dict[str, Any]:

        data = await self._manager_get("/")

        return data.get("data") or data



    async def get_manager_info(self) -> dict[str, Any]:

        data = await self._manager_get("/manager/info")

        return (data.get("data") or {}).get("affected_items", [{}])[0]



    async def list_agents(self, *, limit: int = 500, offset: int = 0) -> tuple[list[WazuhAgent], int]:

        data = await self._manager_get("/agents", params={"limit": limit, "offset": offset})

        block = data.get("data") or {}

        items = block.get("affected_items") or []

        total = int(block.get("total_affected_items") or len(items))

        agents = [self._parse_agent(item) for item in items if str(item.get("id")) != "000"]

        return agents, total



    def _parse_agent(self, item: dict[str, Any]) -> WazuhAgent:

        os_info = item.get("os") or {}

        return WazuhAgent(

            id=str(item.get("id", "")),

            name=str(item.get("name", "")),

            ip=str(item.get("ip", "")),

            status=str(item.get("status", "")),

            os=str(os_info.get("name", "")),

            version=str(item.get("version", "")),

            last_keep_alive=str(item.get("lastKeepAlive", "")),

            raw=item,

        )



    async def search_alerts(self, *, limit: int = 50, offset: int = 0) -> tuple[list[WazuhAlert], int]:

        """Alertes via l'API Wazuh Indexer (wazuh-alerts-*/_search) — doc officielle Wazuh."""

        body = {

            "from": offset,

            "size": limit,

            "sort": [{"@timestamp": {"order": "desc"}}],

            "query": {"match_all": {}},

        }

        response = await self._indexer_request("POST", "/wazuh-alerts-*/_search", json=body)

        if response.status_code in (401, 403):

            detail = auth_error_from_status(response.status_code, response.text)

            raise WazuhClientError(

                f"{detail} — l'indexer Wazuh (port 9200) requiert souvent les identifiants "

                "dashboard (ex. admin), distincts de l'utilisateur API manager (wazuh-wui)."

            )

        if response.status_code != 200:

            raise WazuhClientError(

                f"Wazuh Indexer alerts → {response.status_code}: {response.text[:300]}"

            )

        payload = response.json()



        hits = (payload.get("hits") or {}).get("hits") or []

        total_block = (payload.get("hits") or {}).get("total") or {}

        total = int(total_block.get("value") or len(hits))

        alerts = [self._parse_alert(hit) for hit in hits]

        return alerts, total



    async def get_alert(self, alert_id: str) -> WazuhAlert | None:

        encoded_id = quote(alert_id, safe="")

        response = await self._indexer_request("GET", f"/wazuh-alerts-*/_doc/{encoded_id}")

        if response.status_code == 404:

            return None

        if response.status_code in (401, 403):

            detail = auth_error_from_status(response.status_code, response.text)

            raise WazuhClientError(

                f"{detail} — l'indexer Wazuh (port 9200) requiert souvent les identifiants "

                "dashboard (ex. admin), distincts de l'utilisateur API manager (wazuh-wui)."

            )

        if response.status_code != 200:

            raise WazuhClientError(

                f"Wazuh Indexer alert/{alert_id} → {response.status_code}: {response.text[:300]}"

            )

        payload = response.json()



        if not payload.get("found"):

            return None

        return self._parse_alert({"_id": payload.get("_id"), "_source": payload.get("_source", {})})



    def _parse_alert(self, hit: dict[str, Any]) -> WazuhAlert:

        source = hit.get("_source") or hit

        rule = source.get("rule") or {}

        agent = source.get("agent") or {}

        groups = rule.get("groups") or []

        return WazuhAlert(

            id=str(hit.get("_id") or source.get("id") or ""),

            timestamp=str(source.get("@timestamp") or source.get("timestamp") or ""),

            rule_id=str(rule.get("id") or ""),

            rule_level=int(rule.get("level") or 0),

            rule_description=str(rule.get("description") or ""),

            agent_id=str(agent.get("id") or ""),

            agent_name=str(agent.get("name") or ""),

            full_log=str(source.get("full_log") or ""),

            groups=[str(g) for g in groups] if isinstance(groups, list) else [],

            raw=source if isinstance(source, dict) else {},

        )



    async def test_connection(self) -> dict[str, Any]:

        try:

            api_info = await self.get_api_info()

            manager = await self.get_manager_info()

            agents, total = await self.list_agents(limit=1)

            return {

                "success": True,

                "api_version": str(api_info.get("api_version", "")),

                "wazuh_version": str(manager.get("version", "")),

                "manager": str(manager.get("name", "")),

                "agents_sample": len(agents),

                "agents_total": total,

            }

        except (WazuhAuthError, WazuhClientError) as exc:

            return {"success": False, "error": str(exc)}

        except Exception as exc:

            return {"success": False, "error": classify_wazuh_exception(exc)}


