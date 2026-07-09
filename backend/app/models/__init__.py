"""Package des modèles SQLAlchemy.

Importer ``app.models`` (ou n'importe quel symbole exposé ici) enregistre
l'intégralité des classes mappées dans le registry SQLAlchemy. C'est le point
d'entrée unique à utiliser avant toute requête ou tout ``configure_mappers()``,
afin d'éviter les erreurs du type « expression 'Project' failed to locate a
name » lorsqu'un chemin de code (par ex. la CLI ``bootstrap-admin``) ne
manipule qu'un sous-ensemble de modèles.

Les modules sont importés dans un ordre qui respecte les dépendances de clés
étrangères, mais SQLAlchemy résolvant les relations de façon paresseuse, seul
compte le fait que *tous* les modules soient chargés avant la configuration des
mappers.
"""

from __future__ import annotations

from sqlalchemy.orm import configure_mappers

from app.database import Base

from app.models.admin import (
    AuditLog,
    Organization,
    Permission,
    Role,
    RolePermission,
    User,
)
from app.models.entities import (
    AIGovernanceConfig,
    GraphEdge,
    GraphNode,
    HumanDecision,
    OrchestrationRun,
    Project,
    UrbanismEntity,
    UrbanismRelation,
    WazuhConnectorConfig,
)
from app.models.project_core import ProjectActivity, ProjectMember
from app.models.cartography import Cartography, CartographyHistory, CartographyVersion
from app.models.deliverables import Deliverable
from app.models.referentials import ReferentialFramework
from app.models.ebios import (
    EbiosAssessment,
    EbiosLink,
    EbiosRecord,
    EbiosWorkshop,
)


def register_all_models() -> None:
    """Force l'enregistrement et la configuration de tous les mappers.

    Idempotent : peut être appelée plusieurs fois sans effet de bord. À utiliser
    dans les points d'entrée (CLI, application) avant la première requête.
    """
    configure_mappers()


__all__ = [
    "Base",
    "register_all_models",
    # Administration
    "AuditLog",
    "Organization",
    "Permission",
    "Role",
    "RolePermission",
    "User",
    # Projet / cœur métier
    "AIGovernanceConfig",
    "GraphEdge",
    "GraphNode",
    "HumanDecision",
    "OrchestrationRun",
    "Project",
    "ProjectActivity",
    "ProjectMember",
    "UrbanismEntity",
    "UrbanismRelation",
    "WazuhConnectorConfig",
    # Cartographies (multi-cartographies + versionning)
    "Cartography",
    "CartographyVersion",
    "CartographyHistory",
    # Livrables
    "Deliverable",
    # Référentiels
    "ReferentialFramework",
    # EBIOS RM
    "EbiosAssessment",
    "EbiosLink",
    "EbiosRecord",
    "EbiosWorkshop",
]
