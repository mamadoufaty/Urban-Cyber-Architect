"""Page de garde — Urban Cyber Architect."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from app.services.pdf.theme import (
    BRAND_NAME,
    CLASSIFICATION,
    COVER_BAND_HEIGHT,
    DOCUMENT_VERSION,
    FONT_BOLD,
    FONT_REGULAR,
    GOLD,
    MARGIN_LEFT,
    MARGIN_RIGHT,
    NIGHT_BLUE,
    PAGE_HEIGHT,
    PAGE_WIDTH,
    TEXT_DARK,
    WHITE,
)


def _format_date(iso_value: str | None) -> str:
    if not iso_value:
        return datetime.now().strftime("%d/%m/%Y")
    try:
        dt = datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return str(iso_value)[:10]


def draw_cover_page(cnv: canvas.Canvas, meta: dict[str, Any]) -> None:
    """Dessine la page de garde sur le canevas courant."""
    width = PAGE_WIDTH
    height = PAGE_HEIGHT

    # Fond blanc
    cnv.setFillColor(WHITE)
    cnv.rect(0, 0, width, height, fill=1, stroke=0)

    # Bandeau haut bleu nuit
    cnv.setFillColor(NIGHT_BLUE)
    cnv.rect(0, height - COVER_BAND_HEIGHT, width, COVER_BAND_HEIGHT, fill=1, stroke=0)

    # Accent or sous le bandeau
    cnv.setFillColor(GOLD)
    cnv.rect(0, height - COVER_BAND_HEIGHT - 3, width, 3, fill=1, stroke=0)

    # Logo textuel
    cnv.setFillColor(WHITE)
    cnv.setFont(FONT_BOLD, 16)
    cnv.drawString(MARGIN_LEFT, height - COVER_BAND_HEIGHT + 0.95 * cm, BRAND_NAME)

    cnv.setFont(FONT_REGULAR, 8)
    cnv.setFillColor(GOLD)
    cnv.drawString(MARGIN_LEFT, height - COVER_BAND_HEIGHT + 0.45 * cm, "Gouvernance · Urbanisme · Cybersécurité")

    # Titre du livrable
    title_y = height - COVER_BAND_HEIGHT - 3.5 * cm
    cnv.setFillColor(NIGHT_BLUE)
    cnv.setFont(FONT_BOLD, 22)
    title = str(meta.get("title") or "Livrable")
    _draw_wrapped_text(cnv, title, MARGIN_LEFT, title_y, width - MARGIN_LEFT - MARGIN_RIGHT, 26, FONT_BOLD, 22)

    # Ligne or décorative
    line_y = title_y - 2.8 * cm
    cnv.setStrokeColor(GOLD)
    cnv.setLineWidth(2)
    cnv.line(MARGIN_LEFT, line_y, MARGIN_LEFT + 6 * cm, line_y)

    # Métadonnées
    fields = [
        ("Projet", meta.get("project_name") or "—"),
        ("Client", meta.get("client") or "—"),
        ("Version", meta.get("version") or DOCUMENT_VERSION),
        ("Date de génération", _format_date(meta.get("generated_at"))),
        ("Auteur", meta.get("author") or "Urban Cyber Architect"),
        ("Classification", meta.get("classification") or CLASSIFICATION),
    ]
    y = line_y - 1.5 * cm
    label_x = MARGIN_LEFT
    value_x = MARGIN_LEFT + 5.5 * cm
    for label, value in fields:
        cnv.setFillColor(TEXT_DARK)
        cnv.setFont(FONT_BOLD, 9)
        cnv.drawString(label_x, y, f"{label} :")
        cnv.setFont(FONT_REGULAR, 11)
        cnv.drawString(value_x, y, str(value)[:80])
        y -= 0.75 * cm

    # Mention bas de page
    cnv.setFillColor(NIGHT_BLUE)
    cnv.setFont(FONT_REGULAR, 8)
    cnv.drawCentredString(width / 2, 2.5 * cm, "Document généré par Urban Cyber Architect — usage interne")


def _draw_wrapped_text(
    cnv: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    line_height: float,
    font: str,
    size: int,
) -> None:
    words = text.split()
    lines: list[str] = []
    current = ""
    cnv.setFont(font, size)
    for word in words:
        trial = f"{current} {word}".strip()
        if cnv.stringWidth(trial, font, size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    for i, line in enumerate(lines[:3]):
        cnv.drawString(x, y - i * line_height, line)
