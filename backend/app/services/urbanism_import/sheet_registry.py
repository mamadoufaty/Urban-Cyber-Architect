"""Registre des feuilles Excel / CSV — mapping vers le métamodèle Club Urba."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SheetDefinition:
    sheet_key: str
    title: str
    entity_type: str | None
    columns: tuple[str, ...]
    name_column: str = "Nom"
    id_column: str = "ID"
    description_column: str = "Description"
    parent_columns: tuple[tuple[str, str], ...] = ()
    is_flux_sheet: bool = False


SHEET_DEFINITIONS: tuple[SheetDefinition, ...] = (
    SheetDefinition(
        "01_Metiers",
        "Métiers",
        "metier",
        ("ID", "Nom", "Description", "Responsable", "Criticité"),
        parent_columns=(),
    ),
    SheetDefinition(
        "02_Objectifs",
        "Objectifs",
        "objectif",
        ("ID", "Nom", "Métier associé", "Description"),
        parent_columns=(("Métier associé", "metier"),),
    ),
    SheetDefinition(
        "03_Processus",
        "Processus",
        "processus",
        ("ID", "Nom", "Objectif", "Description"),
        parent_columns=(("Objectif", "objectif"),),
    ),
    SheetDefinition(
        "04_Activites",
        "Activités",
        "activite",
        ("ID", "Nom", "Processus", "Description"),
        parent_columns=(("Processus", "processus"),),
    ),
    SheetDefinition(
        "05_Classes",
        "Classes",
        "classe",
        ("ID", "Nom", "Activité", "Description"),
        parent_columns=(("Activité", "activite"),),
    ),
    SheetDefinition(
        "06_Organisation",
        "Organisation",
        "organisation",
        ("ID", "Direction", "Service", "Responsable", "Description"),
        name_column="Service",
        parent_columns=(),
    ),
    SheetDefinition(
        "07_Operations",
        "Opérations",
        "operation",
        ("ID", "Nom", "Organisation", "Description"),
        parent_columns=(("Organisation", "organisation"),),
    ),
    SheetDefinition(
        "08_Fonctionnel",
        "Fonctionnel",
        "ilot_fonctionnel",
        ("ID", "Nom", "Classe", "Description"),
        parent_columns=(("Classe", "classe"),),
    ),
    SheetDefinition(
        "09_Applicatif",
        "Applicatif",
        "ilot_applicatif",
        ("ID", "Nom", "Fonction", "Editeur", "Version", "Criticité"),
        parent_columns=(("Fonction", "ilot_fonctionnel"),),
    ),
    SheetDefinition(
        "10_Technique",
        "Technique",
        None,
        ("ID", "Nom", "Application", "Serveur", "Réseau", "Site", "Cloud", "Description"),
        is_flux_sheet=False,
    ),
    SheetDefinition(
        "11_Serveurs",
        "Serveurs",
        "serveur",
        ("ID", "Nom", "OS", "Adresse IP", "Virtualisation", "Criticité"),
    ),
    SheetDefinition(
        "12_Reseaux",
        "Réseaux",
        "reseau",
        ("ID", "Nom", "VLAN", "Adresse", "Site"),
        parent_columns=(),
    ),
    SheetDefinition(
        "13_Sites",
        "Sites",
        "site",
        ("ID", "Nom", "Ville", "Adresse"),
    ),
    SheetDefinition(
        "14_Equipements",
        "Équipements",
        "poste_travail",
        ("ID", "Nom", "Type", "Constructeur", "Serveur", "Réseau"),
        parent_columns=(("Serveur", "serveur"), ("Réseau", "reseau")),
    ),
    SheetDefinition(
        "15_Flux",
        "Flux",
        None,
        ("Source", "Destination", "Type", "Protocole", "Description"),
        is_flux_sheet=True,
    ),
)

SHEET_BY_KEY = {s.sheet_key: s for s in SHEET_DEFINITIONS}
SHEET_ALIASES = {
    s.sheet_key.lower(): s.sheet_key for s in SHEET_DEFINITIONS
}
for s in SHEET_DEFINITIONS:
    SHEET_ALIASES[s.title.lower()] = s.sheet_key


def resolve_sheet_name(raw: str) -> str | None:
    key = raw.strip()
    if key in SHEET_BY_KEY:
        return key
    return SHEET_ALIASES.get(key.lower())


def count_key_for_entity(entity_type: str) -> str | None:
    mapping = {
        "metier": "metiers",
        "objectif": "objectifs",
        "processus": "processus",
        "activite": "activites",
        "classe": "classes",
        "organisation": "organisations",
        "operation": "operations",
        "ilot_fonctionnel": "fonctions",
        "ilot_applicatif": "applications",
        "serveur": "serveurs",
        "reseau": "reseaux",
        "site": "sites",
        "poste_travail": "equipements",
    }
    return mapping.get(entity_type)


def extra_property_columns(defn: SheetDefinition) -> tuple[str, ...]:
    parent_cols = {p[0] for p in defn.parent_columns}
    skip = {defn.id_column, defn.name_column, defn.description_column, *parent_cols}
    return tuple(c for c in defn.columns if c not in skip)


def row_to_properties(defn: SheetDefinition, cells: dict[str, Any]) -> dict[str, Any]:
    props: dict[str, Any] = {}
    for col in extra_property_columns(defn):
        val = cells.get(col)
        if val is not None and str(val).strip():
            props[col.lower().replace(" ", "_")] = str(val).strip()
    return props
