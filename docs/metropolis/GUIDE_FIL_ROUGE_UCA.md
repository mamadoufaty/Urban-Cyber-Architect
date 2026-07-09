# GUIDE FIL ROUGE — URBAN CYBER ARCHITECT

**De l’urbanisme SI à EBIOS RM, PSSI et livrables**

**Cas pédagogique :** Métropolis — Métropole de 800 000 habitants  
**Module :** ISRC10 — Urban Cyber Architect  
**Public :** RSSI, architectes SI, consultants cyber, auditeurs, étudiants  
**Durée estimée :** 2 à 3 jours (formation) ou 5 demi-journées (auto-formation)

---

## Comment utiliser ce guide

Ce document est un **parcours pas à pas** dans la plateforme **Urban Cyber Architect (UCA)**.  
Chaque section indique **où cliquer**, **quoi saisir** et **comment vérifier** le résultat.

**Prérequis :**

- Compte utilisateur avec accès aux modules : Projets, Urbanisme, EBIOS RM, GRC, SOC, Livrables
- Navigateur récent (Chrome, Edge, Firefox)
- Backend UCA et frontend accessibles (local ou déployé)

**Documents complémentaires :**

- `docs/metropolis/NOTE_EXPLICATIVE_DU_PROJET.md` — dossier d’architecture de référence
- Template plateforme : **Exemple — Smart City (Métropolis)**

**Légende des encadrés :**

| Symbole | Signification |
|---------|---------------|
| 🖱️ | Action dans l’interface |
| ✏️ | Texte à saisir tel quel ou à adapter |
| ✅ | Point de contrôle |
| 💡 | Conseil pédagogique |

---

## Vue d’ensemble du parcours

```
1. Créer le projet Métropolis
        ↓
2. Saisir les 5 couches Club Urba (urbanisme SI)
        ↓
3. Modéliser les flux SI
        ↓
4. Constituer l’équipe projet + journal d’activité
        ↓
5. EBIOS RM — Ateliers 1 à 5
        ↓
6. GRC — Registre des risques, PTR, SoA, Dashboard RSSI
        ↓
7. SOC — Wazuh, corrélations
        ↓
8. Livrables automatiques (PDF / DOCX / Markdown)
        ↓
9. Synthèse direction (Dashboard projet 360°)
```

---

# 1. Création du projet

## 1.1 Contexte pédagogique

**Métropolis** est une métropole fictive de **800 000 habitants** engagée dans un **audit de cybersécurité prédictive** couvrant :

- infrastructures critiques urbaines (eau, énergie, transport)
- sécurité publique (CSU, vidéoprotection)
- services numériques citoyens (portail, open data)
- transport intelligent (ITS)
- smart grid et gestion de l’eau
- télécommunications et fibre métropolitaine
- **SIEM centralisé (Wazuh)** et **dashboard prédictif** RSSI

## 1.2 Accès à l’écran

🖱️ Menu **Principal → Projets** (`/projects`)  
🖱️ Bouton **+ Nouveau projet**

## 1.3 Valeurs à saisir dans la modale

| Champ | Valeur à saisir |
|-------|-----------------|
| **Type de création** | **Modèle exemple** → *Exemple — Smart City (Métropolis)* **ou** Projet vierge si vous saisissez tout manuellement |
| **Nom** | `Métropolis – Sécurité publique & Services numériques` |
| **Code** | `metropolis-isrc10` |
| **Description** | `Projet fil rouge ISRC10 — audit cybersécurité prédictive, infrastructures critiques, SIEM Wazuh, dashboard RSSI et conformité NIS2/RGPD pour métropole 800 000 hab.` |
| **Client** | `Métropole Métropolis` |
| **Organisation** | Sélectionner l’organisation métropole (ex. *Métropolis Test* en environnement de démo) |
| **Statut** | `En cours` |
| **Priorité** | `Haute` |
| **Date début** | `2025-01-15` |
| **Date fin** | `2026-12-31` |
| **Responsable** | Utilisateur RSSI / chef de projet (ex. compte `rssi` ou `admin`) |
| **Référentiels** | Cocher : **RGPD**, **NIS2**, **EBIOS RM**, **ISO 27001**, **ISO 27005**, **ANSSI** |
| **Tags** | `fil-rouge, isrc10, smart-city, securite-publique, siem, wazuh, audit-predictif` |

🖱️ **Créer le projet**

## 1.4 Ouvrir le projet actif

🖱️ Dans le tableau, bouton **Ouvrir**  
→ URL : `/projects/{id}`  
→ Le projet devient **projet actif** (badge en haut de l’écran)

✅ Vérifier : onglet **Dashboard** affiche nom, code, référentiels, tags  
✅ Vérifier : barre **Projet actif** visible dans le header

## 1.5 Équipe projet (recommandé)

🖱️ Onglet **Équipe** → Ajouter les membres :

| Utilisateur | Rôle projet |
|-------------|-------------|
| Compte RSSI | `rssi` |
| Compte admin / architecte | `architecte_si` |
| Compte RSSI ou dédié | `architecte_cyber` |
| Compte métier | `responsable_metier` |
| Compte SOC | `soc_manager` |
| Compte DPO (si existant) | `dpo` |
| Compte chef de projet | `chef_projet` |

✅ Vérifier : onglet **Activité** enregistre `member.added`

---

# 2. Couche métier

## 2.1 Accès urbanisme

🖱️ Projet Métropolis → onglet **Urbanisme SI** → **Moteur d’urbanisme**  
   ou menu **Urbanisme → Moteur d’urbanisme** (`/schema-urbanisme?project={id}`)

🖱️ Vérifier que le sélecteur de projet en haut pointe bien sur **Métropolis**

