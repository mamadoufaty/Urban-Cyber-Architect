"""Charte graphique Urban Cyber Architect — PDF V2.1."""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm

# Couleurs
NIGHT_BLUE = colors.HexColor("#0B1426")
GOLD = colors.HexColor("#C9A227")
WHITE = colors.white
LIGHT_GRAY = colors.HexColor("#E8ECF0")
MID_GRAY = colors.HexColor("#94A3B8")
TEXT_DARK = colors.HexColor("#1E293B")
TABLE_ROW_ALT = colors.HexColor("#F4F6F9")

# Typographie
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

# Mise en page
PAGE_SIZE = A4
PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE
MARGIN_LEFT = 2.0 * cm
MARGIN_RIGHT = 2.0 * cm
MARGIN_TOP = 2.6 * cm
MARGIN_BOTTOM = 2.2 * cm
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT

HEADER_HEIGHT = 1.2 * cm
FOOTER_HEIGHT = 1.0 * cm
COVER_BAND_HEIGHT = 2.8 * cm

DOCUMENT_VERSION = "2.1"
CLASSIFICATION = "Confidentiel"
BRAND_NAME = "URBAN CYBER ARCHITECT"
BRAND_SHORT = "Urban Cyber Architect"
