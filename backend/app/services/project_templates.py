"""Project templates with preloaded Club Urba cartography data."""

import copy
from typing import Any

from app.services.urbanism_schema import _empty_club_urba

TEMPLATE_IDS = ("blank", "metropolis", "banque", "sante", "industrie")

METROPOLIS_CLUB_URBA: dict[str, dict[str, list[str]]] = {
    "metier": {
        "objectifs": [
            "Services publics numériques sécurisés",
            "Conformité NIS2 et RGPD",
            "Résilience des services urbains critiques",
        ],
        "processus": [
            "Supervision temps réel des infrastructures",
            "Gestion des incidents citoyens",
            "Planification mobilité durable",
            "Gestion de crise métropolitaine",
        ],
        "activites": [
            "Pilotage du trafic routier",
            "Distribution d'eau potable",
            "Gestion de l'éclairage public",
            "Accueil et information citoyenne",
        ],
        "resultats": [
            "Continuité de service 24/7",
            "Satisfaction usagers > 85%",
            "Réduction incidents majeurs",
            "Conformité audits NIS2",
        ],
    },
    "organisation": {
        "organisation": [
            "Métropolis — Métropole territoriale",
            "Direction du numérique",
            "Pôle sécurité des systèmes d'information",
        ],
        "procedures": [
            "Procédure gestion d'incident cyber",
            "Procédure gestion des changements",
            "Procédure continuité d'activité",
        ],
        "operations": [
            "Exploitation SCADA eau et énergie",
            "Support utilisateurs métiers",
            "Supervision SOC municipal",
            "Maintenance réseaux capteurs IoT",
        ],
        "acteurs": [
            "RSSI métropolitain",
            "Exploitants OT/SCADA",
            "Responsables métiers",
            "Élus et direction générale",
            "Prestataires infogérants",
        ],
    },
    "fonctionnel": {
        "ilots": [
            "Mobilité et transports",
            "Eau et assainissement",
            "Énergie et éclairage",
            "Sécurité publique et vidéoprotection",
        ],
        "quartiers": [
            "Transport intelligent (ITS)",
            "Réseau eau potable",
            "Réseau électrique intelligent",
            "Vidéosurveillance urbaine",
            "Gestion des déchets",
        ],
        "zones": [
            "Supervision centralisée",
            "Relation usager / portail citoyen",
            "Alerting et notification",
            "Reporting réglementaire",
        ],
    },
    "applicatif": {
        "ilots": [
            "Portail métropolitain",
            "SCADA eau et assainissement",
            "Gestion de flotte",
            "Centre de supervision urbaine",
        ],
        "quartiers": [
            "Gestion des titres de transport",
            "Télégestion réseau eau",
            "GMAO équipements publics",
            "Plateforme open data",
        ],
        "zones": [
            "API ouverture des données",
            "Moteur d'alerting multi-canal",
            "Authentification citoyenne",
            "Tableaux de bord décisionnels",
        ],
    },
    "technique": {
        "postes": [
            "Postes supervision SCADA",
            "Postes bureautiques agents",
            "Postes salle de crise",
        ],
        "serveurs": [
            "Serveur SCADA eau",
            "Cluster virtualisation datacenter",
            "Serveurs applicatifs portail",
            "Collecteurs logs SIEM",
        ],
        "reseaux": [
            "Réseau OT industriel",
            "Fibre optique métropolitaine",
            "Réseau Wi-Fi services publics",
            "Interconnexion sites distants",
        ],
        "sites": [
            "Datacenter principal Métropolis",
            "Site secours PRA",
            "Régie eau — site OT",
            "Hôtel de métropole",
        ],
    },
}

