# Guide utilisateur — Import cartographie urbanisme SI (V1.4)

## Objectif

Permettre à un consultant d'importer une cartographie complète depuis Excel ou CSV, sans saisie manuelle objet par objet.

## Accès

1. Menu **Urbanisme** → **Importer une cartographie**
2. Ou URL : `/import-cartographie?project={id_projet}`

## Étapes

### 1. Télécharger le modèle Excel

Cliquez sur **Télécharger le modèle Excel**. Le fichier officiel contient 15 feuilles :

| Feuille | Contenu |
|---------|---------|
| 01_Metiers | Métiers |
| 02_Objectifs | Objectifs liés aux métiers |
| 03_Processus | Processus |
| 04_Activites | Activités |
| 05_Classes | Classes |
| 06_Organisation | Directions / services |
| 07_Operations | Opérations |
| 08_Fonctionnel | Îlots fonctionnels |
| 09_Applicatif | Applications |
| 10_Technique | Liens application → infra |
| 11_Serveurs | Serveurs |
| 12_Reseaux | Réseaux |
| 13_Sites | Sites |
| 14_Equipements | Postes / équipements |
| 15_Flux | Flux applicatifs |

Fichier fourni : `docs/urbanism/UCA_Modele_Cartographie_Urbanisme_V1.4.xlsx`

### 2. Remplir le modèle

- Les **ID** doivent être uniques par type d'objet.
- Les colonnes de référence (ex. « Métier associé ») acceptent l'**ID** ou le **Nom** de l'objet parent.
- Une ligne d'exemple est fournie sur chaque feuille.

### 3. Choisir le mode

| Mode | Comportement |
|------|--------------|
| **Fusionner** | Met à jour les objets existants (même ID ou même libellé), ajoute les nouveaux, ne supprime rien |
| **Remplacer** | Efface la cartographie du projet puis reconstruit depuis le fichier |

### 4. Importer et prévisualiser

1. Sélectionnez le projet
2. Importez le fichier `.xlsx` ou `.csv`
3. Cliquez **Prévisualiser les données**

La prévisualisation affiche :

- le nombre d'objets par couche
- le nombre de relations prévues
- les erreurs : référence inconnue, doublon, nom vide, relation impossible

### 5. Valider

Cliquez **Valider et construire la cartographie**. Un rapport récapitule :

- objets créés / mis à jour
- relations créées
- objets orphelins
- taux de complétude
- progression Urbanisme

### 6. Vérifier le résultat

Ouvrez le **Moteur d'urbanisme** pour visualiser le graphe généré.

## Import CSV

Deux formats acceptés :

- Fichier nommé selon la feuille : `03_Processus.csv`
- CSV unique avec colonne `Feuille` (ex. `01_Metiers`)

## Exploitation par les autres modules

Les objets sont stockés dans `urbanism_entities` et `urbanism_relations`, exploitables directement par EBIOS RM, GRC, SOC, livrables et agents IA sans ressaisie.
