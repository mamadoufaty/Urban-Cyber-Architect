"""Isolation des études EBIOS RM — chaque étude (project_id + cartography_id +
study_id) est totalement indépendante : aucune donnée, score ou progression
ne doit fuiter entre deux études, deux cartographies ou deux projets.

Reproduit et corrige le bug rapporté : une nouvelle cartographie affichait à
tort une analyse déjà à 100 % avec les 5 ateliers terminés et des données
(SOC, MFA, ISO 27001, PCA…) provenant d'une étude précédente, car
``get_or_create_assessment`` résolvait « la dernière étude créée pour le
projet » sans jamais tenir compte de la cartographie.
"""

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project
from app.services import cartography_service
from app.services.ebios import assessment_service


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


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _complete_workshop1(client: AsyncClient, base: str, assessment_id: str) -> str:
    stakeholder_id = None
    for record_type, label, props in [
        ("security_scope", "Périmètre", {"business_objectives": "Continuité"}),
        ("stakeholder", "RSSI", {"role": "RSSI"}),
        ("security_baseline", "Pare-feu", {"status": "En place"}),
        ("reference_document", "PSSI", {"doc_type": "PSSI"}),
    ]:
        resp = await client.post(
            f"{base}/assessments/{assessment_id}/records",
            json={"workshop_number": 1, "record_type": record_type, "label": label, "properties": props},
        )
        assert resp.status_code == 201
        if record_type == "stakeholder":
            stakeholder_id = resp.json()["id"]
    return stakeholder_id


# ————————————————————————————————————————————————————————————————
# Initialisation d'une nouvelle étude — toujours vierge
# ————————————————————————————————————————————————————————————————


