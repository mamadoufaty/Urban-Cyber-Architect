"""Tests génération automatique Atelier 1 depuis la cartographie active.

Couvre :
- les fonctions pures de proposition (périmètre, parties prenantes, socle) ;
- l'orchestration (idempotence, régénération, traçabilité) ;
- le fait qu'une proposition non validée ne fait jamais progresser l'atelier ;
- le cycle Valider / Rejeter / Restaurer via l'API existante (PATCH record).
"""

import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project, UrbanismEntity, UrbanismRelation
from app.services import cartography_service
from app.services.ebios.workshop1_cartography_generator import (
    build_baseline_proposals,
    build_fallback_stakeholder_role_proposals,
    build_scope_proposal,
    build_stakeholder_proposals,
)
from app.services.ebios.workshop1_service import (
    compute_workshop1_progress,
    generate_workshop1_from_cartography,
)


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


async def _seed_cartography(db_session: AsyncSession) -> tuple[Project, list[UrbanismEntity]]:
    project = Project(name="Métropolis test", organization={})
    db_session.add(project)
    await db_session.flush()

    cartography = await cartography_service.ensure_default_cartography(db_session, project)
    version = await cartography_service.get_current_version(db_session, cartography)

    def make(entity_type: str, couche: str, label: str) -> UrbanismEntity:
        entity = UrbanismEntity(
            project_id=project.id,
            cartography_version_id=version.id,
            entity_type=entity_type,
            couche=couche,
            label=label,
        )
        db_session.add(entity)
        return entity

    metier = make("metier", "metier", "Sécurité publique")
    processus = make("processus", "metier", "Gestion des incidents")
    appli = make("ilot_applicatif", "applicatif", "SI Vidéoprotection")
    serveur = make("serveur", "technique", "Serveur SIEM")
    site = make("site", "technique", "Datacenter métropole")
    organisation = make("organisation", "organisation", "DSI Métropolis")
    acteur = make("acteur", "organisation", "RSSI Métropolis")
    await db_session.flush()

    db_session.add(
        UrbanismRelation(
            project_id=project.id,
            cartography_version_id=version.id,
            source_id=acteur.id,
            target_id=organisation.id,
            relation_type="appartient à",
            category="organisation",
        )
    )
    await db_session.commit()
    await db_session.refresh(project)
    return project, [metier, processus, appli, serveur, site, organisation, acteur]


# ————————————————————————————————————————————————————————————————
# Fonctions pures
# ————————————————————————————————————————————————————————————————


def test_build_scope_proposal_uses_business_and_technical_entities():
    entities = [
        UrbanismEntity(entity_type="metier", couche="metier", label="Sécurité publique"),
        UrbanismEntity(entity_type="ilot_applicatif", couche="applicatif", label="SI Vidéo"),
    ]
    for e in entities:
        e.id = uuid.uuid4()
    proposal = build_scope_proposal(entities, None, None)
    assert proposal is not None
    assert "Sécurité publique" in proposal["properties"]["business_objectives"]
    assert "SI Vidéo" in proposal["properties"]["applications"]
    assert proposal["properties"]["generated_from"]["source"] == "cartography"


def test_build_scope_proposal_returns_none_when_no_relevant_entity():
    entities = [UrbanismEntity(entity_type="reseau", couche="technique", label="LAN")]
    assert build_scope_proposal(entities, None, None) is None


def test_build_stakeholder_proposals_resolves_role_and_organization():
    import uuid

    org = UrbanismEntity(entity_type="organisation", couche="organisation", label="DSI")
    org.id = uuid.uuid4()
    acteur = UrbanismEntity(entity_type="acteur", couche="organisation", label="RSSI Dupont")
    acteur.id = uuid.uuid4()
    rel = UrbanismRelation(source_id=acteur.id, target_id=org.id, relation_type="appartient à")

    proposals = build_stakeholder_proposals([org, acteur], [rel], None, None)
    # Un acteur nommé ET l'organisation elle-même sont proposés comme parties
    # prenantes (une organisation ne doit jamais rester absente de la liste).
    assert len(proposals) == 2
    by_label = {p["label"]: p for p in proposals}
    assert by_label["RSSI Dupont"]["properties"]["role"] == "RSSI"
    assert by_label["RSSI Dupont"]["properties"]["organization"] == "DSI"
    assert by_label["DSI"]["properties"]["role"] == "DSI"
    assert by_label["DSI"]["properties"]["organization"] == "DSI"


def test_build_stakeholder_proposals_empty_without_acteur_or_organisation():
    entities = [
        UrbanismEntity(entity_type="serveur", couche="technique", label="Serveur A"),
    ]
    assert build_stakeholder_proposals(entities, [], None, None) == []


