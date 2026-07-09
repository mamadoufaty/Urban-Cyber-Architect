"""Construction des relations automatiques selon le métamodèle Club Urba."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.metamodel.urbanism import validate_relation
from app.services.urbanism_import.types import ImportRow


@dataclass
class PlannedRelation:
    source_type: str
    source_ref: str
    relation_type: str
    target_type: str
    target_ref: str
    commentaire: str | None = None
    criticite: str | None = None


PARENT_RELATION_RULES: dict[tuple[str, str], tuple[str, str, str]] = {
    ("objectif", "metier"): ("metier", "définit", "objectif"),
    ("processus", "objectif"): ("objectif", "est pris en compte dans", "processus"),
    ("activite", "processus"): ("processus", "se décompose en", "activite"),
    ("classe", "activite"): ("activite", "manipule", "classe"),
    ("ilot_fonctionnel", "classe"): ("classe", "donne lieu à", "ilot_fonctionnel"),
}


def build_planned_relations(rows: list[ImportRow]) -> list[PlannedRelation]:
    planned: list[PlannedRelation] = []
    metier_by_objectif: dict[str, str] = {}

    for row in rows:
        if row.entity_type == "objectif":
            metier_ref = row.parent_refs.get("metier")
            if metier_ref:
                metier_by_objectif[row.external_id] = metier_ref

    for row in rows:
        if row.entity_type == "_technique_link":
            app_ref = row.parent_refs.get("ilot_applicatif")
            srv_ref = row.parent_refs.get("serveur")
            net_ref = row.parent_refs.get("reseau")
            site_ref = row.parent_refs.get("site")
            if app_ref and srv_ref:
                planned.append(
                    PlannedRelation(
                        source_type="ilot_applicatif",
                        source_ref=app_ref,
                        relation_type="est accessible via",
                        target_type="poste_travail",
                        target_ref=f"__access__{app_ref}",
                        commentaire="Import technique — accès applicatif",
                    )
                )
                planned.append(
                    PlannedRelation(
                        source_type="poste_travail",
                        source_ref=f"__access__{app_ref}",
                        relation_type="est connecté à",
                        target_type="serveur",
                        target_ref=srv_ref,
                    )
                )
            if app_ref and net_ref:
                planned.append(
                    PlannedRelation(
                        source_type="poste_travail",
                        source_ref=f"__access__{app_ref}",
                        relation_type="est connecté à",
                        target_type="reseau",
                        target_ref=net_ref,
                    )
                )
            if srv_ref and site_ref:
                planned.append(
                    PlannedRelation(
                        source_type="serveur",
                        source_ref=srv_ref,
                        relation_type="est hébergé sur",
                        target_type="site",
                        target_ref=site_ref,
                    )
                )
            continue

        for parent_type, parent_ref in row.parent_refs.items():
            rule = PARENT_RELATION_RULES.get((row.entity_type, parent_type))
            if rule:
                src_type, rel_type, tgt_type = rule
                if tgt_type == row.entity_type:
                    planned.append(
                        PlannedRelation(
                            source_type=src_type,
                            source_ref=parent_ref,
                            relation_type=rel_type,
                            target_type=tgt_type,
                            target_ref=row.external_id,
                        )
                    )
                else:
                    planned.append(
                        PlannedRelation(
                            source_type=row.entity_type,
                            source_ref=row.external_id,
                            relation_type=rel_type,
                            target_type=tgt_type,
                            target_ref=parent_ref,
                        )
                    )
            elif parent_type == "ilot_fonctionnel" and row.entity_type == "ilot_applicatif":
                planned.append(
                    PlannedRelation(
                        source_type="ilot_fonctionnel",
                        source_ref=parent_ref,
                        relation_type="__derived_fonc_applic__",
                        target_type="ilot_applicatif",
                        target_ref=row.external_id,
                    )
                )
            elif parent_type == "organisation" and row.entity_type == "operation":
                planned.append(
                    PlannedRelation(
                        source_type="organisation",
                        source_ref=parent_ref,
                        relation_type="__org_operation__",
                        target_type="operation",
                        target_ref=row.external_id,
                    )
                )
            elif parent_type == "serveur" and row.entity_type == "poste_travail":
                planned.append(
                    PlannedRelation(
                        source_type="poste_travail",
                        source_ref=row.external_id,
                        relation_type="est connecté à",
                        target_type="serveur",
                        target_ref=parent_ref,
                    )
                )
            elif parent_type == "reseau" and row.entity_type == "poste_travail":
                planned.append(
                    PlannedRelation(
                        source_type="poste_travail",
                        source_ref=row.external_id,
                        relation_type="est connecté à",
                        target_type="reseau",
                        target_ref=parent_ref,
                    )
                )

    for row in rows:
        if row.entity_type == "processus":
            for obj_row in rows:
                if obj_row.entity_type != "objectif":
                    continue
                if row.parent_refs.get("objectif") == obj_row.external_id:
                    metier_ref = obj_row.parent_refs.get("metier") or metier_by_objectif.get(obj_row.external_id)
                    if metier_ref:
                        planned.append(
                            PlannedRelation(
                                source_type="metier",
                                source_ref=metier_ref,
                                relation_type="pilote",
                                target_type="processus",
                                target_ref=row.external_id,
                            )
                        )

    return _dedupe_planned(planned)


def _dedupe_planned(planned: list[PlannedRelation]) -> list[PlannedRelation]:
    seen: set[tuple[str, str, str, str, str]] = set()
    out: list[PlannedRelation] = []
    for rel in planned:
        key = (
            rel.source_type,
            rel.source_ref.lower(),
            rel.relation_type,
            rel.target_type,
            rel.target_ref.lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(rel)
    return out


def is_valid_metamodel_relation(rel: PlannedRelation) -> bool:
    if rel.relation_type.startswith("__"):
        return True
    return validate_relation(rel.source_type, rel.relation_type, rel.target_type)


def resolve_entity_id(
    lookup: dict[tuple[str, str], UUID],
    entity_type: str,
    ref: str,
) -> UUID | None:
    ref_l = ref.strip().lower()
    return lookup.get((entity_type, ref_l))
