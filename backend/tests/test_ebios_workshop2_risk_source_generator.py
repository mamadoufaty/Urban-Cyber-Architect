"""Tests génération automatique Atelier 2 — sources de risque.

Couvre :
- les fonctions pures de proposition (objectif visé, liaison biens
  supports/parties prenantes selon l'archétype de source de risque) ;
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
from app.models.ebios import EbiosAssessment, EbiosRecord
from app.models.entities import Project, UrbanismEntity
from app.services import cartography_service
from app.services.ebios.risk_source_generator import build_risk_source_proposals
from app.services.ebios.workshop2_service import (
    compute_workshop2_progress,
    generate_workshop2_risk_sources,
    is_risk_source_complete,
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


def _entity(entity_type: str, couche: str, label: str) -> UrbanismEntity:
    entity = UrbanismEntity(entity_type=entity_type, couche=couche, label=label)
    entity.id = uuid.uuid4()
    return entity


def _stakeholder(role: str, label: str | None = None) -> EbiosRecord:
    record = EbiosRecord(
        workshop_number=1,
        record_type="stakeholder",
        label=label or role,
        properties={"role": role},
        status="validated",
    )
    record.id = uuid.uuid4()
    return record


def _asset(couche: str, label: str) -> EbiosRecord:
    record = EbiosRecord(
        workshop_number=2,
        record_type="supporting_asset",
        label=label,
        properties={"couche": couche},
        status="imported",
    )
    record.id = uuid.uuid4()
    return record


async def _seed_cartography(db_session: AsyncSession) -> tuple[Project, UrbanismEntity, UrbanismEntity]:
    project = Project(name="Métropolis test W2", organization={})
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

    make("metier", "metier", "Sécurité publique")
    make("processus", "metier", "Gestion des incidents")
    appli = make("ilot_applicatif", "applicatif", "SI Vidéoprotection")
    serveur = make("serveur", "technique", "Serveur SIEM")
    await db_session.commit()
    await db_session.refresh(project)
    return project, appli, serveur


async def _seed_workshop1_and_assets(
    db_session: AsyncSession,
    assessment_id,
    appli: UrbanismEntity,
    serveur: UrbanismEntity,
) -> None:
    """Atelier 1 validé + biens supports synchronisés pour un assessment donné."""
    db_session.add(
        EbiosRecord(
            assessment_id=assessment_id,
            workshop_number=1,
            record_type="security_scope",
            label="Périmètre validé",
            properties={
                "business_objectives": "Sécurité publique",
                "activities": "Gestion des incidents",
            },
            status="validated",
        )
    )
    db_session.add(
        EbiosRecord(
            assessment_id=assessment_id,
            workshop_number=1,
            record_type="stakeholder",
            label="RSSI Métropolis",
            properties={"role": "RSSI"},
            status="validated",
        )
    )
    db_session.add(
        EbiosRecord(
            assessment_id=assessment_id,
            workshop_number=2,
            record_type="supporting_asset",
            label=appli.label,
            properties={"urbanism_entity_id": str(appli.id), "couche": "applicatif"},
            status="imported",
        )
    )
    db_session.add(
        EbiosRecord(
            assessment_id=assessment_id,
            workshop_number=2,
            record_type="supporting_asset",
            label=serveur.label,
            properties={"urbanism_entity_id": str(serveur.id), "couche": "technique"},
            status="imported",
        )
    )
    await db_session.commit()


async def _seed_full_assessment(db_session: AsyncSession) -> tuple[Project, EbiosAssessment]:
    """Cartographie + Atelier 1 validé + biens supports synchronisés."""
    project, appli, serveur = await _seed_cartography(db_session)

    cartography, _version = await cartography_service.resolve_read_version(db_session, project.id)
    assessment = EbiosAssessment(project_id=project.id, cartography_id=cartography.id)
    db_session.add(assessment)
    await db_session.flush()

    await _seed_workshop1_and_assets(db_session, assessment.id, appli, serveur)
    await db_session.refresh(assessment)
    return project, assessment


# ————————————————————————————————————————————————————————————————
# Fonctions pures
# ————————————————————————————————————————————————————————————————


def test_build_risk_source_proposals_covers_expected_archetypes_when_fully_equipped():
    """Cartographie complète (technique + signal prestataire) : les 9
    archétypes EBIOS RM sont proposés."""
    entities = [
        _entity("metier", "metier", "Sécurité publique"),
        _entity("serveur", "technique", "Serveur SIEM"),
        _entity("organisation", "organisation", "Prestataire infogérance"),
    ]
    proposals = build_risk_source_proposals(entities, None, [], [], None, None)
    labels = {p["label"] for p in proposals}
    assert labels == {
        "Cybercriminel",
        "Employé malveillant",
        "Prestataire",
        "Sous-traitant",
        "Concurrent",
        "APT (menace persistante avancée)",
        "Erreur humaine",
        "Défaillance technique",
        "Catastrophe naturelle",
    }
    for proposal in proposals:
        props = proposal["properties"]
        assert props["feared_event"].strip()
        assert props["severity"]
        assert props["generated_from"]["source"] == "cartography"


def test_each_proposal_carries_explainability_fields():
    entities = [
        _entity("metier", "metier", "Sécurité publique"),
        _entity("serveur", "technique", "Serveur SIEM"),
    ]
    proposals = build_risk_source_proposals(entities, None, [], [], None, None)
    for proposal in proposals:
        props = proposal["properties"]
        assert isinstance(props["justification"], list)
        assert len(props["justification"]) >= 1
        assert all(isinstance(b, str) and b.strip() for b in props["justification"])
        assert 0 <= props["confidence_score"] <= 100
        assert props["confidence_label"] in {"Faible", "Moyenne", "Élevée"}


def test_contextual_gating_excludes_technique_and_prestataire_archetypes_when_absent():
    """Sans composant technique ni signal prestataire/contrat, le moteur ne
    doit proposer ni scénario technique, ni « Prestataire »/« Sous-traitant »."""
    entities = [_entity("metier", "metier", "Sécurité publique")]
    proposals = build_risk_source_proposals(entities, None, [], [], None, None)
    labels = {p["label"] for p in proposals}
    assert "Défaillance technique" not in labels
    assert "Catastrophe naturelle" not in labels
    assert "Prestataire" not in labels
    assert "Sous-traitant" not in labels
    assert "Cybercriminel" in labels


def test_contextual_gating_includes_prestataire_when_contract_entity_detected():
    entities = [
        _entity("metier", "metier", "Sécurité publique"),
        _entity("organisation", "organisation", "Prestataire infogérance réseau"),
    ]
    proposals = build_risk_source_proposals(entities, None, [], [], None, None)
    labels = {p["label"] for p in proposals}
    assert "Prestataire" in labels
    assert "Sous-traitant" in labels


def test_contextual_gating_includes_prestataire_when_stakeholder_role_present():
    entities = [_entity("metier", "metier", "Sécurité publique")]
    stakeholders = [_stakeholder("Prestataire")]
    proposals = build_risk_source_proposals(entities, None, stakeholders, [], None, None)
    labels = {p["label"] for p in proposals}
    assert "Prestataire" in labels


def test_contextual_gating_includes_technical_archetypes_when_technique_present():
    entities = [
        _entity("metier", "metier", "Sécurité publique"),
        _entity("serveur", "technique", "Serveur SIEM"),
    ]
    proposals = build_risk_source_proposals(entities, None, [], [], None, None)
    labels = {p["label"] for p in proposals}
    assert "Défaillance technique" in labels
    assert "Catastrophe naturelle" in labels


def test_justification_mentions_ot_when_ot_keywords_detected():
    entities = [
        _entity("metier", "metier", "Sécurité publique"),
        _entity("serveur", "technique", "Automate SCADA usine"),
    ]
    proposals = build_risk_source_proposals(entities, None, [], [], None, None)
    cybercriminel = next(p for p in proposals if p["label"] == "Cybercriminel")
    assert any("OT" in bullet for bullet in cybercriminel["properties"]["justification"])


def test_target_objective_prefers_validated_workshop1_scope():
    scope = EbiosRecord(
        record_type="security_scope",
        properties={"business_objectives": "Sécurité publique", "activities": "Patrouilles"},
    )
    proposals = build_risk_source_proposals([], scope, [], [], None, None)
    for proposal in proposals:
        assert "Sécurité publique" in proposal["properties"]["target_objective"]
        assert "Patrouilles" in proposal["properties"]["target_objective"]


def test_target_objective_falls_back_to_cartography_entities_without_scope():
    entities = [_entity("metier", "metier", "Sécurité publique")]
    proposals = build_risk_source_proposals(entities, None, [], [], None, None)
    for proposal in proposals:
        assert "Sécurité publique" in proposal["properties"]["target_objective"]


def test_asset_linking_prefers_matching_couche_and_falls_back_to_all():
    # Un composant technique doit être présent dans la cartographie pour que
    # l'archétype « Défaillance technique » reste applicable (§ contextuel).
    entities = [_entity("serveur", "technique", "Serveur applicatif")]
    assets = [_asset("technique", "Serveur SIEM"), _asset("organisation", "RH")]
    proposals = build_risk_source_proposals(entities, None, [], assets, None, None)
    by_label = {p["label"]: p for p in proposals}

    # « Défaillance technique » ne cible que les biens supports techniques.
    technical = by_label["Défaillance technique"]["properties"]["supporting_asset_ids"]
    assert technical == [str(assets[0].id)]

    # « Concurrent » cible métier/applicatif : aucun bien support ne correspond
    # => repli sur l'ensemble des biens supports disponibles (jamais vide).
    concurrent = by_label["Concurrent"]["properties"]["supporting_asset_ids"]
    assert set(concurrent) == {str(a.id) for a in assets}


def test_stakeholder_linking_prefers_matching_role_and_falls_back_to_all():
    stakeholders = [_stakeholder("Prestataire"), _stakeholder("RSSI")]
    proposals = build_risk_source_proposals([], None, stakeholders, [], None, None)
    by_label = {p["label"]: p for p in proposals}

    prestataire_ids = by_label["Prestataire"]["properties"]["stakeholder_ids"]
    assert prestataire_ids == [str(stakeholders[0].id)]

    # « Cybercriminel » n'a pas de rôle préféré => tous les interlocuteurs.
    generic_ids = by_label["Cybercriminel"]["properties"]["stakeholder_ids"]
    assert set(generic_ids) == {str(s.id) for s in stakeholders}


def test_is_risk_source_complete_excludes_proposed_and_rejected():
    record = EbiosRecord(
        record_type="risk_source",
        label="Cybercriminel",
        properties={
            "target_objective": "X",
            "feared_event": "Y",
            "severity": "Critique",
            "stakeholder_ids": ["a"],
            "supporting_asset_ids": ["b"],
        },
        status="proposed",
    )
    assert is_risk_source_complete(record) is False
    record.status = "rejected"
    assert is_risk_source_complete(record) is False
    record.status = "validated"
    assert is_risk_source_complete(record) is True
    record.status = "draft"
    assert is_risk_source_complete(record) is True


# ————————————————————————————————————————————————————————————————
# Orchestration
# ————————————————————————————————————————————————————————————————


@pytest.mark.asyncio
async def test_generate_creates_proposed_risk_sources_with_traceability(
    db_session: AsyncSession,
):
    project, assessment = await _seed_full_assessment(db_session)

    created = await generate_workshop2_risk_sources(db_session, assessment.id, project.id)
    # La cartographie de test (technique présent, aucun signal prestataire) ne
    # justifie pas les archétypes « Prestataire »/« Sous-traitant » (7 = 9 - 2).
    assert len(created) == 7
    for record in created:
        assert record.status == "proposed"
        assert record.properties["generated_from"]["source"] == "cartography"
        assert record.properties["stakeholder_ids"]
        assert record.properties["supporting_asset_ids"]

    # Une proposition non validée ne doit jamais faire progresser l'atelier.
    assert compute_workshop2_progress(created) == 0


@pytest.mark.asyncio
async def test_generate_is_idempotent_without_regenerate(db_session: AsyncSession):
    project, assessment = await _seed_full_assessment(db_session)

    first = await generate_workshop2_risk_sources(db_session, assessment.id, project.id)
    second = await generate_workshop2_risk_sources(db_session, assessment.id, project.id)
    assert first
    assert second == []


@pytest.mark.asyncio
async def test_regenerate_preserves_validated_risk_sources(db_session: AsyncSession):
    project, assessment = await _seed_full_assessment(db_session)

    created = await generate_workshop2_risk_sources(db_session, assessment.id, project.id)
    cybercriminel = next(r for r in created if r.label == "Cybercriminel")
    cybercriminel.status = "validated"
    await db_session.commit()

    regenerated = await generate_workshop2_risk_sources(
        db_session, assessment.id, project.id, regenerate=True
    )
    # Le libellé déjà présent (validé) n'est jamais recréé ni supprimé.
    assert "Cybercriminel" not in {r.label for r in regenerated}
    await db_session.refresh(cybercriminel)
    assert cybercriminel.status == "validated"


@pytest.mark.asyncio
async def test_generate_returns_empty_without_cartography_entities(db_session: AsyncSession):
    project = Project(name="Empty W2 project", organization={})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    assessment = EbiosAssessment(project_id=project.id)
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)

    created = await generate_workshop2_risk_sources(db_session, assessment.id, project.id)
    assert created == []


# ————————————————————————————————————————————————————————————————
# API — génération, validation, rejet
# ————————————————————————————————————————————————————————————————


@pytest.mark.asyncio
async def test_api_generate_then_validate_unlocks_progress(db_session: AsyncSession):
    project, appli, serveur = await _seed_cartography(db_session)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    ebios_base = f"/api/projects/{project.id}/ebios"

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            assessment_id = (await client.get(f"{ebios_base}/assessment")).json()["id"]
            base = f"{ebios_base}/assessments/{assessment_id}"
            await _seed_workshop1_and_assets(
                db_session, uuid.UUID(assessment_id), appli, serveur
            )

            endpoint = f"{base}/workshop2/generate-risk-sources"

            first = await client.post(endpoint)
            assert first.status_code == 200
            body = first.json()
            assert body["generated_count"] == 7
            for record in body["records"]:
                assert record["status"] == "proposed"

            # Les propositions non validées ne font pas progresser l'atelier 2.
            workshops = (await client.get(f"{base}/workshops")).json()
            workshop2 = next(w for w in workshops if w["workshop_number"] == 2)
            workshop3 = next(w for w in workshops if w["workshop_number"] == 3)
            assert workshop2["progress_percent"] == 0
            assert workshop3["status"] == "locked"

            # Cliquer une seconde fois est sans effet (idempotent).
            second = await client.post(endpoint)
            assert second.json()["generated_count"] == 0

            risk_source_id = body["records"][0]["id"]
            validated = await client.patch(
                f"{base}/records/{risk_source_id}",
                json={"status": "validated"},
            )
            assert validated.status_code == 200
            assert validated.json()["status"] == "validated"

            workshops = (await client.get(f"{base}/workshops")).json()
            workshop2 = next(w for w in workshops if w["workshop_number"] == 2)
            assert workshop2["progress_percent"] == 25

            rejected = await client.patch(
                f"{base}/records/{risk_source_id}",
                json={"status": "rejected"},
            )
            assert rejected.status_code == 200

            workshops = (await client.get(f"{base}/workshops")).json()
            workshop2 = next(w for w in workshops if w["workshop_number"] == 2)
            assert workshop2["progress_percent"] == 0
    finally:
        app.dependency_overrides.clear()
