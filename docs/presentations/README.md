# Présentation Premium UCA

## Fichier

- **`UCA_Presentation_Premium.pptx`** — 81 diapositives, format 16:9, thème sombre aligné sur la charte UCA (`#00d4aa`).

## Contenu

| Partie | Thème | Diapositives |
|--------|-------|--------------|
| 1 | Vision, objectifs, positionnement | 9 |
| 2 | Architecture technique | 11 |
| 3 | Urbanisme SI (7 couches + cartographie) | 14 |
| 4 | Référentiels (ISO, EBIOS, NIST, CIS, DORA, NIS2, ANSSI) | 20 |
| 5 | Gouvernance SSI (PSSI, risques, PTR, SoA, PCA/PRA) | 8 |
| 6 | Modules UCA | 8 |
| 7 | Démonstration Métropolis | 4 |
| 8 | Roadmap V1–V3 | 4 |
| 9 | Conclusion | 4 |

Durée estimée : **~60 minutes** (45 s à 1 min par diapositive selon le public).

## Régénération

```bash
cd backend
.venv\Scripts\pip.exe install python-pptx
.venv\Scripts\python.exe ..\scripts\generate_uca_presentation.py
```

## Personnalisation

1. **Captures d'écran** — Insérer manuellement dans PowerPoint les captures de l'application (Urbanisme, EBIOS, Dashboard, Livrables, SOC).
2. **Logo client** — Ajouter sur la diapositive de titre et en pied de page.
3. **SmartArt** — Le script génère des diagrammes vectoriels (formes) ; vous pouvez les convertir en SmartArt natif dans PowerPoint si souhaité.

## Scénario fil rouge

La démonstration s'appuie sur le projet **Métropolis** (680 000 habitants, NIS2, SCADA, CSU) documenté dans `docs/metropolis/NOTE_EXPLICATIVE_DU_PROJET.md`.
