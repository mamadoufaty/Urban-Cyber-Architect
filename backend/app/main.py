from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api.routes import admin, auth, connectors_wazuh, deliverables, ebios, governance, grc, grc_ptr, grc_soa, knowledge, orchestration, projects, prompts, soc, urbanism
from app.config import settings
from app.database import Base, async_session, engine
import app.models.admin  # noqa: F401 — enregistrement des tables Administration
import app.models.ebios  # noqa: F401 — enregistrement des tables EBIOS
import app.models.deliverables  # noqa: F401 — enregistrement des tables livrables
import app.models.project_core  # noqa: F401 — membres et activité projet V1.3
from app.services.admin.seed_service import run_admin_seed

logging.basicConfig(level=logging.INFO)
logging.getLogger("app.services.urbanism_engine").setLevel(logging.INFO)
logging.getLogger("app.connectors.wazuh.client").setLevel(logging.INFO)
logging.getLogger("app.connectors.wazuh.service").setLevel(logging.INFO)
logging.getLogger("app.services.soc.correlation_service").setLevel(logging.INFO)


def _ensure_schema_columns(sync_conn) -> None:
    insp = inspect(sync_conn)
    if insp.has_table("urbanism_relations"):
        cols = {c["name"] for c in insp.get_columns("urbanism_relations")}
        if "properties" not in cols:
            sync_conn.execute(text("ALTER TABLE urbanism_relations ADD COLUMN properties JSON"))
            sync_conn.execute(
                text("UPDATE urbanism_relations SET properties = '{}' WHERE properties IS NULL")
            )
    if insp.has_table("wazuh_connector_config"):
        cols = {c["name"] for c in insp.get_columns("wazuh_connector_config")}
        if "indexer_username" not in cols:
            sync_conn.execute(
                text("ALTER TABLE wazuh_connector_config ADD COLUMN indexer_username VARCHAR(255)")
            )
        if "indexer_password" not in cols:
            sync_conn.execute(
                text("ALTER TABLE wazuh_connector_config ADD COLUMN indexer_password VARCHAR(255)")
            )
    if insp.has_table("projects"):
        cols = {c["name"] for c in insp.get_columns("projects")}
        project_columns = {
            "organization_id": "VARCHAR(36)",
            "code": "VARCHAR(100)",
            "client": "VARCHAR(255)",
            "priority": "VARCHAR(50)",
            "start_date": "DATE",
            "end_date": "DATE",
            "owner_id": "VARCHAR(36)",
            "tags": "JSON",
            "created_by": "VARCHAR(36)",
            "archived_at": "DATETIME",
        }
        for col_name, col_type in project_columns.items():
            if col_name not in cols:
                sync_conn.execute(text(f"ALTER TABLE projects ADD COLUMN {col_name} {col_type}"))
                cols.add(col_name)
        if "priority" in cols:
            sync_conn.execute(
                text("UPDATE projects SET priority = 'medium' WHERE priority IS NULL")
            )
        if "tags" in cols:
            sync_conn.execute(text("UPDATE projects SET tags = '[]' WHERE tags IS NULL"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_schema_columns)
    async with async_session() as session:
        await run_admin_seed(session)
        await session.commit()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Plateforme d'aide à la décision pour l'architecture d'entreprise et cybersécurité",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(orchestration.router, prefix="/api")
app.include_router(governance.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(urbanism.router, prefix="/api")
app.include_router(ebios.router, prefix="/api")
app.include_router(grc.router, prefix="/api")
app.include_router(grc_soa.router, prefix="/api")
app.include_router(grc_ptr.router, prefix="/api")
app.include_router(connectors_wazuh.router, prefix="/api")
app.include_router(soc.router, prefix="/api")
app.include_router(deliverables.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name, "version": "1.0.0"}
