"""Orchestration import cartographie urbanisme."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.urbanism_assistant.progress_calculator import calculate_progress
from app.services.urbanism_engine import _analyze_graph, sync_missing_r05_relations
from app.services.urbanism_import.entity_writer import (
    build_lookup,
    clear_project_cartography,
    load_existing_entities,
    upsert_entities,
)
from app.services.urbanism_import.import_logger import log_import
from app.services.urbanism_import.readers.csv_reader import CsvImportReader
from app.services.urbanism_import.readers.excel_reader import ExcelImportReader
from app.services.urbanism_import.relation_builder import build_planned_relations
from app.services.urbanism_import.relation_writer import (
    create_relations,
    load_existing_relations,
    store_flux_on_applications,
)
from app.services.urbanism_import.types import ImportCounts, ImportMode, ImportPreview, ImportReport
from app.services.urbanism_import.validator import count_planned_relations, validate_parsed


def _reader_for_filename(filename: str):
    lower = filename.lower()
    if lower.endswith(".csv"):
        return CsvImportReader()
    return ExcelImportReader()


def parse_file(content: bytes, filename: str):
    reader = _reader_for_filename(filename)
    return reader.read(content, filename)


def build_preview(parsed, mode: ImportMode) -> ImportPreview:
    issues = validate_parsed(parsed)
    counts = parsed.counts
    counts.relations = count_planned_relations(parsed)
    sample = [
        {
            "sheet": row.sheet,
            "id": row.external_id,
            "type": row.entity_type,
            "label": row.label,
            "parents": row.parent_refs,
        }
        for row in parsed.rows[:20]
    ]
    return ImportPreview(counts=counts, issues=issues, sample_rows=sample, mode=mode)


async def execute_import(
    db: AsyncSession,
    project_id: UUID,
    content: bytes,
    filename: str,
    mode: ImportMode,
    *,
    user_id: UUID | None = None,
    skip_validation_errors: bool = False,
    cartography_id: UUID | None = None,
) -> ImportReport:
    from app.services import cartography_service

    parsed = parse_file(content, filename)
    issues = validate_parsed(parsed)
    blocking = [i for i in issues if i.severity == "error"]
    if blocking and not skip_validation_errors:
        return ImportReport(
            created={},
            updated={},
            relations_created=0,
            orphans=0,
            inconsistencies=len(blocking),
            completeness_rate=0.0,
            urbanism_progress={},
            issues=blocking,
            flux_stored=0,
        )

    # §12 — l'import ne cible jamais que le projet actif et sa cartographie
    # active (ou celle explicitement sélectionnée) ; les autres cartographies
    # ne sont jamais écrasées.
    _cartography, version, _id_map = await cartography_service.resolve_editable_version(
        db, project_id, cartography_id
    )
    version_id = version.id

    if mode == ImportMode.REPLACE:
        await clear_project_cartography(db, project_id, version_id)
        existing: list = []
        existing_relations: list = []
    else:
        existing = await load_existing_entities(db, project_id, version_id)
        existing_relations = await load_existing_relations(db, project_id, version_id)

    entities, created, updated = await upsert_entities(
        db, project_id, parsed.rows, mode, existing, version_id
    )
    lookup = build_lookup(entities)
    planned = build_planned_relations(parsed.rows)
    relations_created, rel_issues = await create_relations(
        db, project_id, planned, lookup, existing_relations, version_id
    )
    flux_stored = await store_flux_on_applications(db, parsed.flux_rows, lookup)

    await db.flush()
    all_relations = await load_existing_relations(db, project_id, version_id)
    await sync_missing_r05_relations(db, project_id, entities, all_relations, version_id)
    all_relations = await load_existing_relations(db, project_id, version_id)

    analysis = _analyze_graph(entities, all_relations)
    orphan_ids = {o["id"] for o in analysis.get("orphans", [])}
    progress = calculate_progress(entities, all_relations, orphan_ids)

    total_expected = max(len(entities), 1)
    connected = sum(1 for e in entities if str(e.id) not in orphan_ids)
    completeness = round(connected / total_expected * 100, 1)

    report = ImportReport(
        created=created,
        updated=updated,
        relations_created=relations_created,
        orphans=len(analysis.get("orphans", [])),
        inconsistencies=len(analysis.get("inconsistencies", [])) + len(rel_issues),
        completeness_rate=completeness,
        urbanism_progress=progress,
        issues=issues + rel_issues,
        flux_stored=flux_stored,
    )

    await log_import(
        db,
        project_id=project_id,
        mode=mode,
        filename=filename,
        report=report,
        user_id=user_id,
    )
    await cartography_service.log_history(
        db,
        _cartography,
        version,
        author=None,
        action="imported",
        comment=f"Import « {filename} » ({mode.value}) — {sum(created.values())} créé(s), {sum(updated.values())} mis à jour.",
    )
    await db.commit()
    return report


def preview_from_bytes(content: bytes, filename: str, mode: ImportMode) -> dict:
    parsed = parse_file(content, filename)
    preview = build_preview(parsed, mode)
    return {
        "counts": preview.counts.as_dict(),
        "issues": [
            {
                "code": i.code.value,
                "message": i.message,
                "sheet": i.sheet,
                "row": i.row_number,
                "field": i.field,
                "severity": i.severity,
            }
            for i in preview.issues
        ],
        "sample_rows": preview.sample_rows,
        "mode": preview.mode.value,
        "can_import": not any(i.severity == "error" for i in preview.issues),
    }


def report_to_dict(report: ImportReport) -> dict:
    return {
        "created": report.created,
        "updated": report.updated,
        "relations_created": report.relations_created,
        "orphans": report.orphans,
        "inconsistencies": report.inconsistencies,
        "completeness_rate": report.completeness_rate,
        "urbanism_progress": report.urbanism_progress,
        "flux_stored": report.flux_stored,
        "issues": [
            {
                "code": i.code.value,
                "message": i.message,
                "sheet": i.sheet,
                "row": i.row_number,
                "field": i.field,
                "severity": i.severity,
            }
            for i in report.issues
        ],
    }
