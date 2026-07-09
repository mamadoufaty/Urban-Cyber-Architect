"""Routes API — module EBIOS RM."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.metamodel.ebios import list_ebios_metamodel
from app.models.ebios import EbiosAssessment, EbiosLink, EbiosRecord, EbiosWorkshop
from app.schemas.ebios import (
    EbiosAssessmentCreate,
    EbiosAssessmentResponse,
    EbiosAssessmentUpdate,
    EbiosGenerateOperationalResponse,
    EbiosGenerateScenariosResponse,
    EbiosGenerateWorkshop1Response,
    EbiosGenerateWorkshop2Response,
    EbiosLinkCreate,
    EbiosLinkResponse,
    EbiosOverviewResponse,
    EbiosGenerateTreatmentResponse,
    EbiosOperationalScenarioPatch,
    EbiosRecordCreate,
    EbiosRecordPropertiesPatch,
    EbiosRecordResponse,
    EbiosRecordUpdate,
    EbiosRiskEvaluationPatch,
    EbiosUrbanismImportResponse,
    EbiosWorkshop4Response,
    EbiosWorkshop5Response,
    EbiosWorkshopResponse,
    EbiosWorkshopUpdate,
)
from app.services.ebios.assessment_service import (
    build_overview,
    create_assessment,
    create_record,
    get_assessment,
    get_or_create_assessment,
    get_workshop,
    list_assessments,
    list_records,
    list_workshops,
)
from app.services.ebios.registry import get_extension_registry
from app.services.ebios.urbanism_import import import_urbanism_supporting_assets
from app.services.ebios.workshop1_service import (
    generate_workshop1_from_cartography,
    recalculate_workshop1_progress,
)
from app.services.ebios.workshop2_service import (
    cleanup_risk_source_graph,
    generate_workshop2_risk_sources,
    recalculate_workshop2_progress,
    sync_risk_source_graph,
)
from app.services.ebios.workshop3_service import (
    cleanup_scenario_graph,
    generate_strategic_scenarios,
    is_scenario_validated,
    mark_scenario_modified,
    recalculate_workshop3_progress,
    sync_scenario_graph,
)
from app.services.ebios.workshop4_service import (
    delete_operational_scenario,
    generate_operational_scenarios,
    list_workshop4_scenarios,
    recalculate_workshop4_progress,
    update_operational_scenario,
)
from app.services.ebios.workshop5_service import (
    delete_risk_evaluation,
    generate_risk_treatments,
    get_workshop5_bundle,
    recalculate_workshop5_progress,
    update_risk_evaluation,
    update_security_measure,
    update_treatment_action,
)

router = APIRouter(tags=["ebios"])


@router.get("/metamodel/ebios")
async def get_ebios_metamodel():
    return list_ebios_metamodel()


@router.get("/ebios/extensions")
async def get_ebios_extensions():
    return get_extension_registry()


@router.get("/projects/{project_id}/ebios/assessment", response_model=EbiosAssessmentResponse)
async def get_project_ebios_assessment(
    project_id: UUID,
    cartography_id: UUID | None = Query(
        None, description="Cartographie ciblée — par défaut la cartographie active du projet."
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        assessment = await get_or_create_assessment(db, project_id, cartography_id)
        return assessment
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get(
    "/projects/{project_id}/ebios/assessments",
    response_model=list[EbiosAssessmentResponse],
)
async def get_project_ebios_assessments(
    project_id: UUID,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await list_assessments(db, project_id, cartography_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.post("/projects/{project_id}/ebios/assessments", response_model=EbiosAssessmentResponse, status_code=201)
async def post_ebios_assessment(
    project_id: UUID, data: EbiosAssessmentCreate, db: AsyncSession = Depends(get_db)
):
    try:
        return await create_assessment(
            db, project_id, data.title, data.description, data.cartography_id
        )
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get("/projects/{project_id}/ebios/assessments/{assessment_id}", response_model=EbiosAssessmentResponse)
async def get_ebios_assessment(project_id: UUID, assessment_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await get_assessment(db, project_id, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.patch("/projects/{project_id}/ebios/assessments/{assessment_id}", response_model=EbiosAssessmentResponse)
async def patch_ebios_assessment(
    project_id: UUID,
    assessment_id: UUID,
    data: EbiosAssessmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    try:
        assessment = await get_assessment(db, project_id, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "metadata":
            assessment.metadata_ = value
        else:
            setattr(assessment, field, value)
    await db.commit()
    await db.refresh(assessment)
    return assessment


@router.get(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/overview",
    response_model=EbiosOverviewResponse,
)
async def get_ebios_overview(project_id: UUID, assessment_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        assessment = await get_assessment(db, project_id, assessment_id)
        overview = await build_overview(db, assessment)
        return overview
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshops",
    response_model=list[EbiosWorkshopResponse],
)
async def get_ebios_workshops(project_id: UUID, assessment_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        await get_assessment(db, project_id, assessment_id)
        return await list_workshops(db, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshops/{workshop_number}",
    response_model=EbiosWorkshopResponse,
)
async def get_ebios_workshop(
    project_id: UUID, assessment_id: UUID, workshop_number: int, db: AsyncSession = Depends(get_db)
):
    try:
        await get_assessment(db, project_id, assessment_id)
        return await get_workshop(db, assessment_id, workshop_number)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.patch(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshops/{workshop_number}",
    response_model=EbiosWorkshopResponse,
)
async def patch_ebios_workshop(
    project_id: UUID,
    assessment_id: UUID,
    workshop_number: int,
    data: EbiosWorkshopUpdate,
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_assessment(db, project_id, assessment_id)
        workshop = await get_workshop(db, assessment_id, workshop_number)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(workshop, field, value)
    await db.commit()
    await db.refresh(workshop)
    return workshop


@router.get(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/records",
    response_model=list[EbiosRecordResponse],
)
async def get_ebios_records(
    project_id: UUID,
    assessment_id: UUID,
    workshop_number: int | None = Query(None, ge=1, le=5),
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_assessment(db, project_id, assessment_id)
        return await list_records(db, assessment_id, workshop_number)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.post(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/records",
    response_model=EbiosRecordResponse,
    status_code=201,
)
async def post_ebios_record(
    project_id: UUID,
    assessment_id: UUID,
    data: EbiosRecordCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_assessment(db, project_id, assessment_id)
        record = await create_record(
            db,
            assessment_id,
            data.workshop_number,
            data.record_type,
            data.label,
            data.description,
            data.properties,
            data.status,
            data.sort_order,
        )
        if data.workshop_number == 1:
            await recalculate_workshop1_progress(db, assessment_id)
            await db.refresh(record)
        elif data.workshop_number == 2 and data.record_type == "risk_source":
            await sync_risk_source_graph(db, record)
            await db.commit()
            await recalculate_workshop2_progress(db, assessment_id)
            await db.refresh(record)
        elif data.workshop_number == 3 and data.record_type == "strategic_scenario":
            await sync_scenario_graph(db, record)
            await db.commit()
            await recalculate_workshop3_progress(db, assessment_id)
            await db.refresh(record)
        return record
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.patch(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/records/{record_id}",
    response_model=EbiosRecordResponse,
)
async def patch_ebios_record(
    project_id: UUID,
    assessment_id: UUID,
    record_id: UUID,
    data: EbiosRecordUpdate,
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_assessment(db, project_id, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    record = await db.get(EbiosRecord, record_id)
    if not record or record.assessment_id != assessment_id:
        raise HTTPException(404, "Enregistrement introuvable")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    if record.workshop_number == 3 and record.record_type == "strategic_scenario":
        props_update = data.properties or {}
        if "workflow_status" not in props_update:
            mark_scenario_modified(record)
    await db.commit()
    if record.workshop_number == 1:
        await recalculate_workshop1_progress(db, assessment_id)
    elif record.workshop_number == 2 and record.record_type == "risk_source":
        await sync_risk_source_graph(db, record)
        await db.commit()
        await recalculate_workshop2_progress(db, assessment_id)
    elif record.workshop_number == 3 and record.record_type == "strategic_scenario":
        await sync_scenario_graph(db, record)
        await db.commit()
        await recalculate_workshop3_progress(db, assessment_id)
    await db.refresh(record)
    return record


@router.delete(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/records/{record_id}",
    status_code=204,
)
async def delete_ebios_record(
    project_id: UUID, assessment_id: UUID, record_id: UUID, db: AsyncSession = Depends(get_db)
):
    try:
        await get_assessment(db, project_id, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    record = await db.get(EbiosRecord, record_id)
    if not record or record.assessment_id != assessment_id:
        raise HTTPException(404, "Enregistrement introuvable")
    workshop_number = record.workshop_number
    record_type = record.record_type
    risk_source_id = record.id
    scenario_id = record.id
    if workshop_number == 2 and record_type == "risk_source":
        await cleanup_risk_source_graph(db, assessment_id, risk_source_id)
    elif workshop_number == 3 and record_type == "strategic_scenario":
        await cleanup_scenario_graph(db, assessment_id, scenario_id)
    await db.delete(record)
    await db.commit()
    if workshop_number == 1:
        await recalculate_workshop1_progress(db, assessment_id)
    elif workshop_number == 2:
        await recalculate_workshop2_progress(db, assessment_id)
    elif workshop_number == 3:
        await recalculate_workshop3_progress(db, assessment_id)


@router.post(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshop1/generate-from-cartography",
    response_model=EbiosGenerateWorkshop1Response,
)
async def post_generate_workshop1_from_cartography(
    project_id: UUID,
    assessment_id: UUID,
    regenerate: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_assessment(db, project_id, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    records = await generate_workshop1_from_cartography(
        db, assessment_id, project_id, regenerate=regenerate
    )
    await recalculate_workshop1_progress(db, assessment_id)
    return {"generated_count": len(records), "records": records}


@router.post(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshop2/import-urbanism-assets",
    response_model=EbiosUrbanismImportResponse,
)
async def post_import_urbanism_assets(
    project_id: UUID, assessment_id: UUID, db: AsyncSession = Depends(get_db)
):
    try:
        assessment = await get_assessment(db, project_id, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    records, count = await import_urbanism_supporting_assets(db, assessment.id, project_id)
    return {"imported_count": count, "records": records}


@router.post(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshop2/generate-risk-sources",
    response_model=EbiosGenerateWorkshop2Response,
)
async def post_generate_workshop2_risk_sources(
    project_id: UUID,
    assessment_id: UUID,
    regenerate: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_assessment(db, project_id, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    records = await generate_workshop2_risk_sources(
        db, assessment_id, project_id, regenerate=regenerate
    )
    await recalculate_workshop2_progress(db, assessment_id)
    return {"generated_count": len(records), "records": records}


@router.post(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshop3/generate-scenarios",
    response_model=EbiosGenerateScenariosResponse,
)
async def post_generate_strategic_scenarios(
    project_id: UUID,
    assessment_id: UUID,
    regenerate: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_assessment(db, project_id, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    records = await generate_strategic_scenarios(
        db, assessment_id, project_id, regenerate=regenerate
    )
    await recalculate_workshop3_progress(db, assessment_id)
    return {"generated_count": len(records), "records": records}


@router.get(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshop4",
    response_model=EbiosWorkshop4Response,
)
async def get_workshop4(
    project_id: UUID, assessment_id: UUID, db: AsyncSession = Depends(get_db)
):
    try:
        await get_assessment(db, project_id, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    w3 = await list_records(db, assessment_id, workshop_number=3)
    scenarios = await list_workshop4_scenarios(db, assessment_id)
    validated_strategic = sum(1 for r in w3 if is_scenario_validated(r))
    return {
        "scenarios": scenarios,
        "validated_strategic_count": validated_strategic,
        "operational_count": len(scenarios),
    }


@router.post(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshop4/generate-operational-scenarios",
    response_model=EbiosGenerateOperationalResponse,
)
async def post_generate_operational_scenarios(
    project_id: UUID,
    assessment_id: UUID,
    regenerate: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_assessment(db, project_id, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    records = await generate_operational_scenarios(db, assessment_id, regenerate=regenerate)
    await recalculate_workshop4_progress(db, assessment_id)
    return {"generated_count": len(records), "records": records}


@router.patch(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshop4/scenarios/{scenario_id}",
    response_model=EbiosRecordResponse,
)
async def patch_workshop4_scenario(
    project_id: UUID,
    assessment_id: UUID,
    scenario_id: UUID,
    data: EbiosOperationalScenarioPatch,
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_assessment(db, project_id, assessment_id)
        record = await update_operational_scenario(
            db,
            assessment_id,
            scenario_id,
            label=data.label,
            properties=data.properties,
            validate=data.set_validated,
        )
        await recalculate_workshop4_progress(db, assessment_id)
        return record
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.delete(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshop4/scenarios/{scenario_id}",
    status_code=204,
)
async def delete_workshop4_scenario(
    project_id: UUID, assessment_id: UUID, scenario_id: UUID, db: AsyncSession = Depends(get_db)
):
    try:
        await get_assessment(db, project_id, assessment_id)
        await delete_operational_scenario(db, assessment_id, scenario_id)
        await recalculate_workshop4_progress(db, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshop5",
    response_model=EbiosWorkshop5Response,
)
async def get_workshop5(
    project_id: UUID, assessment_id: UUID, db: AsyncSession = Depends(get_db)
):
    try:
        await get_assessment(db, project_id, assessment_id)
        return await get_workshop5_bundle(db, assessment_id, project_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.post(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshop5/generate-treatments",
    response_model=EbiosGenerateTreatmentResponse,
)
async def post_generate_treatments(
    project_id: UUID,
    assessment_id: UUID,
    regenerate: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_assessment(db, project_id, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    records = await generate_risk_treatments(db, assessment_id, project_id, regenerate=regenerate)
    await recalculate_workshop5_progress(db, assessment_id)
    return {"generated_count": len(records), "records": records}


@router.patch(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshop5/evaluations/{evaluation_id}",
    response_model=EbiosRecordResponse,
)
async def patch_workshop5_evaluation(
    project_id: UUID,
    assessment_id: UUID,
    evaluation_id: UUID,
    data: EbiosRiskEvaluationPatch,
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_assessment(db, project_id, assessment_id)
        record = await update_risk_evaluation(
            db,
            assessment_id,
            evaluation_id,
            treatment_decision=data.treatment_decision,
            properties=data.properties,
            set_validated=data.set_validated,
        )
        await recalculate_workshop5_progress(db, assessment_id)
        return record
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.patch(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshop5/measures/{measure_id}",
    response_model=EbiosRecordResponse,
)
async def patch_workshop5_measure(
    project_id: UUID,
    assessment_id: UUID,
    measure_id: UUID,
    data: EbiosRecordPropertiesPatch,
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_assessment(db, project_id, assessment_id)
        return await update_security_measure(db, assessment_id, measure_id, data.properties)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.patch(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshop5/actions/{action_id}",
    response_model=EbiosRecordResponse,
)
async def patch_workshop5_action(
    project_id: UUID,
    assessment_id: UUID,
    action_id: UUID,
    data: EbiosRecordPropertiesPatch,
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_assessment(db, project_id, assessment_id)
        return await update_treatment_action(db, assessment_id, action_id, data.properties)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.delete(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/workshop5/evaluations/{evaluation_id}",
    status_code=204,
)
async def delete_workshop5_evaluation(
    project_id: UUID, assessment_id: UUID, evaluation_id: UUID, db: AsyncSession = Depends(get_db)
):
    try:
        await get_assessment(db, project_id, assessment_id)
        await delete_risk_evaluation(db, assessment_id, evaluation_id)
        await recalculate_workshop5_progress(db, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.post(
    "/projects/{project_id}/ebios/assessments/{assessment_id}/links",
    response_model=EbiosLinkResponse,
    status_code=201,
)
async def post_ebios_link(
    project_id: UUID,
    assessment_id: UUID,
    data: EbiosLinkCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        await get_assessment(db, project_id, assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    link = EbiosLink(
        assessment_id=assessment_id,
        source_record_id=data.source_record_id,
        target_record_id=data.target_record_id,
        link_type=data.link_type,
        properties=data.properties,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link
