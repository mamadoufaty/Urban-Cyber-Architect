"""Tests socle documentaire par défaut — Atelier 1 EBIOS RM.

Une nouvelle étude reçoit automatiquement un jeu de documents de référence
proposés (jamais validés d'office), et le générateur cartographie peut
ensuite compléter cette liste sans jamais dupliquer les documents déjà
présents.
"""

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project, UrbanismEntity
from app.services import cartography_service
from app.services.ebios.assessment_service import list_records
from app.services.ebios.workshop1_default_documents import (
    DEFAULT_REFERENCE_DOCUMENTS,
    build_default_reference_document_proposals,
)
from app.services.ebios.workshop1_service import generate_workshop1_from_cartography


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


def test_default_reference_document_proposals_are_all_proposed_and_traceable():
    proposals = build_default_reference_document_proposals()
    assert len(proposals) == len(DEFAULT_REFERENCE_DOCUMENTS) == 12
    labels = {p["label"] for p in proposals}
    for expected in (
        "EBIOS RM v1.5",
        "ISO/IEC 27001:2022",
        "ISO/IEC 27002:2022",
        "PSSI",
        "Cartographie d'urbanisme",
        "Dossier d'architecture",
        "PCA",
        "PRA",
        "Politique IAM",
        "Politique de sauvegarde",
        "Politique de journalisation",
        "Contrats critiques",
    ):
        assert expected in labels
    for proposal in proposals:
        assert proposal["properties"]["source"] == "default_framework"
        assert proposal["properties"]["doc_type"]


@pytest.mark.asyncio
async def test_new_assessment_seeds_default_documents_via_api(db_session: AsyncSession):
    project = Project(name="Socle documentaire", organization={})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    base = f"/api/projects/{project.id}/ebios"

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            assessment_id = (await client.get(f"{base}/assessment")).json()["id"]
            records = (
                await client.get(f"{base}/assessments/{assessment_id}/records")
            ).json()
            assert len(records) == 12
            assert all(r["record_type"] == "reference_document" for r in records)
            assert all(r["status"] == "proposed" for r in records)
            assert all(r["properties"]["source"] == "default_framework" for r in records)

            # Aucun document n'est jamais compté comme acquis avant validation.
            workshops = (
                await client.get(f"{base}/assessments/{assessment_id}/workshops")
            ).json()
            assert workshops[0]["progress_percent"] == 0

            # L'utilisateur peut Valider, Modifier, Supprimer ou Ajouter librement.
            target = records[0]
            validated = await client.patch(
                f"{base}/assessments/{assessment_id}/records/{target['id']}",
                json={"status": "validated"},
            )
            assert validated.json()["status"] == "validated"

            modified = await client.patch(
                f"{base}/assessments/{assessment_id}/records/{records[1]['id']}",
                json={"properties": {**records[1]["properties"], "version": "2.0"}},
            )
            assert modified.json()["properties"]["version"] == "2.0"

            deleted = await client.delete(
                f"{base}/assessments/{assessment_id}/records/{records[2]['id']}"
            )
            assert deleted.status_code == 204

            added = await client.post(
                f"{base}/assessments/{assessment_id}/records",
                json={
                    "workshop_number": 1,
                    "record_type": "reference_document",
                    "label": "Charte informatique",
                    "properties": {"doc_type": "Autre"},
                },
            )
            assert added.status_code == 201

            remaining = (
                await client.get(f"{base}/assessments/{assessment_id}/records")
            ).json()
            assert len(remaining) == 12  # -1 supprimé + 1 ajouté
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_getting_existing_assessment_again_does_not_reseed_documents(
    db_session: AsyncSession,
):
    project = Project(name="Pas de double semis", organization={})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    base = f"/api/projects/{project.id}/ebios"

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            first = (await client.get(f"{base}/assessment")).json()
            second = (await client.get(f"{base}/assessment")).json()
            assert first["id"] == second["id"]

            records = (
                await client.get(f"{base}/assessments/{first['id']}/records")
            ).json()
            assert len(records) == 12
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_cartography_generator_completes_documents_without_duplicating_defaults(
    db_session: AsyncSession,
):
    project = Project(name="Complément cartographie", organization={})
    db_session.add(project)
    await db_session.flush()

    cartography = await cartography_service.ensure_default_cartography(db_session, project)
    version = await cartography_service.get_current_version(db_session, cartography)

    db_session.add(
        UrbanismEntity(
            project_id=project.id,
            cartography_version_id=version.id,
            entity_type="acteur",
            couche="organisation",
            label="Prestataire infogérance réseau",
        )
    )
    await db_session.commit()
    await db_session.refresh(project)

    from app.models.ebios import EbiosAssessment

    assessment = EbiosAssessment(project_id=project.id, cartography_id=cartography.id)
    db_session.add(assessment)
    await db_session.flush()

    from app.services.ebios.assessment_service import _seed_default_reference_documents

    db_session.add_all(_seed_default_reference_documents(assessment.id))
    await db_session.commit()
    await db_session.refresh(assessment)

    created = await generate_workshop1_from_cartography(db_session, assessment.id, project.id)
    document_proposals = [r for r in created if r.record_type == "reference_document"]

    # Le document "Contrats critiques" par défaut existe déjà : la détection
    # cartographie ne le duplique pas, elle ajoute un document distinct.
    labels = {r.label for r in document_proposals}
    assert "Contrats critiques" not in labels
    assert any("Cartographie d'urbanisme" in label for label in labels)
    assert any("Contrats critiques" in label and label != "Contrats critiques" for label in labels)

    all_records = await list_records(db_session, assessment.id, workshop_number=1)
    doc_labels = [r.label for r in all_records if r.record_type == "reference_document"]
    assert doc_labels.count("Contrats critiques") == 1