## 2.2 Méthode de saisie Club Urba

Pour chaque élément :

1. Sélectionner la **couche** (Métier, Organisation, Fonctionnel, Applicatif, Technique)
2. Choisir la **zone** (objectifs, processus, acteurs…)
3. 🖱️ **Assistant urbanisme** ou saisie directe dans l’éditeur Club Urba
4. Créer l’**entité** avec label + description
5. Relier via **relations** (ex. *processus pilote objectif*)

💡 Si vous avez utilisé le **modèle Métropolis**, des éléments sont préremplis : complétez-les, ne les supprimez pas sans raison pédagogique.

---

## 2.3 Métier 1 — Sécurité publique

| Attribut | Contenu à saisir |
|----------|------------------|
| **Nom** | `Sécurité publique` |
| **Finalité** | Assurer la tranquillité publique, la coordination de crise et la supervision vidéo urbaine |
| **Enjeux** | Continuité CSU 24/7 ; conformité CNIL vidéo ; non-divulgation flux sensibles |
| **Acteurs** | Direction sécurité publique, Opérateurs CSU, RSSI, Forces de l’ordre (externe), Prestataire VMS |
| **Processus associés** | `Gestion de crise métropolitaine`, `Supervision temps réel des infrastructures` |
| **Données manipulées** | Flux vidéo, alarmes CSU, logs accès, rapports d’incident (classification **Critique**) |
| **Criticité** | **Critique** |

**Entités Club Urba à créer / vérifier :**

| Type | Label | Zone |
|------|-------|------|
| Objectif | `Sécurité publique et résilience urbaine` | métier / objectifs |
| Processus | `Gestion de crise métropolitaine` | métier / processus |
| Activité | `Surveillance vidéoprotection CSU` | métier / activités |
| Résultat | `Continuité de service 24/7` | métier / résultats |

---

## 2.4 Métier 2 — Transport intelligent

| Attribut | Contenu |
|----------|---------|
| **Nom** | `Transport intelligent` |
| **Finalité** | Piloter mobilité urbaine, information voyageurs, billettique |
| **Enjeux** | Disponibilité ITS ; intégrité données transport ; interopérabilité |
| **Acteurs** | Direction mobilité, Exploitants ITS, Usagers, Opérateur transport |
| **Processus** | `Planification mobilité durable`, `Gestion des incidents citoyens` |
| **Données** | Horaires, perturbations, données billettique (Sensibles) |
| **Criticité** | **Élevée** |

**Entités :**

- Objectif : `Mobilité durable et fluide`
- Processus : `Planification mobilité durable`
- Activité : `Pilotage du trafic routier`

---

## 2.5 Métier 3 — Énergie urbaine (smart grid)

| Attribut | Contenu |
|----------|---------|
| **Nom** | `Énergie urbaine` |
| **Finalité** | Piloter réseaux électriques intelligents et éclairage public |
| **Enjeux** | Continuité éclairage ; cyber OT ; sobriété énergétique |
| **Acteurs** | Direction énergie, Exploitants SCADA énergie, ENEDIS |
| **Processus** | `Supervision temps réel des infrastructures` |
| **Données** | Télémesures compteurs, états armoires (Critiques OT) |
| **Criticité** | **Critique** |

---

## 2.6 Métier 4 — Gestion de l’eau

| Attribut | Contenu |
|----------|---------|
| **Nom** | `Gestion de l’eau` |
| **Finalité** | Production et distribution eau potable, télégestion réseau |
| **Enjeux** | Service public essential NIS2 ; sécurité SCADA ; qualité eau |
| **Acteurs** | Régie eau, Exploitants OT/SCADA, RSSI, Prestataire AquaControl |
| **Processus** | `Supervision temps réel des infrastructures` |
| **Données** | Télémesures pression/débit, alarmes SCADA (Critiques) |
| **Criticité** | **Critique** |

---

## 2.7 Métier 5 — Services numériques citoyens

| Attribut | Contenu |
|----------|---------|
| **Nom** | `Services numériques citoyens` |
| **Finalité** | Portail citoyen, démarches en ligne, open data |
| **Enjeux** | RGPD ; disponibilité 99,5 % ; confiance usagers |
| **Acteurs** | DNum, Agents relation usager, Citoyens, DPO |
| **Processus** | `Gestion des incidents citoyens`, `Accueil et information citoyenne` |
| **Données** | Comptes citoyens, tickets, jeux open data (Sensibles / Internes) |
| **Criticité** | **Élevée** |

---

## 2.8 Tableau récapitulatif couche métier

| Métier | Processus clés | Criticité | Objectif lié |
|--------|----------------|-----------|--------------|
| Sécurité publique | Crise, supervision | Critique | Résilience urbaine |
| Transport intelligent | Planification mobilité | Élevée | Services numériques |
| Énergie urbaine | Supervision infra | Critique | Résilience |
| Gestion de l’eau | Supervision SCADA | Critique | Conformité NIS2 |
| Services numériques | Incidents citoyens | Élevée | RGPD / satisfaction |

✅ **Contrôle :** barre de progression urbanisme > 30 % sur la couche Métier  
✅ **Contrôle :** export PDF cartographie disponible depuis le moteur d’urbanisme

---

# 3. Couche organisationnelle

## 3.1 Directions et services à modéliser

| Entité organisation | Type Club Urba | Label |
|---------------------|--------------|-------|
| Métropole Métropolis | organisation | `Métropolis — Métropole territoriale` |
| Direction du numérique | organisation | `Direction du numérique (DNum)` |
| Pôle SSI | organisation | `Pôle sécurité des systèmes d'information` |
| Direction mobilité | organisation | `Direction mobilité` |
| Régie eau | organisation | `Régie eau Métropolis` |
| Direction sécurité publique | organisation | `Direction sécurité publique` |

