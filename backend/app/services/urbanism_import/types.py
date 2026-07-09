"""Types partagés — import cartographie urbanisme."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ImportMode(str, Enum):
    REPLACE = "replace"
    MERGE = "merge"


class ImportErrorCode(str, Enum):
    MISSING_OBJECT = "missing_object"
    UNKNOWN_REFERENCE = "unknown_reference"
    DUPLICATE = "duplicate"
    EMPTY_NAME = "empty_name"
    INVALID_RELATION = "invalid_relation"
    INVALID_SHEET = "invalid_sheet"


@dataclass
class ImportRow:
    sheet: str
    row_number: int
    external_id: str
    entity_type: str
    label: str
    description: str | None = None
    parent_refs: dict[str, str] = field(default_factory=dict)
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportIssue:
    code: ImportErrorCode
    message: str
    sheet: str | None = None
    row_number: int | None = None
    field: str | None = None
    severity: str = "error"


@dataclass
class ImportCounts:
    metiers: int = 0
    objectifs: int = 0
    processus: int = 0
    activites: int = 0
    classes: int = 0
    organisations: int = 0
    operations: int = 0
    fonctions: int = 0
    applications: int = 0
    serveurs: int = 0
    reseaux: int = 0
    sites: int = 0
    equipements: int = 0
    flux: int = 0
    relations: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "metiers": self.metiers,
            "objectifs": self.objectifs,
            "processus": self.processus,
            "activites": self.activites,
            "classes": self.classes,
            "organisations": self.organisations,
            "operations": self.operations,
            "applications": self.applications,
            "fonctions": self.fonctions,
            "serveurs": self.serveurs,
            "reseaux": self.reseaux,
            "sites": self.sites,
            "equipements": self.equipements,
            "flux": self.flux,
            "relations": self.relations,
        }


@dataclass
class ParsedImport:
    rows: list[ImportRow] = field(default_factory=list)
    flux_rows: list[dict[str, Any]] = field(default_factory=list)
    issues: list[ImportIssue] = field(default_factory=list)
    counts: ImportCounts = field(default_factory=ImportCounts)


@dataclass
class ImportPreview:
    counts: ImportCounts
    issues: list[ImportIssue]
    sample_rows: list[dict[str, Any]]
    mode: ImportMode


@dataclass
class ImportReport:
    created: dict[str, int]
    updated: dict[str, int]
    relations_created: int
    orphans: int
    inconsistencies: int
    completeness_rate: float
    urbanism_progress: dict[str, Any]
    issues: list[ImportIssue]
    flux_stored: int
