# Guide utilisateur — Cartographies multiples et versionning

## Objectif

Un projet Urban Cyber Architect peut désormais contenir **plusieurs cartographies
indépendantes** (Urbanisme Métier, Urbanisme Technique, Cybersécurité, Architecture
cible, Réseau, Cloud…), chacune évoluant dans le temps au travers de **versions**
(brouillon → en validation → validée → archivée), avec un historique complet des
modifications.

## Accès

Menu **Urbanisme** → **Urbanisme SI** (`/schema-urbanisme?project={id}`). Le bandeau en
haut de l'écran permet de choisir le **Projet**, la **Cartographie** et la **Version**.

## 1. Le bandeau du moteur

```
Projet          Cartographie              Version                          Actions
▼ Métropolis    ▼ Urbanisme Technique     ▼ v1.2 — Brouillon    [+ Nouvelle cartographie]  [Actions ▾]
```

- Changer le **Projet**, la **Cartographie** ou la **Version** recharge automatiquement
  le graphe correspondant — aucune donnée n'est partagée entre deux cartographies.
- Un badge de statut (Brouillon / En validation / Validée / Archivée) est affiché à côté
  des sélecteurs.
- Sélectionner une version qui **n'est pas** la version courante bascule l'écran en
  **lecture seule** (bandeau orange « Lecture seule — version archivée du fil ») : les
  formulaires de création et les boutons de suppression sont masqués. Utilisez
  **Restaurer** (voir § 4) pour repartir de son contenu.

## 2. Créer une nouvelle cartographie

1. Cliquer **+ Nouvelle cartographie**.
2. Renseigner :
   - **Nom*** (obligatoire)
   - **Type** : Urbanisme SI, Urbanisme Métier, Urbanisme Fonctionnel, Urbanisme
     Applicatif, Urbanisme Technique, Cybersécurité, Architecture actuelle, Architecture
     cible, Réseau, Cloud, Libre
   - **Description** (facultative)
3. Valider. La cartographie créée devient immédiatement active et le moteur affiche un
   graphe vide avec le message :

   > Cette cartographie est vide. Commencez à créer vos premiers objets.

## 3. Cycle de vie d'une version

```
Brouillon ──Soumettre pour validation──▶ En validation ──Valider cette version──▶ Validée ──▶ Archivée
```

- Une version **Validée** ou **Archivée** est figée : elle reste consultable mais ne
  peut plus être modifiée directement.
- Si vous modifiez malgré tout le graphe pendant que la version courante est figée
  (ajout d'objet, relation, ou simple déplacement), UCA crée **automatiquement** une
  nouvelle version brouillon (copie complète du contenu) — la version validée n'est
  jamais altérée.

Exemple : `Urbanisme Technique v1.0 (Validée)` + ajout d'un serveur ⇒ création
silencieuse de `v1.1 (Brouillon)` contenant l'ancien graphe + le nouveau serveur.

## 4. Menu Actions

Le bouton **Actions ▾** (visible dès qu'une cartographie est sélectionnée) propose :

| Action | Effet |
|--------|-------|
| **Historique** | Ouvre la liste des versions et le journal des modifications (voir § 5) |
| **Enregistrer sous…** | Copie la cartographie courante sous un nouveau nom (devient la sélection active) |
| **Créer une nouvelle version** | Force la création d'un nouveau brouillon, même si la version courante n'est pas figée |
| **Dupliquer la cartographie** | Copie totalement indépendante — aucune modification croisée avec l'original |
| **Soumettre pour validation** | Passe la version de Brouillon à En validation |
| **Valider cette version** | Fige la version (Validée), horodatée avec le nom du validateur |
| **Archiver / Désarchiver** | Rend la cartographie consultable uniquement (ou la réactive) |

## 5. Historique et restauration

**Actions ▾ → Historique** affiche deux tableaux :

- **Versions** : version, statut, auteur, date, avec un bouton **Restaurer** sur chaque
  version qui n'est pas la version courante.
- **Journal des modifications** : version, auteur, date, action (création,
  modification, nouvelle version, validation, restauration, duplication, archivage,
  désarchivage), commentaire.

**Restaurer une version** crée une nouvelle version brouillon dont le contenu est une
copie exacte de la version choisie — les versions intermédiaires restent visibles dans
l'historique.

## 6. Export et import

- **Export** (PNG, PDF, JSON, CSV) : porte uniquement sur la **cartographie et la
  version actuellement sélectionnées** dans le bandeau. Le nom du fichier généré inclut
  le projet, la cartographie et la version (ex. `metropolis-urbanisme-technique-v1.2.csv`).
- **Import** (`/import-cartographie`) : un sélecteur **Cartographie cible** permet de
  choisir précisément dans quelle cartographie du projet actif les données seront
  importées. Les autres cartographies du projet ne sont jamais modifiées.

## 7. Cartographies existantes (migration)

Aucune action n'est requise : tout projet créé avant cette évolution reçoit
automatiquement, dès son premier accès, une cartographie **« Cartographie
principale »** contenant l'intégralité de son graphe existant.

## 8. Bonnes pratiques

- Nommez vos cartographies par usage (« Urbanisme Métier », « Cybersécurité ») plutôt
  que par date, et utilisez les versions pour l'historique temporel.
- Validez une cartographie avant tout comité ou export officiel : cela fige son contenu
  et évite les modifications accidentelles.
- Utilisez **Dupliquer** pour explorer une cible d'architecture sans risquer l'existant
  (ex. « Architecture Technique 2028 » dupliquée depuis « Urbanisme Technique »).
