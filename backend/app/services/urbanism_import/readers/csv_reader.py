"""Lecteur CSV — une feuille par fichier ou CSV multi-sections."""

from __future__ import annotations

import csv
import io
from typing import Any

from app.services.urbanism_import.readers.base import ImportReader
from app.services.urbanism_import.readers.excel_reader import _compute_counts
from app.services.urbanism_import.readers.row_parser import parse_sheet_rows
from app.services.urbanism_import.sheet_registry import resolve_sheet_name
from app.services.urbanism_import.types import ImportIssue, ImportErrorCode, ParsedImport


class CsvImportReader(ImportReader):
    def read(self, content: bytes, filename: str) -> ParsedImport:
        text = content.decode("utf-8-sig")
        parsed = ParsedImport()

        sheet_from_name = _sheet_from_filename(filename)
        if sheet_from_name:
            rows = _csv_to_data_rows(text)
            sheet_rows, sheet_flux, sheet_issues = parse_sheet_rows(sheet_from_name, rows)
            parsed.rows.extend(sheet_rows)
            parsed.flux_rows.extend(sheet_flux)
            parsed.issues.extend(sheet_issues)
        else:
            sections = _split_multi_section_csv(text)
            if not sections:
                parsed.issues.append(
                    ImportIssue(
                        code=ImportErrorCode.INVALID_SHEET,
                        message="CSV non reconnu : nommez le fichier 01_Metiers.csv ou ajoutez une colonne Feuille",
                    )
                )
            for sheet_key, section_text in sections.items():
                rows = _csv_to_data_rows(section_text)
                sheet_rows, sheet_flux, sheet_issues = parse_sheet_rows(sheet_key, rows)
                parsed.rows.extend(sheet_rows)
                parsed.flux_rows.extend(sheet_flux)
                parsed.issues.extend(sheet_issues)

        parsed.counts = _compute_counts(parsed)
        return parsed


def _sheet_from_filename(filename: str) -> str | None:
    base = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    name = base.rsplit(".", 1)[0]
    return resolve_sheet_name(name)


def _csv_to_data_rows(text: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(text))
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(reader, start=2):
        if not any(str(v).strip() for v in row.values() if v is not None):
            continue
        rows.append({"row_number": idx, "cells": dict(row)})
    return rows


def _split_multi_section_csv(text: str) -> dict[str, str]:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return {}
    sheet_col = None
    for candidate in ("Feuille", "Sheet", "feuille", "sheet"):
        if candidate in reader.fieldnames:
            sheet_col = candidate
            break
    if not sheet_col:
        return {}
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in reader:
        raw_sheet = (row.get(sheet_col) or "").strip()
        resolved = resolve_sheet_name(raw_sheet) if raw_sheet else None
        if not resolved:
            continue
        clean = {k: v for k, v in row.items() if k != sheet_col}
        grouped.setdefault(resolved, []).append(clean)
    result: dict[str, str] = {}
    for sheet_key, items in grouped.items():
        if not items:
            continue
        headers = list(items[0].keys())
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=headers)
        writer.writeheader()
        writer.writerows(items)
        result[sheet_key] = buf.getvalue()
    return result
