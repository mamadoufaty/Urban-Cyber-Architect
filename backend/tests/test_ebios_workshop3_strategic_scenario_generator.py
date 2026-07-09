"""Tests génération automatique Atelier 3 — scénarios stratégiques.

Couvre :
- la fonction pure de proposition (motivation, objectif stratégique, bien
  essentiel ciblé, justification IA, confiance IA, traçabilité) ;
- l'orchestration (n'exploite que l'Atelier 1 et l'Atelier 2 *validés*,
  idempotence, régénération sans écraser les scénarios déjà traités) ;
- le fait qu'une proposition non validée ne fait jamais progresser l'atelier,
  et qu'un scénario rejeté ne bloque jamais la progression ;
- le cycle Valider / Rejeter / Restaurer via l'API existante (PATCH record)
  et le déverrouillage de l'Atelier 4.
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
from app.services.ebios.strategic_scenario_generator import generate_strategic_scenario
from app.services.ebios.workshop3_service import (
    compute_workshop3_progress,
    generate_strategic_scenarios,
    is_scenario_validated,
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


def _risk_source(label: str, *, stakeholder_ids=None, asset_ids=None, severity="Critique") -> EbiosRecord:
    record = EbiosRecord(
        workshop_number=2,
        record_type="risk_source",
        label=label,
        properties={
            "target_objective": "Sécurité publique ; Gestion des incidents",
            "feared_event": "Interruption du service public",
            "severity": severity,
            "stakeholder_ids": stakeholder_ids or [],
            "supporting_asset_ids": asset_ids or [],
            "confidence_score": 70,
        },
        status="validated",
    )
    record.id = uuid.uuid4()
    return record


def _stakeholder(label: str) -> EbiosRecord:
    record = EbiosRecord(workshop_number=1, record_type="stakeholder", label=label, properties={})
    record.id = uuid.uuid4()
    return record


def _asset(label: str) -> EbiosRecord:
    record = EbiosRecord(workshop_number=2, record_type="supporting_asset", label=label, properties={})
    record.id = uuid.uuid4()
    return record


# ————————————————————————————————————————————————————————————————
# Fonction pure
# ————————————————————————————————————————————————————————————————


def test_generate_strategic_scenario_maps_known_motivation():
    source = _risk_source("Cybercriminel")
    result = generate_strategic_scenario(source, [], [])
    assert result["motivation"] == "Gain financier"


def test_generate_strategic_scenario_falls_back_to_default_motivation():
    source = _risk_source("Source inconnue")
    result = generate_strategic_scenario(source, [], [])
    assert result["motivation"] == "Déstabilisation"


def test_generate_strategic_scenario_targeted_essential_asset_from_first_objective_segment():
    source = _risk_source("Cybercriminel")
    result = generate_strategic_scenario(source, [], [])
    assert result["targeted_essential_asset"] == "Sécurité publique"
    assert result["strategic_objective"] == "Sécurité publique ; Gestion des incidents"


def test_generate_strategic_scenario_carries_explainability_and_traceability():
    stakeholder = _stakeholder("RSSI")
    asset = _asset("SI Vidéoprotection")
    source = _risk_source(
        "Erreur humaine", stakeholder_ids=[str(stakeholder.id)], asset_ids=[str(asset.id)]
    )
    cartography_id = uuid.uuid4()
    version_id = uuid.uuid4()

    result = generate_strategic_scenario(
        source,
        [stakeholder],
        [asset],
        cartography_id=cartography_id,
        cartography_version_id=version_id,
    )

    assert result["motivation"] == "Erreur humaine"
    assert isinstance(result["justification"], list)
    assert len(result["justification"]) >= 1
    assert all(isinstance(b, str) and b.strip() for b in result["justification"])
    assert 0 <= result["confidence_score"] <= 100
    assert result["confidence_label"] in {"Faible", "Moyenne", "Élevée"}
    assert result["stakeholder_labels"] == ["RSSI"]
    assert result["supporting_asset_labels"] == ["SI Vidéoprotection"]
    assert result["generated_from"] == {
        "source": "cartography",
        "cartography_id": str(cartography_id),
        "cartography_version_id": str(version_id),
        "risk_source_id": str(source.id),
    }


def test_compute_workshop3_progress_excludes_rejected_from_denominator():
    class R:
        record_type = "strategic_scenario"

        def __init__(self, status, workflow_status):
            self.status = status
            self.properties = {"workflow_status": workflow_status}

    validated = R("validated", "Validé")
    proposed = R("proposed", "Proposé automatiquement")
    rejected = R("rejected", "Proposé automatiquement")

    # Un scénario rejeté ne compte ni au numérateur ni au dénominateur.
    assert compute_workshop3_progress([validated, rejected]) == 100
    assert compute_workshop3_progress([validated, proposed, rejected]) == 50
    assert is_scenario_validated(validated)
    assert not is_scenario_validated(rejected)


# ————————————————————————————————————————————————————————————————
# Orchestration
# ————————————————————————————————————————————————————————————————


async def _seed_cartography(db_session: AsyncSession) -> Project:
    project = Project(name="Métropolis test W3", organization={})
    db_session.add(project)
    await db_session.flush()
    await cartography_service.ensure_default_cartography(db_session, project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


async def _seed_assessment(db_session: AsyncSession, project: Project) -> EbiosAssessment:
    cartography, _version = await cartography_service.resolve_read_version(db_session, project.id)
    assessment = EbiosAssessment(project_id=project.id, cartography_id=cartography.id)
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)
    return assessment


@pytest.mark.asyncio
async def test_generate_uses_only_validated_workshop1_and_workshop2_data(db_session: AsyncSession):
    project = await _seed_cartography(db_session)
    assessment = await _seed_assessment(db_session, project)

    validated_stakeholder = EbiosRecord(
        assessment_id=assessment.id,
        workshop_number=1,
        record_type="stakeholder",
        label="RSSI validé",
        properties={},
        status="validated",
    )
    proposed_stakeholder = EbiosRecord(
        assessment_id=assessment.id,
        workshop_number=1,
        record_type="stakeholder",
        label="Rôle proposé non validé",
        properties={},
        status="proposed",
    )
    db_session.add_all([validated_stakeholder, proposed_stakeholder])
    await db_session.flush()

    asset = EbiosRecord(
        assessment_id=assessment.id,
        workshop_number=2,
        record_type="supporting_asset",
        label="SI Vidéoprotection",
        properties={},
        status="imported",
    )
    db_session.add(asset)
    await db_session.flush()

    risk_source = EbiosRecord(
        assessment_id=assessment.id,
        workshop_number=2,
        record_type="risk_source",
        label="Cybercriminel",
        properties={
            "target_objective": "Sécurité publique ; Gestion des incidents",
            "feared_event": "Interruption du service public",
            "severity": "Critique",
            "stakeholder_ids": [str(validated_stakeholder.id), str(proposed_stakeholder.id)],
            "supporting_asset_ids": [str(asset.id)],
        },
        status="validated",
    )
    db_session.add(risk_source)
    await db_session.commit()

    created = await generate_strategic_scenarios(db_session, assessment.id, project.id)
    assert len(created) == 1
    scenario = created[0]
    assert scenario.status == "proposed"
    assert scenario.properties["generated_from"]["source"] == "cartography"
    assert scenario.properties["motivation"] == "Gain financier"
    assert scenario.properties["targeted_essential_asset"] == "Sécurité publique"
    # Seule la partie prenante validée en Atelier 1 doit être reprise.
    assert scenario.properties["stakeholder_labels"] == ["RSSI validé"]

    # Une proposition non validée ne fait jamais progresser l'atelier.
    assert compute_workshop3_progress(created) == 0


@pytest.mark.asyncio
async def test_generate_is_idempotent_without_regenerate(db_session: AsyncSession):
    project = await _seed_cartography(db_session)
    assessment = await _seed_assessment(db_session, project)

    stakeholder = EbiosRecord(
        assessment_id=assessment.id,
        workshop_number=1,
        record_type="stakeholder",
        label="RSSI",
        properties={},
        status="validated",
    )
    asset = EbiosRecord(
        assessment_id=assessment.id,
        workshop_number=2,
        record_type="supporting_asset",
        label="SI Vidéoprotection",
        properties={},
        status="imported",
    )
    db_session.add_all([stakeholder, asset])
    await db_session.flush()

    db_session.add(
        EbiosRecord(
            assessment_id=assessment.id,
            workshop_number=2,
            record_type="risk_source",
            label="Cybercriminel",
            properties={
                "target_objective": "Sécurité publique",
                "feared_event": "Interruption du service",
                "severity": "Critique",
                "stakeholder_ids": [str(stakeholder.id)],
                "supporting_asset_ids": [str(asset.id)],
            },
            status="validated",
        )
    )
    await db_session.commit()

    first = await generate_strategic_scenarios(db_session, assessment.id, project.id)
    second = await generate_strategic_scenarios(db_session, assessment.id, project.id)
    assert len(first) == 1
    assert second == []


@pytest.mark.asyncio
async def test_regenerate_preserves_validated_and_rejected_scenarios(db_session: AsyncSession):
    project = await _seed_cartography(db_session)
    assessment = await _seed_assessment(db_session, project)

    stakeholder = EbiosRecord(
        assessment_id=assessment.id,
        workshop_number=1,
        record_type="stakeholder",
        label="RSSI",
        properties={},
        status="validated",
    )
    asset = EbiosRecord(
        assessment_id=assessment.id,
        workshop_number=2,
        record_type="supporting_asset",
        label="SI Vidéoprotection",
        properties={},
        status="imported",
    )
    db_session.add_all([stakeholder, asset])
    await db_session.flush()

    db_session.add_all(
        [
            EbiosRecord(
                assessment_id=assessment.id,
                workshop_number=2,
                record_type="risk_source",
                label="Cybercriminel",
                properties={
                    "target_objective": "Sécurité publique",
                    "feared_event": "Interruption du service",
                    "severity": "Critique",
                    "stakeholder_ids": [str(stakeholder.id)],
                    "supporting_asset_ids": [str(asset.id)],
                },
                status="validated",
            ),
            EbiosRecord(
                assessment_id=assessment.id,
                workshop_number=2,
                record_type="risk_source",
                label="Erreur humaine",
                properties={
                    "target_objective": "Sécurité publique",
                    "feared_event": "Fuite de données",
                    "severity": "Élevée",
                    "stakeholder_ids": [str(stakeholder.id)],
                    "supporting_asset_ids": [str(asset.id)],
                },
                status="validated",
            ),
        ]
    )
    await db_session.commit()

    created = await generate_strategic_scenarios(db_session, assessment.id, project.id)
    assert len(created) == 2
    validated_scenario = next(r for r in created if r.label.endswith("Cybercriminel"))
    validated_scenario.status = "validated"
    await db_session.commit()

    regenerated = await generate_strategic_scenarios(
        db_session, assessment.id, project.id, regenerate=True
    )
    # Le scénario déjà validé n'est jamais recréé ni supprimé par la régénération.
    assert "Cybercriminel" not in {r.label.split("— ")[-1] for r in regenerated}
    await db_session.refresh(validated_scenario)
    assert validated_scenario.status == "validated"


# ————————————————————————————————————————————————————————————————
# API — génération, validation, rejet, déverrouillage Atelier 4
# ————————————————————————————————————————————————————————————————


@pytest.mark.asyncio
async def test_api_generate_then_validate_unlocks_workshop4(db_session: AsyncSession):
    project = await _seed_cartography(db_session)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    ebios_base = f"/api/projects/{project.id}/ebios"

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            assessment_id = (await client.get(f"{ebios_base}/assessment")).json()["id"]
            base = f"{ebios_base}/assessments/{assessment_id}"

            await client.post(
                f"{base}/records",
                json={
                    "workshop_number": 1,
                    "record_type": "stakeholder",
                    "label": "RSSI",
                    "properties": {},
                },
            )
            stakeholder_records = await client.get(f"{base}/records?workshop_number=1")
            stakeholder_id = stakeholder_records.json()[0]["id"]
            await client.patch(
                f"{base}/records/{stakeholder_id}", json={"status": "validated"}
            )

            asset_resp = await client.post(
                f"{base}/records",
                json={
                    "workshop_number": 2,
                    "record_type": "supporting_asset",
                    "label": "SI Vidéoprotection",
                    "properties": {},
                },
            )
            asset_id = asset_resp.json()["id"]

            await client.post(
                f"{base}/records",
                json={
                    "workshop_number": 2,
                    "record_type": "risk_source",
                    "label": "Cybercriminel",
                    "properties": {
                        "target_objective": "Sécurité publique ; Gestion des incidents",
                        "feared_event": "Interruption du service public",
                        "severity": "Critique",
                        "stakeholder_ids": [stakeholder_id],
                        "supporting_asset_ids": [asset_id],
                    },
                },
            )

            endpoint = f"{base}/workshop3/generate-scenarios"
            first = await client.post(endpoint)
            assert first.status_code == 200
            body = first.json()
            assert body["generated_count"] == 1
            scenario = body["records"][0]
            assert scenario["status"] == "proposed"
            assert scenario["properties"]["motivation"] == "Gain financier"
            assert scenario["properties"]["targeted_essential_asset"]
            assert scenario["properties"]["justification"]
            assert scenario["properties"]["confidence_label"] in {"Faible", "Moyenne", "Élevée"}

            workshops = (await client.get(f"{base}/workshops")).json()
            workshop3 = next(w for w in workshops if w["workshop_number"] == 3)
            workshop4 = next(w for w in workshops if w["workshop_number"] == 4)
            assert workshop3["progress_percent"] == 0
            assert workshop4["status"] == "locked"

            second = await client.post(endpoint)
            assert second.json()["generated_count"] == 0

            scenario_id = scenario["id"]
            validated = await client.patch(
                f"{base}/records/{scenario_id}", json={"status": "validated"}
            )
            assert validated.status_code == 200
            assert validated.json()["status"] == "validated"

            workshops = (await client.get(f"{base}/workshops")).json()
            workshop3 = next(w for w in workshops if w["workshop_number"] == 3)
            workshop4 = next(w for w in workshops if w["workshop_number"] == 4)
            assert workshop3["progress_percent"] == 100
            assert workshop3["status"] == "completed"
            assert workshop4["status"] == "available"

            rejected = await client.patch(
                f"{base}/records/{scenario_id}", json={"status": "rejected"}
            )
            assert rejected.status_code == 200

            workshops = (await client.get(f"{base}/workshops")).json()
            workshop3 = next(w for w in workshops if w["workshop_number"] == 3)
            # Un scénario rejeté ne bloque ni ne compte plus dans la progression.
            assert workshop3["progress_percent"] == 0

            restored = await client.patch(
                f"{base}/records/{scenario_id}", json={"status": "proposed"}
            )
            assert restored.status_code == 200
            workshops = (await client.get(f"{base}/workshops")).json()
            workshop3 = next(w for w in workshops if w["workshop_number"] == 3)
            assert workshop3["progress_percent"] == 0
    finally:
        app.dependency_overrides.clear()