## 3.2 Acteurs internes

| Acteur | Type | Rôle |
|--------|------|------|
| RSSI métropolitain | acteur | Gouvernance cyber, EBIOS, SOC |
| Exploitants OT/SCADA | acteur | Run eau / énergie |
| Responsables métiers | acteur | MOA métier |
| Opérateurs CSU | acteur | Supervision vidéo |
| Élus / Direction générale | acteur | Arbitrage, crise |
| DPO | acteur | Conformité RGPD |

## 3.3 Acteurs externes

| Acteur | Type | Commentaire |
|--------|------|-------------|
| Infogéo SA | acteur (externe) | Infogérant datacenter |
| CloudMunicipal | acteur (externe) | Hébergeur cloud portail |
| CyberDef Municipales | acteur (externe) | SOC L2 externalisé |
| ANSSI / CNIL | acteur (externe) | Autorités |

## 3.4 Procédures et opérations

| Label | Zone |
|-------|------|
| `Procédure gestion d'incident cyber` | organisation / procedures |
| `Procédure gestion des changements` | organisation / procedures |
| `Procédure continuité d'activité` | organisation / procedures |
| `Supervision SOC municipal` | organisation / operations |
| `Exploitation SCADA eau et énergie` | organisation / operations |

## 3.5 RACI simplifié (à consigner en description d’entité « Pôle SSI »)

| Activité | Sponsor | DSI | RSSI | Métiers | Infogéreur |
|----------|---------|-----|------|---------|------------|
| Urbanisme SI | I | A | R | C | C |
| EBIOS RM | I | C | A/R | C | I |
| SOC / SIEM | I | I | A | I | R |
| Portail citoyen | I | A | C | R | R |
| PCA/PRA | A | R | C | C | R |

✅ **Contrôle :** au moins 6 acteurs et 3 procédures saisis  
✅ **Contrôle :** relations *acteur réalise operation* créées

---

# 4. Couche fonctionnelle

## 4.1 Fonctions métier (îlots fonctionnels)

| Îlot | Label à saisir | Métier source |
|------|----------------|---------------|
| IF-01 | `Mobilité et transports` | Transport intelligent |
| IF-02 | `Eau et assainissement` | Gestion de l'eau |
| IF-03 | `Énergie et éclairage` | Énergie urbaine |
| IF-04 | `Sécurité publique et vidéoprotection` | Sécurité publique |
| IF-05 | `Relation usager / portail citoyen` | Services numériques |

## 4.2 Services fonctionnels (zones)

| Service | Zone | Consommateurs |
|---------|------|---------------|
| `Supervision centralisée` | zones | CSU, SOC, exploitants |
| `Alerting et notification` | zones | Tous métiers critiques |
| `Reporting réglementaire` | zones | RSSI, DPO, élus |
| `Transport intelligent (ITS)` | quartiers | Usagers, mobilité |

## 4.3 Cas d’usage à documenter

| ID | Cas d’usage | Acteur | Îlot |
|----|-------------|--------|------|
| UC-01 | Consulter flux vidéo CSU | Opérateur CSU | Sécurité publique |
| UC-02 | Signaler incident voirie | Citoyen | Services numériques |
| UC-03 | Traiter alarme SCADA eau | Exploitant OT | Gestion de l'eau |
| UC-04 | Investiguer alerte SIEM | Analyste SOC | Supervision |
| UC-05 | Publier open data | Agent DNum | Services numériques |
| UC-06 | Consulter dashboard prédictif RSSI | RSSI | Reporting |

## 4.4 Exigences fonctionnelles (propriétés entité / description)

| ID | Exigence |
|----|----------|
| EF-01 | Centraliser les logs IT/OT dans le SIEM Wazuh |
| EF-02 | Corréler alertes SOC avec entités urbanisme et risques GRC |
| EF-03 | Fournir un dashboard prédictif RSSI (risques, incidents, conformité) |
| EF-04 | Permettre la gestion des accès vidéo nominative CSU |
| EF-05 | Assurer l’interopérabilité portail ↔ API mobilité |

## 4.5 Exigences non fonctionnelles

| ID | Exigence | Cible |
|----|----------|-------|
| ENF-01 | Disponibilité portail citoyen | 99,5 % |
| ENF-02 | Disponibilité SCADA eau | 99,9 % |
| ENF-03 | MTTD incident cyber (SOC) | < 30 min |
| ENF-04 | RTO datacenter | ≤ 4 h |
| ENF-05 | Rétention logs SIEM | 12 mois online |

✅ **Contrôle :** 5 îlots + 4 zones fonctionnelles renseignés

---

# 5. Couche applicative

## 5.1 Applications à saisir

| Application | Îlot applicatif | Criticité | Description courte |
|-------------|-----------------|-----------|-------------------|
| `Portail métropolitain` | Portail métropolitain | Élevée | Démarches citoyennes, SSO |
| `SCADA eau AquaControl` | SCADA eau | Critique | Supervision OT eau |
| `Centre supervision urbaine (CSU)` | CSU | Critique | Supervision sécurité publique |
| `VideoManage Pro (VMS)` | Vidéo | Critique | Enregistrement caméras |
| `API Management / Open data` | API open data | Élevée | Exposition API |
| `KeyMetropolis (IAM)` | Auth citoyenne | Critique | SSO agents + citoyens |
| `Wazuh SIEM` | Moteur alerting | Élevée | SIEM centralisé |
| `Metropolis Analytics` | Tableaux de bord | Élevée | Dashboard prédictif RSSI |
| `GMAO MaintCity` | GMAO | Moyenne | Maintenance équipements |

## 5.2 Interfaces et API

