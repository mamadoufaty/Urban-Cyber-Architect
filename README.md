# Urban Cyber Architect

Plateforme d'aide à la décision pour construire une architecture d'entreprise et de cybersécurité à partir des objectifs métier, processus, contraintes réglementaires, risques et bonnes pratiques.

## Architecture V1

```
Utilisateur → Context Builder → Knowledge Base → AI Orchestrator
  → Multi-LLM Engine → Judge Engine → Validation Humaine → Knowledge Graph
```

### Couches implémentées

| Couche | Statut |
|--------|--------|
| Context Builder | ✅ Organisation, référentiels, urbanisme, KB sectorielle |
| Knowledge Base | ✅ Smart City, Banque, Santé, Industrie |
| AI Orchestrator | ✅ Pipeline complet |
| Multi-LLM Engine | ✅ 3 mocks + interfaces OpenAI, Anthropic, Google, Ollama, Azure |
| Judge Engine | ✅ Scoring pondéré (Urbanisme, Conformité, EBIOS, Architecture) |
| Validation Humaine | ✅ Accept / Modify / Merge / Reject + historique |
| Knowledge Graph | ✅ Construction automatique post-validation |
| AI Governance | ✅ Modèles, juge, pondérations |
| Prompt Studio | ✅ Templates versionnés |

## Démarrage rapide

### Avec Docker

```bash
docker compose up --build
```

- API : http://localhost:8000
- Frontend : http://localhost:5173
- Docs API : http://localhost:8000/docs

### Sans Docker (SQLite par défaut)

```bash
cp .env.example .env

cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

La base SQLite est créée automatiquement : `backend/urban_cyber_architect.db`.

Pour PostgreSQL, définir `DATABASE_URL` dans `.env` :
`postgresql+asyncpg://uca:uca@localhost:5432/urban_cyber_architect`

```bash
cd ../frontend
npm install
npm run dev
```

## API principale

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/projects` | Créer un projet |
| GET | `/api/projects/{id}/context` | Contexte projet |
| POST | `/api/projects/{id}/orchestrate` | Pipeline multi-LLM + Judge |
| POST | `/api/projects/{id}/decisions` | Validation humaine |
| GET | `/api/projects/{id}/graph` | Knowledge Graph |
| GET/PUT | `/api/ai-governance` | Configuration IA |
| GET/PUT | `/api/prompts/{name}` | Prompt Studio |
| GET | `/api/knowledge-base/sectors` | Secteurs métier |

## Abstraction LLM (V1)

Les providers sont découplés via `LLMProvider` et `JudgeProvider` :

```python
# backend/app/ai/interfaces.py
class LLMProvider(ABC):
    async def complete(self, prompt: str, context: ProjectContext) -> ModelResponse: ...
```

Providers disponibles :
- `mock-gpt`, `mock-claude`, `mock-gemini` (par défaut, sans clé API)
- `gpt-4o`, `claude-sonnet-4-20250514`, `gemini-2.0-flash`, `llama3.2`, `azure-gpt-4o`

Ajouter un provider = implémenter l'interface + enregistrer dans `registry.py`.

## Structure

```
Urban_Cyber_Architect/
├── backend/app/
│   ├── ai/              # Orchestrator, Judge, Providers
│   ├── context/         # Context Builder
│   ├── prompts/         # Prompt Studio
│   ├── models/          # Entités SQLAlchemy
│   ├── api/routes/      # Endpoints REST
│   └── services/        # Graph, Validation
├── frontend/src/        # React + Vite
├── knowledge-base/      # Données sectorielles YAML
└── docker-compose.yml
```

## Licence

Propriétaire — Urban Cyber Architect
