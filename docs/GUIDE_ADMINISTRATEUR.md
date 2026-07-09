# Guide administrateur — Urban Cyber Architect

## Protection du dernier administrateur

Urban Cyber Architect **refuse** la suppression ou la désactivation du dernier compte possédant un rôle administrateur (`admin` ou `superadmin`).

Message affiché :

> Impossible de supprimer le dernier administrateur de la plateforme.

Cette protection s'applique également lors d'une rétrogradation de rôle (passage à consultant, RSSI, etc.).

### Bonnes pratiques

- Maintenir **au moins deux comptes administrateurs** actifs (ex. `admin` + `admin1`).
- Utiliser la **désactivation** plutôt que la suppression pour les comptes temporairement inutilisés.
- Réserver le rôle `superadmin` au compte principal d'urgence.

---

## Recréer un administrateur (situation de verrouillage)

Si tous les comptes administrateurs ont été supprimés, trois mécanismes officiels sont disponibles **sans modifier manuellement SQLite**.

### 1. Commande CLI (recommandée en production)

Depuis le répertoire `backend` :

```bash
python -m app.cli bootstrap-admin --username admin --password "VotreMotDePasse@123"
```

Options utiles :

| Option | Description |
|--------|-------------|
| `--username` | Login (défaut : `admin`) |
| `--password` | Mot de passe (invite sécurisée si omis) |
| `--first-name` / `--last-name` | Identité affichée |
| `--email` | Adresse e-mail |
| `--reset` | Réinitialise le mot de passe si le compte existe |

La commande :

- recrée les rôles et l'organisation par défaut si nécessaire ;
- crée l'utilisateur s'il est absent ;
- réinitialise le mot de passe et le rôle administrateur s'il existe déjà.

### 2. Écran de récupération (développement / bootstrap activé)

Sur la page de connexion, si **aucun administrateur actif** n'est détecté et que le bootstrap est autorisé, le formulaire **Créer un administrateur** s'affiche automatiquement.

Activation via l'une des conditions suivantes :

- mode développement (`DEBUG=true`) ;
- variable d'environnement `ENABLE_BOOTSTRAP_ADMIN=true`.

**En production**, laissez `ENABLE_BOOTSTRAP_ADMIN=false` (défaut) et utilisez la CLI.

### 3. API (même restrictions que l'écran)

- `GET /api/auth/bootstrap/status` — état de récupération
- `POST /api/auth/bootstrap` — création du premier administrateur

Accessible uniquement si bootstrap activé **et** aucun administrateur actif.

---

## Réinitialiser un mot de passe administrateur

| Contexte | Méthode |
|----------|---------|
| Un autre admin est connecté | Administration → Utilisateurs → Réinit. MDP |
| Accès admin disponible | Même procédure sur le compte concerné |
| Plateforme verrouillée | `python -m app.cli bootstrap-admin --username admin --reset` |

---

## Audit

Chaque opération de bootstrap génère une entrée d'audit :

- **Action** : `admin.bootstrap`
- **Champs** : date, utilisateur, adresse IP, résultat (`created` / `password_reset`)

Consultation : Administration → Journaux d'audit (ou `GET /api/admin/audit-logs`).

---

## Fichiers techniques

| Composant | Emplacement |
|-----------|-------------|
| Protection | `backend/app/services/admin/admin_guard.py` |
| Bootstrap | `backend/app/services/admin/bootstrap_admin_service.py` |
| CLI | `backend/app/cli/__main__.py` |
| API | `backend/app/api/routes/auth.py` |
| Interface | `frontend/src/pages/LoginPage.tsx` |

---

## Tests

```bash
cd backend
python -m pytest tests/test_admin_bootstrap.py -q
```