| Interface | Type | Source → Cible | Protocole |
|-----------|------|----------------|-----------|
| IF-POR-IAM | API REST | Portail → IAM | HTTPS/OAuth2 |
| IF-POR-MOB | API REST | Portail → Mobilité | HTTPS |
| IF-VMS-CSU | RTSP | VMS → CSU | RTSP/TLS |
| IF-SCADA-HIST | OPC-UA | SCADA → Historian | OPC-UA |
| IF-LOG-SIEM | Syslog | Tous SI → Wazuh | TLS 514 |

## 5.3 Dépendances applicatives

```
Portail → IAM (obligatoire)
CSU → VMS (obligatoire)
SCADA eau → Historian → Analytics
Toutes apps → Wazuh (agents)
Portail → API Management → Mobilité
```

🖱️ Créer les **relations** applicatives dans le moteur d’urbanisme (couche Applicatif → Technique si besoin).

## 5.4 Données échangées

| Flux | Données | Classification |
|------|---------|----------------|
| Portail ↔ IAM | Tokens, profils | Sensibles |
| VMS → CSU | Métadonnées alertes vidéo | Critiques |
| SCADA → Historian | Télémesures | Critiques |
| Apps → SIEM | Logs, événements | Internes |

✅ **Contrôle :** minimum 8 applications et 5 relations inter-applications

---

# 6. Couche technique

## 6.1 Serveurs

| Label | Zone technique | Rôle |
|-------|----------------|------|
| `SRV-SCADA-01` | serveurs | SCADA eau primaire |
| `CLU-VIRT-01..06` | serveurs | Cluster VMware datacenter |
| `SRV-SIEM-01..03` | serveurs | Wazuh manager + indexer |
| `SRV-VMS-01` | serveurs | Enregistrement vidéo |
| `SRV-IAM-01` | serveurs | KeyMetropolis |

## 6.2 Réseaux

| Label | Rôle |
|-------|------|
| `Réseau OT industriel` | Segment SCADA eau/énergie |
| `Fibre optique métropolitaine` | Interconnexion sites |
| `Réseau Wi-Fi services publics` | Agents terrain |
| `DMZ portail citoyen` | Exposition Internet |

## 6.3 Cloud

| Label | Usage |
|-------|-------|
| `CloudMunicipal PaaS` | Hébergement portail citoyen |
| `Object storage open data` | Static assets, jeux CSV |

## 6.4 Bases de données

| Label | SGBD | Application |
|-------|------|-------------|
| `DB-PORTAIL` | PostgreSQL | Portail |
| `DB-HISTORIAN` | TimescaleDB | SCADA |
| `DB-SIEM` | OpenSearch | Wazuh indexer |

## 6.5 IAM, sauvegardes, supervision

| Domaine | Élément à saisir (site / serveur / réseau) |
|---------|---------------------------------------------|
| **IAM** | AD métropole, KeyMetropolis, MFA, PAM Wallix |
| **Sauvegardes** | Veeam → PRA ; RPO 4h SI / 1h SCADA |
| **Supervision** | Zabbix infra + Grafana + Wazuh |
| **SIEM/SOAR** | Wazuh 4.x ; playbooks SOAR en maturation |
| **Wazuh** | 220 agents ; corrélations UCA |

## 6.6 Sites

- `Datacenter principal Métropolis`
- `Site secours PRA`
- `Régie eau — site OT`
- `Hôtel de métropole — CSU`

✅ **Contrôle :** couche Technique ≥ 20 entités  
✅ **Contrôle :** barre progression globale urbanisme > 60 %

---

# 7. Flux SI

## 7.1 Où modéliser les flux

🖱️ Moteur d’urbanisme → créer des entités **relation** entre composants  
🖱️ Documenter le flux dans le **commentaire** de relation ou champ **description**

## 7.2 Exemples de flux à créer

### Flux 1 — Utilisateur → Application

| Élément | Valeur |
|---------|--------|
| **Nom** | `Citoyen accède au portail` |
| **Source** | Client (citoyen) |
| **Cible** | Portail métropolitain |
| **Protocole** | HTTPS |
| **Données** | Identifiants, démarches |
| **Contrôle** | WAF + OAuth2 |

### Flux 2 — Application → Base de données

| Élément | Valeur |
|---------|--------|
| **Nom** | `Portail persiste compte citoyen` |
| **Source** | Portail métropolitain |
| **Cible** | DB-PORTAIL |
| **Données** | Profil usager (PII) |

### Flux 3 — Application → SIEM/SOAR

| Élément | Valeur |
|---------|--------|
| **Nom** | `Logs applicatifs vers Wazuh` |
| **Source** | Portail, IAM, SCADA (logs) |
| **Cible** | Wazuh SIEM |
| **Protocole** | Syslog TLS / agents |

### Flux 4 — Capteurs IoT → Supervision

| Élément | Valeur |
|---------|--------|
| **Nom** | `Capteurs urbains → plateforme supervision` |
| **Source** | Capteurs IoT (800+) |
| **Cible** | SCADA / Historian / Zabbix |
| **Données** | Télémesures, alarmes |

### Flux 5 — Caméras → CSU

| Élément | Valeur |
|---------|--------|
| **Nom** | `Flux vidéo vers CSU` |
| **Source** | Caméras IP (1850) |
| **Cible** | VMS → CSU |
| **Protocole** | RTSP |
| **Classification** | Critique |

### Flux 6 — Portail citoyen → API Management

| Élément | Valeur |
|---------|--------|
| **Nom** | `Portail consomme API mobilité` |
| **Source** | Portail métropolitain |
| **Cible** | API Management |
| **API** | `api.metropolis.fr/v1/mobilite` |
| **Auth** | OAuth2 + mTLS partenaires |

