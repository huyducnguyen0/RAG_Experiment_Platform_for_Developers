# Feature Status Matrix

Last updated: 2026-05-29

## Legend

```text
Done       = implemented and usable
Partial    = usable but intentionally limited
Planned    = not implemented yet
Legacy     = still available, not the main product flow
```

## Backend Features

| Feature | Status | Main files | Notes |
|---|---|---|---|
| FastAPI app shell | Done | `app/main.py` | App title is `RAG Experiment Platform for Developers`. CORS allows Vite on 5173. |
| Health endpoint | Done | `app/api/routes/health.py` | `GET /health`. |
| Mock chat endpoint | Done | `app/api/routes/chat.py`, `app/services/chat_service.py` | Basic chat mock. Not the main RAG flow. |
| Workspace CRUD | Done | `app/api/routes/workspaces.py`, `app/services/workspace_service.py` | Create/list/detail/rename/delete workspace. Delete removes workspace folder. |
| Document upload | Done | `app/services/document_service.py` | Supports `.txt` and `.md`, UTF-8 only. |
| Workspace documents | Done | `app/api/routes/workspaces.py`, `app/services/document_service.py` | Main document path is workspace-scoped. |
| Legacy global documents | Legacy | `app/api/routes/documents.py` | Still exists for manual testing, not recommended for frontend. |
| Automatic chunking | Done | `app/services/chunking_service.py` | Character chunking: size 800, overlap 100. |
| Keyword retrieval | Done | `app/services/retrieval_service.py` | Keyword scoring by lowercase token count. |
| RAG mock answer | Partial | `app/services/rag_service.py`, `app/services/ai_service.py` | Uses retrieved context + mock answer, no real LLM yet. |
| Sources in RAG response | Done | `app/services/rag_service.py`, `app/schemas/research.py` | Returns document title, chunk id, score, preview. |
| Golden questions upload/list/delete | Done | `app/services/eval_question_service.py`, `app/schemas/eval.py` | Upload `.jsonl` per workspace. |
| Retrieval metrics | Done | `app/services/evaluation_service.py` | Computes hit@k, recall@k, precision@k, MRR, avg latency. |
| Eval script report export | Done | `scripts/run_retrieval_eval.py` | Saves timestamped JSON/Markdown under `reports/`. |
| Workspace experiment runs | Done | `app/services/experiment_service.py`, `app/schemas/experiment.py` | Runs keyword baseline over workspace golden questions. |
| Experiment history/detail APIs | Done | `app/services/experiment_service.py` | List/detail run JSON from workspace storage. |
| Workspace markdown reports | Done | `app/services/experiment_service.py` | Saves and returns Markdown report per run. |
| Vector retrieval | Planned | `app/vectorstore/*` exists but not integrated | Next recommended phase. |
| Hybrid retrieval | Planned | none | After vector baseline works. |
| Reranking | Planned | none | After hybrid. |
| Real LLM answer mode | Planned | `app/core/config.py` has `OPENAI_API_KEY`; `openai` dep exists | Do not add before eval flow is stable. |
| Agentic router | Planned | agent folders exist but not active in API | Future phase. |
| Production DB | Planned | `app/database/session.py` exists but not used by MVP flow | Local JSON/file storage is current source of truth. |
| Auth/user management | Planned | none | Out of MVP scope. |

## Frontend Features

| Feature | Status | Main files | Notes |
|---|---|---|---|
| Vite React app | Done | `frontend/src/main.tsx` | React 19 + TypeScript. |
| API client | Done | `frontend/src/api/client.ts` | Base URL defaults to `http://127.0.0.1:8000`. |
| Workspace home | Done | `frontend/src/App.tsx` | List/create/select workspaces. |
| Workspace delete | Done | `frontend/src/App.tsx` | Deletes workspace and data through backend. |
| Documents tab | Done | `frontend/src/App.tsx` | Upload/list/detail/delete documents. |
| Golden Questions tab | Done | `frontend/src/App.tsx` | Upload/list/delete JSONL questions. |
| Experiments tab | Done | `frontend/src/App.tsx` | Run keyword baseline, list runs, view metrics. |
| Reports tab | Done | `frontend/src/App.tsx` | Shows selected Markdown report as preformatted text. |
| Playground tab | Done | `frontend/src/App.tsx` | Calls workspace RAG mock query and shows sources. |
| Compare strategies UI | Planned | `frontend/src/App.tsx` | Needs vector/hybrid/rerank backend first. |
| Report rendering polish | Partial | `frontend/src/App.tsx` | Currently raw Markdown in `<pre>`, not rich rendered. |

## Data Storage Status

Current MVP storage is local file storage.

Global legacy data:

```text
data/metadata.json
data/documents/
```

Workspace data:

```text
data/workspaces/metadata.json
data/workspaces/{workspace_id}/metadata.json
data/workspaces/{workspace_id}/documents/
data/workspaces/{workspace_id}/eval_sets/golden_questions.jsonl
data/workspaces/{workspace_id}/experiments/run_*.json
data/workspaces/{workspace_id}/reports/run_*.md
```

Important:

- Runtime data should generally not be committed.
- The current MVP intentionally avoids PostgreSQL/SQLite.
- Local JSON storage is acceptable until the evaluation loop is stable.

## API Status

Primary workspace API:

```text
POST   /workspaces
GET    /workspaces
GET    /workspaces/{workspace_id}
PATCH  /workspaces/{workspace_id}
DELETE /workspaces/{workspace_id}

POST   /workspaces/{workspace_id}/documents/upload
GET    /workspaces/{workspace_id}/documents
GET    /workspaces/{workspace_id}/documents/{document_id}
DELETE /workspaces/{workspace_id}/documents/{document_id}

POST   /workspaces/{workspace_id}/research/retrieve
POST   /workspaces/{workspace_id}/research/query

POST   /workspaces/{workspace_id}/eval/questions/upload
GET    /workspaces/{workspace_id}/eval/questions
DELETE /workspaces/{workspace_id}/eval/questions/{question_id}

POST   /workspaces/{workspace_id}/experiments/run
GET    /workspaces/{workspace_id}/experiments
GET    /workspaces/{workspace_id}/experiments/{run_id}
GET    /workspaces/{workspace_id}/reports/{run_id}
```

Legacy/global API:

```text
GET    /
GET    /health
POST   /chat

POST   /documents/upload
GET    /documents
GET    /documents/{document_id}
DELETE /documents/{document_id}

POST   /research/retrieve
POST   /research/query
```

## Known Limitations

- Retrieval is keyword-only.
- `strategy` in experiments only accepts `keyword`.
- RAG answer generation is mock mode only.
- Frontend cannot compare multiple strategies yet.
- Reports are displayed as raw Markdown.
- There are no automated tests for the new experiment APIs yet.
- Some older project scaffold folders exist but are not active in the current MVP flow.