def test_fallback_role_proposals_cover_present_domains_only():
    import uuid

    entities = [
        UrbanismEntity(entity_type="serveur", couche="technique", label="Serveur SIEM"),
        UrbanismEntity(entity_type="ilot_applicatif", couche="applicatif", label="SI Vidéo"),
    ]
    for e in entities:
        e.id = uuid.uuid4()

    proposals = build_fallback_stakeholder_role_proposals(entities, None, None)
    roles = {p["label"] for p in proposals}
    assert "Direction générale" in roles
    assert "DSI" in roles
    assert "RSSI" in roles
    assert "Responsable application" in roles
    assert "Responsable technique" not in roles or "poste_travail" not in {
        e.entity_type for e in entities
    }
    # Aucun élément OT/industriel détecté => pas de rôle "Responsable OT".
    assert "Responsable OT" not in roles
    for proposal in proposals:
        assert proposal["properties"]["role"] == proposal["label"]
        assert "Rôle organisationnel générique" in proposal["properties"]["responsibility"]


def test_fallback_role_proposals_detect_ot_keywords():
    import uuid

    entity = UrbanismEntity(
        entity_type="serveur", couche="technique", label="Automate SCADA usine"
    )
    entity.id = uuid.uuid4()
    proposals = build_fallback_stakeholder_role_proposals([entity], None, None)
    roles = {p["label"] for p in proposals}
    assert "Responsable OT" in roles


def test_guess_role_does_not_false_positive_on_societe():
    from app.services.ebios.workshop1_cartography_generator import _guess_role

    assert _guess_role("Société Générale Métropolis") == "Autre"


def test_build_baseline_proposals_groups_by_domain():
    entities = [
        UrbanismEntity(entity_type="serveur", couche="technique", label="Serveur A"),
        UrbanismEntity(entity_type="reseau", couche="technique", label="LAN"),
    ]
    proposals = build_baseline_proposals(entities, None, None)
    domains = {p["properties"]["domain"] for p in proposals}
    assert "Sécurité des serveurs et de l'hébergement" in domains
    assert "Sécurité réseau" in domains
    for p in proposals:
        assert p["properties"]["status"] == "À vérifier"


# ————————————————————————————————————————————————————————————————
# Orchestration
# ————————————————————————————————————————————————————————————————


@pytest.mark.asyncio
async def test_generate_creates_proposed_records_with_traceability(db_session: AsyncSession):
    project, entities = await _seed_cartography(db_session)

    from app.models.ebios import EbiosAssessment

    assessment = EbiosAssessment(project_id=project.id)
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    created = await generate_workshop1_from_cartography(db_session, assessment.id, project.id)
    assert created
    record_types = {r.record_type for r in created}
    assert record_types == {
        "security_scope",
        "stakeholder",
        "security_baseline",
        "reference_document",
    }
    for record in created:
        assert record.status == "proposed"
        assert record.properties["generated_from"]["source"] == "cartography"

    # Une proposition non validée ne doit jamais faire progresser l'atelier.
    assert compute_workshop1_progress(created) == 0


@pytest.mark.asyncio
async def test_generate_is_idempotent_without_regenerate(db_session: AsyncSession):
    project, _entities = await _seed_cartography(db_session)

    from app.models.ebios import EbiosAssessment

    assessment = EbiosAssessment(project_id=project.id)
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    first = await generate_workshop1_from_cartography(db_session, assessment.id, project.id)
    second = await generate_workshop1_from_cartography(db_session, assessment.id, project.id)
    assert first
    assert second == []


@pytest.mark.asyncio
async def test_generate_skips_scope_when_manual_scope_exists(db_session: AsyncSession):
    project, _entities = await _seed_cartography(db_session)

    from app.models.ebios import EbiosAssessment, EbiosRecord

    assessment = EbiosAssessment(project_id=project.id)
    db_session.add(assessment)
    await db_session.flush()
    db_session.add(
        EbiosRecord(
            assessment_id=assessment.id,
            workshop_number=1,
            record_type="security_scope",
            label="Périmètre saisi manuellement",
            properties={},
            status="draft",
        )
    )
    await db_session.commit()

    created = await generate_workshop1_from_cartography(db_session, assessment.id, project.id)
    assert "security_scope" not in {r.record_type for r in created}


@pytest.mark.asyncio
async def test_generate_returns_empty_without_cartography_entities(db_session: AsyncSession):
    project = Project(name="Empty project", organization={})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    from app.models.ebios import EbiosAssessment

    assessment = EbiosAssessment(project_id=project.id)
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    created = await generate_workshop1_from_cartography(db_session, assessment.id, project.id)
    assert created == []