## 7.3 Schéma de synthèse (référence)

```
[Citoyen]──HTTPS──►[Portail]──API──►[API Mgmt]──►[Mobilité]
                         │
                         ├──►[IAM]
                         └──logs──►[Wazuh SIEM]──►[SOC / Dashboard RSSI]

[Caméras]──RTSP──►[VMS]──►[CSU]──►[Opérateur]

[IoT / SCADA]──OPC-UA──►[Historian]──►[Analytics prédictif]
```

✅ **Contrôle :** au moins 6 relations nommées documentées  
✅ **Contrôle :** flux critiques (vidéo, SCADA) tagués *criticité élevée* en commentaire

---

# 8. Préparation EBIOS RM

## 8.1 Accès module

🖱️ Menu **Cybersécurité → EBIOS RM** (`/ebios?project={id}`)  
🖱️ Sélectionner projet **Métropolis**

## 8.2 Mapping urbanisme → EBIOS

| Urbanisme (BS / actif) | Atelier EBIOS |
|------------------------|---------------|
| SCADA eau, Datacenter | Atelier 2 — Biens supports |
| CSU, VMS, Portail | Atelier 2 — Biens supports |
| Objectifs métier | Atelier 1 — Valeurs / périmètre |
| Processus crise, SCADA | Atelier 3 — Scénarios |
| Mesures IAM, SOC, PSSI | Atelier 4 — Mesures |
| Risques résiduels | Atelier 5 — Traitement |

## 8.3 Biens essentiels (Valeurs métier — Atelier 1)

| ID | Bien essentiel | Impact |
|----|----------------|--------|
| VM-01 | Continuité approvisionnement eau | Critique |
| VM-02 | Confiance services numériques citoyens | Élevé |
| VM-03 | Sécurité des personnes (CSU, crise) | Critique |
| VM-04 | Conformité NIS2 / RGPD | Élevé |
| VM-05 | Audit prédictif et anticipation cyber | Élevé |

## 8.4 Biens supports (Atelier 2)

| ID | Bien support | VM liées |
|----|--------------|----------|
| BS-01 | SCADA eau + automates | VM-01 |
| BS-02 | Datacenter principal | VM-01, VM-02, VM-04 |
| BS-03 | Portail + IAM | VM-02, VM-04 |
| BS-04 | VMS + CSU | VM-03 |
| BS-05 | SIEM Wazuh + SOC | VM-04, VM-05 |
| BS-06 | Fibre métropolitaine | Toutes |

🖱️ **Atelier 2** → bouton **Importer biens supports depuis urbanisme** (si disponible)

## 8.5 Événements redoutés (Atelier 3)

| ID | Événement redouté |
|----|-------------------|
| ER-01 | Arrêt production / distribution eau (cyber OT) |
| ER-02 | Fuite massive données citoyens (RGPD) |
| ER-03 | Indisponibilité portail > 48 h |
| ER-04 | Manipulation / perte flux vidéo CSU |
| ER-05 | Ransomware IT propagé vers OT |
| ER-06 | Défaillance SIEM — angles morts non détectés |

## 8.6 Sources de risque

| ID | Source | Type |
|----|--------|------|
| SR-01 | Cybercriminels (ransomware) | Externe |
| SR-02 | Erreur / malveillance interne | Interne |
| SR-03 | Prestataire infogérant compromis | Tierce partie |
| SR-04 | Vulnérabilité non corrigée (OT/IT) | Technique |
| SR-05 | Obsolescence SIEM / règles inadaptées | Organisationnel |

## 8.7 Scénarios stratégiques (extrait)

| SS | Enchaînement | Vraisemblance |
|----|--------------|---------------|
| SS-01 | SR-01 → ER-05 (ransomware IT→OT) | Élevée |
| SS-02 | SR-03 → ER-02 (fuite via infogéreur) | Moyenne |
| SS-03 | SR-04 → ER-01 (exploit SCADA) | Moyenne |
| SS-04 | SR-05 → ER-06 (audit prédictif insuffisant) | Moyenne |

## 8.8 Scénarios opérationnels (extrait)

| SO | Scénario opérationnel | BS cible |
|----|----------------------|----------|
| SO-01 | Phishing agent → lateral movement → SCADA | BS-01 |
| SO-02 | Compte admin portail compromis → exfiltration BDD | BS-03 |
| SO-03 | Flux RTSP intercepté / sabotage VMS | BS-04 |
| SO-04 | Saturation logs → alerte non traitée | BS-05 |

## 8.9 Mesures de sécurité (Atelier 4)

| Mesure | Type | Cible |
|--------|------|-------|
| Segmentation OT/IT + bastion | Préventive | BS-01 |
| MFA + PAM | Préventive | BS-03 |
| SIEM Wazuh + SOC 24/7 | Détective | BS-05 |
| PCA/PRA datacenter | Corrective | BS-02 |
| Procédure incident cyber | Organisationnelle | Tous |
| Exercice crise annuel | Organisationnelle | VM-03 |

## 8.10 Plan de traitement (Atelier 5)

| Risque | Décision | Action | Échéance |
|--------|----------|--------|----------|
| R-01 Ransomware OT | Réduire | EDR OT, backup air-gap | T2 2025 |
| R-02 Fuite PII | Réduire | Pentest, DLP portail | T1 2025 |
| R-03 SIEM incomplet | Réduire | Couverture agents 100 %, tuning règles | T3 2025 |
| R-04 Dashboard prédictif | Réduire | Enrichir corrélations UCA + ML (future) | T4 2025 |

✅ **Contrôle :** vue d’ensemble EBIOS — 5 ateliers progressent  
✅ **Contrôle :** registre GRC alimenté (section 9 et GRC)

---

