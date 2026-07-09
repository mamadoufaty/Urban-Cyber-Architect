#!/usr/bin/env python3
"""Generate UCA Premium PowerPoint presentation (60–80 slides)."""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

# ── Brand palette (from frontend/src/index.css) ──────────────────────────────
BG = RGBColor(0x0A, 0x0E, 0x17)
SURFACE = RGBColor(0x11, 0x18, 0x27)
SURFACE2 = RGBColor(0x1A, 0x22, 0x34)
BORDER = RGBColor(0x2A, 0x35, 0x48)
TEXT = RGBColor(0xE8, 0xED, 0xF5)
MUTED = RGBColor(0x88, 0x96, 0xAB)
ACCENT = RGBColor(0x00, 0xD4, 0xAA)
ACCENT2 = RGBColor(0x3B, 0x82, 0xF6)
WARNING = RGBColor(0xF5, 0x9E, 0x0B)
DANGER = RGBColor(0xEF, 0x44, 0x44)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "presentations" / "UCA_Presentation_Premium.pptx"


def _rgb(c: RGBColor) -> str:
    return f"{c}"


def _set_bg(slide, color: RGBColor = BG) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_rect(slide, left, top, width, height, fill_color, line_color=None, line_width=0):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(line_width or 1)
    else:
        shape.line.fill.background()
    return shape


def _add_rounded(slide, left, top, width, height, fill_color, text="", font_size=11, bold=False, text_color=TEXT):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.color.rgb = BORDER
    shape.line.width = Pt(1)
    if text:
        tf = shape.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(font_size)
        p.font.bold = bold
        p.font.color.rgb = text_color
        p.alignment = PP_ALIGN.CENTER
    return shape


def _add_text_box(slide, left, top, width, height, text, size=14, color=TEXT, bold=False, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.alignment = align
    return box


def _add_bullets(slide, left, top, width, height, title, bullets, title_size=28, bullet_size=14):
    _add_text_box(slide, left, top, width, Inches(0.6), title, size=title_size, color=WHITE, bold=True)
    _add_rect(slide, left, top + Inches(0.65), Inches(1.2), Inches(0.06), ACCENT)
    box = slide.shapes.add_textbox(left, top + Inches(0.85), width, height - Inches(0.85))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = item
        p.level = 0
        p.font.size = Pt(bullet_size)
        p.font.color.rgb = TEXT
        p.space_after = Pt(8)
    return box


def _add_table_slide(slide, title, headers, rows, left=Inches(0.8), top=Inches(1.5)):
    _add_bullets(slide, left, Inches(0.45), Inches(11.5), Inches(0.9), title, [])
    cols, rs = len(headers), len(rows) + 1
    tbl = slide.shapes.add_table(rs, cols, left, top, Inches(11.5), Inches(0.45 * rs)).table
    for j, h in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = SURFACE2
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(11)
            p.font.color.rgb = ACCENT
    for i, row in enumerate(rows, 1):
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.text = str(val)
            cell.fill.solid()
            cell.fill.fore_color.rgb = SURFACE if i % 2 else BG
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(10)
                p.font.color.rgb = TEXT
    return tbl


def title_slide(prs, title, subtitle="", tagline=""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide)
    _add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(0.12), ACCENT)
    _add_text_box(slide, Inches(0.8), Inches(2.2), Inches(11), Inches(1.2), title, size=44, color=WHITE, bold=True)
    if subtitle:
        _add_text_box(slide, Inches(0.8), Inches(3.5), Inches(11), Inches(0.8), subtitle, size=22, color=ACCENT)
    if tagline:
        _add_text_box(slide, Inches(0.8), Inches(4.4), Inches(11), Inches(0.6), tagline, size=16, color=MUTED)
    _add_text_box(slide, Inches(0.8), Inches(6.5), Inches(5), Inches(0.4), "Urban Cyber Architect", size=12, color=MUTED)
    _add_text_box(slide, Inches(9), Inches(6.5), Inches(4), Inches(0.4), "Présentation Premium — 2025", size=12, color=MUTED, align=PP_ALIGN.RIGHT)


def section_slide(prs, part_num, part_title, subtitle=""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, SURFACE)
    _add_rect(slide, Inches(0), Inches(0), Inches(0.35), SLIDE_H, ACCENT)
    _add_text_box(slide, Inches(1), Inches(2.5), Inches(2), Inches(1), f"PARTIE {part_num}", size=18, color=ACCENT, bold=True)
    _add_text_box(slide, Inches(1), Inches(3.3), Inches(11), Inches(1.2), part_title, size=40, color=WHITE, bold=True)
    if subtitle:
        _add_text_box(slide, Inches(1), Inches(4.5), Inches(10), Inches(0.8), subtitle, size=18, color=MUTED)


def content_slide(prs, title, bullets, subtitle=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide)
    items = bullets if not subtitle else [subtitle] + bullets
    _add_bullets(slide, Inches(0.8), Inches(0.45), Inches(11.5), Inches(6.5), title, items, bullet_size=15 if len(items) <= 6 else 13)


def two_column_slide(prs, title, left_title, left_bullets, right_title, right_bullets):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide)
    _add_bullets(slide, Inches(0.8), Inches(0.45), Inches(11.5), Inches(0.9), title, [])
    _add_rounded(slide, Inches(0.8), Inches(1.4), Inches(5.6), Inches(5.5), SURFACE)
    _add_text_box(slide, Inches(1), Inches(1.55), Inches(5.2), Inches(0.4), left_title, size=16, color=ACCENT, bold=True)
    _add_bullets(slide, Inches(1), Inches(2), Inches(5.2), Inches(4.5), "", left_bullets, title_size=1, bullet_size=12)
    _add_rounded(slide, Inches(6.9), Inches(1.4), Inches(5.6), Inches(5.5), SURFACE)
    _add_text_box(slide, Inches(7.1), Inches(1.55), Inches(5.2), Inches(0.4), right_title, size=16, color=ACCENT2, bold=True)
    _add_bullets(slide, Inches(7.1), Inches(2), Inches(5.2), Inches(4.5), "", right_bullets, title_size=1, bullet_size=12)


