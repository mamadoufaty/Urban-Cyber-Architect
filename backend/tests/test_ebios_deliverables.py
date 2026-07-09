"""Tests — Livrables automatiques EBIOS RM (rapport, registre, PTR, COMEX)."""

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import Project, UrbanismEntity, UrbanismRelation
from tests.test_ebios_workshop5 import _setup_validated_operational


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


async def _seed_project(db_session: AsyncSession) -> Project:
    project = Project(name="Livrables EBIOS", organization={})
    db_session.add(project)
    await db_session.flush()
    serveur = UrbanismEntity(
        project_id=project.id, entity_type="serveur", couche="technique", label="Serveur QRadar"
    )
    owner_acteur = UrbanismEntity(
        project_id=project.id, entity_type="acteur", couche="organisation", label="Responsable SI"
    )
    decideur = UrbanismEntity(
        project_id=project.id, entity_type="acteur", couche="organisation", label="Décideur métier"
    )
    db_session.add_all([serveur, owner_acteur, decideur])
    await db_session.flush()
    db_session.add(
        UrbanismRelation(
            project_id=project.id,
            source_id=serveur.id,
            target_id=owner_acteur.id,
            relation_type="est_exploité_par",
            category="exploitation",
        )
    )
    db_session.add(
        UrbanismRelation(
            project_id=project.id,
            source_id=serveur.id,
            target_id=decideur.id,
            relation_type="décide_pour",
            category="gouvernance",
        )
    )
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_deliverables_from_complete_study(db_session: AsyncSession):
    project = await _seed_project(db_session)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    ebios_base = f"/api/projects/{project.id}/ebios"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assessment_id = (await client.get(f"{ebios_base}/assessment")).json()["id"]
        await _setup_validated_operational(client, ebios_base, assessment_id)

        # Atelier 2 nécessite plusieurs sources de risque qualifiées pour
        # atteindre 100 % — on complète avec 3 sources supplémentaires,
        # réutilisant la même partie prenante et le même bien support.
        w1_stakeholders = (
            await client.get(f"{ebios_base}/assessments/{assessment_id}/records?workshop_number=1")
        ).json()
        stakeholder_id = next(r["id"] for r in w1_stakeholders if r["record_type"] == "stakeholder")
        w2_records = (
            await client.get(f"{ebios_base}/assessments/{assessment_id}/records?workshop_number=2")
        ).json()
        asset_id = next(
            r["id"]
            for r in w2_records
            if r["record_type"] == "supporting_asset" and r["properties"].get("entity_type") == "serveur"
        )
        for label in ("Employé malveillant", "Erreur humaine", "Défaillance technique"):
            await client.post(
                f"{ebios_base}/assessments/{assessment_id}/records",
                json={
                    "workshop_number": 2,
                    "record_type": "risk_source",
                    "label": label,
                    "properties": {
                        "target_objective": "Continuité de service",
                        "feared_event": "Indisponibilité du système",
                        "severity": "Élevée",
                        "stakeholder_ids": [stakeholder_id],
                        "supporting_asset_ids": [asset_id],
                    },
                },
            )

        # Valider explicitement toutes les propositions restantes de l'Atelier 1
        # (documents de référence par défaut, socle de sécurité auto-générés…)
        # afin que la progression globale de l'étude atteigne 100 %.
        w1_records = (
            await client.get(f"{ebios_base}/assessments/{assessment_id}/records?workshop_number=1")
        ).json()
        for record in w1_records:
            if record["status"] == "proposed":
                await client.patch(
                    f"{ebios_base}/assessments/{assessment_id}/records/{record['id']}",
                    json={"status": "validated"},
                )

        generated = await client.post(
            f"{ebios_base}/assessments/{assessment_id}/workshop5/generate-treatments"
        )
        evaluation = generated.json()["records"][0]
        await client.patch(
            f"{ebios_base}/assessments/{assessment_id}/workshop5/evaluations/{evaluation['id']}",
            json={"set_validated": True},
        )

        overview = (await client.get(f"{ebios_base}/assessments/{assessment_id}/overview")).json()
        assert overview["overall_progress_percent"] == 100

        deliverables_base = f"/api/projects/{project.id}/ebios/assessments/{assessment_id}/deliverables"

        report = await client.get(f"{deliverables_base}/report")
        assert report.status_code == 200
        report_data = report.json()
        assert report_data["is_complete"] is True
        assert report_data["completeness_warning"] is None
        assert report_data["overall_progress_percent"] == 100
        assert len(report_data["sections"]) >= 5
        assert any("Atelier 1" in s["title"] for s in report_data["sections"])
        assert any("Atelier 5" in s["title"] for s in report_data["sections"])

        register = await client.get(f"{deliverables_base}/risk-register")
        assert register.status_code == 200
        register_data = register.json()
        assert register_data["is_complete"] is True
        assert register_data["data"]["total"] == 1
        assert register_data["data"]["rows"][0]["risk_source"]
        assert any(c["key"] == "risk_id" for c in register_data["data"]["columns"])

        plan = await client.get(f"{deliverables_base}/treatment-plan")
        assert plan.status_code == 200
        plan_data = plan.json()
        assert plan_data["is_complete"] is True
        assert plan_data["data"]["summary"]["total_actions"] >= 1

        comex = await client.get(f"{deliverables_base}/executive-summary")
        assert comex.status_code == 200
        comex_data = comex.json()
        assert comex_data["is_complete"] is True
        assert comex_data["data"]["kpis"]["overall_progress_percent"] == 100
        assert comex_data["data"]["kpis"]["risks_total"] == 1

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_deliverables_from_incomplete_study_show_warning(db_session: AsyncSession):
    project = Project(name="Livrables incomplet", organization={})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    ebios_base = f"/api/projects/{project.id}/ebios"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Une étude fraîchement créée n'a aucune donnée validée : seuls les
        # documents de référence par défaut existent, à l'état "proposed".
        assessment_id = (await client.get(f"{ebios_base}/assessment")).json()["id"]

        overview = (await client.get(f"{ebios_base}/assessments/{assessment_id}/overview")).json()
        assert overview["overall_progress_percent"] == 0

        deliverables_base = f"/api/projects/{project.id}/ebios/assessments/{assessment_id}/deliverables"

        for path in ("report", "risk-register", "treatment-plan", "executive-summary"):
            resp = await client.get(f"{deliverables_base}/{path}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["is_complete"] is False
            assert data["completeness_warning"]
            assert "complète" in data["completeness_warning"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_deliverable_unknown_assessment_returns_404(db_session: AsyncSession):
    project = Project(name="Livrables 404", organization={})
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        fake_id = "11111111-1111-1111-1111-111111111111"
        resp = await client.get(
            f"/api/projects/{project.id}/ebios/assessments/{fake_id}/deliverables/report"
        )
        assert resp.status_code == 404

    app.dependency_overrides.clear()