# 9. Exemple EBIOS RM complet — Métier « Sécurité publique »

Ce chapitre déroule **uniquement** le métier **Sécurité publique** dans les 5 ateliers.

---

## 9.1 Atelier 1 — Cadrage et valeurs

🖱️ EBIOS RM → **Atelier 1**

| Champ | Saisie |
|-------|--------|
| **Périmètre** | `Sécurité publique : CSU, VMS, salle de crise, procédures vidéo, coordination crise` |
| **Valeur métier VM-SEC-01** | `Continuité supervision sécurité publique 24/7` |
| **Valeur métier VM-SEC-02** | `Confiance citoyenne en dispositifs vidéo` |
| **Impact** | Disponibilité : 5 — Intégrité : 5 — Confidentialité : 4 |
| **Parties prenantes** | Dir. sécurité publique, RSSI, Opérateurs CSU, DPO |

✅ Enregistrer → statut atelier 1 **En cours** puis **Terminé**

---

## 9.2 Atelier 2 — Biens supports

🖱️ **Atelier 2** → Créer fiches :

| BS | Label | Description | Criticité |
|----|-------|-------------|-----------|
| BS-SEC-01 | `VMS VideoManage Pro` | Enregistrement 1850 caméras | Critique |
| BS-SEC-02 | `CSU — Centre supervision urbaine` | Postes opérateurs | Critique |
| BS-SEC-03 | `Réseau CSU dédié` | VLAN 120 | Élevée |
| BS-SEC-04 | `Stockage vidéo 450 To` | Rétention 30 jours | Critique |

🖱️ Lier BS-SEC-* aux VM-SEC-* de l’atelier 1

---

## 9.3 Atelier 3 — Scénarios

🖱️ **Atelier 3**

**Événements redoutés :**

- ER-SEC-01 : Perte totale supervision vidéo en situation de crise
- ER-SEC-02 : Divulgation non autorisée d’enregistrements

**Sources de risque :**

- SR-SEC-01 : Attaque ransomware sur VMS
- SR-SEC-02 : Accès insider non autorisé CSU

**Scénario stratégique SS-SEC-01 :**  
SR-SEC-01 → ER-SEC-01 — *Ransomware chiffre stockage VMS pendant événement public*

**Scénario opérationnel SO-SEC-01 :**  
Phishing opérateur CSU → compromission poste → accès console VMS

---

## 9.4 Atelier 4 — Mesures de sécurité

🖱️ **Atelier 4**

| Mesure | Efficacité | Liée à |
|--------|------------|--------|
| Réseau CSU isolé (VLAN dédié) | Élevée | BS-SEC-03 |
| Habilitations nominatives VMS | Élevée | BS-SEC-01 |
| Journalisation accès vidéo → Wazuh | Moyenne | BS-SEC-02 |
| Sauvegarde stockage vidéo | Élevée | BS-SEC-04 |
| Procédure gestion crise (PPMS cyber) | Élevée | VM-SEC-01 |

---

## 9.5 Atelier 5 — Traitement des risques

🖱️ **Atelier 5**

| Risque | Criticité initiale | Décision | Mesure retenue | Risque résiduel |
|--------|-------------------|----------|----------------|-----------------|
| R-SEC-01 Ransomware VMS | Critique | Réduire | EDR + backup immuable | Modéré |
| R-SEC-02 Accès insider | Élevé | Réduire | PAM + revue trimestrielle | Faible |
| R-SEC-03 Indisponibilité SIEM | Élevé | Réduire | Règles Wazuh dédiées VMS | Modéré |

🖱️ Pousser les risques vers **GRC → Registre des risques**  
🖱️ Créer actions dans **Plan de traitement (PTR)**

✅ **Contrôle :** risque R-SEC-01 visible dans `/registre-risques?project={id}`

---

# 10. PSSI — Structure à produire

La PSSI n’est pas un écran unique : elle se **structure** à partir du projet et se **génère** via Livrables (section 11).

## 10.1 Plan de la PSSI Métropolis

| Chapitre PSSI | Contenu | Source UCA |
|---------------|---------|------------|
| **1. Gouvernance SSI** | CoPil, comité cyber, rôles RSSI/DSI/DPO | Équipe projet + note explicative |
| **2. Gestion des accès** | IAM, MFA, PAM, revues trimestrielles | Urbanisme IAM + EBIOS mesures |
| **3. Sécurité réseau** | Segmentation OT/IT/DMZ/CSU | Couche technique |
| **4. Sécurité applicative** | SSDLC, WAF, durcissement | Couche applicative |
| **5. Journalisation** | Wazuh, rétention 12 mois | SOC / technique |
| **6. Gestion des incidents** | Playbooks, notification ANSSI < 24h | EBIOS + procédures org |
| **7. Continuité d’activité** | PCA/PRA, RTO/RPO | Technique + EBIOS |
| **8. Conformité** | NIS2, RGPD, ISO 27001, EBIOS | Référentiels projet |
| **9. Sensibilisation** | Agents, opérateurs CSU, prestataires | Gouvernance |
| **10. Contrôle et audit** | Audits internes, pentest annuel | GRC + Dashboard RSSI |

## 10.2 Extraits rédactionnels (à copier dans une note ou livrable)

**Gouvernance SSI :**  
*« Le RSSI métropolitain pilote la PSSI. Le comité cyber se réunit mensuellement. Toute exception aux règles est tracée et validée par le DSI et le RSSI. »*

**Gestion des accès :**  
*« MFA obligatoire pour administrateurs, accès distants et bastion OT. Comptes privilégiés via PAM Wallix avec enregistrement de session. »*

**Journalisation :**  
*« L’ensemble des SI critiques (portail, IAM, SCADA logs, VMS, firewalls) alimente le SIEM Wazuh. Rétention 12 mois online. »*

