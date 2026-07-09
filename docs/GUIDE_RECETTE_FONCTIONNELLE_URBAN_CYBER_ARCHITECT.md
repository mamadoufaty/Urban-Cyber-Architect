# GUIDE DE RECETTE FONCTIONNELLE — URBAN CYBER ARCHITECT

**Documentation fonctionnelle officielle — Version 1.0**

| Attribut | Valeur |
|----------|--------|
| **Produit** | Urban Cyber Architect (UCA) |
| **Cas d'étude fil rouge** | Métropolis – Sécurité publique & Services numériques |
| **Public** | Utilisateurs, formateurs, RSSI, architectes SI, auditeurs recette, consultants |
| **Statut** | Document officiel — recette fonctionnelle et manuel utilisateur |
| **Documents associés** | `docs/metropolis/NOTE_EXPLICATIVE_DU_PROJET.md`, `docs/metropolis/GUIDE_FIL_ROUGE_UCA.md` |

---

## Préface

Ce guide est la **référence fonctionnelle unique** de la plateforme **Urban Cyber Architect**. Il permet à un utilisateur **sans connaissance préalable** de :

1. créer et paramétrer un projet ;
2. construire l'urbanisme SI complet (métamodèle Club Urba) ;
3. cartographier les flux et dépendances ;
4. dérouler l'analyse **EBIOS RM** ;
5. alimenter la **GRC** (risques, traitement, SoA, dashboard RSSI) ;
6. exploiter le **SOC** (Wazuh, corrélations) ;
7. préparer la **PSSI** et les politiques associées ;
8. générer l'ensemble des **livrables** documentaires ;
9. comprendre l'alimentation future des **agents IA**.

Le cas **Métropolis** (métropole de **800 000 habitants**, audit cybersécurité prédictive, infrastructures critiques, SIEM Wazuh, dashboard RSSI) sert de fil conducteur : toutes les valeurs de saisie proviennent ou prolongent les données du projet Metropolis déjà présentes dans UCA (template `metropolis`, note explicative ISRC10).

---

## Conventions du document

| Symbole | Signification |
|---------|---------------|
| **Écran** | Route ou menu exact dans UCA |
| **Action** | Séquence clic / saisie |
| **Valeur Métropolis** | Donnée de recette à reproduire |
| **Alimentation** | Module(s) aval consommant la donnée |
| **Contrôle** | Critère de recette (OK / KO) |
| **⚠️ Erreur fréquente** | Piège utilisateur |
| **✅ Bonne pratique** | Recommandation métier |

**Paramètre URL projet :** la plupart des modules utilisent `?project={uuid}` ou le **projet actif** sélectionné via **Ouvrir** sur `/projects`.

---

## Vue d'ensemble du parcours produit

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1. PROJET — Création, équipe, métadonnées, référentiels              │
└───────────────────────────────┬─────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  2. URBANISME SI — Club Urba (Métier → Org → Fonct → Appli → Tech)     │
└───────────────────────────────┬─────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  3. FLUX — Relations inter-couches, dépendances                        │
└───────────────────────────────┬─────────────────────────────────────┘
                                ▼
┌──────────────┬──────────────┬──────────────┬──────────────┬────────────┐
│ 4. EBIOS RM  │ 5. PSSI      │ 6. GRC       │ 7. SOC       │ 8. IA      │
└──────────────┴──────────────┴──────────────┴──────────────┴────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  9. LIVRABLES — Génération documentaire automatique (PDF/DOCX/MD)       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# PARTIE 1 — CRÉATION DU PROJET

## 1.1 Écran et accès

| Élément | Détail |
|---------|--------|
| **Menu** | Principal → **Projets** |
| **Route** | `/projects` |
| **Droit requis** | Module `projects` (rôle : admin, rssi, consultant, etc. selon matrice RBAC) |
| **Action d'entrée** | Bouton **+ Nouveau projet** |

## 1.2 Champs du formulaire — Détail complet

### 1.2.1 Nom

| Attribut | Détail |
|----------|--------|
| **Rôle** | Identifiant lisible du programme ; affiché partout (header, dashboard, livrables, exports PDF) |
| **Signification métier** | Désigne le périmère de gouvernance (programme, audit, transformation) |
| **Obligatoire** | Oui |
| **Valeur Métropolis** | `Métropolis – Sécurité publique & Services numériques` |
| **Alimentation aval** | Context Builder, couverture livrables, synthèse exécutive dashboard 360°, `project_activity` |
| **Contrôle recette** | Nom visible dans barre **Projet actif** après ouverture |
| **⚠️ Erreur fréquente** | Nom trop générique (« Projet test ») — exports non identifiables |
| **✅ Bonne pratique** | Inclure client + thématique (sécurité publique, services numériques) |

### 1.2.2 Code

| Attribut | Détail |
|----------|--------|
| **Rôle** | Identifiant technique court, unique en base |
| **Signification métier** | Référence projet pour GRC, exports, intégrations futures |
| **Obligatoire** | Non — **génération automatique** si vide |
| **Règle auto** | Slug dérivé du nom : minuscules, tirets, sans caractères spéciaux (ex. `metropolis-securite-publique-services-numeriques`) |
| **Valeur Métropolis** | `metropolis-isrc10` (recommandé pour recette ; évite collision) |
| **Alimentation aval** | Colonne **Code** du tableau projets, badge dashboard, métadonnées livrables |
| **Contrôle recette** | Code affiché dans fiche projet et export PDF |
| **⚠️ Erreur fréquente** | Dupliquer un code existant → erreur API à la création |
| **✅ Bonne pratique** | Pattern `{client}-{programme}-{année}` |

### 1.2.3 Description

| Attribut | Détail |
|----------|--------|
| **Rôle** | Résumé contextuel pour humains et moteur de livrables |
| **Signification métier** | Périmètre, objectifs, contraintes réglementaires |
| **Valeur Métropolis** | `Projet fil rouge ISRC10 — audit cybersécurité prédictive sur métropole 800 000 hab. : infrastructures critiques (eau, énergie, transport), sécurité publique (CSU, vidéo), services numériques citoyens, SIEM Wazuh centralisé, dashboard RSSI prédictif, conformité NIS2/RGPD/ISO 27001.` |
| **Alimentation aval** | Livrables (plan de management), synthèse exécutive, prompts IA |
| **Contrôle recette** | Visible onglet Dashboard → carte projet |

### 1.2.4 Client

| Attribut | Détail |
|----------|--------|
| **Rôle** | Entité commanditaire ou bénéficiaire métier |
| **Signification métier** | Sépare le **client** (métropole) de l'**organisation** MOA technique |
| **Valeur Métropolis** | `Métropole Métropolis` |
| **Alimentation aval** | Tableau projets, registre risques (colonne organisation), rapports RSSI |
| **Contrôle recette** | Colonne **Client** du cockpit `/projects` |

### 1.2.5 Organisation

| Attribut | Détail |
|----------|--------|
| **Rôle** | Lien FK vers entité **Organisation** (module Administration) |
| **Signification métier** | Structure juridique porteuse du SI (MOA, tenant) |
| **Composant** | **Combobox recherchable** (V1) — chargement dynamique de **toutes les organisations actives**, triées alphabétiquement |
| **Recherche** | Champ de saisie intégré : filtre par nom **ou** code, insensible à la casse et aux accents |
| **Liste vide** | Message explicite « Aucune organisation active. Créez-en une pour continuer. » |
| **Création inline** | Bouton **+ Créer une organisation** en pied de liste → ouvre la fenêtre de création ; l'organisation créée apparaît **immédiatement** et est présélectionnée |
| **Présélection** | L'organisation de l'utilisateur connecté est **présélectionnée** en création |
| **Verrouillage** | Modifiable **uniquement** par un rôle **Administrateur** ou **SuperAdmin** ; sinon champ verrouillé avec mention explicative |
| **Écran admin** | `/administration/organizations` |
| **Valeur Métropolis** | Organisation `Métropolis Test` ou `Métropolis — Métropole territoriale` |
| **Alimentation aval** | Dashboard projet, GRC, multi-projets par tenant |
| **⚠️ Erreur fréquente** | Confondre organisation JSON (urbanisme legacy) et `organization_id` — les deux coexistent ; privilégier FK pour V1.3+ |
| **✅ Bonne pratique** | Le projet **n'est plus limité** à une seule organisation : toutes les organisations actives sont sélectionnables |

### 1.2.6 Responsable

