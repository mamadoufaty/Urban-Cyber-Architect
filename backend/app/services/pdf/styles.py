"""Styles ReportLab — charte Urban Cyber Architect."""

from __future__ import annotations

from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

from app.services.pdf.theme import (
    FONT_BOLD,
    FONT_REGULAR,
    GOLD,
    MID_GRAY,
    NIGHT_BLUE,
    TEXT_DARK,
    WHITE,
)


def get_pdf_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "document_title": ParagraphStyle(
            "UCA_DocumentTitle",
            parent=base["Title"],
            fontName=FONT_BOLD,
            fontSize=22,
            leading=28,
            textColor=NIGHT_BLUE,
            spaceAfter=10,
            alignment=TA_LEFT,
        ),
        "chapter": ParagraphStyle(
            "UCA_Chapter",
            parent=base["Heading1"],
            fontName=FONT_BOLD,
            fontSize=14,
            leading=18,
            textColor=NIGHT_BLUE,
            spaceBefore=18,
            spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "UCA_Subtitle",
            parent=base["Heading2"],
            fontName=FONT_BOLD,
            fontSize=11,
            leading=14,
            textColor=GOLD,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "UCA_Body",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=10,
            leading=14,
            textColor=TEXT_DARK,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "UCA_Bullet",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=10,
            leading=13,
            textColor=TEXT_DARK,
            leftIndent=14,
            bulletIndent=0,
            spaceAfter=3,
        ),
        "objective_box": ParagraphStyle(
            "UCA_ObjectiveBox",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=10,
            leading=14,
            textColor=TEXT_DARK,
            backColor=LIGHT_GRAY_BG(),
            borderPadding=10,
            spaceBefore=4,
            spaceAfter=10,
            alignment=TA_JUSTIFY,
        ),
        "recommendation_box": ParagraphStyle(
            "UCA_RecommendationBox",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=10,
            leading=14,
            textColor=TEXT_DARK,
            backColor=GOLD_TINT(),
            borderPadding=10,
            spaceBefore=4,
            spaceAfter=10,
            alignment=TA_JUSTIFY,
        ),
        "cover_logo": ParagraphStyle(
            "UCA_CoverLogo",
            parent=base["Title"],
            fontName=FONT_BOLD,
            fontSize=18,
            leading=22,
            textColor=WHITE,
            alignment=TA_LEFT,
            letterSpacing=2,
        ),
        "cover_meta_label": ParagraphStyle(
            "UCA_CoverMetaLabel",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=9,
            leading=12,
            textColor=MID_GRAY,
            spaceAfter=2,
        ),
        "cover_meta_value": ParagraphStyle(
            "UCA_CoverMetaValue",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=11,
            leading=14,
            textColor=NIGHT_BLUE,
            spaceAfter=10,
        ),
        "closing": ParagraphStyle(
            "UCA_Closing",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=11,
            leading=16,
            textColor=TEXT_DARK,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "table_cell": ParagraphStyle(
            "UCA_TableCell",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=9,
            leading=12,
            textColor=TEXT_DARK,
        ),
        "table_header": ParagraphStyle(
            "UCA_TableHeader",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=9,
            leading=12,
            textColor=WHITE,
        ),
    }


def LIGHT_GRAY_BG():
    from reportlab.lib import colors

    return colors.HexColor("#F1F5F9")


def GOLD_TINT():
    from reportlab.lib import colors

    return colors.HexColor("#FBF6E8")