---

# 11. Livrables — Prompts prêts à copier

🖱️ Menu **Cybersécurité → Livrables** (`/livrables?project={id}`)  
🖱️ **Nouveau livrable** → coller **Titre** + **Besoin utilisateur** + cocher **Sources de données**

Types disponibles dans UCA : Plan de management, Analyse parties prenantes, Matrice exigences, Rapport EBIOS, Registre des risques, SoA, PTR, Rapport RSSI, Rapport SOC, etc.

---

## 11.1 Note de cadrage

| Champ | Valeur |
|-------|--------|
| **Type** | `Plan de management de projet` |
| **Titre** | `Note de cadrage — Métropolis ISRC10` |
| **Sources** | urbanism, ebios, grc |
| **Format** | PDF |

**Besoin utilisateur (copier) :**

```
Rédiger une note de cadrage pour le programme Métropolis (800 000 habitants) :
contexte audit cybersécurité prédictive, périmètre OT/IT (eau, énergie, transport,
sécurité publique, portail citoyen), objectifs NIS2/RGPD, gouvernance (CoPil, RSSI),
planning 2025-2026, livrables attendus (cartographies, EBIOS, PSSI, registre risques),
hypothèses et contraintes (SIEM Wazuh, dashboard prédictif RSSI).
Public : direction générale et comité de pilotage.
```

---

## 11.2 Cartographie métier

| Champ | Valeur |
|-------|--------|
| **Type** | `Matrice des exigences` ou `Autre` |
| **Titre** | `Cartographie métier — Métropolis` |
| **Sources** | urbanism |

**Besoin utilisateur :**

```
Produire une cartographie métier structurée pour Métropolis : 5 métiers (sécurité publique,
transport intelligent, énergie urbaine, gestion de l'eau, services numériques citoyens).
Pour chaque métier : finalité, enjeux, acteurs, processus, données, criticité.
Format professionnel avec tableaux. Source : couche métier Club Urba du projet.
```

---

## 11.3 Cartographie applicative

| Champ | Valeur |
|-------|--------|
| **Titre** | `Cartographie applicative — Métropolis` |
| **Sources** | urbanism |

**Besoin utilisateur :**

```
Documenter la couche applicative Métropolis : portail citoyen, SCADA eau, CSU, VMS,
IAM KeyMetropolis, API Management, Wazuh SIEM, Metropolis Analytics. Inclure interfaces,
API, dépendances, données échangées, criticité applicative. Diagramme textuel des flux
inter-applications.
```

---

## 11.4 Cartographie technique

| Champ | Valeur |
|-------|--------|
| **Titre** | `Cartographie technique — Métropolis` |
| **Sources** | urbanism, wazuh |

**Besoin utilisateur :**

```
Décrire l'infrastructure technique : datacenter, PRA, cloud CloudMunicipal, réseaux OT/IT/DMZ,
serveurs SCADA/SIEM/VMS/IAM, bases de données, segmentation, sauvegardes, supervision
(Zabbix, Grafana, Wazuh). Inclure flux techniques syslog et corrélations SOC.
```

---

## 11.5 Analyse EBIOS RM

| Champ | Valeur |
|-------|--------|
| **Type** | `Rapport EBIOS RM` |
| **Titre** | `Analyse EBIOS RM — Métropolis` |
| **Sources** | urbanism, ebios, grc |

**Besoin utilisateur :**

```
Synthèse EBIOS RM du projet Métropolis : valeurs métier, biens supports, événements redoutés,
sources de risque, scénarios stratégiques et opérationnels, mesures de sécurité, risques
résiduels. Insister sur le métier sécurité publique (CSU/VMS) et les scénarios OT/IT.
Conforme méthode ANSSI EBIOS RM.
```

---

## 11.6 Registre des risques

| Champ | Valeur |
|-------|--------|
| **Type** | `Registre des risques` |
| **Titre** | `Registre des risques — Métropolis` |
| **Sources** | ebios, grc, urbanism |

**Besoin utilisateur :**

```
Générer un registre des risques consolidé : identifiants, descriptions, biens supports,
scénarios, criticité, décisions de traitement, mesures, responsables, échéances, risque
résiduel. Prioriser risques sécurité publique, SCADA eau et portail citoyen.
```

---

## 11.7 PSSI

| Champ | Valeur |
|-------|--------|
| **Type** | `Spécifications techniques` ou `Autre` |
| **Titre** | `PSSI — Métropole Métropolis v1.0` |
| **Sources** | urbanism, ebios, grc |

**Besoin utilisateur :**

```
Rédiger une PSSI complète en 10 chapitres : gouvernance SSI, accès/IAM/MFA/PAM,
sécurité réseau (OT/IT/DMZ), sécurité applicative, journalisation Wazuh, gestion incidents
(notification ANSSI), continuité PCA/PRA, conformité NIS2/RGPD/ISO 27001, sensibilisation,
audit. Contexte métropole 800 000 hab., SIEM centralisé, dashboard prédictif RSSI.
```

---

## 11.8 Plan de traitement

| Champ | Valeur |
|-------|--------|
| **Type** | `PTR` |
| **Titre** | `Plan de traitement des risques — Métropolis` |
| **Sources** | ebios, grc |

**Besoin utilisateur :**

```
Produire le PTR : actions correctives et préventives par risque, responsable, budget
indicatif, échéance, statut, indicateur de succès. Inclure actions SIEM (couverture agents),
segmentation OT, exercice crise CSU, DLP portail.
```

---

## 11.9 Tableau de bord RSSI

| Champ | Valeur |
|-------|--------|
| **Type** | `Rapport RSSI` |
| **Titre** | `Tableau de bord RSSI — Métropolis` |
| **Sources** | grc, ebios, soc, wazuh, urbanism |

