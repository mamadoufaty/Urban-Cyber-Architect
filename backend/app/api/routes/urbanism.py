from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.metamodel.urbanism import (
    get_entity_meta,
    list_metamodel,
    validate_metamodel_implementation,
    validate_relation,
)
from app.models.entities import Project, UrbanismEntity, UrbanismRelation
from app.schemas.urbanism import (
    AssistedCreateRequest,
    AssistedCreateResponse,
    AssistedFormSchema,
    AssistedLinkRequest,
    AssistedLinkResponse,
    DeduplicateResponse,
    UrbanismImportPreviewResponse,
    UrbanismImportReportResponse,
    UrbanismEntityCreate,
    UrbanismEntityResponse,
    UrbanismEntityUpdate,
    UrbanismRelationCreate,
    UrbanismEntityLayoutBulkUpdate,
    UrbanismEntityLayoutUpdate,
    UrbanismRelationLayoutUpdate,
    UrbanismRelationResponse,
)
from app.services import cartography_service
from app.services.cartography_service import CartographyError
from app.services.urbanism_assistant import AssistantError, assisted_create, assisted_link, calculate_progress, get_form_schema
from app.services.urbanism_deduplicate import deduplicate_project
from app.services.urbanism_edge_layout import clear_edge_layout, save_edge_layout
from app.services.urbanism_entity_layout import (
    clear_entity_layout,
    save_entity_layout,
    save_entity_layouts_bulk,
)
from app.services.urbanism_engine import _category_for_relation, get_project_cartography
from app.services.urbanism_import import (
    ImportMode,
    execute_import,
    generate_official_template,
    preview_from_bytes,
    report_to_dict,
)

router = APIRouter(tags=["urbanism"])


def _cartography_http_error(e: CartographyError) -> HTTPException:
    message = str(e)
    status_code = 404 if "introuvable" in message.lower() else 400
    return HTTPException(status_code, message)


@router.get("/metamodel")
async def get_metamodel():
    return list_metamodel()


@router.get("/metamodel/validation")
async def get_metamodel_validation():
    return validate_metamodel_implementation()


