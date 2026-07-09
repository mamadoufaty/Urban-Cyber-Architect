"""Atelier 1 EBIOS RM — progression, déverrouillage de l'atelier 2 et
génération automatique de propositions depuis la cartographie active."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ebios import EbiosRecord
from app.services.ebios.assessment_service import get_workshop, list_records

WORKSHOP1_SECTIONS = (
    "security_scope",
    "stakeholder",
    "security_baseline",
    "reference_document",
)
SECTION_WEIGHT = 25

# Une proposition générée automatiquement (ou rejetée) ne compte jamais comme
# acquise : l'utilisateur doit explicitement la Valider pour qu'elle participe
# à la progression de l'atelier — aucune donnée n'est jamais validée d'office
# (méthodologie EBIOS RM, §Contraintes).
_EXCLUDED_FROM_PROGRESS = {"proposed", "rejected"}


def _counts_for_progress(record) -> bool:
    return getattr(record, "status", None) not in _EXCLUDED_FROM_PROGRESS


def _scope_is_complete(records) -> bool:
    for record in records:
        if (
            record.record_type == "security_scope"
            and record.label.strip()
            and _counts_for_progress(record)
        ):
            return True
    return False


def _has_record_type(records, record_type: str) -> bool:
    return any(
        r.record_type == record_type and _counts_for_progress(r) for r in records
    )


def compute_workshop1_progress(records) -> int:
    progress = 0
    if _scope_is_complete(records):
        progress += SECTION_WEIGHT
    for record_type in WORKSHOP1_SECTIONS[1:]:
        if _has_record_type(records, record_type):
            progress += SECTION_WEIGHT
    return progress


async def recalculate_workshop1_progress(db: AsyncSession, assessment_id: UUID) -> int:
    records = await list_records(db, assessment_id, workshop_number=1)
    progress = compute_workshop1_progress(records)

    workshop1 = await get_workshop(db, assessment_id, 1)
    workshop1.progress_percent = progress

    if progress == 100:
        workshop1.status = "completed"
    elif progress > 0:
        workshop1.status = "in_progress"
    else:
        workshop1.status = "available"

    workshop2 = await get_workshop(db, assessment_id, 2)
    if progress == 100:
        if workshop2.status == "locked":
            workshop2.status = "available"
    elif workshop2.progress_percent == 0 and workshop2.status == "available":
        workshop2.status = "locked"

    await db.commit()
    return progress


async def generate_workshop1_from_cartography(
    db: AsyncSession, assessment_id: UUID, project_id: UUID, *, regenerate: bool = False
) -> list[EbiosRecord]:
    """Analyse la cartographie active et propose périmètre, parties prenantes et
    socle de sécurité — toujours à l'état ``proposed`` (jamais validé d'office).

    Idempotent par défaut (``regenerate=False``) : ne recrée jamais une
    proposition déjà présente (même origine urbanisme, même domaine de socle,
    ou périmètre déjà défini). Avec ``regenerate=True``, les propositions non
    encore validées sont remplacées par de nouvelles suggestions (les
    éléments déjà validés ou modifiés manuellement ne sont jamais touchés).
    """
    from app.services import cartography_service
    from app.services.ebios.urbanism_actor_resolver import load_urbanism_graph
    from app.services.ebios.workshop1_cartography_generator import (
        SOURCE_CARTOGRAPHY,
        build_baseline_proposals,
        build_fallback_stakeholder_role_proposals,
        build_reference_document_proposals,
        build_scope_proposal,
        build_stakeholder_proposals,
    )

    entities, relations = await load_urbanism_graph(db, project_id)
    if not entities:
        return []

    try:
        cartography, version = await cartography_service.resolve_read_version(db, project_id)
        cartography_id, cartography_version_id = cartography.id, version.id
        cartography_label = f"{cartography.name} v{version.version}"
    except cartography_service.CartographyError:
        cartography_id, cartography_version_id = None, None
        cartography_label = None

    existing = await list_records(db, assessment_id, workshop_number=1)

    def _is_cartography_generated(record: EbiosRecord) -> bool:
        return (record.properties or {}).get("generated_from", {}).get("source") == SOURCE_CARTOGRAPHY

    if regenerate:
        for record in existing:
            if record.status == "proposed" and _is_cartography_generated(record):
                await db.delete(record)
        await db.flush()
        existing = [
            r for r in existing if not (r.status == "proposed" and _is_cartography_generated(r))
        ]

    created: list[EbiosRecord] = []

    if not any(r.record_type == "security_scope" for r in existing):
        scope = build_scope_proposal(entities, cartography_id, cartography_version_id)
        if scope:
            record = EbiosRecord(
                assessment_id=assessment_id,
                workshop_number=1,
                record_type="security_scope",
                label=scope["label"],
                description=scope["description"],
                properties=scope["properties"],
                status="proposed",
            )
            db.add(record)
            created.append(record)

    # Acteurs et organisations nommés en priorité ; si la cartographie n'en
    # modélise aucun, des rôles organisationnels génériques sont proposés
    # afin que la section Parties prenantes ne reste jamais vide.
    stakeholder_proposals = build_stakeholder_proposals(
        entities, relations, cartography_id, cartography_version_id
    )
    if not stakeholder_proposals:
        stakeholder_proposals = build_fallback_stakeholder_role_proposals(
            entities, cartography_id, cartography_version_id
        )

    existing_stakeholder_labels = {
        (r.label or "").strip().lower() for r in existing if r.record_type == "stakeholder"
    }
    for proposal in stakeholder_proposals:
        if proposal["label"].strip().lower() in existing_stakeholder_labels:
            continue
        record = EbiosRecord(
            assessment_id=assessment_id,
            workshop_number=1,
            record_type="stakeholder",
            label=proposal["label"],
            properties=proposal["properties"],
            status="proposed",
        )
        db.add(record)
        created.append(record)

    existing_baseline_domains = {
        (r.properties or {}).get("domain")
        for r in existing
        if r.record_type == "security_baseline"
    }
    for proposal in build_baseline_proposals(entities, cartography_id, cartography_version_id):
        if proposal["properties"]["domain"] in existing_baseline_domains:
            continue
        record = EbiosRecord(
            assessment_id=assessment_id,
            workshop_number=1,
            record_type="security_baseline",
            label=proposal["label"],
            description=proposal["description"],
            properties=proposal["properties"],
            status="proposed",
        )
        db.add(record)
        created.append(record)

    existing_document_labels = {
        (r.label or "").strip().lower()
        for r in existing
        if r.record_type == "reference_document"
    }
    for proposal in build_reference_document_proposals(
        entities, cartography_id, cartography_version_id, cartography_label
    ):
        if proposal["label"].strip().lower() in existing_document_labels:
            continue
        record = EbiosRecord(
            assessment_id=assessment_id,
            workshop_number=1,
            record_type="reference_document",
            label=proposal["label"],
            description=proposal["description"],
            properties=proposal["properties"],
            status="proposed",
        )
        db.add(record)
        created.append(record)

    if created:
        await db.commit()
        for record in created:
            await db.refresh(record)
    return created
