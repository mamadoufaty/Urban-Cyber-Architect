"""Tableaux professionnels — Urban Cyber Architect."""

from __future__ import annotations

from typing import Any

from reportlab.platypus import Paragraph, Table, TableStyle

from app.services.pdf.styles import get_pdf_styles
from app.services.pdf.theme import CONTENT_WIDTH, LIGHT_GRAY, NIGHT_BLUE, TABLE_ROW_ALT, WHITE
from app.services.pdf.text_sanitize import escape_pdf_text


def build_professional_table(
    headers: list[str],
    rows: list[list[str]],
    *,
    col_widths: list[float] | None = None,
) -> Table:
    """Construit un tableau avec en-tête bleu nuit et alternance de lignes."""
    styles = get_pdf_styles()
    header_cells = [Paragraph(escape_pdf_text(h), styles["table_header"]) for h in headers]
    data: list[list[Any]] = [header_cells]
    for row in rows:
        data.append([Paragraph(escape_pdf_text(str(c)), styles["table_cell"]) for c in row])

    if col_widths is None:
        n = max(len(headers), 1)
        col_widths = [CONTENT_WIDTH / n] * n

    table = Table(data, colWidths=col_widths, repeatRows=1)
    style_commands: list[tuple] = [
        ("BACKGROUND", (0, 0), (-1, 0), NIGHT_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_commands.append(("BACKGROUND", (0, i), (-1, i), TABLE_ROW_ALT))
    table.setStyle(TableStyle(style_commands))
    return table
