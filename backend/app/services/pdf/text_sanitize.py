"""Sanitisation du texte PDF — masquage des UUID."""

from __future__ import annotations

import re
from typing import Any
from xml.sax.saxutils import escape

UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)

MASKED_REFERENCE = "Référence interne masquée"


def escape_pdf_text(text: str) -> str:
    """Échappe le HTML ReportLab et supprime le markdown léger."""
    cleaned = str(text or "")
    cleaned = cleaned.replace("**", "")
    cleaned = cleaned.replace("__", "")
    return escape(cleaned).replace("\n", "<br/>")


def build_uuid_label_map(content: dict[str, Any]) -> dict[str, str]:
    """Construit une table UUID → libellé métier depuis le contexte du livrable."""
    mapping: dict[str, str] = {}
    snapshot = content.get("context_snapshot") or {}
    urbanism = snapshot.get("urbanism") or {}

    for key in (
        "acteurs_detail",
        "organisations_detail",
        "processus_detail",
        "applications_detail",
    ):
        for item in urbanism.get(key) or []:
            label = str(item.get("label") or "").strip()
            if not label:
                continue
            props = item.get("properties") or {}
            for field in ("id", "entity_id", "urbanism_entity_id", "uuid"):
                val = props.get(field)
                if val:
                    mapping[str(val)] = label

    grc = snapshot.get("grc") or {}
    for row in (grc.get("top_risks") or []) + (grc.get("risk_register_sample") or []):
        asset = (
            row.get("asset")
            or row.get("supporting_asset")
            or row.get("label")
            or row.get("risk_label")
        )
        for id_field in ("id", "risk_id", "assessment_id", "owner_id"):
            uid = row.get(id_field)
            if uid and asset:
                mapping[str(uid)] = str(asset)
            elif uid and not asset:
                mapping.setdefault(str(uid), MASKED_REFERENCE)

    ebios = snapshot.get("ebios") or {}
    if ebios.get("assessment_id"):
        mapping[str(ebios["assessment_id"])] = "Évaluation EBIOS RM"

    project_meta = content.get("metadata") or {}
    if project_meta.get("project_id"):
        pname = project_meta.get("project_name") or "Projet"
        mapping[str(project_meta["project_id"])] = str(pname)

    return mapping


def sanitize_for_pdf(text: str, label_map: dict[str, str]) -> str:
    """Remplace les UUID par un libellé métier ou une mention masquée."""

    def _replace(match: re.Match[str]) -> str:
        uid = match.group(0)
        return label_map.get(uid, label_map.get(uid.lower(), MASKED_REFERENCE))

    return UUID_PATTERN.sub(_replace, str(text or ""))
