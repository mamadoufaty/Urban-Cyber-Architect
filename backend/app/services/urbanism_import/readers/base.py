"""Interface de lecture des sources d'import."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.urbanism_import.types import ParsedImport


class ImportReader(ABC):
  @abstractmethod
  def read(self, content: bytes, filename: str) -> ParsedImport:
    """Lit le fichier et retourne les lignes normalisées."""