def diagram_boxes(prs, title, boxes, arrows=None):
    """boxes: list of (label, x_in, y_in, w_in, h_in, color)"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide)
    _add_bullets(slide, Inches(0.8), Inches(0.45), Inches(11.5), Inches(0.9), title, [])
    for label, x, y, w, h, color in boxes:
        _add_rounded(slide, Inches(x), Inches(y), Inches(w), Inches(h), color, text=label, font_size=10, bold=True)
    if arrows:
        for x1, y1, x2, y2 in arrows:
            conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
            conn.line.color.rgb = ACCENT
            conn.line.width = Pt(2)


def timeline_slide(prs, title, events):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide)
    _add_bullets(slide, Inches(0.8), Inches(0.45), Inches(11.5), Inches(0.9), title, [])
    y = 3.0
    _add_rect(slide, Inches(1), Inches(y), Inches(11), Inches(0.08), ACCENT2)
    n = len(events)
    for i, (year, label) in enumerate(events):
        x = 1 + (10 / max(n - 1, 1)) * i
        _add_rounded(slide, Inches(x - 0.35), Inches(y - 0.15), Inches(0.7), Inches(0.35), ACCENT, text=year, font_size=9, bold=True, text_color=BG)
        _add_text_box(slide, Inches(x - 0.6), Inches(y + 0.35), Inches(1.4), Inches(1.2), label, size=9, color=TEXT, align=PP_ALIGN.CENTER)


def matrix_slide(prs, title, row_labels, col_labels, cells):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide)
    _add_bullets(slide, Inches(0.8), Inches(0.45), Inches(11.5), Inches(0.9), title, [])
    rows = len(row_labels) + 1
    cols = len(col_labels) + 1
    left, top = Inches(1.5), Inches(1.6)
    cw, rh = Inches(1.8), Inches(0.55)
    for j, cl in enumerate(col_labels):
        _add_rounded(slide, left + cw * (j + 1), top, cw, rh, SURFACE2, text=cl, font_size=9, bold=True, text_color=ACCENT)
    for i, rl in enumerate(row_labels):
        _add_rounded(slide, left, top + rh * (i + 1), cw, rh, SURFACE2, text=rl, font_size=9, bold=True, text_color=ACCENT2)
        for j in range(len(col_labels)):
            val = cells[i][j] if i < len(cells) and j < len(cells[i]) else ""
            color = SURFACE
            if val in ("Élevé", "Critique", "Haute"):
                color = DANGER
            elif val in ("Moyen", "Moyenne"):
                color = WARNING
            elif val in ("Faible", "Basse"):
                color = ACCENT
            _add_rounded(slide, left + cw * (j + 1), top + rh * (i + 1), cw, rh, color, text=val, font_size=9)


def layer_slide(prs, layer_name, definition, objectif, contenu, exemples, role, uca_link):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide)
    _add_text_box(slide, Inches(0.8), Inches(0.45), Inches(8), Inches(0.7), f"Couche {layer_name}", size=32, color=WHITE, bold=True)
    _add_rect(slide, Inches(0.8), Inches(1.1), Inches(1.5), Inches(0.06), ACCENT)
    blocks = [
        ("Définition", definition),
        ("Objectif / Mission", objectif),
        ("Contenu", contenu),
        ("Exemples Métropolis", exemples),
        ("Gouvernance", role),
        ("Dans UCA", uca_link),
    ]
    for i, (lbl, txt) in enumerate(blocks):
        col, row = i % 2, i // 2
        x = 0.8 + col * 6.1
        y = 1.4 + row * 1.85
        _add_rounded(slide, Inches(x), Inches(y), Inches(5.8), Inches(1.65), SURFACE)
        _add_text_box(slide, Inches(x + 0.15), Inches(y + 0.1), Inches(5.5), Inches(0.3), lbl, size=11, color=ACCENT, bold=True)
        _add_text_box(slide, Inches(x + 0.15), Inches(y + 0.4), Inches(5.5), Inches(1.1), txt, size=10, color=TEXT)


def referential_slide(prs, name, contexte, objectifs, structure, cas_usage, uca_integration, extra_bullets=None):
    bullets = [
        f"Contexte : {contexte}",
        f"Objectifs : {objectifs}",
        f"Structure : {structure}",
        f"Cas d'usage : {cas_usage}",
        f"Intégration UCA : {uca_integration}",
    ]
    if extra_bullets:
        bullets.extend(extra_bullets)
    content_slide(prs, name, bullets)


def build_presentation() -> Presentation:
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    # ══════════════════════════════════════════════════════════════════════════
    # PARTIE 1 — PRÉSENTATION GÉNÉRALE
    # ══════════════════════════════════════════════════════════════════════════
    title_slide(
        prs,
        "Urban Cyber Architect",
        "Plateforme intégrée de cybersécurité & urbanisme SI",
        "Gouverner · Cartographier · Évaluer · Piloter · Livrer",
    )

    section_slide(prs, 1, "Présentation générale", "Vision, valeur métier et positionnement")

    content_slide(
        prs,
        "Vision",
        [
            "Unifier urbanisme SI, analyse de risques EBIOS RM et gouvernance SSI dans une plateforme unique",
            "Passer de la conformité documentaire à la pilotage opérationnel des risques cyber",
            "Capitaliser la connaissance organisationnelle dans un graphe de connaissances exploitable",
            "Accompagner RSSI, DSI, métiers et COMEX avec des livrables prêts à l'emploi",
            "Industrialiser la chaîne : cartographie → risques → traitement → SOC → reporting",
        ],
    )

    content_slide(
        prs,
        "Objectifs stratégiques",
        [
            "Réduire le time-to-value des études EBIOS RM de plusieurs semaines à quelques jours",
            "Maintenir une cartographie SI vivante, versionnée et alignée sur le terrain",
            "Automatiser la production de PSSI, registre des risques, PTR et synthèses COMEX",
            "Corréler les risques théoriques (GRC) avec les alertes opérationnelles (SOC/Wazuh)",
            "Démontrer la conformité ISO 27001, NIS2, DORA et recommandations ANSSI",
        ],
    )

    content_slide(
        prs,
        "Valeur métier",
        [
            "Vision 360° du SI : organisation, métiers, processus, applications, infra, flux",
            "Décisions éclairées : heatmaps, KPIs RSSI, priorisation budgétaire des mesures",
            "Traçabilité complète : historique des versions, validations, justifications EBIOS",
            "Réduction des silos entre urbanisme, sécurité, conformité et exploitation",
            "ROI mesurable : moins de ressaisie, moins d'ateliers répétitifs, livrables instantanés",
        ],
    )

    content_slide(
        prs,
        "Problématique",
        [
            "Cartographies Excel obsolètes, non partagées, sans lien avec l'analyse de risques",
            "Études EBIOS longues, peu capitalisées, déconnectées du SI réel",
            "Registres de risques et PTR maintenus manuellement, hors synchronisation",
            "SOC et GRC en silos : alertes Wazuh sans contexte métier ni actif cartographié",
            "Pression réglementaire croissante : NIS2, DORA, ISO 27001, ANSSI collectivités",
        ],
    )

    two_column_slide(
        prs,
        "Cas d'usage",
        "Secteur public",
        [
            "Métropoles et collectivités (NIS2, ANSSI)",
            "Opérateurs de services essentiels",
            "Administrations et établissements publics",
            "Centres de supervision urbaine (CSU)",
        ],
        "Secteur privé",
        [
            "Industrie et OT/IT (EBIOS, PCA/PRA)",
            "Services financiers (DORA, ISO 27001)",
            "SSII et infogéreurs (multi-clients)",
            "Cabinets de conseil en cybersécurité",
        ],
    )

    content_slide(
        prs,
        "Public cible",
        [
            "COMEX / CODIR — synthèses exécutives, arbitrages budgétaires, vision stratégique",
            "RSSI / CISO — pilotage des risques, EBIOS, PSSI, conformité, SOC",
            "DSI / DNum — urbanisme SI, cartographie, architecture, projets",
            "DPO / Conformité — RGPD, NIS2, traçabilité des traitements",
            "Consultants & auditeurs — méthodologie structurée, livrables standardisés",
        ],
    )

    content_slide(
        prs,
        "Positionnement produit",
        [
            "Ni un simple outil de cartographie, ni un SIEM isolé",
            "Plateforme GRC augmentée par l'urbanisme SI et l'IA",
            "Méthodologie EBIOS RM native, pas un module générique",
            "Connecteur SOC Wazuh intégré pour corrélation risque ↔ alerte",
            "Comparable aux offres cabinet (Wavestone, Deloitte) mais industrialisée et outillée",
        ],
    )

    # ══════════════════════════════════════════════════════════════════════════
    # PARTIE 2 — ARCHITECTURE TECHNIQUE
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, 2, "Architecture technique", "Stack, composants et intégrations")

    diagram_boxes(
        prs,
        "Architecture globale Urban Cyber Architect",
        [
            ("React 19\nFrontend SPA", 0.8, 1.5, 2.2, 1.0, SURFACE2),
            ("FastAPI\nBackend REST", 3.5, 1.5, 2.2, 1.0, SURFACE2),
            ("SQLite / PostgreSQL\nBase de données", 6.2, 1.5, 2.5, 1.0, SURFACE2),
            ("Moteur Urbanisme\nLayout & Import", 0.8, 3.2, 2.5, 1.0, ACCENT),
            ("EBIOS RM Engine\n5 Ateliers", 3.8, 3.2, 2.5, 1.0, ACCENT),
            ("IA / Copilot RSSI\nRecommandations", 7.0, 3.2, 2.5, 1.0, ACCENT2),
            ("GRC & Livrables\nPSSI · PTR · SoA", 0.8, 5.0, 2.5, 1.0, SURFACE),
            ("SOC / Wazuh\nConnecteur alertes", 3.8, 5.0, 2.5, 1.0, SURFACE),
            ("Knowledge Graph\nCapitalisation", 7.0, 5.0, 2.5, 1.0, SURFACE),
        ],
        [(3.0, 2.0, 3.5, 2.0), (5.7, 2.0, 6.2, 2.0)],
    )

    content_slide(
        prs,
        "Frontend — React 19 + TypeScript",
        [
            "SPA moderne : navigation par modules (Urbanisme, EBIOS, GRC, SOC, Admin)",
            "Visualisation graphique Club Urba : couches, zones, entités, relations",
            "Composants métier : ateliers EBIOS, heatmaps, dashboards RSSI, livrables",
            "Gestion des permissions par rôle (RSSI, consultant, admin, lecteur)",
            "Déploiement Vercel / conteneur, thème sombre professionnel",
        ],
    )

    content_slide(
        prs,
        "Backend — FastAPI + Python",
        [
            "API REST structurée par domaines : auth, urbanism, cartography, ebios, admin",
            "Services métier découplés : import Excel, moteur urbanisme, générateurs EBIOS",
            "ORM SQLAlchemy, migrations, isolation multi-projets",
            "CLI d'administration : bootstrap admin, seed démo Métropolis",
            "Tests automatisés : 230+ tests backend, couverture des workflows critiques",
        ],
    )

    content_slide(
        prs,
        "API & Intégrations",
        [
            "Authentification JWT, gestion utilisateurs et rôles",
            "Import/export cartographie Excel (template Club Urba V1.4)",
            "Endpoints EBIOS : ateliers 1 à 5, propositions IA, validation/rejet",
            "Livrables : rapport complet, registre, PTR, synthèse COMEX",
            "Connecteur Wazuh : corrélation alertes ↔ actifs cartographiés",
        ],
    )

    content_slide(
        prs,
        "Base de données",
        [
            "Modèle relationnel : projets, entités urbanisme, cartographies versionnées",
            "Référentiels : ISO 27001/02, NIST CSF, CIS, DORA, NIS2, ANSSI",
            "EBIOS : événements redoutés, sources de risque, scénarios, mesures",
            "GRC : risques, traitements, SoA, documents générés",
            "SQLite (dev) / PostgreSQL (production)",
        ],
    )

    content_slide(
        prs,
        "Moteur IA & Copilot RSSI",
        [
            "Génération assistée : sources de risque, scénarios stratégiques, mesures de sécurité",
            "Justifications contextuelles basées sur la cartographie active",
            "Score de confiance et workflow proposer → valider → rejeter",
            "Copilot RSSI : recommandations alignées référentiels (ISO, CIS, ANSSI)",
            "Roadmap : prédiction des risques, jumeau numérique, agent autonome",
        ],
    )

    content_slide(
        prs,
        "Moteur Urbanisme SI",
        [
            "Import Excel multi-feuilles : entités, relations, métadonnées par couche",
            "Layout automatique : positionnement graphique, zones Club Urba",
            "Déduplication, validation, fusion de cartographies",
            "Versioning : brouillon → publiée → archivée, historique complet",
            "Alimentation directe des ateliers EBIOS (actifs, parties prenantes)",
        ],
    )

    content_slide(
        prs,
        "EBIOS RM — Moteur méthodologique",
        [
            "5 ateliers implémentés : cadrage, sources, scénarios, impacts, mesures",
            "Génération automatique à partir de la cartographie validée",
            "Lien bidirectionnel urbanisme ↔ risques ↔ mesures",
            "Progression calculée, blocage si prérequis non validés",
            "Livrables réglementaires générés à la demande",
        ],
    )

    two_column_slide(
        prs,
        "SOC & Wazuh",
        "Supervision opérationnelle",
        [
            "Collecte alertes Wazuh (agents, règles, corrélation)",
            "Mapping alerte → actif cartographié",
            "MTTD, tendances, criticité",
            "Pont GRC ↔ opérationnel",
        ],
        "Valeur ajoutée UCA",
        [
            "Contexte métier sur chaque alerte",
            "Priorisation selon registre des risques",
            "Remontée COMEX : risque théorique vs réel",
            "Boucle fermée détection → traitement",
        ],
    )

    content_slide(
        prs,
        "GRC & Livrables",
        [
            "PSSI générée depuis cartographie et référentiels",
            "Registre des risques synchronisé avec EBIOS atelier 4",
            "Plan de traitement des risques (PTR) avec priorités et budgets",
            "Déclaration d'applicabilité (SoA) ISO 27001",
            "4 livrables EBIOS : rapport, registre, PTR, synthèse exécutive COMEX",
        ],
    )

    # ══════════════════════════════════════════════════════════════════════════
    # PARTIE 3 — URBANISME SI
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, 3, "Urbanisme SI", "Cartographie multi-couches et gouvernance du SI")

    content_slide(
        prs,
        "Qu'est-ce que l'urbanisme SI ?",
        [
            "Discipline de gouvernance alignant le SI sur la stratégie de l'organisation",
            "Représentation structurée du SI en couches : du métier à l'infrastructure",
            "Outil de dialogue entre DSI, métiers, RSSI, architecture et prestataires",
            "Fondation indispensable pour EBIOS RM, PCA/PRA, audits et projets de transformation",
            "Urban Cyber Architect implémente le référentiel Club Urba",
        ],
    )

    content_slide(
        prs,
        "Pourquoi une cartographie est indispensable",
        [
            "Sans cartographie : analyse de risques sur des hypothèses, pas sur le réel",
            "Identification des actifs supports et biens essentiels (EBIOS atelier 1)",
            "Visualisation des dépendances critiques (cascade de pannes)",
            "Support de décision pour investissements, obsolescence, cloud, externalisation",
            "Base documentaire pour NIS2, ISO 27001, ANSSI et audits",
        ],
    )

    diagram_boxes(
        prs,
        "Les 7 couches de la cartographie Club Urba",
        [
            ("Organisation", 5.5, 1.3, 2.2, 0.7, ACCENT),
            ("Métier", 5.5, 2.2, 2.2, 0.7, ACCENT),
            ("Processus", 5.5, 3.1, 2.2, 0.7, ACCENT),
            ("Fonctionnel", 5.5, 4.0, 2.2, 0.7, ACCENT2),
            ("Applicatif", 5.5, 4.9, 2.2, 0.7, ACCENT2),
            ("Technique", 5.5, 5.8, 2.2, 0.7, ACCENT2),
            ("Flux", 2.0, 3.5, 2.2, 0.7, WARNING),
        ],
    )

    layer_slide(
        prs,
        "Organisation",
        "Structure hiérarchique, rôles, responsabilités et instances de gouvernance.",
        "Clarifier qui décide, qui opère, qui contrôle le SI.",
        "Directions, pôles, services, rôles (RSSI, DPO, DSI), comités.",
        "Métropole Métropolis : DG, DNum, Pôle SSI, directions métiers (mobilité, eau).",
        "Alimente les parties prenantes EBIOS et la chaîne de responsabilité.",
        "Import Excel + visualisation ; lien vers stakeholders EBIOS W1.",
    )

    layer_slide(
        prs,
        "Métier",
        "Activités et capacités métier de l'organisation, indépendantes du SI.",
        "Exprimer les besoins métiers et la valeur délivrée aux usagers.",
        "Domaines métier, capacités, objectifs stratégiques, indicateurs.",
        "Métropolis : mobilité, eau/assainissement, énergie, sécurité publique, open data.",
        "Justifie les investissements SI et priorise les biens essentiels.",
        "Couleur #00d4aa ; mapping vers événements redoutés EBIOS.",
    )

    layer_slide(
        prs,
        "Processus",
        "Enchaînements d'activités métier créant de la valeur (chaîne de valeur).",
        "Modéliser les flux métier pour identifier points de fragilité.",
        "Processus bout-en-bout, activités, acteurs, entrées/sorties.",
        "Gestion crise CSU, traitement demandes citoyennes, exploitation SCADA eau.",
        "Base pour scénarios opérationnels et continuité d'activité (PCA).",
        "Relations processus ↔ applications ↔ données dans le graphe.",
    )

    layer_slide(
        prs,
        "Fonctionnel",
        "Services fonctionnels transverses offerts par le SI aux métiers.",
        "Décrire QUOI le SI doit faire, sans préciser QUELLE application.",
        "Fonctions : authentification, notification, cartographie, reporting, supervision.",
        "IAM métropolitain, portail citoyen, API open data, supervision SCADA.",
        "Interface entre besoins métier et solutions applicatives.",
        "Entités fonctionnelles liées aux applications et aux flux.",
    )

    layer_slide(
        prs,
        "Applicatif",
        "Applications, logiciels, modules et leurs interrelations.",
        "Inventorier le parc applicatif et les dépendances logicielles.",
        "Applications métier, SaaS, ERP, SCADA, GED, CRM, API.",
        "Portail citoyen, SIEM Wazuh, SCADA eau, GMAO énergie, vidéoprotection.",
        "Cible des vulnérabilités, obsolescence, DORA tests de résilience.",
        "Import multi-feuilles ; relations ; alimentation actifs supports EBIOS.",
    )

    layer_slide(
        prs,
        "Technique",
        "Infrastructure physique et virtuelle hébergeant les applications.",
        "Documenter l'hébergement, les réseaux, le stockage, le cloud.",
        "Serveurs, VM, conteneurs, cloud IaaS/PaaS, BDD, stockage, réseaux, OT.",
        "Datacenter Métropolis, site PRA, fibre métropolitaine, automates SCADA.",
        "Support des analyses de résilience, PRA, segmentation ANSSI.",
        "Cartographie technique liée aux actifs supports et flux réseau.",
    )

    layer_slide(
        prs,
        "Flux",
        "Échanges de données et d'informations entre composants du SI.",
        "Identifier les flux critiques, les protocoles, les points de contrôle.",
        "Flux applicatifs (API REST), techniques (MQTT SCADA), métiers (éditiques).",
        "Flux vidéo CSU → stockage, portail → SI métier, SCADA → supervision.",
        "Analyse des flux = surface d'attaque, segmentation, surveillance SOC.",
        "Visualisation graphique des edges ; corrélation alertes Wazuh par flux.",
    )

    content_slide(
        prs,
        "Cartographie — Versioning",
        [
            "Cycle de vie : brouillon → en revue → publiée → archivée",
            "Numéro de version sémantique (v1.0, v1.1…)",
            "Une seule cartographie active par projet à la fois",
            "Historique des modifications et auteurs",
            "Comparaison inter-versions (roadmap)",
        ],
    )

    content_slide(
        prs,
        "Cartographie — Import Excel",
        [
            "Template Club Urba V1.4 : une feuille par type d'entité",
            "Validation structurelle avant import (colonnes, types, relations)",
            "Journal d'import détaillé : créées, mises à jour, erreurs",
            "Support CSV et XLSX, encodage UTF-8",
            "Projet fil rouge Métropolis : 680 000 habitants, 5 métiers",
        ],
    )

    content_slide(
        prs,
        "Cartographie — Visualisation & Gouvernance",
        [
            "Vue graphique interactive : zoom, filtres par couche, recherche",
            "Layout automatique Club Urba avec zones colorées",
            "Fusion de cartographies, déduplication intelligente",
            "Workflow de validation avant publication",
            "Bannière d'état : cartographie active, version, date de publication",
        ],
    )

    # ══════════════════════════════════════════════════════════════════════════
    # PARTIE 4 — RÉFÉRENTIELS
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, 4, "Référentiels", "Normes, méthodes et cadres réglementaires")

    referential_slide(
        prs,
        "ISO 27001 — Contexte & SMSI",
        "Norme internationale de management de la sécurité de l'information (2022).",
        "Établir, implémenter, maintenir et améliorer un SMSI.",
        "Clauses 4 à 10 (contexte, leadership, planification, support, opération, évaluation, amélioration).",
        "Certification organisation, audits, marchés publics exigeant ISO 27001.",
        "UCA : référentiel intégré, SoA, lien contrôles ↔ risques ↔ mesures EBIOS.",
        ["Annexe A : 93 contrôles de sécurité", "Cycle PDCA : Plan → Do → Check → Act"],
    )

    referential_slide(
        prs,
        "ISO 27002 — Contrôles de sécurité",
        "Catalogue de 93 mesures de sécurité organisées en 4 thèmes (2022).",
        "Guider la sélection et l'implémentation des contrôles Annexe A.",
        "4 thèmes : Organisationnel (37), Personnel (8), Physique (14), Technologique (34).",
        "Matrice contrôle ↔ risque ↔ mesure dans le PTR.",
        "UCA : base des recommandations atelier 5 et génération PSSI.",
    )

    referential_slide(
        prs,
        "ISO 27005 — Gestion des risques",
        "Guide ISO pour la gestion des risques de sécurité de l'information.",
        "Identifier, analyser, évaluer, traiter et surveiller les risques.",
        "Processus en 5 étapes : contexte, identification, analyse, évaluation, traitement.",
        "Complémentaire à EBIOS RM (méthode française plus opérationnelle).",
        "UCA : registre des risques, heatmap, échelles d'impact/vraisemblance.",
    )

    content_slide(
        prs,
        "EBIOS RM — Historique & objectifs",
        [
            "EBIOS Risk Manager : méthode ANSSI (2018, v1.1) d'analyse des risques cyber",
            "Remplace EBIOS 2010 ; alignée ISO 27005 et doctrine ANSSI",
            "Objectif : identifier et traiter les risques cyber sur les biens essentiels",
            "Approche par ateliers collaboratifs avec parties prenantes",
            "Urban Cyber Architect : implémentation complète des 5 ateliers",
        ],
    )

    diagram_boxes(
        prs,
        "EBIOS RM — Les 5 ateliers",
        [
            ("Atelier 1\nCadrage &\nÉvénements redoutés", 0.8, 2.0, 2.0, 1.2, ACCENT),
            ("Atelier 2\nSources de\nrisque", 3.2, 2.0, 2.0, 1.2, ACCENT),
            ("Atelier 3\nScénarios\nstratégiques", 5.6, 2.0, 2.0, 1.2, ACCENT),
            ("Atelier 4\nScénarios\nopérationnels", 8.0, 2.0, 2.0, 1.2, ACCENT2),
            ("Atelier 5\nMesures de\nsécurité", 10.4, 2.0, 2.0, 1.2, ACCENT2),
        ],
        [(2.8, 2.6, 3.2, 2.6), (5.2, 2.6, 5.6, 2.6), (7.6, 2.6, 8.0, 2.6), (10.0, 2.6, 10.4, 2.6)],
    )

    content_slide(
        prs,
        "EBIOS — Atelier 1 : Cadrage",
        [
            "Définir le périmètre, les valeurs métier, les biens essentiels",
            "Identifier les événements redoutés (impact métier unacceptable)",
            "Parties prenantes : résolues depuis la cartographie organisation",
            "Documents de référence : PSSI, politiques, contrats",
            "UCA : générateur automatique depuis cartographie + contexte projet",
        ],
    )

    content_slide(
        prs,
        "EBIOS — Atelier 2 : Sources de risque",
        [
            "Identifier les sources de risque par événement redouté",
            "Couples source/cible : acteurs, vulnérabilités, menaces",
            "Génération IA contextuelle avec justifications et score de confiance",
            "Validation/rejet par le consultant RSSI",
            "UCA : résolution automatique des actifs depuis la cartographie active",
        ],
    )

    content_slide(
        prs,
        "EBIOS — Atelier 3 : Scénarios stratégiques",
        [
            "Enchaînements source → vulnérabilité → impact stratégique",
            "Scénarios motivés par les événements redoutés validés",
            "Propositions IA avec justification et niveau de confiance",
            "Workflow proposer → valider → rejeter",
            "UCA : générateur connecté aux W1/W2 validés + cartographie",
        ],
    )

    content_slide(
        prs,
        "EBIOS — Atelier 4 : Scénarios opérationnels",
        [
            "Déclinaison opérationnelle des scénarios stratégiques validés",
            "Évaluation des impacts : confidentialité, intégrité, disponibilité, traçabilité",
            "Grille impact × vraisemblance → niveau de risque brut",
            "Identification des actifs supports et biens essentiels impactés",
            "UCA : alimentation directe du registre des risques et de la heatmap",
        ],
    )

    content_slide(
        prs,
        "EBIOS — Atelier 5 : Mesures de sécurité",
        [
            "Sélection des mesures pour traiter les risques identifiés",
            "Référentiels de conformité : ISO 27002, CIS Controls, ANSSI",
            "Estimation coût/bénéfice, priorisation automatique, échéances",
            "Lien mesure ↔ risque ↔ contrôle SoA",
            "UCA : génération PTR, bannière exécutive, recommandations IA",
        ],
    )

    content_slide(
        prs,
        "EBIOS — Workflow & intégration UCA",
        [
            "Progression globale calculée : prérequis atelier N avant N+1",
            "Workflow universel : générer → proposer → valider / rejeter",
            "Justifications IA ancrées sur la cartographie active",
            "Livrables automatiques si étude complète (sinon avertissements)",
            "Traçabilité complète pour audit et soutenance",
        ],
    )

    referential_slide(
        prs,
        "NIST Cybersecurity Framework (CSF)",
        "Cadre américain de référence pour la cybersécurité (v2.0, 2024).",
        "Organiser et améliorer la posture de sécurité de l'organisation.",
        "6 fonctions : Govern, Identify, Protect, Detect, Respond, Recover.",
        "Profils CSF, tiers de mise en œuvre, communication inter-parties.",
        "UCA : mapping modules vers fonctions NIST, dashboard de couverture.",
        ["Govern : gouvernance et stratégie", "Identify : cartographie et actifs", "Detect/Respond : SOC Wazuh"],
    )

    referential_slide(
        prs,
        "CIS Controls v8",
        "18 mesures de sécurité prioritaires, ordonnées par efficacité.",
        "Prioriser les actions à fort impact avec ressources limitées.",
        "18 contrôles en 3 groupes : Basique (1-6), Fondamental (7-16), Organisationnel (17-18).",
        "Benchmark de maturité, recommandations opérationnelles.",
        "UCA : référentiel des recommandations atelier 5, tags par mesure.",
    )

    referential_slide(
        prs,
        "DORA — Digital Operational Resilience Act",
        "Règlement UE 2022/2554 pour le secteur financier (applicable depuis 2025).",
        "Renforcer la résilience opérationnelle numérique des entités financières.",
        "5 piliers : gouvernance ICT, gestion risques ICT, incidents, tests, tiers.",
        "Établissements financiers, prestataires ICT critiques (TPPRM).",
        "UCA : registre des risques ICT, tests de résilience, cartographie des tiers.",
        ["Reporting incidents aux autorités", "Tests TLPT périodiques"],
    )

    referential_slide(
        prs,
        "NIS2 — Directive européenne",
        "Directive (UE) 2022/2555 renforçant la cybersécurité des OSE/OIV.",
        "Harmoniser le niveau de cybersécurité en Europe, sanctions dissuasives.",
        "Mesures : analyse de risques, gestion incidents, supply chain, chiffrement.",
        "Métropolis = opérateur de services essentiels : obligations renforcées.",
        "UCA : EBIOS + cartographie + SOC + registre = dossier de conformité NIS2.",
        ["Sanctions : jusqu'à 10 M€ ou 2% CA mondial", "Notification incidents < 24h"],
    )

    referential_slide(
        prs,
        "ANSSI — Doctrine & Guides",
        "Agence nationale de la sécurité des systèmes d'information (France).",
        "Définir la doctrine française de cybersécurité.",
        "EBIOS RM, guides PSSI, architecture SSI, recommandations collectivités.",
        "Classification, habilitation, réaction aux incidents.",
        "UCA : méthode EBIOS native, modèles PSSI ANSSI, référentiel intégré.",
        ["Guide d'hygiène informatique", "Recommandations pour les collectivités"],
    )

    # ══════════════════════════════════════════════════════════════════════════
    # PARTIE 5 — GOUVERNANCE SSI
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, 5, "Gouvernance SSI", "Modules GRC et pilotage des risques")

    content_slide(
        prs,
        "PSSI — Politique de Sécurité SI",
        [
            "Document fondateur définissant les règles de sécurité de l'organisation",
            "Structure : gouvernance, classification, contrôle d'accès, incidents, continuité",
            "Cycle de vie : rédaction → validation COMEX → diffusion → révision annuelle",
            "UCA : génération assistée depuis cartographie, référentiels et contexte projet",
            "Chapitres alignés ISO 27001 et recommandations ANSSI collectivités",
        ],
    )

    content_slide(
        prs,
        "Cartographie des risques",
        [
            "Représentation visuelle des risques par impact et vraisemblance",
            "Heatmap interactive : zones critique / élevée / modérée / faible",
            "Construction depuis les scénarios EBIOS atelier 4 validés",
            "Filtrage par domaine métier, actif, source de risque",
            "Support de décision pour le comité cyber et le COMEX",
        ],
    )

    matrix_slide(
        prs,
        "Heatmap des risques — Exemple Métropolis",
        ["Faible", "Moyen", "Élevé", "Critique"],
        ["Rare", "Peu probable", "Probable", "Quasi-certain"],
        [
            ["Faible", "Faible", "Moyen", "Élevé"],
            ["Faible", "Moyen", "Élevé", "Critique"],
            ["Moyen", "Élevé", "Critique", "Critique"],
            ["Élevé", "Critique", "Critique", "Critique"],
        ],
    )

    content_slide(
        prs,
        "Registre des risques",
        [
            "Inventaire structuré de tous les risques identifiés",
            "Champs : ID, scénario, actif, impact, vraisemblance, niveau, statut, propriétaire",
            "Cycle de vie : identifié → évalué → en traitement → accepté/résiduel → clôturé",
            "Synchronisation automatique avec EBIOS ateliers 3-4",
            "Export livrable réglementaire (EBIOS deliverable)",
        ],
    )

    content_slide(
        prs,
        "Plan de traitement des risques (PTR)",
        [
            "Décisions : réduire, transférer, accepter, éviter",
            "Mesures de sécurité avec échéances, responsables, budgets",
            "Priorisation automatique selon criticité et coût",
            "Pilotage : % avancement, mesures en retard, budget consommé",
            "UCA : généré depuis EBIOS atelier 5 + enrichissement manuel",
        ],
    )

    content_slide(
        prs,
        "Déclaration d'applicabilité (SoA)",
        [
            "Document ISO 27001 listant les 93 contrôles Annexe A",
            "Pour chaque contrôle : applicable/non applicable, justification, statut",
            "Lien direct avec les mesures du PTR et les risques du registre",
            "Support d'audit de certification ISO 27001",
            "UCA : génération et mise à jour depuis les mesures validées",
        ],
    )

    two_column_slide(
        prs,
        "PCA & PRA",
        "Plan de Continuité d'Activité (PCA)",
        [
            "Maintenir les activités critiques en cas de crise",
            "Scénarios : cyberattaque, sinistre, pandémie",
            "BIA : analyse d'impact sur les métiers",
            "UCA : lien processus ↔ applications critiques",
        ],
        "Plan de Reprise d'Activité (PRA)",
        [
            "Restaurer le SI dans des délais définis (RTO/RPO)",
            "Scénarios : perte datacenter, ransomware",
            "Basé sur la cartographie technique",
            "UCA : actifs supports, dépendances, site PRA Métropolis",
        ],
    )

    # ══════════════════════════════════════════════════════════════════════════
    # PARTIE 6 — MODULES UCA
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, 6, "Modules Urban Cyber Architect", "Tour d'horizon fonctionnel")

    modules = [
        ("Urbanisme SI", "Cartographie multi-couches, import Excel, visualisation Club Urba, versioning"),
        ("EBIOS RM", "5 ateliers complets, IA générative, validation workflow, progression"),
        ("Référentiels", "ISO 27001/02/05, NIST CSF, CIS, DORA, NIS2, ANSSI — base normative"),
        ("PSSI", "Génération assistée, chapitres structurés, alignement ANSSI"),
        ("Cartographie des risques", "Heatmap interactive, filtres, export"),
        ("Registre des risques", "Synchronisé EBIOS, cycle de vie, propriétaires"),
        ("PTR", "Mesures, priorités, budgets, pilotage avancement"),
        ("Dashboard RSSI", "KPIs, progression EBIOS, alertes SOC, synthèse COMEX"),
        ("Livrables", "Rapport EBIOS, registre, PTR, synthèse exécutive HTML/PDF"),
        ("SOC / Wazuh", "Connecteur alertes, corrélation actifs, tendances MTTD"),
        ("IA / Knowledge Graph", "Génération contextuelle, capitalisation, Copilot RSSI"),
    ]
    for i in range(0, len(modules), 2):
        pair = modules[i : i + 2]
        if len(pair) == 2:
            two_column_slide(prs, "Modules UCA", pair[0][0], [pair[0][1]], pair[1][0], [pair[1][1]])
        else:
            content_slide(prs, "Modules UCA", [f"{pair[0][0]} : {pair[0][1]}"])

    content_slide(
        prs,
        "Dashboard RSSI — Vue exécutive",
        [
            "KPIs : risques critiques, progression EBIOS, mesures en retard",
            "Synthèse par domaine métier et par référentiel",
            "Alertes SOC récentes corrélées aux actifs cartographiés",
            "Prochaines actions recommandées (Copilot RSSI)",
            "Exportable en synthèse COMEX (1 page exécutive)",
        ],
    )

    # ══════════════════════════════════════════════════════════════════════════
    # PARTIE 7 — DÉMONSTRATION
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, 7, "Démonstration", "Scénario fil rouge Métropolis")

    diagram_boxes(
        prs,
        "Scénario complet — Projet Métropolis",
        [
            ("1. Créer\nprojet", 0.5, 2.5, 1.5, 0.9, SURFACE2),
            ("2. Import\nExcel", 2.3, 2.5, 1.5, 0.9, SURFACE2),
            ("3. Urbanisme\n& validation", 4.1, 2.5, 1.5, 0.9, ACCENT),
            ("4. EBIOS\n5 ateliers", 5.9, 2.5, 1.5, 0.9, ACCENT),
            ("5. Registre\n& PTR", 7.7, 2.5, 1.5, 0.9, ACCENT2),
            ("6. Dashboard\nRSSI", 9.5, 2.5, 1.5, 0.9, ACCENT2),
            ("7. Livrables\nCOMEX", 11.3, 2.5, 1.5, 0.9, WARNING),
        ],
        [(2.0, 2.9, 2.3, 2.9), (3.8, 2.9, 4.1, 2.9), (5.6, 2.9, 5.9, 2.9), (7.4, 2.9, 7.7, 2.9), (9.2, 2.9, 9.5, 2.9), (11.0, 2.9, 11.3, 2.9)],
    )

    content_slide(
        prs,
        "Étape 1-2 : Projet & Import",
        [
            "Création du projet « Métropolis – Sécurité publique & Services numériques »",
            "Paramétrage : 680 000 habitants, 5 métiers, 6 objectifs stratégiques",
            "Import du fichier Excel Club Urba V1.4 (42 communes, SCADA, CSU)",
            "Validation : 200+ entités, relations, 7 couches renseignées",
            "Publication de la cartographie v1.0",
        ],
    )

    content_slide(
        prs,
        "Étape 3-4 : Urbanisme & EBIOS",
        [
            "Visualisation graphique : zones métier, applications, flux SCADA",
            "Lancement EBIOS : atelier 1 — 8 événements redoutés générés",
            "Atelier 2 : sources de risque IA avec justifications contextuelles",
            "Atelier 3 : scénarios stratégiques (ransomware IT→OT, fuite vidéo)",
            "Validation par le RSSI à chaque étape",
        ],
    )

    content_slide(
        prs,
        "Étape 5-7 : GRC, SOC & Livrables",
        [
            "Registre des risques : 24 risques évalués, 6 critiques",
            "PTR : 45 mesures priorisées, budget 1,8 M€ sur 3 ans",
            "Dashboard RSSI : heatmap, KPIs, alertes Wazuh corrélées",
            "Génération des 4 livrables EBIOS (rapport, registre, PTR, synthèse COMEX)",
            "Boucle fermée : alerte SOC → risque cartographié → mesure PTR",
        ],
    )

    # ══════════════════════════════════════════════════════════════════════════
    # PARTIE 8 — ROADMAP
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, 8, "Roadmap", "Évolutions V1 → V2 → V3")

    timeline_slide(
        prs,
        "Feuille de route produit",
        [
            ("V1\n2025", "Urbanisme\nEBIOS 5 ateliers\nGRC de base\nSOC Wazuh"),
            ("V2\n2026", "Copilot RSSI\nKnowledge Graph\nExport PDF/DOCX\nMulti-tenant"),
            ("V3\n2027", "Agent IA autonome\nPrédiction risques\nJumeau numérique\nTPRM DORA"),
        ],
    )

    content_slide(
        prs,
        "V1 — Fondations (actuel)",
        [
            "Cartographie Club Urba complète avec import Excel et versioning",
            "EBIOS RM 5 ateliers avec génération IA et workflow de validation",
            "GRC : PSSI, registre, PTR, SoA, heatmap",
            "Livrables EBIOS : rapport, registre, PTR, synthèse COMEX",
            "Connecteur SOC Wazuh, dashboard RSSI",
        ],
    )

    content_slide(
        prs,
        "V2 & V3 — Ambition",
        [
            "V2 : Copilot RSSI conversationnel, Knowledge Graph complet",
            "V2 : Exports PDF/DOCX/XLSX, intégration SIEM multi-sources",
            "V3 : Agent IA autonome de veille et recommandation",
            "V3 : Prédiction des risques par ML sur historique SOC + GRC",
            "V3 : Jumeau numérique du SI pour simulation de scénarios cyber",
        ],
    )

    # ══════════════════════════════════════════════════════════════════════════
    # PARTIE 9 — CONCLUSION
    # ══════════════════════════════════════════════════════════════════════════
    section_slide(prs, 9, "Conclusion", "Valeur, ROI et vision long terme")

    content_slide(
        prs,
        "Valeur métier & ROI",
        [
            "Réduction de 60-70% du temps d'une étude EBIOS complète",
            "Élimination de la double saisie cartographie → analyse de risques",
            "Livrables COMEX en un clic vs. plusieurs jours de rédaction",
            "Conformité NIS2/DORA/ISO démontrable à tout instant",
            "ROI estimé : retour sur investissement < 12 mois pour une métropole",
        ],
    )

    content_slide(
        prs,
        "Différenciateurs",
        [
            "Seule plateforme intégrant urbanisme SI + EBIOS RM + GRC + SOC",
            "Méthode EBIOS RM native ANSSI, pas un module générique",
            "IA contextuelle alimentée par la cartographie réelle",
            "Projet fil rouge Métropolis démontrant la chaîne complète",
            "Approche cabinet de conseil industrialisée dans un outil",
        ],
    )

    content_slide(
        prs,
        "Vision long terme",
        [
            "Devenir la plateforme de référence GRC pour le secteur public français",
            "Jumeau numérique cyber : simuler l'impact d'une attaque sur le SI réel",
            "Écosystème ouvert : connecteurs SIEM, CMDB, GRC tiers, threat intelligence",
            "Communauté Club Urba : partage de bonnes pratiques et cartographies types",
            "Agent IA RSSI : copilote permanent de la gouvernance SSI",
        ],
    )

    title_slide(
        prs,
        "Merci",
        "Urban Cyber Architect",
        "Questions & démonstration live",
    )

    return prs


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs = build_presentation()
    prs.save(str(OUTPUT))
    slide_count = len(prs.slides)
    print(f"Presentation generated: {OUTPUT}")
    print(f"Total slides: {slide_count}")


if __name__ == "__main__":
    main()
