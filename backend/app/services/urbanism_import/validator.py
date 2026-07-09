"""Validation des données importées."""

from __future__ import annotations

from collections import defaultdict

from app.services.urbanism_import.types import ImportErrorCode, ImportIssue, ImportRow, ParsedImport


def validate_parsed(parsed: ParsedImport) -> list[ImportIssue]:
    issues = list(parsed.issues)
    by_type_id: dict[tuple[str, str], list[ImportRow]] = defaultdict(list)
    id_index: dict[tuple[str, str], ImportRow] = {}

    for row in parsed.rows:
        if row.entity_type == "_technique_link":
            continue
        key = (row.entity_type, row.external_id.lower())
        by_type_id[key].append(row)
        id_index[(row.entity_type, row.external_id.lower())] = row
        if not row.label.strip():
            issues.append(
                ImportIssue(
                    code=ImportErrorCode.EMPTY_NAME,
                    message="Nom vide",
                    sheet=row.sheet,
                    row_number=row.row_number,
                )
            )

    for key, group in by_type_id.items():
        if len(group) > 1:
            issues.append(
                ImportIssue(
                    code=ImportErrorCode.DUPLICATE,
                    message=f"Identifiant dupliqué : {key[1]} ({key[0]})",
                    sheet=group[0].sheet,
                    row_number=group[0].row_number,
                    field="ID",
                )
            )

    label_seen: dict[tuple[str, str], ImportRow] = {}
    for row in parsed.rows:
        if row.entity_type == "_technique_link":
            continue
        norm = (row.entity_type, row.label.strip().lower())
        if norm in label_seen:
            issues.append(
                ImportIssue(
                    code=ImportErrorCode.DUPLICATE,
                    message=f"Libellé dupliqué pour {row.entity_type} : {row.label}",
                    sheet=row.sheet,
                    row_number=row.row_number,
                )
            )
        else:
            label_seen[norm] = row

    for row in parsed.rows:
        for parent_type, ref in row.parent_refs.items():
            if parent_type in {"serveur", "reseau", "site", "ilot_applicatif"}:
                continue
            ref_key = (parent_type, ref.lower())
            if ref_key not in id_index:
                alt = _find_by_label(parsed.rows, parent_type, ref)
                if not alt:
                    issues.append(
                        ImportIssue(
                            code=ImportErrorCode.UNKNOWN_REFERENCE,
                            message=f"Référence inconnue « {ref} » ({parent_type})",
                            sheet=row.sheet,
                            row_number=row.row_number,
                        )
                    )

    for flux in parsed.flux_rows:
        if not _ref_exists(parsed, "ilot_applicatif", flux["source"]):
            issues.append(
                ImportIssue(
                    code=ImportErrorCode.UNKNOWN_REFERENCE,
                    message=f"Flux : application source inconnue « {flux['source']} »",
                    sheet=flux.get("sheet"),
                    row_number=flux.get("row_number"),
                )
            )
        if not _ref_exists(parsed, "ilot_applicatif", flux["destination"]):
            issues.append(
                ImportIssue(
                    code=ImportErrorCode.UNKNOWN_REFERENCE,
                    message=f"Flux : application cible inconnue « {flux['destination']} »",
                    sheet=flux.get("sheet"),
                    row_number=flux.get("row_number"),
                )
            )

    return issues


def _find_by_label(rows: list[ImportRow], entity_type: str, label: str) -> ImportRow | None:
    target = label.strip().lower()
    for row in rows:
        if row.entity_type == entity_type and row.label.strip().lower() == target:
            return row
    return None


def _ref_exists(parsed: ParsedImport, entity_type: str, ref: str) -> bool:
    ref_l = ref.strip().lower()
    for row in parsed.rows:
        if row.entity_type != entity_type:
            continue
        if row.external_id.lower() == ref_l or row.label.strip().lower() == ref_l:
            return True
    return False


def count_planned_relations(parsed: ParsedImport) -> int:
    total = 0
    for row in parsed.rows:
        if row.entity_type == "_technique_link":
            total += len(row.parent_refs)
            continue
        total += len(row.parent_refs)
    total += len(parsed.flux_rows) * 2
    return total
