"""Assemblage PDF livrables — Urban Cyber Architect V2.1."""

from __future__ import annotations

import io
from typing import Any

from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.services.pdf.cover import draw_cover_page
from app.services.pdf.header_footer import draw_closing_page, draw_header_footer
from app.services.pdf.styles import get_pdf_styles
from app.services.pdf.tables import build_professional_table
from app.services.pdf.text_sanitize import (
    build_uuid_label_map,
    escape_pdf_text,
    sanitize_for_pdf,
)
from app.services.pdf.theme import (
    CLASSIFICATION,
    CONTENT_WIDTH,
    DOCUMENT_VERSION,
    FOOTER_HEIGHT,
    GOLD,
    HEADER_HEIGHT,
    MARGIN_BOTTOM,
    MARGIN_LEFT,
    MARGIN_RIGHT,
    MARGIN_TOP,
    NIGHT_BLUE,
    PAGE_HEIGHT,
    PAGE_SIZE,
    PAGE_WIDTH,
)

TABLE_SECTION_IDS = frozenset(
    {
        "equipe",
        "roles",
        "parties_prenantes",
        "risques",
        "metropolitain",
        "conclusion",
    }
)


def extract_document_meta(content: dict[str, Any]) -> dict[str, Any]:
    meta = dict(content.get("metadata") or {})
    snapshot = content.get("context_snapshot") or {}
    urbanism = snapshot.get("urbanism") or {}
    orgs = urbanism.get("organisations") or []

    return {
        "title": content.get("title") or "Livrable",
        "project_name": meta.get("project_name") or "—",
        "client": meta.get("client") or (orgs[0] if orgs else meta.get("project_name") or "—"),
        "version": meta.get("version") or DOCUMENT_VERSION,
        "generated_at": meta.get("generated_at"),
        "author": "Urban Cyber Architect",
        "classification": CLASSIFICATION,
        "deliverable_type_label": meta.get("deliverable_type_label"),
    }


class _NumberedCanvas(canvas.Canvas):
    """Canvas deux passes pour pagination Page X / Y."""

    def __init__(self, *args: Any, doc_meta: dict[str, Any], **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._page_states: list[dict[str, Any]] = []
        self.doc_meta = doc_meta

    def showPage(self) -> None:
        self._page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._page_states)
        numbered_total = max(total - 1, 1)
        for index, state in enumerate(self._page_states):
            self.__dict__.update(state)
            page_no = index + 1
            if page_no > 1:
                draw_header_footer(
                    self,
                    self.doc_meta,
                    page_number=page_no - 1,
                    total_pages=numbered_total,
                )
            super().showPage()
        super().save()


class _DeliverableDocTemplate(BaseDocTemplate):
    def __init__(self, buffer: io.BytesIO, meta: dict[str, Any], **kwargs: Any) -> None:
        self.doc_meta = meta
        super().__init__(buffer, **kwargs)

        content_height = (
            PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM - HEADER_HEIGHT - FOOTER_HEIGHT
        )
        content_frame = Frame(
            MARGIN_LEFT,
            MARGIN_BOTTOM + FOOTER_HEIGHT,
            CONTENT_WIDTH,
            content_height,
            id="content",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        cover_frame = Frame(
            0,
            0,
            PAGE_WIDTH,
            PAGE_HEIGHT,
            id="cover",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        closing_frame = Frame(
            0,
            0,
            PAGE_WIDTH,
            PAGE_HEIGHT,
            id="closing",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )

        self.addPageTemplates(
            [
                PageTemplate("cover", [cover_frame], onPage=self._on_cover),
                PageTemplate("content", [content_frame]),
                PageTemplate("closing", [closing_frame], onPage=self._on_closing),
            ]
        )

    def _on_cover(self, cnv: canvas.Canvas, _doc: BaseDocTemplate) -> None:
        draw_cover_page(cnv, self.doc_meta)

    def _on_closing(self, cnv: canvas.Canvas, _doc: BaseDocTemplate) -> None:
        draw_closing_page(cnv, self.doc_meta)


def _section_separator() -> Table:
    bar = Table([[""]], colWidths=[CONTENT_WIDTH], rowHeights=[3])
    bar.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), NIGHT_BLUE),
                ("LINEBELOW", (0, 0), (0, 0), 1, GOLD),
            ]
        )
    )
    return bar