@pytest.mark.asyncio
async def test_generate_never_leaves_stakeholders_empty_with_organisations_only(
    db_session: AsyncSession,
):
    """Reproduit le cas rapporté (cartographie « Infrastructure_Telco ») : des
    organisations existent mais aucun acteur individuel n'est modélisé — la
    section Parties prenantes ne doit jamais rester vide."""
    project = Project(name="Infrastructure_Telco", organization={})
    db_session.add(project)
    await db_session.flush()

    cartography = await cartography_service.ensure_default_cartography(db_session, project)
    version = await cartography_service.get_current_version(db_session, cartography)

    db_session.add_all(
        [
            UrbanismEntity(
                project_id=project.id,
                cartography_version_id=version.id,
                entity_type="organisation",
                couche="organisation",
                label="Direction des Systèmes d'Information",
            ),
            UrbanismEntity(
                project_id=project.id,
                cartography_version_id=version.id,
                entity_type="organisation",
                couche="organisation",
                label="Direction de l'Exploitation Réseau",
            ),
            UrbanismEntity(
                project_id=project.id,
                cartography_version_id=version.id,
                entity_type="serveur",
                couche="technique",
                label="Cœur de réseau",
            ),
        ]
    )
    await db_session.commit()
    await db_session.refresh(project)

    from app.models.ebios import EbiosAssessment

    assessment = EbiosAssessment(project_id=project.id, cartography_id=cartography.id)
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    created = await generate_workshop1_from_cartography(db_session, assessment.id, project.id)
    stakeholders = [r for r in created if r.record_type == "stakeholder"]
    assert len(stakeholders) == 2
    labels = {s.label for s in stakeholders}
    assert "Direction des Systèmes d'Information" in labels
    assert "Direction de l'Exploitation Réseau" in labels
    for s in stakeholders:
        assert s.status == "proposed"
        assert s.properties["generated_from"]["source"] == "cartography"


@pytest.mark.asyncio
async def test_generate_proposes_generic_roles_when_no_actors_or_organisations(
    db_session: AsyncSession,
):
    """Cartographie purement technique/applicative (aucun acteur, aucune
    organisation) : le moteur propose des rôles organisationnels génériques."""
    project = Project(name="SI sans acteurs", organization={})
    db_session.add(project)
    await db_session.flush()

    cartography = await cartography_service.ensure_default_cartography(db_session, project)
    version = await cartography_service.get_current_version(db_session, cartography)

    db_session.add_all(
        [
            UrbanismEntity(
                project_id=project.id,
                cartography_version_id=version.id,
                entity_type="ilot_applicatif",
                couche="applicatif",
                label="SI Facturation",
            ),
            UrbanismEntity(
                project_id=project.id,
                cartography_version_id=version.id,
                entity_type="serveur",
                couche="technique",
                label="Serveur de production",
            ),
        ]
    )
    await db_session.commit()
    await db_session.refresh(project)

    from app.models.ebios import EbiosAssessment

    assessment = EbiosAssessment(project_id=project.id, cartography_id=cartography.id)
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    created = await generate_workshop1_from_cartography(db_session, assessment.id, project.id)
    stakeholders = [r for r in created if r.record_type == "stakeholder"]
    assert stakeholders
    labels = {s.label for s in stakeholders}
    assert {"Direction générale", "DSI", "RSSI"}.issubset(labels)
    for s in stakeholders:
        assert s.status == "proposed"
        assert s.properties["role"] == s.label


# ————————————————————————————————————————————————————————————————
# API — génération, validation, rejet
# ————————————————————————————————————————————————————————————————


@pytest.mark.asyncio
async def test_api_generate_then_validate_unlocks_progress(db_session: AsyncSession):
    project, _entities = await _seed_cartography(db_session)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    base = f"/api/projects/{project.id}/ebios"

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            assessment_id = (await client.get(f"{base}/assessment")).json()["id"]
            endpoint = f"{base}/assessments/{assessment_id}/workshop1/generate-from-cartography"

            first = await client.post(endpoint)
            assert first.status_code == 200
            body = first.json()
            assert body["generated_count"] > 0
            for record in body["records"]:
                assert record["status"] == "proposed"

            # Les propositions non validées ne font pas progresser l'atelier 1.
            workshops = (
                await client.get(f"{base}/assessments/{assessment_id}/workshops")
            ).json()
            assert workshops[0]["progress_percent"] == 0
            assert workshops[1]["status"] == "locked"

            # Cliquer une seconde fois est sans effet (idempotent).
            second = await client.post(endpoint)
            assert second.json()["generated_count"] == 0

            scope_id = next(
                r["id"] for r in body["records"] if r["record_type"] == "security_scope"
            )
            validated = await client.patch(
                f"{base}/assessments/{assessment_id}/records/{scope_id}",
                json={"status": "validated"},
            )
            assert validated.status_code == 200
            assert validated.json()["status"] == "validated"

            workshops = (
                await client.get(f"{base}/assessments/{assessment_id}/workshops")
            ).json()
            assert workshops[0]["progress_percent"] == 25

            rejected = await client.patch(
                f"{base}/assessments/{assessment_id}/records/{scope_id}",
                json={"status": "rejected"},
            )
            assert rejected.status_code == 200

            workshops = (
                await client.get(f"{base}/assessments/{assessment_id}/workshops")
            ).json()
            assert workshops[0]["progress_percent"] == 0
    finally:
        app.dependency_overrides.clear()
