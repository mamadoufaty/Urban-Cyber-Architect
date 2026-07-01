"""Tests — moteur PDF Urban Cyber Architect V2.1."""

from __future__ import annotations

import io
import re
import uuid

from pypdf import PdfReader

from app.services.deliverables.deliverable_export import (
    export_deliverable_docx,
    export_deliverable_markdown,
    export_deliverable_pdf,
)
from app.services.pdf.document_builder import build_deliverable_pdf

UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _sample_content(*, with_uuid: bool = False) -> dict:
    uid = str(uuid.uuid4())
    risk_line = (
        f"{uid} — Datacenter Métropolis (criticité élevée, décision traiter)"
        if with_uuid
        else "Datacenter Métropolis (criticité élevée, décision traiter)"
    )
    return {
        "title": "Plan de management de projet",
        "user_need": "Organisation multiculturelle et gouvernance projet.",
        "metadata": {
            "project_name": "Métropolis",
            "deliverable_type_label": "Plan de management de projet",
            "generated_at": "2026-06-24T12:00:00+00:00",
            "version": "2.1",
        },
        "context_snapshot": {
            "urbanism": {
                "acteurs_detail": [
                    {"label": "RSSI", "couche": "organisation", "description": "Pilotage sécurité"},
                    {"label": "Serveur QRadar", "couche": "technique", "description": "SOC"},
                ],
                "organisations_detail": [
                    {"label": "Direction du numérique", "couche": "organisation", "description": ""},
                ],
                "applications_detail": [
                    {"label": "Portail citoyen", "couche": "application", "description": ""},
                ],
                "biens_supports": ["Datacenter Métropolis"],
            },
            "grc": {
                "risk_register_total": 2,
                "ptr_total": 3,
                "top_risks": [
                    {
                        "id": uid if with_uuid else "risk-1",
                        "asset": "Datacenter Métropolis",
                        "criticality": "élevée",
                        "decision": "traiter",
                    }
                ],
            },
        },
        "sections": [
            {
                "id": "presentation",
                "title": "1. Présentation du projet",
                "content": "Ce document présente le plan de management du projet Métropolis.",
                "bullets": [],
            },
            {
                "id": "contexte",
                "title": "2. Contexte et objectifs",
                "content": "Contexte projet aligné sur la transformation numérique.",
                "bullets": [],
            },
            {
                "id": "equipe",
                "title": "3. Organisation de l'équipe projet",
                "content": "Équipe projet identifiée.",
                "bullets": ["RSSI", "Architecte SI"],
            },
            {
                "id": "risques",
                "title": "9. Gestion des risques projet",
                "content": "Registre des risques consolidé.",
                "bullets": [risk_line],
            },
            {
                "id": "conclusion",
                "title": "11. Conclusion",
                "content": "Synthèse du plan de management.",
                "bullets": ["Document à valider en comité de pilotage."],
            },
        ],
    }


def test_pdf_generation_succeeds_and_not_empty():
    pdf = export_deliverable_pdf(_sample_content())
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 2000


def test_pdf_contains_brand_and_cover_elements():
    pdf = build_deliverable_pdf(_sample_content())
    text = _extract_pdf_text(pdf)
    assert "URBAN CYBER ARCHITECT" in text
    assert "Metropolis" in text or "Métropolis" in text
    assert "Plan de management de projet" in text
    assert "Confidentiel" in text
    assert len(PdfReader(io.BytesIO(pdf)).pages) >= 3


def test_pdf_hides_raw_uuid():
    uid = str(uuid.uuid4())
    content = _sample_content(with_uuid=True)
    content["context_snapshot"]["grc"]["top_risks"][0]["id"] = uid
    pdf = export_deliverable_pdf(content)
    text = _extract_pdf_text(pdf)
    assert uid not in text
    assert not UUID_RE.search(text)


def test_pdf_contains_closing_page():
    pdf = build_deliverable_pdf(_sample_content())
    text = _extract_pdf_text(pdf)
    assert "Urban Cyber Architect" in text
    assert "pilotage" in text.lower() or "valider" in text.lower()
    assert "Page" in text and "/" in text


def test_markdown_and_docx_exports_still_work():
    content = _sample_content()
    md = export_deliverable_markdown(content).decode("utf-8")
    assert "# Plan de management de projet" in md
    assert "Métropolis" in md
    docx = export_deliverable_docx(content)
    assert docx[:2] == b"PK"