**Besoin utilisateur :**

```
Rapport dashboard RSSI : KPI conformité NIS2/RGPD, nombre risques ouverts/critiques,
couverture SIEM, MTTD/MTTR SOC, maturité EBIOS (% ateliers), progression urbanisme SI,
incidents du trimestre, top 5 risques, recommandations direction. Ton synthétique exécutif.
```

💡 Compléter avec l’écran **Dashboard RSSI** (`/dashboard-rssi?project={id}`) pour les graphiques interactifs.

---

## 11.10 Rapport de synthèse direction

| Champ | Valeur |
|-------|--------|
| **Type** | `Rapport RSSI` ou `Plan de management de projet` |
| **Titre** | `Rapport de synthèse direction — Métropolis` |
| **Sources** | urbanism, ebios, grc, soc, ai |

**Besoin utilisateur :**

```
Rapport exécutif 5 pages pour le CoPil : état du programme audit cybersécurité prédictive,
résultats clés (urbanisme, EBIOS, risques), décisions attendues, budget, prochaines étapes
2025-2026. Public non technique : président métropole et DG.
```

🖱️ **Aperçu** avant génération finale → vérifier → **Générer** → **Exporter PDF**

---

# 12. Mode opératoire utilisateur — Pas à pas condensé

## Jour 1 — Projet et urbanisme (matin)

| Étape | Action | Détail |
|-------|--------|--------|
| 1 | Connexion UCA | `/login` |
| 2 | Créer projet | `/projects` → **+ Nouveau projet** → valeurs section 1 |
| 3 | Ouvrir projet | **Ouvrir** → vérifier Dashboard 360° |
| 4 | Équipe | Onglet **Équipe** → ajouter 5 membres |
| 5 | Urbanisme | `/schema-urbanisme?project=` → couche **Métier** → 5 métiers section 2 |
| 6 | Vérifier | Progression Métier > 30 % |

## Jour 1 — Urbanisme (après-midi)

| Étape | Action | Détail |
|-------|--------|--------|
| 7 | Organisation | Couche **Organisation** → section 3 |
| 8 | Fonctionnel | Couche **Fonctionnelle** → section 4 |
| 9 | Applicatif | Couche **Applicative** → section 5 |
| 10 | Technique | Couche **Technique** → section 6 |
| 11 | Relations | Relier entités + documenter flux section 7 |
| 12 | Vérifier | Progression globale > 60 % ; export PDF cartographie |

## Jour 2 — EBIOS et GRC

| Étape | Action | Détail |
|-------|--------|--------|
| 13 | EBIOS A1 | `/ebios?project=` → Atelier 1 → VM section 8 |
| 14 | EBIOS A2 | Atelier 2 → BS + import urbanisme |
| 15 | EBIOS A3 | Atelier 3 → scénarios |
| 16 | EBIOS SEC | Section 9 — métier Sécurité publique complet |
| 17 | EBIOS A4-A5 | Mesures + traitement |
| 18 | Registre | `/registre-risques?project=` → vérifier risques |
| 19 | PTR | `/plan-traitement-risques?project=` |
| 20 | SoA | `/declaration-applicabilite?project=` |

## Jour 3 — SOC, livrables, synthèse

| Étape | Action | Détail |
|-------|--------|--------|
| 21 | Wazuh | `/parametres/connecteurs/wazuh` → vérifier connecteur |
| 22 | SOC | `/soc/correlations?project=` → corrélations |
| 23 | Dashboard RSSI | `/dashboard-rssi?project=` |
| 24 | Livrables | `/livrables?project=` → générer 3 livrables section 11 |
| 25 | Dashboard projet | `/projects/{id}?tab=dashboard` → vue 360° |
| 26 | Activité | Onglet **Activité** → journal complet |
| 27 | Export | PDF note de cadrage + Rapport EBIOS + PSSI |

---

## Checklist finale formateur

| # | Critère | OK |
|---|---------|-----|
| 1 | Projet Métropolis créé avec tous les champs section 1 | ☐ |
| 2 | 5 métiers documentés couche Métier | ☐ |
| 3 | Organisation + 6 acteurs + RACI | ☐ |
| 4 | Couches fonctionnelle, applicative, technique renseignées | ☐ |
| 5 | 6 flux SI documentés | ☐ |
| 6 | EBIOS 5 ateliers — sécurité publique complet | ☐ |
| 7 | Registre des risques alimenté | ☐ |
| 8 | ≥ 3 livrables PDF générés | ☐ |
| 9 | Dashboard RSSI consulté | ☐ |
| 10 | Projet actif + équipe configurée | ☐ |

---

## Annexe — Correspondance écrans UCA

| Besoin | Route / menu |
|--------|--------------|
| Liste projets | `/projects` |
| Détail projet 360° | `/projects/{id}` |
| Moteur urbanisme | `/schema-urbanisme?project={id}` |
| Validation métamodèle | `/validation-metamodele?project={id}` |
| EBIOS RM | `/ebios?project={id}` |
| Registre risques | `/registre-risques?project={id}` |
| Dashboard RSSI | `/dashboard-rssi?project={id}` |
| SoA | `/declaration-applicabilite?project={id}` |
| PTR | `/plan-traitement-risques?project={id}` |
| Livrables | `/livrables?project={id}` |
| SOC corrélations | `/soc/correlations?project={id}` |
| Connecteur Wazuh | `/parametres/connecteurs/wazuh` |

---

*Guide fil rouge ISRC10 — Urban Cyber Architect*  
*Cas Métropolis — 800 000 habitants — Audit cybersécurité prédictive*  
*Support de formation — Version 1.0*