BANQUE_CLUB_URBA: dict[str, dict[str, list[str]]] = {
    "metier": {
        "objectifs": ["Conformité DORA", "Sécurisation des paiements", "Protection des données clients"],
        "processus": ["Traitement des transactions", "Octroi de crédit", "Transferts SWIFT", "Onboarding client"],
        "activites": ["Paiement carte", "Gestion comptes", "Conformité LCB-FT", "Trading salle des marchés"],
        "resultats": ["Zéro fraude majeure", "Disponibilité core banking 99.99%", "Audit PCI-DSS validé"],
    },
    "organisation": {
        "organisation": ["Banque Régionale SA", "Direction des risques", "DSI groupe"],
        "procedures": ["Procédure incident cyber bancaire", "Gestion des accès privilégiés", "PCA/PRA bancaire"],
        "operations": ["Exploitation core banking", "Monitoring SOC 24/7", "Gestion réseau SWIFT"],
        "acteurs": ["RSSI", "DPO", "Exploitants SI", "Auditeurs internes", "Responsables métier paiement"],
    },
    "fonctionnel": {
        "ilots": ["Paiement et monétique", "Crédit et financement", "Opérations internationales"],
        "quartiers": ["Cartes et e-paiement", "Scoring et décision crédit", "Messagerie SWIFT", "Conformité réglementaire"],
        "zones": ["Autorisation transaction", "Détection fraude", "Reporting Bâle/DORA"],
    },
    "applicatif": {
        "ilots": ["Core Banking", "Plateforme paiement", "SWIFT Alliance"],
        "quartiers": ["Moteur anti-fraude", "CRM clientèle", "Data warehouse réglementaire"],
        "zones": ["API banking", "Portail client", "Middleware intégration"],
    },
    "technique": {
        "postes": ["Postes traders", "Postes agences", "Postes SOC"],
        "serveurs": ["Serveurs core banking", "HSM cryptographiques", "Serveurs messagerie SWIFT"],
        "reseaux": ["Réseau LAN agences", "DMZ bancaire", "Liens SWIFT sécurisés"],
        "sites": ["Datacenter primaire", "Datacenter secours", "Site de repli messagerie"],
    },
}

SANTE_CLUB_URBA: dict[str, dict[str, list[str]]] = {
    "metier": {
        "objectifs": ["Protection des données de santé", "Certification HDS", "Continuité des soins"],
        "processus": ["Parcours patient", "Prescription et dispensation", "Imagerie médicale", "Archivage DMP"],
        "activites": ["Admission urgences", "Consultation spécialisée", "Bloc opératoire", "Laboratoire"],
        "resultats": ["Disponibilité DPI 99.9%", "Conformité HDS", "Traçabilité des accès dossiers"],
    },
    "organisation": {
        "organisation": ["CHU Régional", "Direction des systèmes d'information", "DPO santé"],
        "procedures": ["Procédure accès dossier patient", "Gestion incident ransomware", "Procédure HDS"],
        "operations": ["Exploitation DPI", "Support PACS", "Supervision réseau hospitalier"],
        "acteurs": ["RSSI", "Médecins prescripteurs", "Infirmiers", "Administrateurs DPI", "Hébergeur HDS"],
    },
    "fonctionnel": {
        "ilots": ["Dossier patient", "Imagerie médicale", "Laboratoire et pharmacie"],
        "quartiers": ["Prescription électronique", "PACS radiologie", "Gestion lits et admissions", "DMP"],
        "zones": ["Accès dossier sécurisé", "Partage inter-établissements", "Traçabilité médicamenteuse"],
    },
    "applicatif": {
        "ilots": ["DPI principal", "PACS", "Gestion pharmacie"],
        "quartiers": ["Portail professionnel de santé", "Module urgences", "Bus intégration HL7/FHIR"],
        "zones": ["API interopérabilité", "Portail patient", "Moteur de consentement"],
    },
    "technique": {
        "postes": ["Postes médicaux", "Postes administratifs", "Postes laboratoire"],
        "serveurs": ["Serveurs DPI HDS", "Stockage PACS", "Serveurs virtualisation"],
        "reseaux": ["Réseau clinique segmenté", "Wi-Fi patients", "Interconnexion hébergeur HDS"],
        "sites": ["Site principal CHU", "Site annexe", "Datacenter HDS certifié"],
    },
}

INDUSTRIE_CLUB_URBA: dict[str, dict[str, list[str]]] = {
    "metier": {
        "objectifs": ["Sécurisation OT/IT", "Conformité IEC 62443", "Zéro arrêt production non planifié"],
        "processus": ["Pilotage ligne production", "Maintenance préventive", "Ordonnancement MES", "Contrôle qualité"],
        "activites": ["Assemblage", "Conditionnement", "Logistique sortie usine", "Supervision automates"],
        "resultats": ["OEE > 90%", "Aucun incident cyber OT majeur", "Traçabilité produit complète"],
    },
    "organisation": {
        "organisation": ["Usine Industrie 4.0", "Direction industrielle", "DSI & OT security"],
        "procedures": ["Procédure accès bastion OT", "Gestion vulnérabilités ICS", "Plan de continuité production"],
        "operations": ["Exploitation SCADA", "Maintenance automates", "Supervision MES"],
        "acteurs": ["RSSI", "Ingénieurs automatisme", "Opérateurs production", "Responsable maintenance"],
    },
    "fonctionnel": {
        "ilots": ["Production", "Maintenance", "Qualité et traçabilité"],
        "quartiers": ["Ligne assemblage A", "Ligne conditionnement B", "Ordonnancement MES", "Laboratoire qualité"],
        "zones": ["Supervision temps réel", "Gestion des alarmes", "Traçabilité lots"],
    },
    "applicatif": {
        "ilots": ["MES", "SCADA supervision", "ERP industriel"],
        "quartiers": ["Historian process", "GMAO maintenance", "Module qualité"],
        "zones": ["API MES-ERP", "Dashboard production", "Reporting OEE"],
    },
    "technique": {
        "postes": ["Postes supervision OT", "Postes ingénierie automates", "Postes bureautiques IT"],
        "serveurs": ["Serveur SCADA", "Historian", "Serveurs MES"],
        "reseaux": ["Réseau terrain automates", "DMZ OT/IT", "Réseau bureautique"],
        "sites": ["Site production principal", "Atelier maintenance", "Datacenter usine"],
    },
}


