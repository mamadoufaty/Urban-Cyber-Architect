"""En-tête et pied de page — Urban Cyber Architect."""

from __future__ import annotations

from typing import Any

from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from app.services.pdf.theme import (
    BRAND_SHORT,
    CLASSIFICATION,
    DOCUMENT_VERSION,
    FONT_BOLD,
    FONT_REGULAR,
    GOLD,
    LIGHT_GRAY,
    MARGIN_LEFT,
    MARGIN_RIGHT,
    MID_GRAY,
    NIGHT_BLUE,
    PAGE_HEIGHT,
    PAGE_WIDTH,
)


def draw_header_footer(
    cnv: canvas.Canvas,
    meta: dict[str, Any],
    *,
    page_number: int,
    total_pages: int,
) -> None:
    """Dessine l'en-tête et le pied de page (pages de contenu uniquement)."""
    width = PAGE_WIDTH
    top_y = PAGE_HEIGHT - 1.5 * cm

    cnv.setStrokeColor(GOLD)
    cnv.setLineWidth(0.5)
    cnv.line(MARGIN_LEFT, top_y + 0.4 * cm, width - MARGIN_RIGHT, top_y + 0.4 * cm)

    cnv.setFillColor(NIGHT_BLUE)
    cnv.setFont(FONT_BOLD, 8)
    cnv.drawString(MARGIN_LEFT, top_y, BRAND_SHORT)

    project = str(meta.get("project_name") or "—")
    deliverable = str(meta.get("title") or "Livrable")
    center_text = f"{project}  ·  {deliverable}"
    cnv.setFont(FONT_REGULAR, 8)
    cnv.setFillColor(MID_GRAY)
    text_width = cnv.stringWidth(center_text, FONT_REGULAR, 8)
    cnv.drawString((width - text_width) / 2, top_y, center_text[:90])

    bottom_y = 1.2 * cm
    cnv.setStrokeColor(LIGHT_GRAY)
    cnv.setLineWidth(0.5)
    cnv.line(MARGIN_LEFT, bottom_y + 0.55 * cm, width - MARGIN_RIGHT, bottom_y + 0.55 * cm)

    version = str(meta.get("version") or DOCUMENT_VERSION)
    cnv.setFont(FONT_REGULAR, 7)
    cnv.setFillColor(MID_GRAY)
    cnv.drawString(MARGIN_LEFT, bottom_y, CLASSIFICATION)
    cnv.drawString(MARGIN_LEFT + 3.5 * cm, bottom_y, f"v{version}")

    page_label = f"Page {page_number} / {total_pages}"
    cnv.drawRightString(width - MARGIN_RIGHT, bottom_y, page_label)


def draw_closing_page(cnv: canvas.Canvas, meta: dict[str, Any]) -> None:
    """Dessine la page de clôture."""
    from app.services.pdf.cover import _format_date

    width = PAGE_WIDTH
    height = PAGE_HEIGHT

    cnv.setFillColor(NIGHT_BLUE)
    cnv.setFont(FONT_BOLD, 14)
    cnv.drawCentredString(width / 2, height / 2 + 2 * cm, "Document généré automatiquement")
    cnv.setFont(FONT_BOLD, 12)
    cnv.drawCentredString(width / 2, height / 2 + 1.2 * cm, "par Urban Cyber Architect")

    cnv.setFillColor(MID_GRAY)
    cnv.setFont(FONT_REGULAR, 10)
    date_str = _format_date(meta.get("generated_at"))
    version = str(meta.get("version") or DOCUMENT_VERSION)
    classification = str(meta.get("classification") or CLASSIFICATION)

    lines = [
        f"Date : {date_str}",
        f"Version : {version}",
        f"Classification : {classification}",
        "",
        "À valider par le comité de pilotage",
    ]
    y = height / 2 - 0.5 * cm
    for line in lines:
        cnv.drawCentredString(width / 2, y, line)
        y -= 0.65 * cm

    cnv.setStrokeColor(GOLD)
    cnv.setLineWidth(2)
    cnv.line(width / 2 - 3 * cm, y + 0.3 * cm, width / 2 + 3 * cm, y + 0.3 * cm)
