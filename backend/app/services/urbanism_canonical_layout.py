"""Layout canonique Club Urba — bandes horizontales par couche."""

from __future__ import annotations

from typing import Any

from app.services.urbanism_entity_utils import resolve_entity_couche

COUCHE_ORDER = ["metier", "organisation", "fonctionnel", "applicatif", "technique", "transverse"]

SLOT_COL_WIDTH = 250
SLOT_ROW_HEIGHT = 100
HORIZONTAL_NODE_OFFSET = 220
BAND_PAD_TOP = 44
BAND_PAD_LEFT = 168
BAND_GAP = 32
NODE_VISUAL_HEIGHT = 72
BAND_BOTTOM_PAD = 24

BAND_HEIGHT_BY_COUCHE: dict[str, int] = {
    "metier": 380,
    "organisation": 300,
    "fonctionnel": 220,
    "applicatif": 220,
    "technique": 300,
    "transverse": 200,
}

CANONICAL_SLOTS: dict[str, dict[str, dict[str, int]]] = {
    "metier": {
        "metier": {"col": 1, "row": 0},
        "client": {"col": 0, "row": 0},
        "objectif": {"col": 0, "row": 1},
        "processus": {"col": 2, "row": 1},
        "evenement": {"col": 0, "row": 2},
        "activite": {"col": 2, "row": 2},
        "resultat": {"col": 1, "row": 2},
        "classe": {"col": 1, "row": 3},
    },
    "organisation": {
        "organisation": {"col": 1, "row": 0},
        "acteur": {"col": 0, "row": 1},
        "procedure": {"col": 1, "row": 1},
        "operation": {"col": 1, "row": 2},
    },
    "fonctionnel": {
        "ilot_fonctionnel": {"col": 0, "row": 1},
        "quartier_fonctionnel": {"col": 1, "row": 1},
        "zone_fonctionnelle": {"col": 2, "row": 1},
    },
    "applicatif": {
        "ilot_applicatif": {"col": 0, "row": 1},
        "quartier_applicatif": {"col": 1, "row": 1},
        "zone_applicative": {"col": 2, "row": 1},
    },
    "technique": {
        "poste_travail": {"col": 0, "row": 1},
        "byod": {"col": 1, "row": 1},
        "serveur": {"col": 0, "row": 2},
        "reseau": {"col": 1, "row": 2},
        "site": {"col": 2, "row": 2},
    },
    "transverse": {
        "systeme_information": {"col": 1, "row": 1},
    },
}

METIER_ALIGNED_ROWS = {1, 2}


def _band_y_offsets(heights: dict[str, int]) -> dict[str, int]:
    offsets: dict[str, int] = {}
    y = 0
    for couche in COUCHE_ORDER:
        offsets[couche] = y
        y += heights.get(couche, 220) + BAND_GAP
    return offsets


def compute_canonical_positions(
    nodes: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, float]], dict[str, int]]:
    """Calcule les positions x,y et les hauteurs de bande dynamiques."""
    by_couche: dict[str, list[dict[str, Any]]] = {c: [] for c in COUCHE_ORDER}
    for node in nodes:
        couche = resolve_entity_couche(node["entity_type"], node.get("couche"))
        by_couche.setdefault(couche, []).append({**node, "couche": couche})

    heights = dict(BAND_HEIGHT_BY_COUCHE)

    def place(heights_map: dict[str, int]) -> dict[str, dict[str, float]]:
        positions: dict[str, dict[str, float]] = {}
        offsets = _band_y_offsets(heights_map)
        for couche in COUCHE_ORDER:
            couche_nodes = by_couche.get(couche, [])
            slots = CANONICAL_SLOTS.get(couche, {})
            if not couche_nodes or not slots:
                continue
            base_y = offsets[couche] + BAND_PAD_TOP
            base_x = float(BAND_PAD_LEFT)
            by_type: dict[str, list[dict[str, Any]]] = {}
            for node in couche_nodes:
                by_type.setdefault(node["entity_type"], []).append(node)
            for entity_type, typed_nodes in by_type.items():
                slot = slots.get(entity_type, {"col": 1, "row": 4})
                row_y = base_y + slot["row"] * SLOT_ROW_HEIGHT
                sorted_nodes = sorted(typed_nodes, key=lambda n: n["label"].lower())
                for index, node in enumerate(sorted_nodes):
                    positions[str(node["id"])] = {
                        "x": base_x + slot["col"] * SLOT_COL_WIDTH + index * HORIZONTAL_NODE_OFFSET,
                        "y": row_y,
                    }
            if couche == "metier":
                for row in METIER_ALIGNED_ROWS:
                    row_y = base_y + row * SLOT_ROW_HEIGHT
                    for node in couche_nodes:
                        slot = slots.get(node["entity_type"])
                        if not slot or slot["row"] != row:
                            continue
                        pos = positions.get(str(node["id"]))
                        if pos:
                            positions[str(node["id"])] = {"x": pos["x"], "y": row_y}
        return positions

    for _ in range(5):
        positions = place(heights)
        changed = False
        offsets = _band_y_offsets(heights)
        for couche in COUCHE_ORDER:
            couche_nodes = by_couche.get(couche, [])
            if not couche_nodes:
                continue
            band_start = offsets[couche]
            max_bottom = band_start
            for node in couche_nodes:
                pos = positions.get(str(node["id"]))
                if not pos:
                    continue
                max_bottom = max(max_bottom, pos["y"] + NODE_VISUAL_HEIGHT)
            needed = int(max_bottom - band_start + BAND_BOTTOM_PAD)
            if needed > heights[couche]:
                heights[couche] = needed
                changed = True
        if not changed:
            break

    return place(heights), heights