def _wrap_club_urba(club: dict[str, dict[str, list[str]]]) -> dict[str, Any]:
    return {"club_urba": club}


TEMPLATES: dict[str, dict[str, Any]] = {
    "blank": {
        "id": "blank",
        "label": "Projet vierge",
        "description": "Cartographie vide — vous renseignez chaque zone manuellement",
        "is_example": False,
        "sector": "generic",
        "referentials": [],
        "objectives": [],
        "urbanism": {"club_urba": _empty_club_urba()},
    },
    "metropolis": {
        "id": "metropolis",
        "label": "Exemple — Smart City (Métropolis)",
        "description": "Modèle exemple optionnel : métropole, mobilité, eau, énergie",
        "is_example": True,
        "default_name": "Métropolis",
        "sector": "smart_city",
        "referentials": ["RGPD", "NIS2", "ISO 27001", "IEC 62443"],
        "objectives": [
            "Services publics numériques sécurisés",
            "Conformité NIS2 et RGPD",
            "Résilience des services urbains critiques",
        ],
        "urbanism": _wrap_club_urba(METROPOLIS_CLUB_URBA),
    },
    "banque": {
        "id": "banque",
        "label": "Exemple — Banque",
        "description": "Modèle exemple optionnel : paiement, crédit, SWIFT, DORA",
        "is_example": True,
        "default_name": "Banque Régionale",
        "sector": "banque",
        "referentials": ["DORA", "RGPD", "PCI-DSS", "ISO 27001"],
        "objectives": ["Conformité DORA", "Sécurisation des paiements"],
        "urbanism": _wrap_club_urba(BANQUE_CLUB_URBA),
    },
    "sante": {
        "id": "sante",
        "label": "Exemple — Santé",
        "description": "Modèle exemple optionnel : DPI, HDS, parcours patient",
        "is_example": True,
        "default_name": "CHU Régional",
        "sector": "sante",
        "referentials": ["HDS", "RGPD", "ISO 27001"],
        "objectives": ["Protection des données de santé", "Certification HDS"],
        "urbanism": _wrap_club_urba(SANTE_CLUB_URBA),
    },
    "industrie": {
        "id": "industrie",
        "label": "Exemple — Industrie",
        "description": "Modèle exemple optionnel : SCADA, MES, IEC 62443",
        "is_example": True,
        "default_name": "Usine Industrie 4.0",
        "sector": "industrie",
        "referentials": ["IEC 62443", "ISO 27001", "NIS2"],
        "objectives": ["Sécurisation OT/IT", "Conformité IEC 62443"],
        "urbanism": _wrap_club_urba(INDUSTRIE_CLUB_URBA),
    },
}


def list_templates() -> list[dict[str, Any]]:
    return [
        {
            "id": t["id"],
            "label": t["label"],
            "description": t["description"],
            "default_name": t.get("default_name"),
            "is_example": t.get("is_example", False),
            "sector": t.get("sector", "generic"),
        }
        for t in TEMPLATES.values()
    ]


def apply_template(template_id: str, name: str | None = None) -> dict[str, Any]:
    if template_id not in TEMPLATES:
        raise ValueError(f"Unknown template: {template_id}")

    tpl = TEMPLATES[template_id]
    project_name = name or tpl.get("default_name") or "Nouveau projet"
    org_name = project_name if template_id != "blank" else (name or "Organisation")

    urbanism = copy.deepcopy(tpl.get("urbanism", {"club_urba": _empty_club_urba()}))

    if template_id == "metropolis":
        urbanism["club_urba"]["organisation"]["organisation"] = [
            "Métropolis — Métropole territoriale",
            "Direction du numérique",
            "Pôle sécurité des systèmes d'information",
        ]

    return {
        "name": project_name,
        "description": tpl.get("description"),
        "organization": {
            "name": org_name,
            "sector": tpl.get("sector", "generic"),
            "size": "ETI" if template_id != "blank" else "PME",
            "country": "France",
        },
        "referentials": list(tpl.get("referentials", [])),
        "objectives": list(tpl.get("objectives", [])),
        "urbanism": urbanism,
    }