def _table_for_section(
    section_id: str,
    content: dict[str, Any],
    label_map: dict[str, str],
) -> Table | None:
    snapshot = content.get("context_snapshot") or {}
    urbanism = snapshot.get("urbanism") or {}
    grc = snapshot.get("grc") or {}

    if section_id in ("equipe", "roles"):
        rows = urbanism.get("acteurs_detail") or []
        if not rows:
            bullets = _section_by_id(content, section_id)
            if bullets:
                return build_professional_table(
                    ["Acteur"],
                    [[sanitize_for_pdf(b, label_map)] for b in bullets[:15]],
                    col_widths=[CONTENT_WIDTH],
                )
            return None
        return build_professional_table(
            ["Acteur", "Couche", "Description"],
            [
                [
                    sanitize_for_pdf(r.get("label") or "—", label_map),
                    sanitize_for_pdf(r.get("couche") or "—", label_map),
                    sanitize_for_pdf(r.get("description") or "—", label_map),
                ]
                for r in rows[:15]
            ],
            col_widths=[CONTENT_WIDTH * 0.35, CONTENT_WIDTH * 0.2, CONTENT_WIDTH * 0.45],
        )

    if section_id == "parties_prenantes":
        actor_rows = [
            [sanitize_for_pdf(r.get("label") or "—", label_map), "Acteur"]
            for r in (urbanism.get("acteurs_detail") or [])[:8]
        ]
        org_rows = [
            [sanitize_for_pdf(r.get("label") or "—", label_map), "Organisation"]
            for r in (urbanism.get("organisations_detail") or [])[:8]
        ]
        combined = actor_rows + org_rows
        if not combined:
            return None
        return build_professional_table(
            ["Partie prenante", "Type"],
            combined,
            col_widths=[CONTENT_WIDTH * 0.7, CONTENT_WIDTH * 0.3],
        )

    if section_id == "risques":
        risks = grc.get("top_risks") or grc.get("risk_register_sample") or []
        if not risks:
            return None
        return build_professional_table(
            ["Bien support / Risque", "Criticité", "Décision"],
            [
                [
                    sanitize_for_pdf(
                        r.get("asset") or r.get("supporting_asset") or r.get("label") or "—",
                        label_map,
                    ),
                    sanitize_for_pdf(str(r.get("criticality") or "—"), label_map),
                    sanitize_for_pdf(str(r.get("decision") or r.get("treatment_decision") or "—"), label_map),
                ]
                for r in risks[:12]
            ],
            col_widths=[CONTENT_WIDTH * 0.5, CONTENT_WIDTH * 0.2, CONTENT_WIDTH * 0.3],
        )

    if section_id == "metropolitain":
        app_rows = [
            [sanitize_for_pdf(r.get("label") or "—", label_map), "Application"]
            for r in (urbanism.get("applications_detail") or [])[:6]
        ]
        asset_rows = [
            [sanitize_for_pdf(l, label_map), "Bien support"]
            for l in (urbanism.get("biens_supports") or [])[:6]
        ]
        combined = app_rows + asset_rows
        if not combined:
            return None
        return build_professional_table(
            ["Élément", "Catégorie"],
            combined,
            col_widths=[CONTENT_WIDTH * 0.7, CONTENT_WIDTH * 0.3],
        )

    if section_id == "conclusion" and grc.get("ptr_total"):
        ptr_total = grc.get("ptr_total", 0)
        return build_professional_table(
            ["Indicateur", "Valeur"],
            [
                ["Actions PTR", str(ptr_total)],
                ["Registre des risques", str(grc.get("risk_register_total", 0))],
            ],
            col_widths=[CONTENT_WIDTH * 0.6, CONTENT_WIDTH * 0.4],
        )

    return None