| Attribut | Détail |
|----------|--------|
| **Rôle** | `owner_id` — utilisateur référent (souvent RSSI ou chef de projet) |
| **Signification métier** | Point de contact unique pour pilotage et escalade |
| **Valeur Métropolis** | Compte `rssi` ou utilisateur « Sophie MARTIN » |
| **Alimentation aval** | Colonne **Responsable** tableau projets, KPI dashboard 360° |
| **Contrôle recette** | Nom affiché sur dashboard projet |

### 1.2.7 Statut

| Attribut | Détail |
|----------|--------|
| **Valeurs** | Brouillon, Actif, En cours, En pause, Terminé, Archivé |
| **Valeur Métropolis** | `En cours` |
| **Alimentation aval** | Filtrage futur, archivage (`POST /archive`), reporting |
| **Contrôle recette** | Badge statut sur fiche projet |

### 1.2.8 Priorité

| Attribut | Détail |
|----------|--------|
| **Valeurs** | Basse, Moyenne, Haute, Critique |
| **Valeur Métropolis** | `Haute` |
| **Alimentation aval** | Tableau projets, priorisation actions GRC / prochaines actions dashboard |

### 1.2.9 Dates (début / fin)

| Attribut | Détail |
|----------|--------|
| **Composant** | **DatePicker** dédié (V1) : clic dans le champ → ouverture d'un **calendrier** |
| **Sélection** | Sélection d'un jour par **clic** ; navigation **mois/année** (flèches + sélecteurs) ; bouton **Aujourd'hui** |
| **Format affichage** | `JJ/MM/AAAA` dans le champ et le tableau |
| **Format stockage** | ISO `YYYY-MM-DD` (envoyé à l'API) |
| **Saisie clavier** | Frappe directe `JJ/MM/AAAA` acceptée et validée automatiquement |
| **Valeur Métropolis** | Début `15/01/2025` — Fin `31/12/2026` |
| **Validation** | Date fin ≥ date début ; les jours antérieurs à la date de début sont **désactivés** dans le calendrier de fin |
| **Message bloquant** | *« La date de fin doit être postérieure à la date de début. »* — enregistrement **impossible** tant que l'erreur persiste |
| **Alimentation aval** | Dashboard 360°, plan de management, PSSI (périmètre temporel) |
| **⚠️ Erreur fréquente** | Inverser les dates → rejet formulaire avec message explicite |

### 1.2.10 Référentiels

| Attribut | Détail |
|----------|--------|
| **Rôle** | Cadre normatif et réglementaire du projet |
| **Source** | **Base de données** (V1) — plus aucune liste codée en dur ; chargement dynamique des référentiels **actifs** |
| **Administration** | Écran dédié `/administration/referentials` (création, modification, activation/désactivation, suppression) |
| **Jeu initial** | RGPD, NIS2, EBIOS RM, ISO 27001, ISO 27002, ISO 27005, IEC 62443, ANSSI, DORA, HDS, PCI DSS, SOC 2 (amorcés en base au démarrage) |
| **Valeurs Métropolis** | RGPD, NIS2, EBIOS RM, ISO 27001, ISO 27005, ANSSI |
| **Ajout rapide** | Bouton **+ Ajouter un référentiel** dans le formulaire projet (Admin/SuperAdmin) — voir § 1bis.6bis |
| **Alimentation aval** | Context Builder, livrables conformité, SoA, prompts orchestration IA, tags dashboard |
| **Contrôle recette** | Badges référentiels visibles sur dashboard projet ; un référentiel ajouté en administration ou depuis le formulaire apparaît immédiatement |

### 1.2.11 Tags

| Attribut | Détail |
|----------|--------|
| **Format** | Liste séparée par virgules |
| **Valeur Métropolis** | `fil-rouge, isrc10, smart-city, securite-publique, siem, wazuh, audit-predictif, metropolis` |
| **Alimentation aval** | Recherche future, classification livrables, contexte IA |

## 1.3 Création via modèle exemple (recommandé recette)

| Étape | Action |
|-------|--------|
| 1 | Type de création : **Modèle exemple** |
| 2 | Sélectionner **Exemple — Smart City (Métropolis)** |
| 3 | Compléter les champs section 1.2 (le modèle préremplit urbanisme JSON, objectifs, référentiels de base) |
| 4 | **Créer le projet** puis **Ouvrir** |

**Alimentation immédiate :** couche Club Urba partiellement préremplie dans `urbanism.club_urba` → accélère recette urbanisme.

## 1.4 Post-création obligatoire

| Action | Écran | Détail |
|--------|-------|--------|
| Ouvrir le projet | `/projects` → **Ouvrir** | Définit le **projet actif** (`localStorage`) |
| Constituer l'équipe | `/projects/{id}?tab=team` | Voir tableau rôles section 1.5 |
| Vérifier activité | `/projects/{id}?tab=activity` | Trace `project.created` |

### 1.5 Équipe projet Métropolis (recette)

| Utilisateur | Rôle projet UCA |
|-------------|-----------------|
| RSSI | `rssi` |
| Architecte SI | `architecte_si` |
| Architecte cyber | `architecte_cyber` |
| Chef de projet | `chef_projet` |
| Responsable métier | `responsable_metier` |
| SOC Manager | `soc_manager` |
| DPO | `dpo` |

**Alimentation aval :** gouvernance, traçabilité `member.added` / `member.removed`, futures notifications.

## 1.6 Critères de recette — Partie 1

| # | Critère | Résultat attendu |
|---|---------|------------------|
| R1.1 | Création projet | HTTP 201, projet listé |
| R1.2 | Projet actif | Badge header visible |
| R1.3 | Dashboard 360° | KPIs chargés sans erreur |
| R1.4 | Équipe | ≥ 3 membres, rôles valides |
| R1.5 | Activité | ≥ 1 entrée `project.created` |
| R1.6 | Modification | `project.updated` après édition |
| R1.7 | Dates | Validation fin ≥ début |

---

# PARTIE 1 bis — CRÉATION D'UN PROJET (COMPORTEMENTS V1 — PRODUCTION)

> Ce chapitre décrit les comportements attendus de l'écran **Créer / Modifier un projet**
> après les corrections de recette V1. Il sert de référence de test pour la validation
> fonctionnelle en production.

## 1bis.1 Objet

L'écran **Créer / Modifier un projet** (`/projects` → **+ Nouveau projet**, ou onglet
**Paramètres** d'un projet → **Modifier le projet**) a été fiabilisé sur six points :

1. sélection d'organisation dynamique et recherchable ;
2. sélection des dates par calendrier (DatePicker) ;
3. validation stricte de la cohérence des dates ;
4. présélection et verrouillage de l'organisation selon le rôle ;
5. référentiels administrables chargés depuis la base ;
6. ajout rapide d'un référentiel directement depuis le formulaire (Admin/SuperAdmin).

## 1bis.2 Organisation — combobox recherchable

| Élément | Comportement attendu |
|---------|----------------------|
| **Chargement** | Toutes les organisations **actives** sont chargées dynamiquement depuis la base (`GET /api/admin/organizations`) |
| **Tri** | Ordre alphabétique (locale FR, insensible aux accents) |
| **Recherche** | Saisie dans le champ intégré → filtrage instantané par **nom ou code** |
| **Liste vide** | Affiche « Aucune organisation active. Créez-en une pour continuer. » |
| **Créer une organisation** | Bouton **+ Créer une organisation** → ouvre la fenêtre de création ; après validation l'organisation **apparaît immédiatement** dans la liste et devient la valeur sélectionnée |
| **Contrôle recette** | Une organisation créée est sélectionnable **sans recharger** la page |

**Figure 1bis.1 — Combobox organisation ouverte (recherche + création)**

![Combobox organisation](./images/creation-projet/organisation-combobox.png)

> _Capture à insérer : liste déroulante ouverte avec champ de recherche, résultats filtrés et bouton « + Créer une organisation »._

## 1bis.3 Dates — DatePicker

| Élément | Comportement attendu |
|---------|----------------------|
| **Ouverture** | Clic dans le champ **ou** sur l'icône calendrier ouvre le calendrier |
| **Sélection** | Clic sur un jour renseigne la date et ferme le calendrier |
| **Affichage** | `JJ/MM/AAAA` |
| **Stockage** | ISO `YYYY-MM-DD` (payload API) |
| **Navigation** | Flèches mois précédent / suivant + sélecteurs **mois** et **année** |
| **Aujourd'hui** | Bouton **Aujourd'hui** sélectionne la date du jour |
| **Validation auto** | Saisie clavier `JJ/MM/AAAA` validée à la volée ; dates impossibles (ex. 31/02) rejetées |
| **Bornage** | Dans le calendrier de **Date fin**, les jours antérieurs à **Date début** sont désactivés |

**Figure 1bis.2 — Calendrier DatePicker ouvert**

![DatePicker](./images/creation-projet/datepicker-calendrier.png)

> _Capture à insérer : calendrier ouvert avec en-tête mois/année, grille des jours, jour sélectionné et bouton « Aujourd'hui »._

## 1bis.4 Validation des dates

| Cas | Résultat attendu |
|-----|------------------|
| Date fin ≥ Date début | Enregistrement autorisé |
| Date fin < Date début | **Blocage** ; message *« La date de fin doit être postérieure à la date de début. »* |
| Une seule date renseignée | Autorisé (pas de contrainte d'ordre) |

**Figure 1bis.3 — Message de validation des dates**

![Validation dates](./images/creation-projet/validation-dates.png)

> _Capture à insérer : formulaire affichant le bandeau d'erreur de cohérence des dates._

## 1bis.5 Organisation par défaut et droits

| Profil connecté | Comportement attendu |
|-----------------|----------------------|
| Utilisateur rattaché à une organisation | Son organisation est **présélectionnée** en création |
| Rôle **Administrateur** / **SuperAdmin** | Peut **modifier** librement l'organisation |
| Autres rôles (rssi, consultant, soc, metier) | Champ **verrouillé** sur l'organisation de rattachement, avec mention : « Organisation rattachée à votre compte. Seul un administrateur peut la modifier. » |

> **Note technique :** la réponse de connexion (`POST /api/auth/login`) expose désormais
> `organizationId`, propagé dans la session pour permettre la présélection.

## 1bis.6 Référentiels administrables

| Élément | Comportement attendu |
|---------|----------------------|
| **Source** | Chargés depuis la base (`GET /api/admin/referentials?active_only=true`) |
| **Administration** | `/administration/referentials` — créer / modifier / activer / désactiver / supprimer |
| **Apparition** | Un référentiel activé en administration apparaît dans le formulaire projet |
| **Rétrocompatibilité** | Un référentiel déjà rattaché mais retiré du catalogue reste affiché et décochable |

**Figure 1bis.4 — Écran d'administration des référentiels**

![Administration référentiels](./images/creation-projet/administration-referentiels.png)

> _Capture à insérer : tableau des référentiels avec actions Modifier / Désactiver / Supprimer._

## 1bis.6bis Ajout rapide d'un référentiel depuis le formulaire projet

Pour éviter un aller-retour vers `/administration/referentials`, le formulaire
**Créer / Modifier un projet** propose un ajout rapide directement dans la section
**Référentiels**.

| Élément | Comportement attendu |
|---------|----------------------|
| **Bouton** | **+ Ajouter un référentiel**, affiché à droite du libellé « Référentiels » |
| **Droits** | Visible **uniquement** pour les rôles **Administrateur** et **SuperAdmin** ; absent du formulaire pour les autres rôles |
| **Ouverture** | Clic → petite fenêtre modale (indépendante du formulaire projet) |
| **Champs** | **Nom** du référentiel *(obligatoire)*, **Code** *(obligatoire)*, **Description** *(libre)*, **Statut** actif/inactif (par défaut : Actif) |
| **Contrôles** | Nom vide → « Le nom du référentiel est obligatoire. » ; Code vide → « Le code du référentiel est obligatoire. » ; code déjà utilisé (insensible à la casse) → « Un référentiel avec le code « … » existe déjà. » |
| **Validation** | Appel `POST /api/admin/referentials` (API existante) ; en cas d'erreur serveur (ex. doublon détecté côté base), le message renvoyé par l'API est affiché tel quel |
| **Après création** | La liste des référentiels du formulaire se **rafraîchit immédiatement** (sans recharger la page) et le nouveau référentiel est **automatiquement pré-coché** pour le projet en cours d'édition |
| **Persistance globale** | Le référentiel créé est aussi disponible pour tous les projets suivants et dans `/administration/referentials` |

**Figure 1bis.4bis — Modale d'ajout rapide d'un référentiel**

![Ajout rapide référentiel](./images/creation-projet/ajout-rapide-referentiel.png)

> _Capture à insérer : formulaire projet avec le bouton « + Ajouter un référentiel » et la
> modale ouverte (Nom, Code, Description, Statut)._

## 1bis.7 Responsive

| Résolution | Attendu |
|-----------|---------|
| **1920 px** | Formulaire centré, grille 2 colonnes aérée |
| **1366 px** | Grille 2 colonnes, popups contenues dans la fenêtre |
| **Tablette (≤ 1024 px)** | Modale ≤ 92 % de la largeur ; grille 1 colonne à partir de 900 px |
| **Mobile (≤ 640 px)** | Champs pleine largeur, calendrier pleine largeur, boutons d'action empilés |

## 1bis.8 Critères de recette — Création d'un projet (V1)

| # | Critère | Résultat attendu |
|---|---------|------------------|
| R1bis.1 | Chargement dynamique des organisations | Toutes les organisations actives listées et triées |
| R1bis.2 | Recherche d'organisation | Filtrage instantané par nom ou code |
| R1bis.3 | Création d'organisation inline | Apparition immédiate + présélection |
| R1bis.4 | Sélection via DatePicker | Date choisie au clic, affichée `JJ/MM/AAAA`, stockée ISO |
| R1bis.5 | Validation des dates | Blocage + message si fin < début |
| R1bis.6 | Organisation par défaut / droits | Présélection ; verrouillage hors admin |
| R1bis.7 | Référentiels dynamiques | Référentiel administré visible dans le formulaire |
| R1bis.7bis | Ajout rapide de référentiel | Création via la modale du formulaire projet ; apparition immédiate et pré-cochage ; bouton invisible hors Admin/SuperAdmin |
| R1bis.8 | Responsive | Utilisable en 1920 / 1366 / tablette / mobile |

---

# PARTIE 2 — CONSTRUCTION DE L'URBANISME SI

## 2.1 Écran principal

| Élément | Détail |
|---------|--------|
| **Menu** | Urbanisme → **Moteur d'urbanisme** |
| **Route** | `/schema-urbanisme?project={id}` |
| **Alternative** | Projet → onglet **Urbanisme SI** → lien module |
| **Complément** | `/validation-metamodele?project={id}` pour contrôles R01–R30 |

## 2.2 Principes Club Urba dans UCA

| Couche | Zones principales | Types d'entités |
|--------|-------------------|-----------------|
| **Métier** | objectifs, processus, activités, classes, résultats | objectif, processus, activité, classe, résultat |
| **Organisation** | organisation, procedures, operations, acteurs | organisation, procedure, operation, acteur |
| **Fonctionnel** | ilots, quartiers, zones | ilot_fonctionnel, quartier_fonctionnel, zone_fonctionnelle |
| **Applicatif** | ilots, quartiers, zones | ilot_applicatif, quartier_applicatif, zone_applicative |
| **Technique** | postes, serveurs, reseaux, sites | poste_travail, serveur, reseau, site |

**Relations de référence (extrait) :** métier pilote processus (R03) ; processus se décompose en activité (R06) ; acteur réalise opération (R15) ; ilot applicatif accessible via serveur (R21).

### Actions génériques (toute entité)

1. Sélectionner couche et zone dans l'éditeur Club Urba  
2. **Assistant urbanisme** (recommandé) ou création manuelle  
3. Saisir **label** + **description** + propriétés  
4. Créer **relations** vers entités existantes  
5. Vérifier barre **progression** (`GET /urbanism/progress`)

---

## 2.3 COUCHE MÉTIER — Métiers Métropolis

### 2.3.1 Métier : Sécurité publique

| Dimension | Contenu Métropolis |
|-----------|-------------------|
| **Mission** | Assurer tranquillité publique, coordination de crise, supervision vidéo urbaine |
| **Objectifs** | Continuité CSU 24/7 ; conformité CNIL vidéo ; résilience événements majeurs |
| **Responsabilités** | Direction sécurité publique, RSSI (partie cyber), opérateurs CSU |
| **Indicateurs** | Disponibilité CSU ≥ 99,5 % ; délai levée alerte < 2 min ; 0 fuite flux vidéo |
| **Parties prenantes** | Élus, préfecture, forces de l'ordre, DPO, prestataire VMS |

#### Objectifs à créer

| Label | Pourquoi | Relations |
|-------|----------|-----------|
| `Sécurité publique et résilience urbaine` | Cadre la valeur métier VM-03 | Définit processus crise |
| `Conformité NIS2 et RGPD` | Transverse réglementaire | Lié à tous processus SI |

#### Processus à créer

| Label | Rôle | Relations |
|-------|------|-----------|
| `Gestion de crise métropolitaine` | Orchestration cellule crise | Acteurs : élus, CSU, RSSI |
| `Supervision temps réel des infrastructures` | Monitoring cross-domaines | Alimente SOC |

#### Activités à créer

| Label | Rôle |
|-------|------|
| `Surveillance vidéoprotection CSU` | Opérationnel 24/7 |
| `Levée et qualification d'alerte` | Lien SOC / SIEM |

#### Classes métier

| Label | Rôle | Données |
|-------|------|---------|
| `Incident sécurité publique` | Typologie événements | Alertes, vidéo, logs |
| `Événement public` | Contexte crise | Manifestations, concerts |

**Alimentation aval :** EBIOS VM/ER sécurité publique, corrélations SOC, risques CSU dans GRC.

---

### 2.3.2 Métier : Mobilité & Transport intelligent

| Dimension | Contenu |
|-----------|---------|
| **Mission** | Piloter mobilité urbaine, information voyageurs, billettique |
| **Objectifs** | Fluidité trafic ; interopérabilité API transport |
| **Indicateurs** | Ponctualité ITS ; disponibilité info voyageurs 99 % |
| **Parties prenantes** | Direction mobilité, opérateur transport, usagers |

**Objectifs :** `Mobilité durable et fluide`  
**Processus :** `Planification mobilité durable`, `Gestion des incidents citoyens`  
**Activités :** `Pilotage du trafic routier`, `Diffusion info voyageurs`  
**Classes :** `Perturbation réseau`, `Demande usager mobilité`

---

### 2.3.3 Métier : Eau

| Dimension | Contenu |
|-----------|---------|
| **Mission** | Production et distribution eau potable |
| **Objectifs** | Continuité service essential NIS2 ; qualité eau |
| **Indicateurs** | Disponibilité SCADA 99,9 % ; 0 arrêt production non maîtrisé |
| **Parties prenantes** | Régie eau, exploitants OT, ANSSI (OT) |

**Processus clé :** `Supervision temps réel des infrastructures`  
**Activités :** `Télégestion réseau eau`, `Traitement alarme SCADA`  
**Classes :** `Alarme pression`, `Mesure qualité eau`

**Alimentation aval :** EBIOS BS SCADA, scénarios ransomware OT, mesures IEC 62443.

---

### 2.3.4 Métier : Énergie (smart grid)

| Dimension | Contenu |
|-----------|---------|
| **Mission** | Piloter réseaux électriques et éclairage public intelligent |
| **Objectifs** | Sobriété ; continuité éclairage |
| **Indicateurs** | Taux armoires connectées ; incidents cyber OT énergie |

**Activités :** `Gestion de l'éclairage public`, `Supervision compteurs intelligents`  
**Classes :** `Incident réseau électrique`, `Commande armoire éclairage`

---

### 2.3.5 Métier : Services numériques citoyens

| Dimension | Contenu |
|-----------|---------|
| **Mission** | Portail citoyen, démarches en ligne, open data |
| **Objectifs** | Satisfaction usagers ; conformité RGPD |
| **Indicateurs** | Disponibilité portail 99,5 % ; NPS > 40 |

**Processus :** `Gestion des incidents citoyens`, `Accueil et information citoyenne`  
**Activités :** `Traitement ticket portail`, `Publication open data`  
**Classes :** `Compte citoyen`, `Jeu de données ouvertes`

---

### 2.3.6 Recette couche Métier

| Contrôle | Seuil Métropolis |
|----------|------------------|
| Objectifs | ≥ 3 |
| Processus | ≥ 4 |
| Activités | ≥ 6 |
| Classes | ≥ 4 |
| Relations métier | ≥ 10 |
| Progression couche | ≥ 40 % |

---

## 2.4 COUCHE ORGANISATION

### 2.4.1 Directions et services

| Type | Label à saisir | Lien métier |
|------|--------------|-------------|
| organisation | `Métropolis — Métropole territoriale` | Tous |
| organisation | `Direction du numérique (DNum)` | Services numériques |
| organisation | `Pôle sécurité des systèmes d'information` | Transverse cyber |
| organisation | `Direction mobilité` | Mobilité |
| organisation | `Régie eau Métropolis` | Eau |
| organisation | `Direction sécurité publique` | Sécurité publique |
| organisation | `Direction énergie` | Énergie |

### 2.4.2 Équipes et acteurs

| Acteur | Type | Responsabilité |
|--------|------|----------------|
| RSSI métropolitain | acteur | Gouvernance SSI, EBIOS, SOC |
| Exploitants OT/SCADA | acteur | Run eau/énergie |
| Opérateurs CSU | acteur | Vidéoprotection |
| Responsables métiers | acteur | MOA |
| DPO | acteur | RGPD |
| Infogéo SA | acteur | Infogérance (externe) |
| CloudMunicipal | acteur | Cloud (externe) |

### 2.4.3 RACI simplifié Métropolis

| Activité | Sponsor | DSI | RSSI | Métiers | Infogéreur |
|----------|---------|-----|------|---------|------------|
| Urbanisme SI | I | A | R | C | C |
| EBIOS RM | I | C | A/R | C | I |
| SOC / SIEM | I | I | A | I | R |
| Portail citoyen | I | A | C | R | R |
| PCA/PRA | A | R | C | C | R |

*À consigner en description de l'entité « Pôle SSI ».*

### 2.4.4 Opérations et procédures

| Type | Exemples Métropolis |
|------|---------------------|
| procedure | Procédure gestion d'incident cyber |
| procedure | Procédure gestion des changements |
| procedure | Procédure continuité d'activité |
| operation | Supervision SOC municipal |
| operation | Exploitation SCADA eau et énergie |

### 2.4.5 Événements organisationnels

| Événement | Déclencheur | Processus lié |
|-----------|-------------|---------------|
| Alerte cyber P1 | SIEM Wazuh | Procédure incident cyber |
| Crise territoriale | Événement public | Gestion crise métropolitaine |
| Audit ISO | Calendrier | Revue conformité |

**Lien métiers :** relation *organisation décide de* (R04) ; *acteur réalise opération* (R15).

---

## 2.5 COUCHE FONCTIONNELLE

Pour **chaque métier**, construire la déclinaison fonctionnelle :

### 2.5.1 Sécurité publique

| Élément | Labels Métropolis |
|---------|-------------------|
| **Îlot fonctionnel** | `Sécurité publique et vidéoprotection` |
| **Quartier** | `Vidéosurveillance urbaine`, `Centre de supervision (CSU)` |
| **Zone** | `Supervision centralisée`, `Alerting et notification` |
| **Cas d'usage** | UC-SEC-01 Consulter flux vidéo ; UC-SEC-02 Gérer crise |
| **Exigences fonctionnelles** | EF-SEC-01 Accès nominatif VMS ; EF-SEC-02 Journalisation accès |
| **Exigences non fonctionnelles** | ENF-SEC-01 Disponibilité CSU 99,5 % |

### 2.5.2 Mobilité

| Îlot | `Mobilité et transports` |
| Quartier | `Transport intelligent (ITS)` |
| Zone | `Reporting réglementaire` |
| UC | UC-MOB-01 Consulter horaires ; UC-MOB-02 Signaler perturbation |

### 2.5.3 Eau / Énergie / Services numériques

*(Structure identique — voir template `METROPOLIS_CLUB_URBA` dans le code source et note explicative section 4.)*

**Construction :** classe métier → ilot fonctionnel (R08) → quartier (R17) → zone (R18).

---

## 2.6 COUCHE APPLICATIVE

### 2.6.1 Applications Métropolis

| Application | Fonction portée | Criticité |
|-------------|-----------------|-----------|
| Portail métropolitain | Services numériques | Élevée |
| SCADA eau AquaControl | Eau OT | Critique |
| CSU | Sécurité publique | Critique |
| VideoManage Pro (VMS) | Vidéo | Critique |
| KeyMetropolis (IAM) | Identités | Critique |
| API Management | Open data / mobilité | Élevée |
| Wazuh SIEM | SOC | Élevée |
| Metropolis Analytics | Dashboard prédictif RSSI | Élevée |
| GMAO MaintCity | Maintenance | Moyenne |

### 2.6.2 API et interfaces

| API / Interface | Protocole | Données | Classification |
|---------------|-----------|---------|----------------|
| api.metropolis.fr/v1/citoyen | HTTPS/OAuth2 | Profil usager | Sensible |
| api.metropolis.fr/v1/mobilite | HTTPS/mTLS | Horaires | Interne |
| api.metropolis.fr/v1/open-data | HTTPS/API Key | Jeux ouverts | Publique |
| SCADA → Historian | OPC-UA | Télémesures | Critique |
| VMS → CSU | RTSP/TLS | Flux vidéo | Critique |
| Apps → Wazuh | Syslog TLS | Logs | Interne |

### 2.6.3 Dépendances applicatives

Documenter dans **commentaires de relation** ou entité dédiée :

```
Portail → IAM (bloquant)
CSU → VMS (bloquant)
SCADA → Historian → Analytics
Tous → Wazuh agents
```

**Alimentation aval :** analyse dépendances (suppression projet 409), GRC, SOC (corrélation par label urbanisme).

---

## 2.7 COUCHE TECHNIQUE

### 2.7.1 Par application — Composants

#### Portail métropolitain

| Composant | Détail Métropolis |
|-----------|-------------------|
| Serveurs | SRV-PORTAIL-01..02 (VM cluster) |
| Conteneurs | 12 pods PaaS CloudMunicipal |
| BDD | DB-PORTAIL PostgreSQL |
| Stockage | Object storage static assets |
| Sauvegarde | RPO 4h, PRA cloud |

#### SCADA eau

| Composant | Détail |
|-----------|--------|
| Serveurs | SRV-SCADA-01/02 |
| Automates | 42 automates terrain |
| Réseau | VLAN OT 110 |
| Sauvegarde | RPO 1h, config air-gap |

#### Wazuh SIEM

| Composant | Détail |
|-----------|--------|
| Serveurs | SRV-SIEM-01..03 |
| BDD | OpenSearch cluster |
| Agents | 220 endpoints |

*Kubernetes : pour Métropolis, le portail PaaS est documenté en conteneurs orchestrés (CloudMunicipal) ; saisir comme propriété de `serveur` ou note sur site cloud.*

### 2.7.2 Réseaux

| Élément | Label / ID | Rôle |
|---------|------------|------|
| VLAN OT | `Réseau OT industriel` | SCADA eau/énergie |
| DMZ | `DMZ portail citoyen` | Internet → portail |
| LAN corp | VLAN 10-50 | Bureautique, serveurs |
| CSU | VLAN 120 | Vidéo isolée |
| IoT | VLAN 130 | Capteurs urbains |
| WAN | `Fibre optique métropolitaine` | Inter-sites |
| VPN | VPN agents distants | Administration |
| Firewall | Palo Alto PA-5220 (paire HA) | Segmentation IT/OT/DMZ |

### 2.7.3 Sites

| Site | Type | Rôle |
|------|------|------|
| Datacenter principal Métropolis | Datacenter | Production |
| Site secours PRA | PRA | Reprise 4h |
| Régie eau — site OT | Site technique | SCADA terrain |
| Hôtel de métropole | Site tertiaire | CSU, direction |

### 2.7.4 Équipements — Inventaire détaillé recette

| Équipement | Type | Utilisateur | Application | Serveur / cible | Réseau | Site |
|------------|------|-------------|-------------|-----------------|--------|------|
| Poste opérateur CSU-01 | poste_travail | Opérateur CSU | VMS, CSU | SRV-VMS-01 | VLAN 120 | Hôtel métropole |
| Poste supervision SCADA | poste_travail | Exploitant OT | AquaControl | SRV-SCADA-01 | VLAN OT | Régie eau |
| Laptop agent DNum | poste_travail | Agent DNum | Portail admin | Cloud PaaS | LAN | Télétravail VPN |
| Smartphone agent terrain | BYOD / mobile | Technicien IoT | GMAO mobile | Cloud | Wi-Fi / 4G | Terrain |
| Caméra IP CAR-#### | capteur / IoT | — | VMS | Enregistreur | VLAN 120 | Voie publique |
| Capteur pression eau | automate / IoT | — | SCADA | Automate | VLAN OT | Réseau eau |
| SRV-SIEM-01 | serveur | SOC | Wazuh | Cluster | LAN | Datacenter |
| Switch core DC | reseau | — | — | — | LAN | Datacenter |
| Firewall OT | reseau | — | — | — | OT/DMZ | Datacenter |

**Contrôle recette technique :** ≥ 20 entités technique, 4 sites, 5 réseaux documentés.

---

# PARTIE 2 bis — CARTOGRAPHIES MULTIPLES ET VERSIONNING

## 2bis.1 Objet

Un projet ne se limite plus à une seule cartographie implicite. UCA se rapproche du
fonctionnement des outils d'architecture d'entreprise (MEGA HOPEX, LeanIX, Bizzdesign) :
un projet **Métropolis** peut contenir plusieurs cartographies indépendantes (Urbanisme
Métier, Urbanisme Technique, Cybersécurité, Architecture cible, Réseau, Cloud…), chacune
avec son propre graphe et son propre historique de versions.

## 2bis.2 Bandeau du moteur

En haut de l'écran **Urbanisme SI**, un bandeau permet de choisir :

| Sélecteur | Rôle |
|-----------|------|
| **Projet** | Change de projet (comme avant) |
| **Cartographie** | Change de cartographie active dans le projet |
| **Version** | Consulte la version courante (modifiable) ou une version historique (lecture seule) |
| **+ Nouvelle cartographie** | Ouvre le formulaire de création |
| **Actions ▾** | Historique, Enregistrer sous…, Créer une nouvelle version, Dupliquer, Soumettre pour validation, Valider, Archiver/Désarchiver |

Changer n'importe lequel des trois sélecteurs recharge automatiquement le graphe
correspondant, sans rechargement de page.

## 2bis.3 Créer une cartographie

1. Cliquer **+ Nouvelle cartographie**.
2. Renseigner **Nom*** (obligatoire), **Type** (Urbanisme SI, Métier, Fonctionnel,
   Applicatif, Technique, Cybersécurité, Architecture actuelle/cible, Réseau, Cloud,
   Libre), **Description** (facultative). La version initiale est fixée à `1.0`.
3. Valider : la cartographie est créée, devient **active**, et le moteur affiche un
   graphe vide avec le message : *« Cette cartographie est vide. Commencez à créer vos
   premiers objets. »*

**Exemple Métropolis :** créer successivement *Urbanisme Métier*, *Urbanisme Technique*,
*Cybersécurité* et *Architecture cible* pour le même projet — chaque graphe reste
totalement indépendant (aucun objet partagé).

## 2bis.4 Cycle de vie d'une version

```
Brouillon → (Soumettre pour validation) → En validation → (Valider) → Validée → Archivée
```

- Une version **Validée** ou **Archivée** est automatiquement **figée** (lecture seule
  dans le sélecteur de version tant qu'elle n'est plus la version courante).
- Toute tentative de modification (création/suppression d'objet, relation, ou même un
  simple déplacement de position) sur une cartographie dont la version courante est
  validée déclenche **automatiquement** la création d'une nouvelle version brouillon
  (copie complète du graphe) — la version validée reste intacte et consultable.

**Exemple Métropolis :** Urbanisme Technique `v1.0 Brouillon` → validation RSSI →
`v1.0 Validée` → un consultant ajoute un serveur → UCA crée silencieusement
`v1.1 Brouillon` avec le nouveau serveur ; `v1.0` reste inchangée dans l'historique.

## 2bis.5 Historique

Le menu **Actions ▾ → Historique** ouvre une fenêtre à deux tableaux :

- **Versions** : version, statut, auteur, date de création, avec un bouton
  **Restaurer** sur chaque version non courante.
- **Journal des modifications** : version, auteur, date, action (création,
  modification, nouvelle version, validation, restauration, duplication, archivage…),
  commentaire.

**Restaurer une version** crée une nouvelle version brouillon dont le contenu est une
copie exacte de la version restaurée (aucune perte des versions intermédiaires).

## 2bis.6 Gestion des versions et duplication

Depuis **Actions ▾** :

| Action | Effet |
|--------|-------|
| **Enregistrer sous…** | Copie la cartographie courante sous un nouveau nom, devient la sélection active |
| **Créer une nouvelle version** | Force un nouveau brouillon même si la version courante n'est pas figée |
| **Dupliquer la cartographie** | Copie totalement indépendante (ex. *Urbanisme Technique* → *Architecture Technique 2028*) |
| **Soumettre pour validation** | Brouillon → En validation |
| **Valider cette version** | En validation (ou brouillon) → Validée, figée |
| **Archiver / Désarchiver** | Cartographie archivée : consultable, non modifiable |

Le contrôle des doublons de nom est appliqué côté formulaire (« Enregistrer sous… » et
« Dupliquer » refusent un nom déjà utilisé dans le projet).

## 2bis.7 Export et import

- **Export** : PNG, PDF, JSON, CSV — toujours limité à la cartographie et à la version
  sélectionnées dans le bandeau (jamais l'ensemble du projet). Une architecture ouverte
  permet d'ajouter un export ArchiMate ultérieurement.
- **Import** (`/import-cartographie`) : un sélecteur **Cartographie cible** a été ajouté
  à l'écran d'import — l'import ne modifie jamais que la cartographie choisie, les
  autres cartographies du projet restent intactes.

## 2bis.8 Compatibilité ascendante

Tous les projets créés avant cette évolution reçoivent automatiquement, au premier
accès, une cartographie **« Cartographie principale »** contenant l'intégralité de leur
graphe existant (aucune perte de données, aucune action manuelle requise).

## 2bis.9 Critères de recette — Cartographies et versionning

| # | Critère | Attendu |
|---|---------|---------|
| 1 | Multi-cartographies | Un même projet affiche plusieurs cartographies indépendantes dans le sélecteur |
| 2 | Graphes indépendants | Créer un objet dans une cartographie ne l'affiche pas dans une autre |
| 3 | Création | Nouvelle cartographie → active, graphe vide, message d'état vide affiché |
| 4 | Versionning | Modifier une version validée crée automatiquement une nouvelle version brouillon |
| 5 | Lecture seule | Une version historique (non courante) empêche toute création/suppression |
| 6 | Historique | Chaque action (création, validation, restauration…) apparaît dans le journal |
| 7 | Restauration | Restaurer une ancienne version crée un nouveau brouillon avec son contenu |
| 8 | Duplication | La cartographie dupliquée est indépendante (aucune modification croisée) |
| 9 | Archivage | Une cartographie archivée est consultable mais non modifiable |
| 10 | Export | L'export ne contient que la cartographie/version sélectionnée |
| 11 | Import ciblé | L'import ne modifie que la cartographie cible choisie |
| 12 | Migration | Un projet préexistant conserve son graphe dans sa cartographie par défaut |

---

# PARTIE 3 — CARTOGRAPHIE DES FLUX

## 3.1 Écran et méthode

| Élément | Détail |
|---------|--------|
| **Où** | Moteur d'urbanisme → onglet relations / assistant lien |
| **Types de flux** | Métier, fonctionnel, applicatif, technique |

## 3.2 Flux métier

| ID | Nom | Source → Cible | Données |
|----|-----|----------------|---------|
| FM-01 | Signalement citoyen | Citoyen → Processus incident | Ticket, géoloc |
| FM-02 | Déclenchement crise | Événement public → Cellule crise | Procédure, rôles |

## 3.3 Flux fonctionnels

| ID | Nom | Source → Cible |
|----|-----|----------------|
| FF-01 | Supervision unifiée | Zone supervision → Îlots métiers |
| FF-02 | Alerting multi-canal | Moteur alerting → SMS/mail agents |

## 3.4 Flux applicatifs

| ID | Nom | Protocole |
|----|-----|-----------|
| FA-01 | Portail → IAM | OAuth2 |
| FA-02 | Portail → API mobilité | REST |
| FA-03 | VMS → CSU | RTSP |
| FA-04 | SCADA → Historian | OPC-UA |
| FA-05 | Apps → Wazuh | Syslog/agent |

## 3.5 Flux techniques

| ID | Nom | Équipements |
|----|-----|-------------|
| FT-01 | Collecte logs DC | Serveurs → SIEM |
| FT-02 | Réplication PRA | Storage primaire → PRA |
| FT-03 | IoT → Broker | Capteurs → Plateforme |

## 3.6 Dépendances inter-couches

```
[Métier: Crise] → pilote → [Processus: Crise]
[Processus] → realise → [Opération: Supervision CSU]
[Opération] → supporte → [Îlot appl: CSU]
[Îlot appl] → heberge sur → [Serveur: SRV-VMS-01]
[Serveur] → connecte → [Réseau: VLAN 120]
```

**Contrôle recette :** ≥ 15 relations nommées ; validation métamodèle sans incohérence bloquante.

---

# PARTIE 4 — PRÉPARATION EBIOS RM

## 4.1 Écran

| Route | `/ebios?project={id}` |
| Menu | Cybersécurité → EBIOS RM |

## 4.2 Chaîne d'alimentation urbanisme → EBIOS

```
Urbanisme (actifs, processus, acteurs)
        ↓ import / saisie guidée
Atelier 1 (VM, périmètre) ← objectifs métier, parties prenantes
        ↓
Atelier 2 (BS) ← applications, serveurs, sites (import urbanisme)
        ↓
Atelier 3 (scénarios) ← processus crise, flux critiques
        ↓
Atelier 4 (mesures) ← IAM, SOC, procédures org
        ↓
Atelier 5 (traitement) → GRC registre + PTR
```

## 4.3 Atelier 1 — Cadrage (exemples Métropolis)

| Saisie | Valeur |
|--------|--------|
| Périmètre | SI Métropolis OT/IT — eau, énergie, mobilité, CSU, portail |
| VM-01 | Continuité approvisionnement eau |
| VM-02 | Confiance services numériques |
| VM-03 | Sécurité des personnes (CSU) |
| VM-04 | Conformité NIS2/RGPD |
| VM-05 | Capacité audit prédictif (SIEM + Analytics) |

**Contrôle :** barre progression atelier 1 → Terminé.

## 4.4 Atelier 2 — Biens supports

| BS | Source urbanisme |
|----|------------------|
| BS-01 SCADA eau | SCADA + automates |
| BS-02 Datacenter | Site DC principal |
| BS-03 Portail + IAM | Applications |
| BS-04 VMS + CSU | Sécurité publique |
| BS-05 SIEM Wazuh | Serveurs SIEM |

**Action recette :** bouton **Importer biens supports depuis urbanisme** si disponible.

## 4.5 Atelier 3 — Scénarios

| Type | Exemple Métropolis |
|------|-------------------|
| ER | Ransomware IT→OT ; fuite PII portail ; perte vidéo CSU |
| SR | Cybercriminels ; insider ; prestataire |
| SS | SR-01 → ER-05 |
| SO | Phishing → SCADA ; compromission compte portail |

## 4.6 Atelier 4 — Mesures

| Mesure | Lien urbanisme |
|--------|----------------|
| Segmentation OT/IT | Réseaux VLAN, firewall |
| MFA + PAM | IAM KeyMetropolis |
| SIEM Wazuh | Serveurs SRV-SIEM-* |
| Procédure incident | Organisation / procédures |

## 4.7 Atelier 5 — Traitement

| Risque | Décision | Export GRC |
|--------|----------|------------|
| R-01 Ransomware OT | Réduire | Oui → registre |
| R-02 Fuite PII | Réduire | Oui |
| R-03 Angles morts SIEM | Réduire | Oui |

**Contrôle recette EBIOS :** 5 ateliers complétés ; overview progression > 80 %.

---

# PARTIE 5 — PSSI

## 5.1 Principes

La **PSSI** n'est pas un écran unique : elle se **compose** à partir de :

| Source UCA | Apport PSSI |
|------------|-------------|
| Projet (référentiels, gouvernance) | Cadre normatif |
| Urbanisme (IAM, réseaux, applications) | Mesures techniques |
| EBIOS (mesures, risques) | Justifications et priorisation |
| Organisation (procédures) | Politiques opérationnelles |

## 5.2 Structure PSSI Métropolis (10 chapitres)

1. Gouvernance SSI (CoPil, comité cyber, rôles)  
2. Gestion des accès (IAM, MFA, PAM)  
3. Sécurité réseau (OT/IT/DMZ/CSU)  
4. Sécurité applicative (WAF, SSDLC)  
5. Journalisation (Wazuh, rétention)  
6. Gestion des incidents (playbooks, ANSSI 24h)  
7. Continuité (PCA/PRA)  
8. Conformité (ISO 27001, NIS2, RGPD, EBIOS)  
9. Sensibilisation  
10. Contrôle et audit  

## 5.3 Génération dans UCA

| Étape | Action |
|-------|--------|
| 1 | `/livrables?project={id}` |
| 2 | Type : **Spécifications techniques** ou **Autre** |
| 3 | Titre : `PSSI — Métropole Métropolis v1.0` |
| 4 | Sources : urbanism, ebios, grc |
| 5 | Besoin utilisateur : décrire les 10 chapitres (voir GUIDE_FIL_ROUGE section 11.7) |
| 6 | Aperçu → Générer → Export PDF |

## 5.4 Lien ISO 27001

| Domaine Annexe A | Source UCA |
|------------------|------------|
| A.5 Politiques | Projet + livrable PSSI |
| A.8 Actifs | Urbanisme technique |
| A.9 Accès | IAM + EBIOS mesures |
| A.12 Exploitation | DEX, procédures org |
| A.16 Incidents | SOC + EBIOS |
| A.17 Continuité | Sites PRA/PCA |

**Contrôle recette :** livrable PSSI généré avec sections citant données Métropolis.

---

# PARTIE 6 — GRC

## 6.1 Modules et écrans

| Module | Route |
|--------|-------|
| Registre des risques | `/registre-risques?project={id}` |
| Plan de traitement (PTR) | `/plan-traitement-risques?project={id}` |
| Déclaration d'applicabilité | `/declaration-applicabilite?project={id}` |
| Dashboard RSSI | `/dashboard-rssi?project={id}` |

## 6.2 Registre des risques

| Champ | Alimentation |
|-------|--------------|
| risk_id | EBIOS atelier 5 |
| supporting_asset | BS atelier 2 / urbanisme |
| strategic_scenario | Atelier 3 |
| criticality | Analyse EBIOS |
| treatment_decision | Atelier 5 |
| residual_risk | Atelier 5 |

**Recette Métropolis :** ≥ 5 risques dont R-SEC-01 (CSU/VMS) et R-OT-01 (SCADA).

## 6.3 Plans de traitement et actions

| Action | Responsable | Échéance |
|--------|-------------|----------|
| Couverture agents Wazuh 100 % | SOC Manager | T3 2025 |
| EDR postes CSU | RSSI | T2 2025 |
| Exercice crise cyber | Chef de projet | T4 2025 |

**Écran PTR :** mise à jour statuts actions ; export PDF.

## 6.4 Dashboard RSSI — Indicateurs

| Indicateur | Source |
|------------|--------|
| Nombre risques critiques ouverts | GRC |
| Progression EBIOS % | Module EBIOS |
| Couverture urbanisme | /urbanism/progress |
| Incidents SOC trimestre | Wazuh / corrélations |
| Conformité référentiels | Projet + SoA |

**Contrôle recette :** dashboard charge sans erreur ; graphiques non vides après saisie EBIOS/GRC.

---

# PARTIE 7 — SOC

## 7.1 Écrans

| Module | Route |
|--------|-------|
| Connecteur Wazuh | `/parametres/connecteurs/wazuh` |
| Dashboard Wazuh | `/soc/wazuh` |
| Corrélations | `/soc/correlations?project={id}` |

## 7.2 Alimentation urbanisme + EBIOS → SOC

| Donnée UCA | Usage SOC |
|------------|-----------|
| Labels entités urbanisme (serveurs, apps) | Enrichissement alertes |
| BS EBIOS | Priorisation incidents |
| Risques GRC | Corrélation incident → risk_id |
| Flux documentés | Playbooks SOAR (cible) |

## 7.3 Wazuh / SIEM

| Paramètre Métropolis | Valeur |
|----------------------|--------|
| Manager URL | `https://wazuh.metropolis.lan` |
| Indexer | OpenSearch cluster |
| Agents déployés | 220 / 240 cibles |
| Règles actives | 340+ |

## 7.4 Corrélations

**Écran :** `/soc/correlations?project={id}`  
**Contrôle :** métadonnées `project_id` = Métropolis ; incidents liés à entités urbanisme (ex. SRV-SCADA-01).

## 7.5 SOAR (maturité cible)

Playbooks documentés : phishing, malware endpoint, alerte OT SCADA, indisponibilité portail.  
**Recette actuelle :** vérifier affichage corrélations ; playbooks manuels acceptés en V1.3.

## 7.6 Dashboard SOC

Générer via **Livrables** → type **Rapport SOC** ; sources : soc, wazuh, urbanism, ebios.

---

# PARTIE 8 — IA

## 8.1 Modules actuels

| Module | Route | Rôle |
|--------|-------|------|
| AI Governance | `/ai-governance?project={id}` | Poids modèles, gouvernance |
| Prompt Studio | `/prompt-studio` | Templates prompts |
| Knowledge Base | `/knowledge-base` | Base de connaissances |

## 8.2 Contexte projet consommé par les agents IA (présent et futur)

| Donnée | Stockage / API | Usage IA |
|--------|----------------|----------|
| Projet actif | localStorage + API projet | Scope des requêtes |
| Urbanisme complet | Context Builder `/projects/{id}/context` | Cartographie, recommandations |
| Actifs et flux | Graph + entités | Analyse impact |
| Risques EBIOS/GRC | API GRC | Priorisation, scénarios |
| Livrables générés | Module livrables | RAG documentaire |
| Référentiels | Champs projet | Conformité des réponses |
| Activité projet | project_activity | Traçabilité |

## 8.3 Bonnes pratiques alimentation IA

1. Maintenir le **projet actif** à jour  
2. Compléter urbanisme avant prompts complexes  
3. Cocher sources **urbanism, ebios, grc** dans les livrables  
4. Utiliser **user_need** explicite (public, ton, structure)  
5. Valider humainement toute sortie IA avant diffusion COMEX  

## 8.4 Recette IA (niveau actuel)

| # | Critère |
|---|---------|
| R8.1 | Context Builder retourne objectifs + référentiels Métropolis |
| R8.2 | Livrable avec source `ai` ne provoque pas d'erreur |
| R8.3 | Prompt Studio accessible |

---

# PARTIE 9 — LIVRABLES

## 9.1 Écran

| Route | `/livrables?project={id}` |
| Action | **Nouveau livrable** |

## 9.2 Types UCA et mapping livrables demandés

| Livrable demandé | Type UCA | Sources recommandées |
|------------------|----------|----------------------|
| Note de cadrage | Plan de management de projet | urbanism, ebios, grc |
| Cartographie métier | Matrice des exigences / Autre | urbanism |
| Cartographie organisationnelle | Analyse des parties prenantes | urbanism |
| Cartographie fonctionnelle | Matrice des exigences | urbanism |
| Cartographie applicative | Spécifications techniques | urbanism |
| Cartographie technique | Spécifications techniques | urbanism, wazuh |
| Cartographie des flux | Autre | urbanism |
| DAT | Spécifications techniques | urbanism, ebios |
| DEX | Autre | urbanism |
| Dossier d'architecture | Plan de management / Autre | urbanism, ebios, grc |
| Analyse EBIOS RM | Rapport EBIOS RM | urbanism, ebios, grc |
| PSSI | Spécifications techniques / Autre | urbanism, ebios, grc |
| Déclaration d'applicabilité | SoA | ebios, grc |
| Registre des risques | Registre des risques | ebios, grc, urbanism |
| Dashboard RSSI | Rapport RSSI | grc, ebios, soc, wazuh, urbanism |
| Dashboard SOC | Rapport SOC | soc, wazuh, urbanism |
| Rapport exécutif | Rapport RSSI | toutes sources |
| Rapport COMEX | Plan de management de projet | urbanism, grc, ebios |

## 9.3 Workflow de génération (chaque livrable)

| Étape | Action |
|-------|--------|
| 1 | Sélectionner projet Métropolis (actif) |
| 2 | Nouveau livrable |
| 3 | Renseigner **Titre** |
| 4 | Choisir **Type** |
| 5 | Rédiger **Besoin utilisateur** (prompt métier) |
| 6 | Cocher **Sources de données** |
| 7 | Choisir format **PDF** (ou DOCX / Markdown) |
| 8 | **Aperçu** — vérifier cohérence Métropolis |
| 9 | **Générer** |
| 10 | **Exporter** — archiver pour recette |

## 9.4 Exemple — Rapport COMEX Métropolis

**Titre :** `Rapport COMEX — Programme audit cybersécurité Métropolis`  
**Type :** Plan de management de projet  
**Sources :** urbanism, ebios, grc, soc  
**Besoin utilisateur :**

```
Rapport COMEX 5 pages : synthèse programme Métropolis (800 000 hab.),
résultats audit cybersécurité prédictif, top 5 risques, décisions demandées
(budget SOC, segmentation OT), planning 2025-2026. Ton exécutif non technique.
Inclure indicateurs dashboard RSSI et maturité EBIOS.
```

## 9.5 Critères de recette livrables

| # | Critère |
|---|---------|
| R9.1 | ≥ 10 livrables générés sans erreur |
| R9.2 | Chaque export PDF ouvrable et ≥ 3 pages (hors carto simple) |
| R9.3 | Contenu cite « Métropolis » et au moins 2 référentiels |
| R9.4 | Registre risques aligné avec écran GRC |
| R9.5 | Rapport EBIOS cite ateliers 1 à 5 |

---

# PARTIE 10 — MODE OPÉRATOIRE RECETTE COMPLÈTE

## 10.1 Scénario bout-en-bout (3 jours formation)

### Jour 1 — Projet + Métier + Organisation

| Heure | Étape | Écran | Contrôle |
|-------|-------|-------|----------|
| 09:00 | Connexion | `/login` | Accès modules OK |
| 09:30 | Création projet | `/projects` | R1.* |
| 10:00 | Équipe | `?tab=team` | Membres ajoutés |
| 10:30 | Métier sécurité publique | `/schema-urbanisme` | Objectifs/processus |
| 11:30 | Métiers eau, mobilité, énergie, SN | Idem | 5 métiers |
| 14:00 | Organisation + acteurs | Couche org | RACI documenté |
| 16:00 | Validation métamodèle | `/validation-metamodele` | Pas d'erreur bloquante |
| 17:00 | Bilan J1 | Dashboard projet | Progression > 25 % |

### Jour 2 — Fonctionnel → Technique + Flux + EBIOS

| Heure | Étape | Écran | Contrôle |
|-------|-------|-------|----------|
| 09:00 | Couches fonctionnelle & applicative | Urbanisme | Apps reliées |
| 11:00 | Couche technique + équipements | Urbanisme | 20+ entités |
| 13:00 | Flux SI | Relations | 15+ liens |
| 14:00 | EBIOS ateliers 1-3 | `/ebios` | VM, BS, scénarios |
| 16:00 | EBIOS ateliers 4-5 | `/ebios` | Mesures, traitement |
| 17:00 | Registre risques | `/registre-risques` | Risques visibles |

### Jour 3 — GRC, SOC, PSSI, Livrables

| Heure | Étape | Écran | Contrôle |
|-------|-------|-------|----------|
| 09:00 | PTR + SoA | GRC | Actions créées |
| 10:00 | Dashboard RSSI | `/dashboard-rssi` | KPIs OK |
| 11:00 | Wazuh + corrélations | `/soc/*` | project_id OK |
| 13:00 | Génération 5 livrables | `/livrables` | PDF OK |
| 15:00 | PSSI + Rapport COMEX | Livrables | Contenu complet |
| 16:00 | Dashboard 360° | `/projects/{id}` | Synthèse OK |
| 17:00 | Recette finale | Checklist § 10.2 | 100 % P1 |

## 10.2 Checklist recette fonctionnelle officielle (P1 = bloquant)

| ID | Exigence | P1 | OK |
|----|----------|----|-----|
| RF-01 | CRUD projet + projet actif | ✓ | ☐ |
| RF-02 | Validation dates projet | ✓ | ☐ |
| RF-03 | Équipe projet + rôles | ✓ | ☐ |
| RF-04 | Journal project_activity | ✓ | ☐ |
| RF-05 | 5 couches Club Urba renseignées | ✓ | ☐ |
| RF-06 | Relations inter-couches | ✓ | ☐ |
| RF-06bis | Multi-cartographies + versionning (§ 2bis) | ✓ | ☐ |
| RF-07 | Progression urbanisme > 60 % | ✓ | ☐ |
| RF-08 | EBIOS 5 ateliers | ✓ | ☐ |
| RF-09 | Registre risques alimenté | ✓ | ☐ |
| RF-10 | PTR + SoA consultables | ✓ | ☐ |
| RF-11 | Dashboard RSSI | ✓ | ☐ |
| RF-12 | Corrélations SOC par projet | | ☐ |
| RF-13 | Connecteur Wazuh paramétrable | | ☐ |
| RF-14 | ≥ 10 livrables générés | ✓ | ☐ |
| RF-15 | Export PDF sans erreur | ✓ | ☐ |
| RF-16 | Dashboard projet 360° | ✓ | ☐ |
| RF-17 | Données Métropolis cohérentes bout-en-bout | ✓ | ☐ |

## 10.3 Erreurs fréquentes globales

| Erreur | Impact | Correction |
|--------|--------|------------|
| Projet non actif | Modules sans contexte | **Ouvrir** le projet |
| Oublier `?project=` | Données vides | Sélectionner projet dans module |
| Urbanisme incomplet | EBIOS/GRC pauvres | Compléter BS avant atelier 3 |
| Sources livrables non cochées | Export générique vide | Cocher urbanism + ebios + grc |
| Supprimer projet avec données | 409 Conflict | Archiver plutôt que supprimer |
| Code projet dupliqué | Échec création | Choisir code unique |

## 10.4 Bonnes pratiques officielles

1. **Toujours** partir du modèle Métropolis en formation  
2. **Nommer** les entités urbanisme comme dans la GRC (même libellés)  
3. **Tracer** chaque atelier EBIOS avant de générer les livrables  
4. **Vérifier** l'aperçu livrable avant export COMEX  
5. **Maintenir** référentiels projet alignés avec SoA  
6. **Documenter** les écarts de recette dans le journal activité (commentaires)  

---

# ANNEXES

## Annexe A — Table de correspondance des écrans

| Fonction | URL |
|----------|-----|
| Projets | `/projects` |
| Détail projet | `/projects/{id}` |
| Urbanisme | `/schema-urbanisme?project={id}` |
| Métamodèle | `/validation-metamodele?project={id}` |
| EBIOS | `/ebios?project={id}` |
| Registre risques | `/registre-risques?project={id}` |
| PTR | `/plan-traitement-risques?project={id}` |
| SoA | `/declaration-applicabilite?project={id}` |
| Dashboard RSSI | `/dashboard-rssi?project={id}` |
| Livrables | `/livrables?project={id}` |
| Corrélations SOC | `/soc/correlations?project={id}` |
| Wazuh | `/soc/wazuh` |
| Connecteur Wazuh | `/parametres/connecteurs/wazuh` |
| AI Governance | `/ai-governance?project={id}` |
| Administration orgs | `/administration/organizations` |
| Administration users | `/administration/users` |

## Annexe B — Données Métropolis de référence (template)

Source : `backend/app/services/project_templates.py` — template `metropolis`.

**Objectifs préremplis :**

- Services publics numériques sécurisés  
- Conformité NIS2 et RGPD  
- Résilience des services urbains critiques  

**Référentiels préremplis :** RGPD, NIS2, ISO 27001, IEC 62443  

**Secteur :** `smart_city`

## Annexe C — Références documentaires

| Document | Chemin |
|----------|--------|
| Note explicative Métropolis | `docs/metropolis/NOTE_EXPLICATIVE_DU_PROJET.md` |
| Guide fil rouge UCA | `docs/metropolis/GUIDE_FIL_ROUGE_UCA.md` |
| Ce guide (officiel) | `docs/GUIDE_RECETTE_FONCTIONNELLE_URBAN_CYBER_ARCHITECT.md` |
| Guide utilisateur — Cartographies et versionning | `docs/urbanism/GUIDE_CARTOGRAPHIES_VERSIONNING.md` |
| Documentation développeur — Cartographies et versionning | `docs/urbanism/DEVELOPPEUR_CARTOGRAPHIES_VERSIONNING.md` |

---

**Fin du guide de recette fonctionnelle officiel — Urban Cyber Architect**

*Document produit — Cas Métropolis ISRC10 — Version 1.0*
