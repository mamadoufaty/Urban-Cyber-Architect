"""Parsing commun des lignes de feuille."""

from __future__ import annotations

from typing import Any

from app.services.urbanism_import.sheet_registry import (
    SHEET_BY_KEY,
    row_to_properties,
)
from app.services.urbanism_import.types import ImportErrorCode, ImportIssue, ImportRow


def parse_sheet_rows(
    sheet_key: str,
    data_rows: list[dict[str, Any]],
) -> tuple[list[ImportRow], list[dict[str, Any]], list[ImportIssue]]:
    defn = SHEET_BY_KEY[sheet_key]
    rows: list[ImportRow] = []
    flux_rows: list[dict[str, Any]] = []
    issues: list[ImportIssue] = []

    if defn.is_flux_sheet:
        for item in data_rows:
            cells = item["cells"]
            source = _cell(cells.get("Source"))
            dest = _cell(cells.get("Destination"))
            if not source and not dest:
                continue
            if not source or not dest:
                issues.append(
                    ImportIssue(
                        code=ImportErrorCode.MISSING_OBJECT,
                        message="Flux incomplet : source et destination requis",
                        sheet=sheet_key,
                        row_number=item["row_number"],
                    )
                )
                continue
            flux_rows.append(
                {
                    "sheet": sheet_key,
                    "row_number": item["row_number"],
                    "source": source,
                    "destination": dest,
                    "type": _cell(cells.get("Type")),
                    "protocol": _cell(cells.get("Protocole")),
                    "description": _cell(cells.get("Description")),
                }
            )
        return rows, flux_rows, issues

    if sheet_key == "10_Technique":
        for item in data_rows:
            cells = item["cells"]
            label = _cell(cells.get(defn.name_column)) or _cell(cells.get("Application"))
            if not label:
                issues.append(
                    ImportIssue(
                        code=ImportErrorCode.EMPTY_NAME,
                        message="Nom ou Application requis",
                        sheet=sheet_key,
                        row_number=item["row_number"],
                    )
                )
                continue
            parent_refs = {
                "ilot_applicatif": _cell(cells.get("Application")) or "",
                "serveur": _cell(cells.get("Serveur")) or "",
                "reseau": _cell(cells.get("Réseau")) or "",
                "site": _cell(cells.get("Site")) or "",
            }
            rows.append(
                ImportRow(
                    sheet=sheet_key,
                    row_number=item["row_number"],
                    external_id=_cell(cells.get(defn.id_column)) or label,
                    entity_type="_technique_link",
                    label=label,
                    description=_cell(cells.get(defn.description_column)),
                    parent_refs={k: v for k, v in parent_refs.items() if v},
                    properties=row_to_properties(defn, cells),
                )
            )
        return rows, flux_rows, issues

    if not defn.entity_type:
        return rows, flux_rows, issues

    for item in data_rows:
        cells = item["cells"]
        external_id = _cell(cells.get(defn.id_column))
        label = _cell(cells.get(defn.name_column))
        if not external_id and not label:
            continue
        if not label:
            issues.append(
                ImportIssue(
                    code=ImportErrorCode.EMPTY_NAME,
                    message=f"Colonne « {defn.name_column} » vide",
                    sheet=sheet_key,
                    row_number=item["row_number"],
                    field=defn.name_column,
                )
            )
            continue
        parent_refs = {
            target_type: _cell(cells.get(col)) or ""
            for col, target_type in defn.parent_columns
            if _cell(cells.get(col))
        }
        rows.append(
            ImportRow(
                sheet=sheet_key,
                row_number=item["row_number"],
                external_id=external_id or label,
                entity_type=defn.entity_type,
                label=label,
                description=_cell(cells.get(defn.description_column)),
                parent_refs=parent_refs,
                properties=row_to_properties(defn, cells),
            )
        )
    return rows, flux_rows, issues


def _cell(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
