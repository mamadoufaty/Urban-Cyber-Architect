# NOTE EXPLICATIVE DU PROJET

**Projet :** Métropolis – Sécurité publique & Services numériques  
**Version :** 1.0  
**Date :** 24 juin 2025  
**Classification :** Interne – Diffusion restreinte  
**Référentiel Urban Cyber Architect :** Projet fil rouge ISRC10 / template `metropolis`

---

## Table des matières

1. [Présentation générale du projet](#1-présentation-générale-du-projet)
2. [Gouvernance](#2-gouvernance)
3. [Présentation de l'organisation](#3-présentation-de-lorganisation)
4. [Urbanisme SI](#4-urbanisme-si)
5. [Flux SI](#5-flux-si)
6. [Inventaire des actifs](#6-inventaire-des-actifs)
7. [Classification des données](#7-classification-des-données)
8. [Analyse des dépendances](#8-analyse-des-dépendances)
9. [Cybersécurité](#9-cybersécurité)
10. [Analyse de risques](#10-analyse-de-risques)
11. [Conformité](#11-conformité)
12. [Livrables attendus](#12-livrables-attendus)

---

## 1. Présentation générale du projet

### 1.1 Contexte

La métropole **Métropolis** regroupe 42 communes et 680 000 habitants sur un territoire dense, exposé à des enjeux de mobilité, de continuité des services publics essentiels et de transformation numérique accélérée. Les services numériques municipaux (portail citoyen, open data, titres de transport, télégestion des réseaux) coexistent avec des systèmes industriels (SCADA eau, énergie, éclairage) et des dispositifs de **sécurité publique** (vidéoprotection urbaine, gestion des flux en centres de supervision, coordination de crise).

La métropole est **opérateur de services essentiels** au sens de la directive **NIS2** et traite des volumes significatifs de données à caractère personnel (usagers, agents, images de vidéoprotection). Elle doit concilier :

- l'ouverture des données et la relation numérique avec le citoyen ;
- la résilience opérationnelle 24/7 des infrastructures critiques ;
- la conformité RGPD, NIS2, ISO 27001 et les recommandations **ANSSI** pour les SI des collectivités ;
- la montée en maturité **EBIOS RM** pour piloter les risques cyber sur l'ensemble OT/IT.

Le programme **« Métropolis – Sécurité publique & Services numériques »** constitue le **projet fil rouge** de la plateforme **Urban Cyber Architect** : il alimente la cartographie Club Urba, les ateliers EBIOS, la GRC, le SOC et la génération automatique de livrables.

### 1.2 Objectifs

| # | Objectif | Indicateur cible |
|---|--------|------------------|
| O1 | Déployer des **services publics numériques sécurisés** | Disponibilité portail citoyen ≥ 99,5 % |
| O2 | Atteindre la **conformité NIS2 et RGPD** | Audit conformité sans écart majeur |
| O3 | Renforcer la **résilience des services urbains critiques** | RTO datacenter ≤ 4 h ; PCA eau validé |
| O4 | Structurer la **gouvernance SSI** et le pilotage RSSI | Comité cyber trimestriel ; registre des risques à jour |
| O5 | Industrialiser la **supervision SOC** et la corrélation SIEM | MTTD incidents cyber < 30 min |
| O6 | Capitaliser la connaissance dans **Urban Cyber Architect** | Cartographie Club Urba complète ; 5 ateliers EBIOS réalisés |

### 1.3 Périmètre

**Inclus :**

- Système d'information métropolitain (SI bureautique, SI métier, SI technique, SI OT)
- Portail citoyen, open data, applications mobilité et transports
- SCADA eau / assainissement, supervision énergie et éclairage
- Centre de supervision urbaine (CSU) et dispositifs vidéoprotection
- Datacenter principal, site PRA, interconnexions fibre métropolitaine
- SOC municipal, SIEM (Wazuh), gestion des identités (IAM)
- Périmètre prestataires infogérants et hébergeurs cloud (IaaS/PaaS)

**Exclus :**

- Réseaux opérateurs télécoms tiers (hors points de peering contractuels)
- Systèmes des communes adhérentes non mutualisés
- Applications métier des hôpitaux publics du territoire (périmètre ARS)

### 1.4 Enjeux

| Domaine | Enjeu | Criticité |
|---------|-------|-----------|
| Continuité de service | Interruption SCADA eau ou CSU | Critique |
| Données personnelles | Fuites RGPD (portail, vidéo) | Élevée |
| Réglementaire | Sanctions NIS2 / non-conformité ANSSI | Élevée |
| OT/IT | Propagation ransomware IT → OT | Critique |
| Réputation | Indisponibilité services citoyens | Élevée |
| Souveraineté | Dépendance cloud et infogérance | Moyenne |

### 1.5 Parties prenantes

| Partie prenante | Rôle | Intérêt |
|-----------------|------|---------|
| Élus – Président de métropole | Sponsor | Vision politique, budget |
| Direction générale | Arbitrage stratégique | Performance globale |
| Direction du numéique (DNum) | Maîtrise d'ouvrage SI | Modernisation, open data |
| Pôle SSI / RSSI | Maîtrise d'œuvre sécurité | Conformité, réduction risques |
| Directions métiers (mobilité, eau, énergie, sécurité publique) | Expression de besoins | Continuité opérationnelle |
| Agents et exploitants OT/SCADA | Utilisateurs terrain | Simplicité, fiabilité |
| Citoyens et usagers | Bénéficiaires finaux | Accessibilité, confiance |
| Prestataires infogérants (Infogéo, CloudMunicipal) | Exploitation externalisée | SLA contractuels |
| ANSSI / CNIL / ARS (contrôle) | Autorités | Conformité |
| Opérateurs (RATP locale, ENEDIS, fournisseurs eau) | Partenaires | Interopérabilité |

---

## 2. Gouvernance

### 2.1 Organisation de gouvernance

```
                    ┌─────────────────────────┐
                    │  Sponsor – Président    │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │ Comité de pilotage (CoPil)│
                    │ Trimestriel               │
                    └───────────┬─────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
┌─────────▼─────────┐ ┌────────▼────────┐ ┌─────────▼─────────┐
│ Comité cyber      │ │ Comité urbanisme│ │ Comité conformité │
│ (mensuel)         │ │ SI (bimestriel) │ │ (semestriel)      │
└─────────┬─────────┘ └────────┬────────┘ └─────────┬─────────┘
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │ Équipe projet Métropolis  │
                    │ (Chef de projet + RSSI)   │
                    └───────────────────────────┘
```

### 2.2 Sponsor

**M. Laurent VERRIER** – Président de la Métropole Métropolis  
Valide la feuille de route, alloue le budget programme (1,8 M€ sur 3 ans) et arbitre les risques résiduels majeurs.

### 2.3 Comité de pilotage

| Membre | Fonction | Rôle dans le CoPil |
|--------|----------|-------------------|
| Laurent VERRIER | Président | Sponsor, décision finale |
| Claire DUBOIS | Directrice générale | Alignement stratégique |
| Marc LEFÈVRE | DSI / Directeur du numérique | MOA SI, priorités projets |
| Sophie MARTIN | RSSI | MO sécurité, risques cyber |
| Jean-Paul RENAUD | Directeur mobilité | Représentant métiers critiques |
| Émilie FONTaine | DPO | Conformité RGPD |
| Représentant contrôle de gestion | DAF | Suivi budget |

**Fréquence :** trimestrielle  
**Livrables CoPil :** tableau de bord RSSI, avancement EBIOS, plan de traitement des risques, jalons urbanisme SI.

### 2.4 Équipe projet

| Rôle projet | Nom / profil | Responsabilités |
|-------------|--------------|-----------------|
| Chef de projet | Thomas BERNARD | Planning, coordination, reporting |
| RSSI / Architecte cyber | Sophie MARTIN | PSSI, EBIOS, SOC, conformité |
| Architecte SI | Nathalie ROUX | Urbanisme SI, cartographie Club Urba |
| Responsable OT/SCADA | Pierre GARNIER | Sécurisation industrielle, IEC 62443 |
| Responsable SOC | Karim BENALI | Wazuh, corrélations, playbooks |
| DPO | Émilie FONTAINE | RGPD, AIPD, registre traitements |
| Responsable infra | David LEROY | Datacenter, cloud, réseaux |
| Responsable portail citoyen | Anne PETIT | Applications grand public |
| Infogéreur référent | Infogéo SA | Exploitation, SLA |

### 2.5 Responsabilités clés

- **MOA :** DNum – définition des besoins, recette fonctionnelle
- **MO :** Pôle SSI – exigences sécurité, validation architecture
- **Exploitation :** Infogéo + équipes internes – run, supervision
- **Audit :** Contrôle interne + auditeur externe ISO 27001

### 2.6 Matrice RACI

Légende : **R** = Responsible, **A** = Accountable, **C** = Consulted, **I** = Informed

| Activité | Sponsor | DG | DSI | RSSI | DPO | Chef projet | Métiers | Infogéreur |
|----------|---------|-----|-----|------|-----|-------------|---------|------------|
| Stratégie SI | A | C | R | C | I | I | C | I |
| Cartographie urbanisme | I | I | C | A | I | R | C | C |
| Analyse EBIOS RM | I | C | C | A | C | R | C | I |
| Registre des risques | I | C | C | A | C | R | C | I |
| PSSI / politique IAM | I | A | C | R | C | C | I | I |
| Incidents cyber (SOC) | I | I | I | A | I | C | I | R |
| Portail citoyen (évolutions) | I | I | A | C | C | R | R | R |
| Conformité NIS2 / RGPD | I | A | C | R | R | C | I | C |
| PCA/PRA datacenter | I | A | R | C | I | R | C | R |
| Budget programme | A | R | C | C | I | R | I | I |

---

## 3. Présentation de l'organisation

### 3.1 Missions de la métropole

La Métropole Métropolis exerce des compétences obligatoires et facultatives en matière de :

- **Transports et mobilité** (TCO, stationnement, vélos en libre-service)
- **Eau et assainissement** (production, distribution, qualité)
- **Énergie et éclairage public** (réseaux intelligents, sobriété)
- **Déchets et propreté**
- **Aménagement et attractivité économique**
- **Sécurité publique et tranquillité** (coordination avec forces de l'ordre, vidéoprotection)
- **Numérique et relation usager** (portail, open data, démarches en ligne)

### 3.2 Métiers

| Métier | Missions opérationnelles | SI associé |
|--------|-------------------------|------------|
| Mobilité | Planification, billettique, info voyageurs | ITS, GTF, portail |
| Eau | Production, distribution, télégestion | SCADA eau, GMAO |
| Énergie / éclairage | Pilotage réseaux, maintenance | SCADA énergie |
| Sécurité publique | Supervision urbaine, vidéo, crise | CSU, VMS |
| Relation usager | Accueil numérique, open data | Portail, API |
| Finances / commande publique | Achats, facturation | ERP, portail fournisseurs |

### 3.3 Directions et services

| Entité | Effectif | Périmètre |
|--------|----------|-----------|
| Direction générale | 12 | Pilotage global |
| Direction du numérique (DNum) | 85 | SI, innovation, open data |
| Pôle sécurité des SI (SSI) | 18 | RSSI, SOC, IAM, conformité |
| Direction mobilité | 120 | Transports, voirie |
| Régie eau Métropolis | 95 | Production et distribution eau |
| Direction énergie | 45 | Éclairage, réseaux |
| Direction sécurité publique | 60 | CSU, vidéoprotection |
| Direction finances | 70 | Budget, comptabilité |

### 3.4 Acteurs internes

| Acteur | Rôle | Systèmes utilisés |
|--------|------|-------------------|
| RSSI métropolitain | Gouvernance cyber, EBIOS | GRC, SOC, UCA |
| Exploitants OT/SCADA | Supervision eau/énergie | SCADA, historian |
| Responsables métiers | Pilotage opérationnel | Portail, BI |
| Agents relation usager | Support citoyens | CRM, portail |
| Élus | Décision, communication | Intranet, reporting |
| Agents techniques terrain | Maintenance IoT, capteurs | GMAO mobile |
| Opérateurs CSU | Surveillance vidéo | VMS, CSU |

### 3.5 Acteurs externes

| Acteur | Type | Interaction |
|--------|------|-------------|
| Infogéo SA | Infogéreur | Datacenter, run SI |
| CloudMunicipal | Hébergeur cloud | Portail, open data (PaaS) |
| CyberDef Municipales | SOC externalisé partiel | Triage alertes L2 |
| ENEDIS | Partenaire énergie | Flux techniques réseau |
| Préfecture / ANSSI | Autorité | Notifications incidents |
| CNIL | Autorité | Contrôles RGPD |
| Éditeur SCADA AquaControl | Fournisseur OT | Maintenance, patches |
| Citoyens | Usagers | Portail, applications |

---

## 4. Urbanisme SI

La cartographie suit le métamodèle **Club Urba** (référence ISRC10 / Métropolis) tel qu'implémenté dans Urban Cyber Architect.

### 4.1 Couche métier

#### 4.1.1 Capacités métier

| ID | Capacité | Description |
|----|----------|-------------|
| CAP-M01 | Gérer la mobilité urbaine | Planification, billettique, info usagers |
| CAP-M02 | Produire et distribuer l'eau | Continuité approvisionnement |
| CAP-M03 | Piloter l'énergie et l'éclairage | Sobriété, maintenance |
| CAP-M04 | Assurer la sécurité publique | Supervision, vidéo, crise |
| CAP-M05 | Servir le citoyen numériquement | Portail, démarches, open data |
| CAP-M06 | Piloter la performance métropole | BI, reporting élus |

#### 4.1.2 Processus métier

| Processus | Déclencheur | Résultat | Criticité |
|-----------|-------------|----------|-----------|
| Supervision temps réel des infrastructures | Alarme SCADA / capteur | Service rétabli ou escalade | Critique |
| Gestion des incidents citoyens | Signalement portail / call center | Ticket résolu, SLAs respectés | Élevée |
| Planification mobilité durable | Calendrier / événement | Plan de transport validé | Moyenne |
| Gestion de crise métropolitaine | Incident majeur / alerte | Cellule crise activée | Critique |
| Gestion des accès vidéoprotection | Demande judiciaire / opération | Accès tracé et limité | Élevée |
| Publication open data | Calendrier publication | Jeux de données disponibles | Moyenne |

#### 4.1.3 Activités métier

- Pilotage du trafic routier (ITS)
- Distribution d'eau potable (production → réseau)
- Gestion de l'éclairage public (telecommande armoires)
- Accueil et information citoyenne (portail, guichet)
- Surveillance vidéoprotection (CSU)
- Maintenance préventive équipements IoT

#### 4.1.4 Acteurs métier

| Acteur | Processus concernés |
|--------|---------------------|
| RSSI métropolitain | Tous (gouvernance) |
| Exploitants OT/SCADA | Supervision, eau, énergie |
| Responsables métiers | Mobilité, eau, sécurité publique |
| Élus et direction générale | Crise, arbitrages |
| Prestataires infogérants | Run SI, cloud |
| Opérateurs CSU | Vidéoprotection |
| Citoyens | Relation usager, signalements |

#### 4.1.5 Organisation (vue métier)

- **Métropolis — Métropole territoriale** (entité juridique)
- **Direction du numérique** (MOA SI)
- **Pôle sécurité des systèmes d'information** (MO sécurité)

#### 4.1.6 Flux métier (macro)

```
Citoyen → Signalement → Gestion incident → Résolution → Notification
Capteur IoT → SCADA → Alarme → Exploitant OT → Intervention terrain
Caméra VMS → CSU → Opérateur → Forces ordre (si escalade)
Élu → Reporting BI → Décision stratégique → Planification métier
```

#### 4.1.7 Objectifs et résultats

**Objectifs :**

1. Services publics numériques sécurisés
2. Conformité NIS2 et RGPD
3. Résilience des services urbains critiques

**Résultats attendus :**

- Continuité de service 24/7
- Satisfaction usagers > 85 %
- Réduction incidents majeurs
- Conformité audits NIS2

---

### 4.2 Couche fonctionnelle

#### 4.2.1 Fonctions

| Fonction | Îlot | Description |
|----------|------|-------------|
| F-MOB | Mobilité et transports | ITS, billettique, info voyageurs |
| F-EAU | Eau et assainissement | Télégestion, qualité, maintenance |
| F-ENE | Énergie et éclairage | Pilotage réseaux intelligents |
| F-SEC | Sécurité publique | CSU, VMS, gestion crise |
| F-USG | Relation usager | Portail, CRM, open data |
| F-SUP | Supervision transverse | Alerting, reporting, BI |

#### 4.2.2 Services

| Service | Consommateurs | SLA |
|---------|---------------|-----|
| SVC-PORTAIL | Citoyens, agents | 99,5 % |
| SVC-SCADA-EAU | Exploitants OT | 99,9 % |
| SVC-OPENAPI | Développeurs tiers | 99,0 % |
| SVC-CSU | Opérateurs sécurité | 99,5 % |
| SVC-IAM | Tous SI | 99,9 % |
| SVC-SIEM | SOC | 99,5 % |

#### 4.2.3 Cas d'utilisation

| ID | Cas d'utilisation | Acteur | Fonction |
|----|-------------------|--------|----------|
| UC-01 | S'inscrire sur le portail citoyen | Citoyen | F-USG |
| UC-02 | Consulter horaires transport | Citoyen | F-MOB |
| UC-03 | Signaler un incident voirie | Citoyen | F-USG |
| UC-04 | Traiter alarme SCADA eau | Exploitant OT | F-EAU |
| UC-05 | Consulter flux vidéo CSU | Opérateur | F-SEC |
| UC-06 | Publier jeu open data | Agent DNum | F-USG |
| UC-07 | Investiguer alerte SIEM | Analyste SOC | F-SUP |
| UC-08 | Valider accès privilégié | RSSI | F-SUP |

#### 4.2.4 Décomposition fonctionnelle (îlots / quartiers / zones)

**Îlots fonctionnels :**

- Mobilité et transports
- Eau et assainissement
- Énergie et éclairage
- Sécurité publique et vidéoprotection

**Quartiers fonctionnels :**

- Transport intelligent (ITS)
- Réseau eau potable
- Réseau électrique intelligent
- Vidéosurveillance urbaine
- Gestion des déchets

**Zones fonctionnelles :**

- Supervision centralisée
- Relation usager / portail citoyen
- Alerting et notification
- Reporting réglementaire

---

### 4.3 Couche applicative

#### 4.3.1 Applications

| Application | Éditeur / type | Fonction | Hébergement |
|-------------|----------------|----------|-------------|
| APP-PORTAIL | Développement interne + CloudMunicipal | Portail citoyen | Cloud PaaS |
| APP-SCADA-EAU | AquaControl 4.2 | Supervision OT eau | On-premise OT |
| APP-GTF | Gestion flotte | Mobilité | Datacenter |
| APP-CSU | Centre supervision urbaine | Sécurité publique | Datacenter |
| APP-OPENAPI | Gateway API | Open data | Cloud |
| APP-VMS | VideoManage Pro | Vidéoprotection | Datacenter |
| APP-GMAO | MaintCity | Maintenance | Datacenter |
| APP-BI | Metropolis Analytics | Reporting | Datacenter |
| APP-IAM | KeyMetropolis | IAM / SSO | Datacenter |
| APP-SIEM | Wazuh + stack ELK | SOC | Datacenter |

#### 4.3.2 Interfaces

| Interface | Type | Source | Cible | Protocole |
|-----------|------|--------|-------|-----------|
| IF-01 | API REST | Portail | IAM | HTTPS/OAuth2 |
| IF-02 | API REST | Portail | GTF (mobilité) | HTTPS |
| IF-03 | OPC-UA | SCADA eau | Historian | OPC-UA/TLS |
| IF-04 | RTSP | VMS | CSU | RTSP/TLS |
| IF-05 | SFTP | Open data | Portail externe | SFTP |
| IF-06 | Syslog/CEF | Tous SI | SIEM Wazuh | TLS 514 |
| IF-07 | LDAPS | IAM | AD métropole | LDAPS |
| IF-08 | Webhook | SIEM | ITSM ServiceNow | HTTPS |

#### 4.3.3 APIs

| API | Exposition | Authentification | Données |
|-----|------------|------------------|---------|
| api.metropolis.fr/v1/citoyen | Internet | OAuth2 + MFA | Profil usager |
| api.metropolis.fr/v1/open-data | Internet | Clé API | Jeux ouverts |
| api.metropolis.fr/v1/mobilite | Internet / partenaires | mTLS | Horaires, perturbations |
| api-interne.metropolis.lan/v1/scada | Intranet OT | Certificat + bastion | Télémesures (lecture) |

#### 4.3.4 Dépendances applicatives

```
Portail citoyen → IAM (obligatoire)
Portail citoyen → API mobilité, CRM
CSU → VMS (obligatoire)
SCADA eau → Historian → BI (reporting)
Tous SI corporate → SIEM (logs)
GMAO → SCADA eau (work orders)
```

#### 4.3.5 Décomposition applicative

**Îlots applicatifs :** Portail métropolitain, SCADA eau, Gestion de flotte, CSU  
**Quartiers applicatifs :** Gestion titres transport, Télégestion eau, GMAO, Open data  
**Zones applicatives :** API open data, Moteur alerting, Auth citoyenne, Tableaux de bord

---

### 4.4 Couche technique

#### 4.4.1 Serveurs

| Serveur | Rôle | OS | Criticité |
|---------|------|-----|-----------|
| SRV-SCADA-01 | SCADA eau primaire | Windows Server + AquaControl | Critique |
| SRV-SCADA-02 | SCADA eau secours | Windows Server | Critique |
| CLU-VIRT-01..06 | Cluster VMware datacenter | ESXi 8 | Critique |
| SRV-PORTAIL-01..02 | Apps portail (VM) | Linux RHEL | Élevée |
| SRV-SIEM-01..03 | Wazuh + Indexer | Linux | Élevée |
| SRV-VMS-01 | Enregistrement vidéo | Linux | Élevée |
| SRV-IAM-01 | KeyMetropolis | Linux | Critique |

#### 4.4.2 Réseaux

| Réseau | VLAN / segment | Usage | Séparation |
|--------|----------------|-------|------------|
| NET-OT-EAU | VLAN 110 | SCADA, automates | Air-gap logique via firewall OT |
| NET-CORP | VLAN 10-50 | Bureautique, serveurs | Standard |
| NET-DMZ | VLAN 100 | Portail, reverse proxy | DMZ |
| NET-CSU | VLAN 120 | VMS, postes opérateurs | Filtrage strict |
| NET-IOT | VLAN 130 | Capteurs urbains | Segmentation micro |
| FIBRE-METRO | DWDM | Inter-sites | Redondance anneau |

#### 4.4.3 Cloud

| Service cloud | Fournisseur | Usage | Données |
|---------------|-------------|-------|---------|
| PaaS portail | CloudMunicipal (France) | Front portail citoyen | Internes / sensibles |
| Object storage | CloudMunicipal | Static assets, backups secondaires | Internes |
| CDN | CloudMunicipal | Cache contenu public | Publiques |

#### 4.4.4 Bases de données

| Base | SGBD | Application | Classification |
|------|------|-------------|----------------|
| DB-PORTAIL | PostgreSQL | Portail citoyen | Sensibles (PII) |
| DB-CRM | PostgreSQL | Relation usager | Sensibles |
| DB-HISTORIAN | TimescaleDB | SCADA eau | Critiques (OT) |
| DB-OPENAPI | PostgreSQL | Catalogue API | Internes |
| DB-SIEM | OpenSearch | Wazuh indexer | Internes |
| DB-BI | PostgreSQL | Analytics | Internes |

#### 4.4.5 Sécurité (couche technique)

- Firewalls Palo Alto (IT/OT/DMZ)
- Bastion OT (Wallix) pour accès SCADA
- WAF devant portail citoyen
- Antivirus / EDR (CrowdStrike) sur postes et serveurs
- DLP email (Microsoft Purview)
- HSM virtualisé pour clés IAM

#### 4.4.6 IAM

| Composant | Description |
|-----------|-------------|
| AD métropole | Annuaire agents (5000 comptes) |
| KeyMetropolis | SSO SAML/OAuth2, fédération portail |
| MFA | Obligatoire admin et accès distants |
| PAM | Wallix – sessions privilégiées enregistrées |
| IAM citoyen | Compte unique portail, FranceConnect |

#### 4.4.7 Supervision

| Outil | Périmètre |
|-------|-----------|
| Wazuh SIEM | Logs, FIM, vulnérabilités, alertes |
| Zabbix | Infra, disponibilité serveurs/réseaux |
| SCADA AquaControl | Alarmes process eau |
| Grafana | Tableaux ops + SOC |
| Urban Cyber Architect | Gouvernance, risques, cartographie |

#### 4.4.8 Sauvegardes

| Périmètre | RPO | RTO | Solution |
|-----------|-----|-----|----------|
| SI corporate | 4 h | 4 h | Veeam → site PRA |
| SCADA eau | 1 h | 2 h | Snapshots + export config |
| Vidéo VMS | 24 h | 8 h | Réplication stockage |
| Cloud portail | 1 h | 2 h | Backup CloudMunicipal + runbook |

#### 4.4.9 Sites

- **Datacenter principal Métropolis** – Hôtel de métropole (Tier II)
- **Site secours PRA** – 15 km, réplication async
- **Régie eau — site OT** – SCADA terrain
- **Hôtel de métropole** – CSU, bureaux direction

#### 4.4.10 Postes de travail

- Postes supervision SCADA (OT)
- Postes bureautiques agents (Windows 11)
- Postes salle de crise (multisources vidéo + visio)

---

## 5. Flux SI

### 5.1 Flux utilisateurs

| Flux | Origine | Destination | Canal | Données |
|------|---------|-------------|-------|---------|
| FU-01 | Citoyen (web/mobile) | Portail citoyen | HTTPS | Compte, démarches |
| FU-02 | Agent (intranet) | GMAO / SCADA (via bastion) | HTTPS/RDP | Ordres travail |
| FU-03 | Opérateur CSU | VMS | Client lourd | Flux vidéo |
| FU-04 | Analyste SOC | Wazuh Dashboard | HTTPS | Alertes, logs |
| FU-05 | Élu | BI Metropolis Analytics | HTTPS | Indicateurs |

### 5.2 Flux applicatifs

| Flux | Source | Cible | Fréquence | Données |
|------|--------|-------|-----------|---------|
| FA-01 | Portail | IAM | Temps réel | Auth tokens |
| FA-02 | SCADA eau | Historian | Continu | Télémesures |
| FA-03 | Historian | BI | Horaire | Agrégats |
| FA-04 | VMS | CSU | Temps réel | Métadonnées alertes |
| FA-05 | ITSM | SIEM | Événementiel | Tickets incidents |
| FA-06 | Open data ETL | API publique | Quotidien | Jeux CSV/JSON |

### 5.3 Flux techniques

| Flux | Protocole | Segments traversés | Contrôle |
|------|-----------|-------------------|----------|
| FT-01 | OPC-UA | OT ↔ Historian | Firewall OT allowlist |
| FT-02 | Syslog TLS | CORP → SIEM | Collecteurs dédiés |
| FT-03 | Réplication storage | DC1 ↔ PRA | Fibre dédiée |
| FT-04 | LDAPS | Apps → AD | Domain controllers |
| FT-05 | SNMP | Infra → Zabbix | Lecture seule |

### 5.4 Flux inter-applications

```
[Citoyen] ──HTTPS──► [WAF] ──► [Portail] ──OAuth──► [IAM]
                              └──API──────► [Mobilité API]
                              └──API──────► [CRM]

[Automates eau] ──OPC-UA──► [SCADA] ──► [Historian] ──► [BI]
                                    └──alerte──► [Moteur alerting] ──► [SOC/SIEM]

[Caméras] ──RTSP──► [VMS] ──► [CSU] ──► [Opérateur]
                    └──événement──► [SIEM]

[Tous serveurs/apps] ──logs──► [Wazuh agents] ──► [Indexer] ──► [SOC Dashboard]
```

---

## 6. Inventaire des actifs

### 6.1 Actifs métier

| ID | Actif | Propriétaire | Criticité |
|----|-------|--------------|-----------|
| AM-01 | Processus distribution eau potable | Direction eau | Critique |
| AM-02 | Service mobilité / transports | Direction mobilité | Élevée |
| AM-03 | Dispositif sécurité publique / CSU | Dir. sécurité publique | Élevée |
| AM-04 | Relation citoyenne numérique | DNum | Élevée |
| AM-05 | Gestion crise métropolitaine | DG | Critique |

### 6.2 Applications

*(Voir section 4.3.1 — 10 applications principales recensées)*

Actifs applicatifs secondaires : ERP finances, messagerie (Exchange Online), visioconférence (Teams), GED (SharePoint).

### 6.3 Données

| Actif données | Volume | Localisation | Référentiel |
|---------------|--------|--------------|-------------|
| Comptes citoyens portail | 320 000 | DB-PORTAIL cloud | RGPD |
| Historique télémesures eau | 8 To | Historian on-prem | NIS2 |
| Enregistrements vidéo | 450 To | VMS stockage | RGPD / CNIL vidéo |
| Logs SIEM | 2 To/mois | OpenSearch | ISO 27001 |
| Jeux open data | 120 Go | Object storage | Licence ouverte |

### 6.4 Infrastructures

| Actif | Quantité | Site |
|-------|----------|------|
| Serveurs physiques | 48 | DC + PRA |
| VMs production | 186 | DC + PRA |
| Switches core | 8 | DC |
| Firewalls | 6 | DC + OT |
| Automates SCADA | 42 | Régies eau |
| Caméra IP | 1 850 | Agglomération |

### 6.5 Cloud

| Ressource | Type | Région |
|-----------|------|--------|
| Portail PaaS | 12 containers | France (CloudMunicipal) |
| Object storage | 15 To | France |
| CDN | Global edge FR | EU |

### 6.6 Équipements

Capteurs IoT urbains (800), armoires éclairage connectées (2 400), bornes vélo (350), panneaux info voyageurs (120).

### 6.7 Identités

| Type | Volume | IAM |
|------|--------|-----|
| Agents AD | 5 000 | AD + KeyMetropolis |
| Comptes privilégiés | 85 | PAM Wallix |
| Comptes citoyens | 320 000 | IAM portail |
| Comptes prestataires | 120 | AD + MFA obligatoire |
| Comptes machine / service | 340 | GMSA / certificats |

---

## 7. Classification des données

### 7.1 Niveaux de classification

| Niveau | Définition | Exemples Métropolis | Contrôles minimaux |
|--------|------------|---------------------|-------------------|
| **Publiques** | Diffusion libre | Open data, horaires transport, communiqués | Intégrité |
| **Internes** | Usage interne métropole | Organigrammes, procédures internes, logs non sensibles | Auth + traçabilité |
| **Sensibles** | Impact modéré si divulgation | Données agents, plans maintenance, stats non publiées | Chiffrement transit/repos, RBAC |
| **Critiques** | Impact sévere (OT, sécurité, PII masse) | SCADA eau, flux vidéo live, MOP OT, health PII | Segmentation, MFA, bastion, chiffrement fort, DLP |

### 7.2 Matrice données / systèmes

| Donnée | Classification | Systèmes | Rétention |
|--------|----------------|----------|-----------|
| Identité citoyen | Sensible | Portail, IAM | Durée compte + 3 ans |
| Vidéo publique space | Critique | VMS, CSU | 30 jours (arrêté préfectoral) |
| Télémesures eau | Critique | SCADA, Historian | 10 ans |
| Logs authentification | Interne | SIEM | 1 an |
| Tickets incidents cyber | Sensible | ITSM, SIEM | 5 ans |

### 7.3 Règles de manipulation

- Interdiction stockage **critiques** sur postes nomades non chiffrés
- Anonymisation obligatoire pour jeux open data dérivés de PII
- Accès vidéo CSU : habilitation nominative + journalisation
- Partage prestataire : clauses RGPD + NIS2 + audit annuel

---

## 8. Analyse des dépendances

### 8.1 Dépendances applications

| Application | Dépend de | Impact si indisponible | Mitigation |
|-------------|-----------|------------------------|------------|
| Portail citoyen | IAM, Cloud PaaS, WAF | Pas d'accès usagers | Cache statique, PRA cloud |
| SCADA eau | Automates, réseau OT, SRV-SCADA | Risque production eau | Serveur secours, mode dégradé local |
| CSU | VMS, réseau CSU | Perte supervision vidéo | Redondance enregistreurs |
| BI | Historian, DB-BI | Perte reporting | Reports différés |
| SOC | SIEM, AD, collecteurs | Angles morts sécurité | Collecte locale buffer |

### 8.2 Dépendances infrastructures

| Composant | Single point of failure ? | Redondance |
|-----------|---------------------------|------------|
| Cluster VMware | Non | 2 datacenters |
| Firewall OT | Oui (pair HA) | Active/passive |
| Fibre métro anneau | Non | Double chemin |
| AD primary DC | Non | 2 DC geo |

### 8.3 Dépendances services

| Service tiers | SLA contractuel | Sortie de secours |
|-------------|-----------------|-------------------|
| Infogéo (run) | 99,5 % | Reversibilité 6 mois |
| CloudMunicipal | 99,9 % | Runbook migration PaaS |
| AquaControl support | 8×5 | Stock pièces + contrat premium |
| ENEDIS (énergie) | N/A | Groupes électrogènes sites critiques |

### 8.4 Dépendances fournisseurs (NIS2 / supply chain)

| Fournisseur | Criticité | Pays | Évaluation risque |
|-------------|-----------|------|-------------------|
| Infogéo SA | Élevée | FR | Annuelle |
| CloudMunicipal | Élevée | FR | Semestrielle |
| AquaControl | Critique (OT) | EU | Annuelle + patches |
| CrowdStrike | Moyenne | US | Contractuelle SCC |
| Wazuh (OSS) | Moyenne | Community | Veille + support interne |

---

## 9. Cybersécurité

### 9.1 Architecture de sécurité

Architecture ** défense en profondeur ** en 5 zones :

1. **Internet / usagers** – WAF, CDN, anti-DDoS
2. **DMZ** – Reverse proxy, API gateway
3. **SI corporate** – EDR, segmentation VLAN, SIEM
4. **Zone OT** – Firewall dédié, bastion, allowlist protocoles
5. **CSU / vidéo** – Réseau isolé, accès nominatif

Principes : moindre privilège, Zero Trust pour accès admin, séparation OT/IT, journalisation centralisée.

### 9.2 IAM

- SSO unique agents via KeyMetropolis (SAML 2.0)
- MFA obligatoire : admins, télétravail, accès OT bastion
- Revue trimestrielle des accès privilégiés (PAM)
- FranceConnect pour citoyens (fédération identité)

### 9.3 Segmentation

| Zone | Contrôle | Flux autorisés |
|------|----------|----------------|
| OT eau | Firewall OT L7 | OPC-UA vers historian uniquement |
| DMZ | WAF + FW | 443 vers portail |
| CSU | FW dédié | RTSP interne, pas Internet |
| IoT | Micro-segmentation | MQTT broker → IoT hub |

### 9.4 SOC

- **Modèle :** hybride internalisé + triage L2 CyberDef Municipales
- **Équipe :** 4 analystes SOC + RSSI (Métropolis)
- **Plages :** 8×5 internalisé, astreinte RSSI 24/7 incidents P1
- **Processus :** NIST incident response, playbooks ransomware / OT / fuite données

### 9.5 SIEM

- **Solution :** Wazuh 4.x (agents) + Indexer OpenSearch + Dashboard
- **Sources :** AD, firewalls, serveurs Linux/Windows, WAF, SCADA (logs applicatifs), VMS
- **Use cases :** brute force, malware, FIM configs SCADA, exfiltration, comptes privilégiés
- **Rétention :** 12 mois online, 36 mois archive froide

### 9.6 SOAR

- **Maturité actuelle :** partielle (playbooks manuels documentés)
- **Cible :** intégration Wazuh → ServiceNow → notifications Teams
- **Playbooks prioritaires :** phishing, malware endpoint, alerte OT, indisponibilité portail

### 9.7 Wazuh

| Composant | Rôle |
|-----------|------|
| Wazuh manager | Règles, corrélation, API |
| Wazuh indexer | Stockage alertes/events |
| Wazuh dashboard | Visualisation SOC |
| Agents | 220 agents déployés (objectif 100 %) |

Connecteur Urban Cyber Architect : corrélations SOC ↔ entités urbanisme ↔ risques GRC.

### 9.8 Journalisation

| Source | Format | Destination |
|--------|--------|-------------|
| AD / IAM | Windows Event / JSON | Wazuh |
| Firewalls | CEF | Wazuh |
| SCADA | Fichiers + syslog | Wazuh via collecteur OT |
| Portail | JSON applicatif | Wazuh + stockage 90 j |
| PAM Wallix | Session logs | Wazuh + archive 1 an |

### 9.9 Supervision sécurité

- KPI SOC : MTTD, MTTR, faux positifs, couverture agents
- KPI RSSI : conformité NIS2, écarts audit, risques ouverts
- Tableaux de bord : Urban Cyber Architect (Dashboard RSSI), Grafana SOC

---

## 10. Analyse de risques

Document préparatoire **EBIOS RM** — Ateliers 1 à 5.

### 10.1 Contexte EBIOS

| Élément | Valeur |
|---------|--------|
| Périmètre étude | SI Métropolis OT/IT |
| Méthode | EBIOS RM (ANSSI) |
| Référentiel | ISO 27005, NIS2, RGPD |
| Responsable | RSSI Sophie MARTIN |

### 10.2 Valeurs métier (Atelier 1)

| VM | Valeur | Impact D/I/C | Commentaire |
|----|--------|--------------|-------------|
| VM-01 | Continuité approvisionnement eau | 5/5/5 | Service public essential |
| VM-02 | Confiance citoyenne (portail) | 4/4/4 | Réputation |
| VM-03 | Sécurité personnes (CSU, crise) | 5/5/4 | Sécurité publique |
| VM-04 | Conformité réglementaire | 4/5/4 | NIS2, RGPD |

### 10.3 Biens supports (Atelier 2)

| BS | Bien support | VM associées | Criticité |
|----|--------------|--------------|-----------|
| BS-01 | SCADA eau + automates | VM-01 | Critique |
| BS-02 | Datacenter principal | VM-01, VM-02, VM-04 | Critique |
| BS-03 | Portail citoyen + IAM | VM-02, VM-04 | Élevée |
| BS-04 | VMS + CSU | VM-03 | Élevée |
| BS-05 | SIEM / SOC | VM-04, VM-03 | Élevée |
| BS-06 | Réseau fibre métropolitain | Toutes | Élevée |

### 10.4 Événements redoutés (Atelier 3)

| ER | Description | VM | Gravité |
|----|-------------|-----|---------|
| ER-01 | Arrêt production eau (cyber OT) | VM-01 | Maximale |
| ER-02 | Fuite massive données citoyens | VM-02, VM-04 | Majeure |
| ER-03 | Indisponibilité portail > 48 h | VM-02 | Majeure |
| ER-04 | Manipulation flux vidéo / sabotage CSU | VM-03 | Majeure |
| ER-05 | Ransomware IT propagé vers OT | VM-01, VM-04 | Maximale |

### 10.5 Sources de risque (Atelier 3)

| SR | Source | Type |
|----|--------|------|
| SR-01 | Cybercriminels (ransomware) | Externe |
| SR-02 | Insiders / erreur agent | Interne |
| SR-03 | Prestataires compromis | Tierce partie |
| SR-04 | Vulnérabilités non corrigées | Technique |
| SR-05 | Défaillance cloud fournisseur | Tierce partie |

### 10.6 Scénarios stratégiques (extrait)

| SS | Source → ER | Vraisemblance initiale |
|----|-------------|------------------------|
| SS-01 | SR-01 → ER-05 (ransomware IT→OT) | Élevée |
| SS-02 | SR-03 → ER-02 (fuite via infogéreur) | Moyenne |
| SS-03 | SR-04 → ER-01 (exploit SCADA) | Moyenne |

### 10.7 Mesures de sécurité existantes (Atelier 4)

- Segmentation OT/IT + bastion
- SIEM Wazuh + SOC
- PCA/PRA datacenter
- MFA admins, PAM
- Procédure gestion incident cyber
- Sauvegardes SCADA testées semestriellement

### 10.8 Risques résiduels et traitement (Atelier 5)

| Risque | Décision | Mesures complémentaires | Échéance |
|--------|----------|-------------------------|----------|
| R-01 Ransomware OT | Réduire | EDR OT, backups air-gap, exercice crise | T2 2025 |
| R-02 Fuite PII portail | Réduire | DLP, pentest annuel, AIPD | T1 2025 |
| R-03 Indisponibilité cloud | Accepter toléré | PRA cloud, multi-région | T3 2025 |
| R-04 SOAR immature | Réduire | Automatisation playbooks Wazuh | T4 2025 |

---

## 11. Conformité

### 11.1 ISO 27001

| Domaine | État | Écarts ouverts |
|---------|------|----------------|
| Politiques SMI | En place (PSSI v3) | Revue annuelle planifiée |
| Gestion actifs | Cartographie UCA en cours | Inventaire OT 92 % |
| Contrôle accès | IAM + PAM | Revue accès prestataires |
| Cryptographie | Chiffrement transit/repos partiel | OT legacy |
| SOC / incidents | Opérationnel | MTTR à améliorer |
| Continuité | PCA/PRA testés | Exercice OT annuel |
| Conformité | Veille NIS2/RGPD | Registre risques à jour |
| Audits internes | Semestriels | 3 NC mineures ouvertes |

**Certification visée :** ISO 27001:2022 — audit blanc T4 2025.

### 11.2 ISO 27005

- Processus gestion des risques aligné EBIOS RM
- Échelles impact/probabilité documentées
- Lien registre risques ↔ plan de traitement ↔ SoA

### 11.3 EBIOS RM

- Atelier 1 : terminé (VM, périmètre)
- Atelier 2 : terminé (BS, import urbanisme)
- Atelier 3 : en cours (scénarios)
- Atelier 4 : planifié T3 2025
- Atelier 5 : planifié T4 2025

### 11.4 NIS2

| Exigence | Mise en œuvre Métropolis |
|----------|-------------------------|
| Gestion risques | EBIOS + registre GRC |
| Incidents | Notification ANSSI < 24 h (procédure) |
| Continuité | PCA/PRA |
| Supply chain | Évaluation prestataires critiques |
| Sécurité OT | Segmentation + IEC 62443 (cible) |

**Statut opérateur services essentiels :** métropole > 500 000 hab. — périmètre NIS2 confirmé.

### 11.5 RGPD

| Traitement | Base légale | DPO validé |
|------------|-------------|------------|
| Comptes portail citoyen | Exécution service public | Oui |
| Vidéoprotection | Mission sécurité publique | Oui + CNIL |
| Logs SIEM | Intérêt légitime sécurité | Oui |
| Open data | Mission publique | Anonymisation |

AIPD portail et vidéo à jour. Registre des activités de traitement maintenu.

### 11.6 DORA

Non applicable directement (non entité financière). **Veille** pour partenaires bancaires (paiement en ligne futur).

### 11.7 ANSSI

- Référentiel **SecNumCloud** pour cloud portail (CloudMunicipal en cours certification)
- Recommandations **guide SI collectivités**
- **IEC 62443** pour périmètre OT eau (roadmap 2025-2026)
- Exercices **CIOT** participés en 2024

---

## 12. Livrables attendus

### 12.1 Cartographies (Urban Cyber Architect / Club Urba)

| Livrable | Format | Source UCA | Statut cible |
|----------|--------|------------|--------------|
| Cartographie métier | Club Urba + exports PDF | Moteur urbanisme | Complet |
| Cartographie fonctionnelle | Club Urba | Moteur urbanisme | Complet |
| Cartographie applicative | Club Urba + diagrammes | Moteur urbanisme | Complet |
| Cartographie technique | Club Urba | Moteur urbanisme | Complet |
| Diagrammes de flux | Annexes flux SI (section 5) | Export PDF | Complet |

### 12.2 Documents d'architecture

| Livrable | Acronyme | Description | Responsable |
|----------|----------|-------------|-------------|
| Dossier architecture technique | **DAT** | Infra, cloud, OT, sécurité | Architecte SI |
| Dossier d'exploitation | **DEX** | Run, SLA, procédures | Infogéo + DNum |
| Politique SSI | **PSSI** | Règles sécurité | RSSI |

### 12.3 GRC / Risques

| Livrable | Module UCA | Fréquence |
|----------|------------|-----------|
| Registre des risques | GRC | Continu |
| Plan de traitement des risques | GRC PTR | Trimestriel |
| Déclaration d'applicabilité | SoA ISO 27001 | Annuel |
| Tableau de bord RSSI | Dashboard RSSI | Mensuel |
| Rapport de gouvernance | Livrables auto | Trimestriel (CoPil) |

### 12.4 Livrables automatiques (module Livrables UCA)

- Plan de management de projet Métropolis
- Rapport EBIOS synthèse
- Rapport conformité NIS2/RGPD
- Export registre risques (PDF/XLSX)
- Rapport SOC mensuel (alertes, MTTD/MTTR)

### 12.5 Planning de production

| Phase | Livrables | Échéance |
|-------|-----------|----------|
| Phase 1 | Note explicative, cartographies v1 | T2 2025 |
| Phase 2 | EBIOS A1-A3, registre risques | T3 2025 |
| Phase 3 | DAT, PSSI v4, SoA | T4 2025 |
| Phase 4 | DEX, rapport gouvernance, certification ISO | T2 2026 |

---

## Annexes

### Annexe A — Correspondance template Urban Cyber Architect

| Élément note explicative | Emplacement UCA |
|--------------------------|-----------------|
| Objectifs / référentiels | Projet → modale création |
| Club Urba zones | Template `metropolis` / urbanisme |
| Acteurs projet | Onglet Équipe / rôles RSSI, architecte… |
| Activité projet | Onglet Activité / `project_activity` |
| EBIOS | Module `/ebios?project=` |
| GRC | Registre, PTR, SoA, Dashboard RSSI |
| SOC | Wazuh, corrélations |
| Livrables | Module `/livrables?project=` |

### Annexe B — Référentiels projet

- RGPD
- NIS2
- ISO 27001
- ISO 27005
- EBIOS RM
- IEC 62443 (OT)
- ANSSI (collectivités, SecNumCloud)

### Annexe C — Glossaire

| Terme | Définition |
|-------|------------|
| CSU | Centre de supervision urbaine |
| OT | Operational Technology (SCADA, automates) |
| SIEM | Security Information and Event Management |
| SOAR | Security Orchestration, Automation and Response |
| PSSI | Politique de sécurité des systèmes d'information |
| SoA | Statement of Applicability (ISO 27001) |
| VM | Valeur métier (EBIOS) |
| BS | Bien support (EBIOS) |
| ER | Événement redouté (EBIOS) |

---

*Document de référence — Métropolis – Sécurité publique & Services numériques*  
*Alimentation plateforme Urban Cyber Architect — usage : urbanisme, EBIOS RM, GRC, SOC, livrables, agents IA.*
