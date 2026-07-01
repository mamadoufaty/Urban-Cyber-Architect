"""Tests layout canonique — bandes horizontales par couche."""

import pytest

from app.services.urbanism_canonical_layout import compute_canonical_positions


def test_two_ilot_applicatif_share_applicatif_band_y():
    nodes = [
        {"id": "a1", "entity_type": "ilot_applicatif", "couche": "applicatif", "label": "Microsoft Sentinel"},
        {"id": "a2", "entity_type": "ilot_applicatif", "couche": "technique", "label": "QRadar"},
    ]
    positions, heights = compute_canonical_positions(nodes)
    assert positions["a1"]["y"] == positions["a2"]["y"]
    assert positions["a1"]["x"] != positions["a2"]["x"]
    assert positions["a1"]["y"] > 400


def test_organisation_below_metier():
    nodes = [
        {"id": "m1", "entity_type": "metier", "couche": "metier", "label": "Cybersécurité"},
        {"id": "o1", "entity_type": "organisation", "couche": "organisation", "label": "DSI"},
    ]
    positions, _ = compute_canonical_positions(nodes)
    assert positions["o1"]["y"] > positions["m1"]["y"]
