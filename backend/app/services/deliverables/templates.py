"""Templates déterministes pour la génération de livrables."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _bullets(items: list[str], fallback: str) -> list[str]:
    cleaned = [i for i in items if i and str(i).strip()]
    return cleaned if cleaned else [fallback]


def _org_name(context: dict[str, Any]) -> str:
    org = (context.get("project") or {}).get("organization") or {}
    return str(org.get("name") or (context.get("project") or {}).get("name") or "Organisation")


def _is_metropolis(context: dict[str, Any]) -> bool:
    name = str((context.get("project") or {}).get("name") or "").lower()
    sector = str(((context.get("project") or {}).get("organization") or {}).get("sector") or "")
    return "metropolis" in name or "métropolis" in name or sector == "smart_city"


def build_project_management_plan(
    *,
    title: str,
    user_need: str,
    context: dict[str, Any],
    type_label: str,
) -> dict[str, Any]:
    project = context.get("project") or {}
    urbanism = context.get("urbanism") or {}
    ebios = context.get("ebios") or {}
    grc = context.get("grc") or {}
    soc = context.get("soc") or {}
    wazuh = context.get("wazuh") or {}
    ai = context.get("ai") or {}
    metropolis = _is_metropolis(context)

    org_name = _org_name(context)
    objectives = project.get("objectives") or []
    referentials = project.get("referentials") or []
    acteurs = urbanism.get("acteurs") or []
    organisations = urbanism.get("organisations") or []
    processus = urbanism.get("processus") or []
    applications = urbanism.get("applications") or []
    biens = urbanism.get("biens_supports") or []
    top_risks = grc.get("top_risks") or []

    sections = [
        {
            "id": "presentation",
            "title": "1. Présentation du projet",
            "content": (
                f"Ce document présente le plan de management du projet **{project.get('name', '—')}** "
                f"pour {org_name}. {title}"
            ),
            "bullets": _bullets(
                [
                    f"Description : {project.get('description') or 'Non renseignée'}",
                    f"Référentiels : {', '.join(referentials) if referentials else 'À définir'}",
                ],
                "Projet piloté via Urban Cyber Architect.",
            ),
        },
        {
            "id": "contexte",
            "title": "2. Contexte et objectifs",
            "content": user_need.strip()
            or "Contexte projet aligné sur la transformation numérique et la cybersécurité.",
            "bullets": _bullets(
                [f"Objectif : {o}" for o in objectives],
                "Objectifs à consolider avec le comité de pilotage.",
            ),
        },
        {
            "id": "equipe",
            "title": "3. Organisation de l'équipe projet",
            "content": (
                "L'équipe projet s'appuie sur les acteurs identifiés dans la cartographie urbanisme "
                "et les ateliers EBIOS RM."
            ),
            "bullets": _bullets(
                acteurs[:12],
                "Équipe projet à constituer (chef de projet, RSSI, architectes, MOA/MOE).",
            ),
        },
        {
            "id": "roles",
            "title": "4. Rôles et responsabilités",
            "content": "Matrice RACI dérivée des acteurs urbanisme et des responsabilités GRC.",
            "bullets": _bullets(
                [f"{a} — rôle projet à valider" for a in acteurs[:8]],
                "RSSI : pilotage sécurité | Architecte SI : urbanisme | MOA : exigences métier",
            ),
        },
        {
            "id": "parties_prenantes",
            "title": "5. Parties prenantes",
            "content": "Parties prenantes internes et externes identifiées dans le référentiel projet.",
            "bullets": _bullets(
                organisations + acteurs,
                "Parties prenantes à cartographier (direction, métiers, fournisseurs, autorités).",
            ),
        },
        {
            "id": "communication",
            "title": "6. Stratégie de communication",
            "content": (
                "Communication structurée : comité de pilotage mensuel, points sécurité avec le RSSI, "
                "reporting COMEX trimestriel."
            ),
            "bullets": [
                "Canaux : COPIL, COPROJ, revues d'architecture, alertes SOC si activées",
                "Livrables de communication : tableaux de bord GRC, rapports SOC, synthèses IA",
            ],
        },
        {
            "id": "planning",
            "title": "7. Planning et jalons",
            "content": "Planning indicatif aligné sur les ateliers EBIOS et la mise en œuvre GRC.",
            "bullets": [
                "J1 — Cadrage et urbanisme SI",
                "J2 — Ateliers EBIOS RM (sources de risque, biens supports)",
                "J3 — Registre des risques et décisions de traitement (PTR)",
                "J4 — Déclaration d'applicabilité et mise en œuvre",
            ],
        },
        {
            "id": "budget",
            "title": "8. Budget prévisionnel",
            "content": "Budget à consolider — répartition indicative ci-dessous.",
            "bullets": [
                "Pilotage projet et gouvernance",
                "Ingénierie urbanisme / architecture",
                "Mesures de sécurité (GRC / SOC / conformité)",
                "Accompagnement changement et formation",
            ],
        },
        {
            "id": "risques",
            "title": "9. Gestion des risques projet",
            "content": (
                f"Registre des risques : {grc.get('risk_register_total', 0)} entrée(s). "
                f"PTR : {grc.get('ptr_total', 0)} action(s)."
            ),
            "bullets": _bullets(
                [
                    f"{r.get('id')} — {r.get('asset')} (criticité {r.get('criticality')}, décision {r.get('decision')})"
                    for r in top_risks
                ],
                "Analyse de risques à enrichir via EBIOS RM et le registre GRC.",
            ),
        },
        {
            "id": "metropolitain",
            "title": "10. Analyse du besoin métropolitain",
            "content": (
                "Analyse spécifique au contexte métropolitain : services publics numériques, "
                "interopérabilité territoriale, résilience des services urbains critiques (mobilité, eau, énergie)."
                if metropolis
                else "Analyse du besoin territorial à adapter selon le périmètre du projet."
            ),
            "bullets": _bullets(
                processus[:6] + applications[:4],
                "Besoins métropolitains : continuité de service, conformité NIS2/RGPD, gouvernance multiculturelle."
                if metropolis
                else "Cartographier les enjeux territoriaux avec les parties prenantes.",
            ),
        },
        {
            "id": "conclusion",
            "title": "11. Conclusion",
            "content": (
                f"Le plan de management intègre {len(acteurs)} acteur(s), {len(processus)} processus, "
                f"{len(applications)} application(s) et {len(biens)} bien(s) support identifiés."
            ),
            "bullets": _bullets(
                [
                    f"SOC : {soc.get('incidents_count', 0)} incident(s) corrélé(s)" if soc else "",
                    f"Wazuh : {wazuh.get('agents_active', 0)} agent(s) actif(s)" if wazuh.get("connected") else "",
                    f"Rapports IA : {ai.get('runs_count', 0)} orchestration(s)" if ai else "",
                ],
                "Document généré automatiquement — à valider en comité de pilotage.",
            ),
        },
    ]

    return _wrap_content(title, user_need, context, type_label, sections)


def build_generic_document(
    *,
    title: str,
    user_need: str,
    context: dict[str, Any],
    type_label: str,
) -> dict[str, Any]:
    project = context.get("project") or {}
    sections = [
        {
            "id": "intro",
            "title": "Introduction",
            "content": f"Livrable « {type_label} » pour le projet {project.get('name', '—')}.",
            "bullets": [f"Besoin : {user_need[:500]}"] if user_need else [],
        },
        {
            "id": "synthese",
            "title": "Synthèse des données sources",
            "content": "Données agrégées depuis Urban Cyber Architect.",
            "bullets": _bullets(
                [
                    f"Urbanisme : {context.get('urbanism', {}).get('entities_count', 0)} entité(s)"
                    if "urbanism" in context.get("data_sources_used", [])
                    else "",
                    f"EBIOS : {context.get('ebios', {}).get('workshop2_records', 0)} enregistrement(s) atelier 2"
                    if "ebios" in context.get("data_sources_used", [])
                    else "",
                    f"GRC : {context.get('grc', {}).get('risk_register_total', 0)} risque(s)"
                    if "grc" in context.get("data_sources_used", [])
                    else "",
                ],
                "Sélectionnez des sources de données pour enrichir le livrable.",
            ),
        },
        {
            "id": "contenu",
            "title": "Contenu",
            "content": user_need or "Contenu à compléter selon le besoin utilisateur.",
            "bullets": [],
        },
    ]
    return _wrap_content(title, user_need, context, type_label, sections)


def _wrap_content(
    title: str,
    user_need: str,
    context: dict[str, Any],
    type_label: str,
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    project = context.get("project") or {}
    return {
        "title": title,
        "user_need": user_need,
        "sections": sections,
        "metadata": {
            "project_name": project.get("name"),
            "deliverable_type_label": type_label,
            "data_sources_used": context.get("data_sources_used") or [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "engine": "deterministic-template-v1",
        },
        "context_snapshot": {
            k: context[k]
            for k in ("urbanism", "ebios", "grc", "soc", "wazuh", "ai")
            if k in context
        },
    }


def build_document_content(
    *,
    deliverable_type: str,
    title: str,
    user_need: str,
    context: dict[str, Any],
    type_label: str,
) -> dict[str, Any]:
    if deliverable_type == "project_management_plan":
        return build_project_management_plan(
            title=title,
            user_need=user_need,
            context=context,
            type_label=type_label,
        )
    return build_generic_document(
        title=title,
        user_need=user_need,
        context=context,
        type_label=type_label,
    )
