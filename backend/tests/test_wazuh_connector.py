"""Tests connecteur Wazuh."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.connectors.wazuh.auth import WazuhAuthenticator, get_shared_authenticator
from app.connectors.wazuh.cache import TtlCache
from app.connectors.wazuh.client import WazuhClient
from app.connectors.wazuh.errors import classify_wazuh_exception
from app.connectors.wazuh.models import WazuhConnectionConfig
from app.connectors.wazuh.service import get_wazuh_status, run_wazuh_connection_test, update_config
from app.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


def test_ttl_cache_expires():
    cache: TtlCache[str] = TtlCache(ttl_seconds=0)
    cache.set("k", "v", ttl_seconds=0)
    import time

    time.sleep(0.01)
    assert cache.get("k") is None


def test_connection_config_indexer_credentials_fallback():
    cfg = WazuhConnectionConfig(
        base_url="https://wazuh.local:55000",
        username="wazuh-wui",
        password="api-secret",
    )
    assert cfg.credentials_for_indexer() == ("wazuh-wui", "api-secret")
    cfg.indexer_username = "admin"
    cfg.indexer_password = "indexer-secret"
    assert cfg.credentials_for_indexer() == ("admin", "indexer-secret")
    cfg.indexer_password = ""
    assert cfg.credentials_for_indexer() == ("admin", "api-secret")


def test_connection_config_indexer_derivation():
    cfg = WazuhConnectionConfig(base_url="https://wazuh.local:55000")
    assert cfg.resolved_indexer_url() == "https://wazuh.local:9200"
    cfg.indexer_url = "https://indexer.local:9200"
    assert cfg.resolved_indexer_url() == "https://indexer.local:9200"


@pytest.mark.asyncio
async def test_wazuh_client_parses_agents():
    config = WazuhConnectionConfig(
        base_url="https://wazuh.test:55000",
        username="wazuh",
        password="wazuh",
        verify_ssl=False,
    )
    client = WazuhClient(config)

    mock_response = {
        "data": {
            "affected_items": [
                {
                    "id": "001",
                    "name": "agent-1",
                    "ip": "10.0.0.1",
                    "status": "active",
                    "os": {"name": "Ubuntu"},
                    "version": "v4.8.0",
                    "lastKeepAlive": "2026-06-24T10:00:00Z",
                }
            ],
            "total_affected_items": 1,
        }
    }

    with patch.object(client, "_manager_get", AsyncMock(return_value=mock_response)):
        agents, total = await client.list_agents()
    assert total == 1
    assert agents[0].name == "agent-1"
    assert agents[0].status == "active"


@pytest.mark.asyncio
async def test_wazuh_search_alerts_uses_manager_jwt_first():
    config = WazuhConnectionConfig(
        base_url="https://wazuh.test:55000",
        username="wazuh-wui",
        password="secret",
        verify_ssl=False,
    )
    client = WazuhClient(config)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_id": "alert-1",
                    "_source": {
                        "@timestamp": "2026-06-24T10:00:00Z",
                        "rule": {"id": "5710", "level": 10, "description": "SSH failed", "groups": ["sshd"]},
                        "agent": {"id": "001", "name": "agent-1"},
                    },
                }
            ],
        }
    }

    with patch.object(client, "_indexer_request", AsyncMock(return_value=mock_response)) as mock_indexer:
        alerts, total = await client.search_alerts()
    assert total == 1
    assert alerts[0].rule_id == "5710"
    mock_indexer.assert_awaited_once()


@pytest.mark.asyncio
async def test_shared_authenticator_reuses_token():
    config = WazuhConnectionConfig(
        base_url="https://localhost:55000",
        username="wazuh-wui",
        password="secret",
        verify_ssl=False,
    )
    auth1 = get_shared_authenticator(config)
    auth2 = get_shared_authenticator(config)
    assert auth1 is auth2


@pytest.mark.asyncio
async def test_wazuh_status_not_configured(db_session: AsyncSession):
    status = await get_wazuh_status(db_session)
    assert status["configured"] is False
    assert status["connected"] is False


@pytest.mark.asyncio
async def test_wazuh_api_routes(db_session: AsyncSession):
    await update_config(
        db_session,
        base_url="https://wazuh.test:55000",
        username="wazuh-wui",
        password="secret",
        verify_ssl=False,
        enabled=True,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    mock_status = {
        "connected": True,
        "configured": True,
        "wazuh_version": "4.8.0",
        "api_version": "4.8.0",
        "manager": "wazuh-manager",
        "agents_total": 3,
        "agents_active": 2,
        "last_sync_at": None,
        "read_only": True,
        "error": None,
        "alerts_source": "wazuh-indexer-api",
    }

    with patch("app.api.routes.connectors_wazuh.get_wazuh_status", AsyncMock(return_value=mock_status)):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            config = await client.get("/api/connectors/wazuh/config")
            assert config.status_code == 200
            assert config.json()["password_configured"] is True

            status = await client.get("/api/connectors/wazuh/status")
            assert status.status_code == 200
            assert status.json()["agents_total"] == 3

    with patch(
        "app.api.routes.connectors_wazuh.run_wazuh_connection_test",
        AsyncMock(return_value={"success": True, "wazuh_version": "4.8.0"}),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            test = await client.post("/api/connectors/wazuh/test")
            assert test.status_code == 200
            assert test.json()["success"] is True

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_wazuh_test_connection_mocked(db_session: AsyncSession):
    await update_config(
        db_session,
        base_url="https://wazuh.test:55000",
        username="wazuh-wui",
        password="secret",
        verify_ssl=False,
        enabled=True,
    )

    with patch(
        "app.connectors.wazuh.service.WazuhClient.test_connection",
        AsyncMock(
            return_value={
                "success": True,
                "api_version": "4.8.0",
                "wazuh_version": "4.8.0",
                "manager": "wazuh-manager",
                "agents_total": 2,
            }
        ),
    ):
        result = await run_wazuh_connection_test(db_session)
    assert result["success"] is True
    assert result["agents_total"] == 2


def test_classify_ssl_connect_error():
    exc = httpx.ConnectError("SSL: CERTIFICATE_VERIFY_FAILED")
    message = classify_wazuh_exception(exc)
    assert "Certificat invalide" in message


def test_manager_client_uses_verify_ssl_false():
    config = WazuhConnectionConfig(
        base_url="https://localhost:55000",
        username="wazuh-wui",
        password="secret",
        verify_ssl=False,
    )
    client = WazuhClient(config)
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        client._manager_client()
    mock_client_cls.assert_called_once()
    assert mock_client_cls.call_args.kwargs["verify"] is False


@pytest.mark.asyncio
async def test_test_endpoint_never_500_on_ssl_error(db_session: AsyncSession):
    await update_config(
        db_session,
        base_url="https://localhost:55000",
        username="wazuh-wui",
        password="secret",
        verify_ssl=True,
        enabled=True,
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    with patch(
        "app.connectors.wazuh.service.WazuhClient.test_connection",
        AsyncMock(
            return_value={
                "success": False,
                "error": "Certificat invalide : le certificat SSL est auto-signé ou non reconnu.",
            }
        ),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/connectors/wazuh/test")
            assert response.status_code == 200
            body = response.json()
            assert body["success"] is False
            assert "Certificat" in body["error"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_auth_raw_token_from_response_text():
    config = WazuhConnectionConfig(
        base_url="https://localhost:55000",
        username="wazuh-wui",
        password="MyS3cr37P450r.*-",
        verify_ssl=False,
    )
    auth = WazuhAuthenticator(config)
    jwt = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.test.signature"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = jwt
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    token = await auth._authenticate(mock_client)
    assert token == jwt
    mock_client.post.assert_awaited_once()
    call_args = mock_client.post.call_args
    assert call_args.args[0].endswith("/security/user/authenticate?raw=true")
    assert call_args.kwargs["auth"] == ("wazuh-wui", "MyS3cr37P450r.*-")


@pytest.mark.asyncio
async def test_auth_401_returns_friendly_message():
    config = WazuhConnectionConfig(
        base_url="https://localhost:55000",
        username="bad",
        password="bad",
        verify_ssl=False,
    )
    auth = WazuhAuthenticator(config)
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = '{"title":"Unauthorized","detail":"Invalid credentials"}'
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    with pytest.raises(Exception) as exc_info:
        await auth._authenticate(mock_client)
    assert "HTTP 401" in str(exc_info.value)
    assert "Invalid credentials" in str(exc_info.value)
