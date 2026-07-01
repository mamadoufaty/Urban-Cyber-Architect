"""Constantes métier — projets V1.3."""

PROJECT_ROLES: frozenset[str] = frozenset(
    {
        "sponsor",
        "chef_projet",
        "ceo_direction_generale",
        "dsi",
        "rssi",
        "architecte_si",
        "architecte_cyber",
        "consultant_cybersecurite",
        "responsable_metier",
        "responsable_infrastructure",
        "responsable_reseau",
        "responsable_cloud",
        "soc_manager",
        "analyste_soc",
        "dpo",
        "responsable_conformite",
        "auditeur",
    }
)

PROJECT_ACTIVITY_CREATED = "project.created"
PROJECT_ACTIVITY_UPDATED = "project.updated"
PROJECT_ACTIVITY_DUPLICATED = "project.duplicated"
PROJECT_ACTIVITY_ARCHIVED = "project.archived"
PROJECT_ACTIVITY_DELETED = "project.deleted"
PROJECT_ACTIVITY_MEMBER_ADDED = "member.added"
PROJECT_ACTIVITY_MEMBER_REMOVED = "member.removed"