@router.get(
    "/projects/{project_id}/urbanism/assistant/form-schema",
    response_model=AssistedFormSchema,
)
async def assistant_form_schema(
    project_id: UUID,
    entity_type: str = Query(..., description="Type d'entité Club Urba"),
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_form_schema(db, project_id, entity_type, cartography_id)
    except AssistantError as e:
        raise HTTPException(400, str(e)) from e


@router.post(
    "/projects/{project_id}/urbanism/assistant/create",
    response_model=AssistedCreateResponse,
    status_code=201,
)
async def assistant_create(
    project_id: UUID,
    data: AssistedCreateRequest,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await assisted_create(
            db, project_id, data.entity_type, data.label, data.bindings, cartography_id
        )
        return AssistedCreateResponse(
            entity=result["entity"],
            relations_created=result["relations_created"],
            analysis=result["analysis"],
            bindings_applied=result["bindings_applied"],
            reused=result.get("reused", False),
        )
    except AssistantError as e:
        raise HTTPException(400, str(e)) from e


@router.post(
    "/projects/{project_id}/urbanism/assistant/link",
    response_model=AssistedLinkResponse,
)
async def assistant_link_endpoint(
    project_id: UUID,
    data: AssistedLinkRequest,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await assisted_link(
            db, project_id, data.action, data.rule_id, data.source_id, data.target_id, cartography_id
        )
        return AssistedLinkResponse(
            action=result["action"],
            relation=result.get("relation"),
            analysis=result["analysis"],
        )
    except AssistantError as e:
        raise HTTPException(400, str(e)) from e


@router.post(
    "/projects/{project_id}/urbanism/deduplicate",
    response_model=DeduplicateResponse,
)
async def urbanism_deduplicate(
    project_id: UUID,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, project_id)
    try:
        _cartography, version, _id_map = await cartography_service.resolve_editable_version(
            db, project_id, cartography_id
        )
    except CartographyError as e:
        raise _cartography_http_error(e) from e
    result = await deduplicate_project(db, project_id, version.id)
    await cartography_service.log_history(
        db, _cartography, version, author=None, action="updated", comment="Déduplication du graphe."
    )
    await db.commit()
    return DeduplicateResponse(**result)


@router.get("/projects/{project_id}/urbanism/progress")
async def urbanism_progress(
    project_id: UUID,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, project_id)
    try:
        _cartography, version = await cartography_service.resolve_read_version(
            db, project_id, cartography_id
        )
    except CartographyError as e:
        raise _cartography_http_error(e) from e
    entities = list(
        (
            await db.execute(
                select(UrbanismEntity).where(UrbanismEntity.cartography_version_id == version.id)
            )
        ).scalars()
    )
    relations = list(
        (
            await db.execute(
                select(UrbanismRelation).where(UrbanismRelation.cartography_version_id == version.id)
            )
        ).scalars()
    )
    from app.services.urbanism_engine import _analyze_graph

    analysis = _analyze_graph(entities, relations)
    orphan_ids = {o["id"] for o in analysis.get("orphans", [])}
    return calculate_progress(entities, relations, orphan_ids)


@router.get("/projects/{project_id}/urbanism/entities", response_model=list[UrbanismEntityResponse])
async def list_entities(
    project_id: UUID,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, project_id)
    try:
        _cartography, version = await cartography_service.resolve_read_version(
            db, project_id, cartography_id
        )
    except CartographyError as e:
        raise _cartography_http_error(e) from e
    result = await db.execute(
        select(UrbanismEntity)
        .where(UrbanismEntity.cartography_version_id == version.id)
        .order_by(UrbanismEntity.couche, UrbanismEntity.label)
    )
    return result.scalars().all()


@router.post("/projects/{project_id}/urbanism/entities", response_model=UrbanismEntityResponse, status_code=201)
async def create_entity(
    project_id: UUID,
    data: UrbanismEntityCreate,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, project_id)
    meta = get_entity_meta(data.entity_type)
    if not meta:
        raise HTTPException(400, f"Type d'entité inconnu: {data.entity_type}")

    try:
        cartography, version, id_map = await cartography_service.resolve_editable_version(
            db, project_id, cartography_id
        )
    except CartographyError as e:
        raise _cartography_http_error(e) from e
    version_id = version.id

    entity = UrbanismEntity(
        project_id=project_id,
        cartography_version_id=version_id,
        entity_type=data.entity_type,
        couche=meta["couche"],
        label=data.label.strip(),
        description=data.description,
        properties=data.properties,
    )
    db.add(entity)
    await db.flush()

    for rel in data.relations:
        if rel.source_id and rel.target_id:
            raise HTTPException(400, "Relation inline : source_id et target_id sont mutuellement exclusifs")
        if rel.source_id:
            source_id = cartography_service.remap_id(id_map, rel.source_id)
            source_entity = await _get_entity(db, project_id, source_id, version_id)
            await _create_relation_internal(
                db, project_id, version_id, source_entity.id, source_entity.entity_type,
                entity.id, rel.relation_type, rel.commentaire, rel.criticite,
            )
        elif rel.target_id:
            target_id = cartography_service.remap_id(id_map, rel.target_id)
            await _create_relation_internal(
                db, project_id, version_id, entity.id, entity.entity_type, target_id, rel.relation_type,
                rel.commentaire, rel.criticite,
            )
        else:
            raise HTTPException(400, "Relation inline : source_id ou target_id requis")

    await cartography_service.log_history(
        db, cartography, version, author=None, action="updated",
        comment=f"Création de « {entity.label} » ({entity.entity_type}).",
    )
    await db.commit()
    await db.refresh(entity)
    return entity


@router.put("/projects/{project_id}/urbanism/entities/{entity_id}", response_model=UrbanismEntityResponse)
async def update_entity(
    project_id: UUID,
    entity_id: UUID,
    data: UrbanismEntityUpdate,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        cartography, version, id_map = await cartography_service.resolve_editable_version(
            db, project_id, cartography_id
        )
    except CartographyError as e:
        raise _cartography_http_error(e) from e
    entity_id = cartography_service.remap_id(id_map, entity_id)
    entity = await _get_entity(db, project_id, entity_id, version.id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(entity, field, value)
    await cartography_service.log_history(
        db, cartography, version, author=None, action="updated",
        comment=f"Modification de « {entity.label} ».",
    )
    await db.commit()
    await db.refresh(entity)
    return entity


@router.delete("/projects/{project_id}/urbanism/entities/{entity_id}", status_code=204)
async def delete_entity(
    project_id: UUID,
    entity_id: UUID,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        cartography, version, id_map = await cartography_service.resolve_editable_version(
            db, project_id, cartography_id
        )
    except CartographyError as e:
        raise _cartography_http_error(e) from e
    entity_id = cartography_service.remap_id(id_map, entity_id)
    entity = await _get_entity(db, project_id, entity_id, version.id)
    await db.execute(delete(UrbanismRelation).where(
        (UrbanismRelation.source_id == entity_id) | (UrbanismRelation.target_id == entity_id)
    ))
    await db.execute(
        delete(UrbanismEntity).where(
            UrbanismEntity.id == entity_id, UrbanismEntity.project_id == project_id
        )
    )
    await cartography_service.log_history(
        db, cartography, version, author=None, action="updated",
        comment=f"Suppression de « {entity.label} ».",
    )
    await db.commit()


@router.get("/projects/{project_id}/urbanism/relations", response_model=list[UrbanismRelationResponse])
async def list_relations(
    project_id: UUID,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, project_id)
    try:
        _cartography, version = await cartography_service.resolve_read_version(
            db, project_id, cartography_id
        )
    except CartographyError as e:
        raise _cartography_http_error(e) from e
    result = await db.execute(
        select(UrbanismRelation)
        .where(UrbanismRelation.cartography_version_id == version.id)
        .order_by(UrbanismRelation.created_at.desc())
    )
    return result.scalars().all()


@router.post("/projects/{project_id}/urbanism/relations", response_model=UrbanismRelationResponse, status_code=201)
async def create_relation(
    project_id: UUID,
    data: UrbanismRelationCreate,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, project_id)
    try:
        cartography, version, id_map = await cartography_service.resolve_editable_version(
            db, project_id, cartography_id
        )
    except CartographyError as e:
        raise _cartography_http_error(e) from e
    source_id = cartography_service.remap_id(id_map, data.source_id)
    target_id = cartography_service.remap_id(id_map, data.target_id)
    source = await _get_entity(db, project_id, source_id, version.id)
    target = await _get_entity(db, project_id, target_id, version.id)
    rel = await _create_relation_internal(
        db, project_id, version.id, source.id, source.entity_type, target.id,
        data.relation_type, data.commentaire, data.criticite,
    )
    await cartography_service.log_history(
        db, cartography, version, author=None, action="updated",
        comment=f"Ajout d'une relation « {data.relation_type} ».",
    )
    await db.commit()
    await db.refresh(rel)
    return rel


@router.delete("/projects/{project_id}/urbanism/relations/{relation_id}", status_code=204)
async def delete_relation(
    project_id: UUID,
    relation_id: UUID,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        cartography, version, id_map = await cartography_service.resolve_editable_version(
            db, project_id, cartography_id
        )
    except CartographyError as e:
        raise _cartography_http_error(e) from e
    relation_id = cartography_service.remap_id(id_map, relation_id)
    result = await db.execute(
        select(UrbanismRelation).where(
            UrbanismRelation.id == relation_id,
            UrbanismRelation.project_id == project_id,
            UrbanismRelation.cartography_version_id == version.id,
        )
    )
    rel = result.scalar_one_or_none()
    if not rel:
        raise HTTPException(404, "Relation not found")
    await db.delete(rel)
    await cartography_service.log_history(
        db, cartography, version, author=None, action="updated", comment="Suppression d'une relation."
    )
    await db.commit()


@router.put(
    "/projects/{project_id}/urbanism/edges/{edge_id}/layout",
    status_code=200,
)
async def save_edge_layout_endpoint(
    project_id: UUID,
    edge_id: str,
    data: UrbanismRelationLayoutUpdate,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, project_id)
    try:
        _cartography, version, _id_map = await cartography_service.resolve_editable_version(
            db, project_id, cartography_id
        )
        layout = await save_edge_layout(
            db, project_id, edge_id, data.layout.model_dump(), version.id
        )
        return {"edge_id": edge_id, "layout": layout}
    except CartographyError as e:
        raise _cartography_http_error(e) from e
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.delete(
    "/projects/{project_id}/urbanism/edges/{edge_id}/layout",
    status_code=204,
)
async def clear_edge_layout_endpoint(
    project_id: UUID,
    edge_id: str,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, project_id)
    try:
        _cartography, version, _id_map = await cartography_service.resolve_editable_version(
            db, project_id, cartography_id
        )
        await clear_edge_layout(db, project_id, edge_id, version.id)
    except CartographyError as e:
        raise _cartography_http_error(e) from e
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.put(
    "/projects/{project_id}/urbanism/entities/{entity_id}/layout",
    status_code=200,
)
async def save_entity_layout_endpoint(
    project_id: UUID,
    entity_id: UUID,
    data: UrbanismEntityLayoutUpdate,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, project_id)
    try:
        _cartography, version, id_map = await cartography_service.resolve_editable_version(
            db, project_id, cartography_id
        )
        entity_id = cartography_service.remap_id(id_map, entity_id)
        layout = await save_entity_layout(
            db, project_id, entity_id, data.layout.model_dump(), version.id
        )
        return {"entity_id": str(entity_id), "layout": layout}
    except CartographyError as e:
        raise _cartography_http_error(e) from e
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.put(
    "/projects/{project_id}/urbanism/entities/layout/bulk",
    status_code=200,
)
async def save_entity_layouts_bulk_endpoint(
    project_id: UUID,
    data: UrbanismEntityLayoutBulkUpdate,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, project_id)
    try:
        _cartography, version, id_map = await cartography_service.resolve_editable_version(
            db, project_id, cartography_id
        )
        layouts = await save_entity_layouts_bulk(
            db,
            project_id,
            [
                {
                    "entity_id": cartography_service.remap_id(id_map, item.entity_id),
                    "layout": item.layout.model_dump(),
                }
                for item in data.layouts
            ],
            version.id,
        )
        return {"layouts": layouts}
    except CartographyError as e:
        raise _cartography_http_error(e) from e
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.delete(
    "/projects/{project_id}/urbanism/entities/{entity_id}/layout",
    status_code=204,
)
async def clear_entity_layout_endpoint(
    project_id: UUID,
    entity_id: UUID,
    cartography_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, project_id)
    try:
        _cartography, version, id_map = await cartography_service.resolve_editable_version(
            db, project_id, cartography_id
        )
        entity_id = cartography_service.remap_id(id_map, entity_id)
        await clear_entity_layout(db, project_id, entity_id, version.id)
    except CartographyError as e:
        raise _cartography_http_error(e) from e
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get("/urbanism/import/template")
async def download_import_template():
    content = generate_official_template()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="UCA_Modele_Cartographie_Urbanisme_V1.4.xlsx"'
        },
    )


@router.post(
    "/projects/{project_id}/urbanism/import/preview",
    response_model=UrbanismImportPreviewResponse,
)
async def urbanism_import_preview(
    project_id: UUID,
    file: UploadFile = File(...),
    mode: str = Form("merge"),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, project_id)
    content = await file.read()
    import_mode = ImportMode.REPLACE if mode == "replace" else ImportMode.MERGE
    return preview_from_bytes(content, file.filename or "import.xlsx", import_mode)


@router.post(
    "/projects/{project_id}/urbanism/import",
    response_model=UrbanismImportReportResponse,
)
async def urbanism_import_execute(
    project_id: UUID,
    file: UploadFile = File(...),
    mode: str = Form("merge"),
    force: bool = Form(False),
    cartography_id: UUID | None = Query(
        None, description="Cartographie ciblée (par défaut : la cartographie active du projet)"
    ),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, project_id)
    content = await file.read()
    import_mode = ImportMode.REPLACE if mode == "replace" else ImportMode.MERGE
    try:
        report = await execute_import(
            db,
            project_id,
            content,
            file.filename or "import.xlsx",
            import_mode,
            skip_validation_errors=force,
            cartography_id=cartography_id,
        )
    except CartographyError as e:
        raise _cartography_http_error(e) from e
    if not report.created and not report.updated and report.inconsistencies and not force:
        raise HTTPException(400, detail=report_to_dict(report))
    return report_to_dict(report)


@router.get("/projects/{project_id}/urbanism/graph")
async def get_urbanism_graph(
    project_id: UUID,
    categories: str | None = Query(None, description="Catégories séparées par virgule: metier,organisation,..."),
    cartography_id: UUID | None = Query(None),
    version_id: UUID | None = Query(
        None, description="Consulter une version précise (lecture seule) au lieu de la version courante"
    ),
    db: AsyncSession = Depends(get_db),
):
    cats = [c.strip() for c in categories.split(",") if c.strip()] if categories else None
    try:
        graph = await get_project_cartography(db, project_id, cats, cartography_id, version_id)
    except CartographyError as e:
        raise _cartography_http_error(e) from e
    if not graph:
        raise HTTPException(404, "Project not found")
    return graph


async def _get_project(db: AsyncSession, project_id: UUID) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


async def _get_entity(
    db: AsyncSession,
    project_id: UUID,
    entity_id: UUID,
    cartography_version_id: UUID | None = None,
) -> UrbanismEntity:
    entity = await db.get(UrbanismEntity, entity_id)
    if not entity or entity.project_id != project_id:
        raise HTTPException(404, "Entity not found")
    if cartography_version_id is not None and entity.cartography_version_id != cartography_version_id:
        raise HTTPException(404, "Entity not found")
    return entity


async def _create_relation_internal(
    db: AsyncSession,
    project_id: UUID,
    cartography_version_id: UUID | None,
    source_id: UUID,
    source_type: str,
    target_id: UUID,
    relation_type: str,
    commentaire: str | None,
    criticite: str | None,
) -> UrbanismRelation:
    target = await db.get(UrbanismEntity, target_id)
    if not target or target.project_id != project_id:
        raise HTTPException(400, "Cible de relation invalide")
    if not validate_relation(source_type, relation_type, target.entity_type):
        raise HTTPException(
            400,
            f"Relation non conforme au métamodèle: {source_type} —{relation_type}→ {target.entity_type}",
        )
    category = _category_for_relation(source_type, relation_type, target.entity_type)
    rel = UrbanismRelation(
        project_id=project_id,
        cartography_version_id=cartography_version_id,
        source_id=source_id,
        target_id=target_id,
        relation_type=relation_type,
        category=category,
        commentaire=commentaire,
        criticite=criticite,
    )
    db.add(rel)
    return rel
