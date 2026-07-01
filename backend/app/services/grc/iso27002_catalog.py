"""Catalogue ISO/IEC 27002:2022 — contrôles de référence pour la SoA."""

from __future__ import annotations

ISO27002_CONTROLS: dict[str, str] = {
    "5.1": "Policies for information security",
    "5.2": "Information security roles and responsibilities",
    "5.9": "Inventory of information and other associated assets",
    "5.15": "Access control",
    "5.17": "Authentication information",
    "5.23": "Information security for use of cloud services",
    "5.36": "Compliance with policies, rules and standards for information security",
    "6.3": "Information security awareness, education and training",
    "6.8": "Information security event reporting",
    "7.4": "Physical security monitoring",
    "8.1": "User endpoint devices",
    "8.5": "Secure authentication",
    "8.7": "Protection against malware",
    "8.8": "Management of technical vulnerabilities",
    "8.9": "Configuration management",
    "8.10": "Information deletion",
    "8.12": "Data leakage prevention",
    "8.13": "Information backup",
    "8.15": "Logging",
    "8.16": "Monitoring activities",
    "8.20": "Networks security",
    "8.22": "Segregation in networks",
    "8.23": "Web filtering",
    "8.24": "Use of cryptography",
    "8.25": "Secure development life cycle",
}

SOA_VERSION_LABEL = "ISO/IEC 27001:2022 — SoA v1.0"
