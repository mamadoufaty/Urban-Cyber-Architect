# Recette fonctionnelle — Import cartographie urbanisme V1.4

## Prérequis

- Backend démarré
- Compte consultant ou admin
- Projet de test créé

## RF-IMP-01 — Téléchargement modèle

| Étape | Action | Résultat attendu |
|-------|--------|------------------|
| 1 | Menu Urbanisme → Importer une cartographie | Page affichée |
| 2 | Clic « Télécharger le modèle Excel » | Fichier `UCA_Modele_Cartographie_Urbanisme_V1.4.xlsx` téléchargé |
| 3 | Ouvrir le fichier | 15 feuilles + README présents |

## RF-IMP-02 — Prévisualisation

| Étape | Action | Résultat attendu |
|-------|--------|------------------|
| 1 | Sélectionner un projet | Projet actif |
| 2 | Importer le modèle pré-rempli (exemples) | Fichier accepté |
| 3 | Clic « Prévisualiser » | Compteurs métiers, objectifs, processus, etc. > 0 |
| 4 | Vérifier erreurs | Aucune erreur bloquante sur le modèle d'exemple |

## RF-IMP-03 — Import fusion

| Étape | Action | Résultat attendu |
|-------|--------|------------------|
| 1 | Mode « Fusionner » | Sélectionné |
| 2 | Valider l'import | Rapport : objets créés > 0, relations créées > 0 |
| 3 | Ouvrir moteur d'urbanisme | Graphe visible avec couches |
| 4 | Réimporter le même fichier | Objets mis à jour, pas de doublon |

## RF-IMP-04 — Import remplacement

| Étape | Action | Résultat attendu |
|-------|--------|------------------|
| 1 | Modifier manuellement le graphe | Changement visible |
| 2 | Mode « Remplacer » + import | Ancienne cartographie remplacée |
| 3 | Vérifier graphe | Conforme au fichier uniquement |

## RF-IMP-05 — Contrôle erreurs

| Cas | Fichier | Résultat attendu |
|-----|---------|------------------|
| Référence inconnue | Objectif avec métier « INEXISTANT » | Erreur `unknown_reference` en prévisualisation |
| Nom vide | Ligne sans Nom | Erreur `empty_name` |
| Doublon ID | Deux métiers même ID | Erreur `duplicate` |

## RF-IMP-06 — Rapport qualité

Après import réussi, le rapport affiche :

- [ ] Objets créés
- [ ] Objets mis à jour
- [ ] Relations créées
- [ ] Objets orphelins
- [ ] Incohérences
- [ ] Taux de complétude (%)
- [ ] Progression Urbanisme (%)

## RF-IMP-07 — Exploitation aval

| Module | Vérification |
|--------|--------------|
| EBIOS RM | Import biens supports depuis urbanisme |
| Dashboard projet | Progression urbanisme mise à jour |
| Livrables | Contexte urbanisme disponible |

## RF-IMP-08 — API

| Test | Commande / appel | Attendu |
|------|------------------|---------|
| Template | GET `/api/urbanism/import/template` | HTTP 200, type xlsx |
| Preview | POST multipart preview | JSON counts + issues |
| Import | POST multipart import | JSON report |