def _section_by_id(content: dict[str, Any], section_id: str) -> list[str]:
    for section in content.get("sections") or []:
        if section.get("id") == section_id:
            return [str(b) for b in (section.get("bullets") or [])]
    return []


def _build_section_flowables(
    section: dict[str, Any],
    content: dict[str, Any],
    styles: dict[str, Any],
    label_map: dict[str, str],
) -> list[Any]:
    flowables: list[Any] = []
    section_id = str(section.get("id") or "")
    title = sanitize_for_pdf(str(section.get("title") or "Section"), label_map)

    flowables.append(Spacer(1, 6))
    flowables.append(Paragraph(escape_pdf_text(title), styles["chapter"]))
    flowables.append(_section_separator())
    flowables.append(Spacer(1, 8))

    body = sanitize_for_pdf(str(section.get("content") or "").strip(), label_map)
    if body:
        if section_id == "contexte":
            flowables.append(Paragraph("<b>Objectif</b>", styles["subtitle"]))
            flowables.append(
                Paragraph(
                    f'<para backColor="#F1F5F9" borderPadding="8">{escape_pdf_text(body)}</para>',
                    styles["objective_box"],
                )
            )
        elif section_id == "conclusion":
            flowables.append(Paragraph(escape_pdf_text(body), styles["body"]))
            flowables.append(Spacer(1, 6))
            flowables.append(Paragraph("<b>Recommandations</b>", styles["subtitle"]))
        else:
            flowables.append(Paragraph(escape_pdf_text(body), styles["body"]))

    table = _table_for_section(section_id, content, label_map) if section_id in TABLE_SECTION_IDS else None
    if table is not None:
        flowables.append(Spacer(1, 8))
        flowables.append(table)
    else:
        bullets = section.get("bullets") or []
        if bullets:
            flowables.append(Spacer(1, 4))
            for bullet in bullets:
                text = sanitize_for_pdf(str(bullet), label_map)
                if section_id == "conclusion":
                    flowables.append(
                        Paragraph(
                            f'<para backColor="#FBF6E8" borderPadding="6">• {escape_pdf_text(text)}</para>',
                            styles["recommendation_box"],
                        )
                    )
                else:
                    flowables.append(Paragraph(f"• {escape_pdf_text(text)}", styles["bullet"]))

    flowables.append(Spacer(1, 10))
    return flowables


def build_deliverable_pdf(content: dict[str, Any]) -> bytes:
    """Génère un PDF professionnel à partir du contenu structuré d'un livrable."""
    meta = extract_document_meta(content)
    label_map = build_uuid_label_map(content)
    styles = get_pdf_styles()

    buffer = io.BytesIO()
    doc = _DeliverableDocTemplate(
        buffer,
        meta,
        pagesize=PAGE_SIZE,
        leftMargin=MARGIN_LEFT,
        rightMargin=MARGIN_RIGHT,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title=meta["title"],
    )

    story: list[Any] = [Spacer(1, 1), NextPageTemplate("content"), PageBreak()]

    if content.get("user_need"):
        story.append(Paragraph("Besoin utilisateur", styles["subtitle"]))
        need = sanitize_for_pdf(str(content["user_need"]), label_map)
        story.append(
            Paragraph(
                f'<para backColor="#F1F5F9" borderPadding="8">{escape_pdf_text(need)}</para>',
                styles["objective_box"],
            )
        )
        story.append(Spacer(1, 12))

    for section in content.get("sections") or []:
        story.extend(_build_section_flowables(section, content, styles, label_map))

    story.append(NextPageTemplate("closing"))
    story.append(PageBreak())
    story.append(Spacer(1, 1))

    def _canvas_maker(*args: Any, **kwargs: Any) -> _NumberedCanvas:
        return _NumberedCanvas(*args, doc_meta=meta, **kwargs)

    doc.build(story, canvasmaker=_canvas_maker)
    return buffer.getvalue()