@pytest.mark.asyncio
async def test_new_assessment_starts_empty_with_only_workshop1_available(
    client: AsyncClient, db_session: AsyncSession
):
    project = Project(name="Nouvelle étude", organization={})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    res = await client.get(f"/api/projects/{project.id}/ebios/assessment")
    assert res.status_code == 200
    assessment = res.json()
    assert assessment["current_workshop"] == 1
    assert assessment["cartography_id"] is not None  # rattachée à la cartographie active

    overview = await client.get(
        f"/api/projects/{project.id}/ebios/assessments/{assessment['id']}/overview"
    )
    assert overview.status_code == 200
    body = overview.json()
    # Le socle documentaire par défaut (12 documents proposés) ne compte pas
    # comme progression tant qu'il n'est pas validé (§ Documents de référence).
    assert body["overall_progress_percent"] == 0
    assert body["record_counts_by_workshop"] == {"1": 12}
    assert body["link_count"] == 0

    statuses = {w["workshop_number"]: w["status"] for w in body["workshops"]}
    progresses = {w["workshop_number"]: w["progress_percent"] for w in body["workshops"]}
    assert statuses == {1: "available", 2: "locked", 3: "locked", 4: "locked", 5: "locked"}
    assert progresses == {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    records = await client.get(
        f"/api/projects/{project.id}/ebios/assessments/{assessment['id']}/records"
    )
    default_documents = records.json()
    assert len(default_documents) == 12
    assert all(r["record_type"] == "reference_document" for r in default_documents)
    assert all(r["status"] == "proposed" for r in default_documents)
    assert all(r["properties"]["source"] == "default_framework" for r in default_documents)


# ————————————————————————————————————————————————————————————————
# Validation séquentielle — chaque atelier dépend de la validation du précédent
# ————————————————————————————————————————————————————————————————


@pytest.mark.asyncio
async def test_full_workflow_unlocks_all_five_workshops_sequentially(
    client: AsyncClient, db_session: AsyncSession
):
    from app.models.entities import UrbanismEntity, UrbanismRelation

    project = Project(name="Workflow complet", organization={})
    db_session.add(project)
    await db_session.flush()
    serveur = UrbanismEntity(
        project_id=project.id, entity_type="serveur", couche="technique", label="Serveur"
    )
    owner = UrbanismEntity(
        project_id=project.id, entity_type="acteur", couche="organisation", label="Responsable SI"
    )
    db_session.add_all([serveur, owner])
    await db_session.flush()
    db_session.add(
        UrbanismRelation(
            project_id=project.id,
            source_id=serveur.id,
            target_id=owner.id,
            relation_type="est_exploité_par",
            category="exploitation",
        )
    )
    await db_session.commit()
    await db_session.refresh(project)

    base = f"/api/projects/{project.id}/ebios"
    assessment_id = (await client.get(f"{base}/assessment")).json()["id"]

    def statuses(workshops):
        return {w["workshop_number"]: w["status"] for w in workshops}

    # Atelier 1 seul disponible au départ.
    workshops = (await client.get(f"{base}/assessments/{assessment_id}/workshops")).json()
    assert statuses(workshops) == {1: "available", 2: "locked", 3: "locked", 4: "locked", 5: "locked"}

    # Validation atelier 1 (tous les éléments renseignés) ⇒ ouverture atelier 2.
    stakeholder_id = await _complete_workshop1(client, base, assessment_id)
    workshops = (await client.get(f"{base}/assessments/{assessment_id}/workshops")).json()
    assert statuses(workshops)[1] == "completed"
    assert statuses(workshops)[2] == "available"
    assert statuses(workshops)[3] == "locked"

    # Validation atelier 2 ⇒ ouverture atelier 3.
    imported = await client.post(f"{base}/assessments/{assessment_id}/workshop2/import-urbanism-assets")
    asset_id = imported.json()["records"][0]["id"]
    for i in range(5):
        await client.post(
            f"{base}/assessments/{assessment_id}/records",
            json={
                "workshop_number": 2,
                "record_type": "risk_source",
                "label": f"Source {i + 1}",
                "properties": {
                    "target_objective": "Objectif",
                    "feared_event": "Événement",
                    "severity": "Critique",
                    "stakeholder_ids": [stakeholder_id],
                    "supporting_asset_ids": [asset_id],
                },
            },
        )
    workshops = (await client.get(f"{base}/assessments/{assessment_id}/workshops")).json()
    assert statuses(workshops)[2] == "completed"
    assert statuses(workshops)[3] == "available"
    assert statuses(workshops)[4] == "locked"

    # Validation atelier 3 ⇒ ouverture atelier 4.
    strategic = await client.post(f"{base}/assessments/{assessment_id}/workshop3/generate-scenarios")
    for scenario in strategic.json()["records"]:
        props = {**scenario["properties"], "workflow_status": "Validé"}
        await client.patch(
            f"{base}/assessments/{assessment_id}/records/{scenario['id']}", json={"properties": props}
        )
    workshops = (await client.get(f"{base}/assessments/{assessment_id}/workshops")).json()
    assert statuses(workshops)[3] == "completed"
    assert statuses(workshops)[4] == "available"
    assert statuses(workshops)[5] == "locked"

    # Validation atelier 4 ⇒ ouverture atelier 5.
    operational = await client.post(
        f"{base}/assessments/{assessment_id}/workshop4/generate-operational-scenarios"
    )
    for op in operational.json()["records"]:
        await client.patch(
            f"{base}/assessments/{assessment_id}/workshop4/scenarios/{op['id']}",
            json={"set_validated": True},
        )
    workshops = (await client.get(f"{base}/assessments/{assessment_id}/workshops")).json()
    assert statuses(workshops)[4] == "completed"
    assert statuses(workshops)[5] == "available"

    # Validation atelier 5 ⇒ étude terminée (100 % global).
    treatments = await client.post(f"{base}/assessments/{assessment_id}/workshop5/generate-treatments")
    for evaluation in treatments.json()["records"]:
        await client.patch(
            f"{base}/assessments/{assessment_id}/workshop5/evaluations/{evaluation['id']}",
            json={"set_validated": True},
        )
    overview = (await client.get(f"{base}/assessments/{assessment_id}/overview")).json()
    assert statuses(overview["workshops"])[5] == "completed"
    assert overview["overall_progress_percent"] == 100


# ————————————————————————————————————————————————————————————————
# Isolation — aucune fuite entre études / cartographies / projets
# ————————————————————————————————————————————————————————————————


@pytest.mark.asyncio
async def test_no_data_leakage_between_two_studies_of_same_cartography(
    client: AsyncClient, db_session: AsyncSession
):
    project = Project(name="Deux études", organization={})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    cartography = await cartography_service.get_active_cartography(db_session, project.id)

    base = f"/api/projects/{project.id}/ebios"
    study_a = (
        await client.post(
            f"{base}/assessments",
            json={"title": "Étude A", "cartography_id": str(cartography.id)},
        )
    ).json()
    study_b = (
        await client.post(
            f"{base}/assessments",
            json={"title": "Étude B", "cartography_id": str(cartography.id)},
        )
    ).json()
    assert study_a["id"] != study_b["id"]
    assert study_a["cartography_id"] == study_b["cartography_id"] == str(cartography.id)

    await client.post(
        f"{base}/assessments/{study_a['id']}/records",
        json={"workshop_number": 1, "record_type": "security_scope", "label": "Périmètre A"},
    )

    records_a = (await client.get(f"{base}/assessments/{study_a['id']}/records")).json()
    records_b = (await client.get(f"{base}/assessments/{study_b['id']}/records")).json()
    # Chaque étude reçoit son propre socle documentaire par défaut (12 docs) —
    # seule l'étude A reçoit en plus le périmètre créé manuellement.
    assert len([r for r in records_a if r["record_type"] == "security_scope"]) == 1
    assert len(records_a) == 13
    assert len(records_b) == 12
    assert all(r["record_type"] == "reference_document" for r in records_b)

    overview_a = (await client.get(f"{base}/assessments/{study_a['id']}/overview")).json()
    overview_b = (await client.get(f"{base}/assessments/{study_b['id']}/overview")).json()
    # 1 section sur 4 remplie en atelier 1 (25 %) => 25/5 ateliers = 5 % global.
    assert overview_a["overall_progress_percent"] == 5
    assert overview_b["overall_progress_percent"] == 0


@pytest.mark.asyncio
async def test_no_data_leakage_between_two_cartographies_of_same_project(
    client: AsyncClient, db_session: AsyncSession
):
    """Régression directe du bug rapporté : une nouvelle cartographie doit
    toujours démarrer une étude EBIOS vierge, jamais celle d'une cartographie
    précédente (même déjà à 100 % avec 5 ateliers terminés)."""
    project = Project(name="Métropolis", organization={})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    base = f"/api/projects/{project.id}/ebios"

    cart_a = await cartography_service.ensure_default_cartography(db_session, project)
    cart_b = await cartography_service.create_cartography(
        db_session, project.id, name="Nouvelle cartographie", type_="libre",
        description=None, author=None,
    )
    assert cart_a.id != cart_b.id

    assessment_a = (
        await client.get(f"{base}/assessment", params={"cartography_id": str(cart_a.id)})
    ).json()
    await _complete_workshop1(client, base, assessment_a["id"])
    overview_a = (await client.get(f"{base}/assessments/{assessment_a['id']}/overview")).json()
    # Atelier 1 complet (100 %) => 100/5 ateliers = 20 % global.
    assert overview_a["overall_progress_percent"] == 20

    # La cartographie B (nouvelle) obtient une étude totalement distincte et vierge.
    assessment_b = (
        await client.get(f"{base}/assessment", params={"cartography_id": str(cart_b.id)})
    ).json()
    assert assessment_b["id"] != assessment_a["id"]
    assert assessment_b["cartography_id"] == str(cart_b.id)

    overview_b = (await client.get(f"{base}/assessments/{assessment_b['id']}/overview")).json()
    assert overview_b["overall_progress_percent"] == 0
    statuses_b = {w["workshop_number"]: w["status"] for w in overview_b["workshops"]}
    assert statuses_b == {1: "available", 2: "locked", 3: "locked", 4: "locked", 5: "locked"}

    records_b = (await client.get(f"{base}/assessments/{assessment_b['id']}/records")).json()
    # Vierge de toute analyse — seul le socle documentaire par défaut existe.
    assert len(records_b) == 12
    assert all(r["record_type"] == "reference_document" for r in records_b)

    # Ré-appeler l'endpoint « courant » pour la cartographie A retrouve bien la
    # même étude — toujours à 25 %, jamais mélangée avec B.
    assessment_a_again = (
        await client.get(f"{base}/assessment", params={"cartography_id": str(cart_a.id)})
    ).json()
    assert assessment_a_again["id"] == assessment_a["id"]
    overview_a_again = (
        await client.get(f"{base}/assessments/{assessment_a['id']}/overview")
    ).json()
    assert overview_a_again["overall_progress_percent"] == 20


@pytest.mark.asyncio
async def test_no_data_leakage_between_two_projects(client: AsyncClient, db_session: AsyncSession):
    project1 = Project(name="Projet 1", organization={})
    project2 = Project(name="Projet 2", organization={})
    db_session.add_all([project1, project2])
    await db_session.commit()
    await db_session.refresh(project1)
    await db_session.refresh(project2)

    assessment1 = (
        await client.get(f"/api/projects/{project1.id}/ebios/assessment")
    ).json()
    assessment2 = (
        await client.get(f"/api/projects/{project2.id}/ebios/assessment")
    ).json()
    assert assessment1["id"] != assessment2["id"]
    assert assessment1["cartography_id"] != assessment2["cartography_id"]

    await _complete_workshop1(
        client, f"/api/projects/{project1.id}/ebios", assessment1["id"]
    )

    overview1 = (
        await client.get(
            f"/api/projects/{project1.id}/ebios/assessments/{assessment1['id']}/overview"
        )
    ).json()
    overview2 = (
        await client.get(
            f"/api/projects/{project2.id}/ebios/assessments/{assessment2['id']}/overview"
        )
    ).json()
    assert overview1["overall_progress_percent"] == 20
    assert overview2["overall_progress_percent"] == 0
    assert overview2["record_counts_by_workshop"] == {"1": 12}


@pytest.mark.asyncio
async def test_backfill_assessment_cartography_ids_is_idempotent_and_scoped(
    db_session: AsyncSession,
):
    """Une étude créée avant l'introduction de ``cartography_id`` (donc NULL)
    est rattachée à la cartographie active de son projet, sans jamais toucher
    aux études déjà correctement rattachées."""
    from app.models.ebios import EbiosAssessment

    project = Project(name="Legacy", organization={})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    cartography = await cartography_service.ensure_default_cartography(db_session, project)

    legacy_assessment = EbiosAssessment(project_id=project.id, cartography_id=None)
    db_session.add(legacy_assessment)
    await db_session.commit()
    await db_session.refresh(legacy_assessment)

    updated = await assessment_service.backfill_assessment_cartography_ids(db_session)
    assert updated == 1

    await db_session.refresh(legacy_assessment)
    assert legacy_assessment.cartography_id == cartography.id

    # Idempotent : un second appel ne modifie plus rien.
    updated_again = await assessment_service.backfill_assessment_cartography_ids(db_session)
    assert updated_again == 0
