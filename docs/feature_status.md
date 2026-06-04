# Feature Status Matrix

Last updated: 2026-06-04

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
| FastAPI app shell | Done | `app/main.py` | App title is `RAG Experiment Platform for Developers`. |
| Health endpoint | Done | `app/api/routes/health.py` | `GET /health`. |
| Mock chat endpoint | Done | `app/api/routes/chat.py`, `app/services/chat_service.py` | Basic chat mock. Not the main product flow. |
| Workspace CRUD | Done | `app/api/routes/workspaces.py`, `app/services/workspace_service.py` | Create/list/detail/rename/delete workspace. |
| Document upload | Done | `app/services/document_service.py` | Supports `.txt` and `.md`, UTF-8 only. |
| Folder/corpus upload | Done | `app/api/routes/workspaces.py`, `app/services/document_service.py`, `frontend/src/App.tsx` | Uploads nested folders, imports `.txt`/`.md`, skips unsupported files. |
| Multi-file document upload UI support | Done | `frontend/src/App.tsx` | Browser file picker can select multiple docs. |
| Workspace documents | Done | `app/api/routes/workspaces.py`, `app/services/document_service.py` | Main document path is workspace-scoped. |
| Legacy global documents | Legacy | `app/api/routes/documents.py` | Still exists for manual testing, not recommended for frontend. |
| Automatic chunking | Done | `app/services/chunking_service.py` | Current active chunking is simple fixed character chunking. |
| Rich document/chunk metadata | Done | `app/schemas/document.py`, `app/services/document_service.py` | Preserves source path, relative path, folder path, doc type, and chunking strategy. |
| Keyword retrieval | Done | `app/services/retrieval_service.py` | Baseline lexical retrieval. |
| Vector retrieval | Done | `app/services/retrieval_service.py`, `app/vectorstore/chroma_client.py` | Uses sentence-transformers + Chroma. |
| Hybrid retrieval | Done | `app/services/retrieval_service.py` | Combines keyword and vector ranked results. |
| RAG mock answer | Partial | `app/services/rag_service.py`, `app/services/ai_service.py` | Uses retrieved context + mock answer, no real LLM answer eval yet. |
| Sources in RAG response | Done | `app/services/rag_service.py`, `app/schemas/research.py` | Returns document title, chunk id, score, preview. |
| Golden questions upload/list/delete | Done | `app/services/eval_question_service.py`, `app/schemas/eval.py` | Upload `.jsonl` or `.csv` per workspace with strong, evidence-text, or weak-label supervision. |
| Golden question repair | Partial | `app/services/eval_question_service.py` | Can infer expected ids from supported notes patterns when possible, but chunk-id annotation is no longer required for upload. |
| Retrieval metrics | Done | `app/services/evaluation_service.py` | Computes hit@k, recall@k, precision@k, MRR, avg latency. |
| Workspace experiment runs | Done | `app/services/experiment_service.py`, `app/schemas/experiment.py` | Runs selected retrieval strategy over workspace golden questions. |
| Experiment history/detail APIs | Done | `app/services/experiment_service.py` | List/detail run JSON from workspace storage. |
| Workspace markdown reports | Done | `app/services/experiment_service.py` | Saves and returns Markdown report per run. |
| Strategy comparison API | Done | `app/services/experiment_service.py`, `app/schemas/experiment.py` | Compares keyword/vector/hybrid on same golden set. |
| RAG phase leaderboard | Done | `app/services/experiment_service.py`, `app/schemas/experiment.py` | Returns rank, score, verdict, and candidate-pool status. |
| Candidate pool concept | Done | `app/schemas/experiment.py`, `app/schemas/phase_artifact.py`, `app/services/phase_artifact_service.py` | Compare output includes candidate-pool status and saves a phase artifact JSON. |
| Phase artifact APIs | Done | `app/api/routes/workspaces.py`, `app/services/phase_artifact_service.py` | List, latest, and detail APIs for persisted candidate pools. |
| Per-question side-by-side analysis | Done | `app/services/experiment_service.py`, `app/schemas/experiment.py` | Compare output groups keyword/vector/hybrid by stable question id. |
| First-class `rag_config` presets | Done | `app/schemas/rag_config.py`, `app/services/rag_config_service.py` | In-memory baseline presets for keyword/vector/hybrid. |
| RAG phase registry | Done | `app/schemas/rag_phase.py`, `app/services/rag_phase_service.py` | Lists all phases; chunking and retriever evaluation are enabled. |
| Chunking evaluation phase | Done | `app/services/chunking_service.py`, `app/services/experiment_service.py`, `app/services/evaluation_service.py` | Runs fixed, paragraph, and recursive chunking candidates with runtime chunks and content-overlap eval. |
| Retriever evaluation from chunking artifacts | Done | `app/services/experiment_service.py`, `app/services/phase_artifact_service.py` | Uses latest kept `chunking_evaluation` candidates as input, combines them with keyword/vector/hybrid retrievers, and saves a parent-linked retriever artifact. |
| Chunk statistics metrics | Done | `app/services/evaluation_service.py`, `app/schemas/experiment.py` | Adds chunk count, avg/min/max size, and coverage ratio to chunking runs. |
| Query transform evaluation phase | Planned | none | Future multi-phase pipeline stage. |
| Reranking | Planned | none | After retriever baseline and side-by-side failure analysis. |
| Context builder evaluation phase | Planned | none | Future multi-phase pipeline stage. |
| Real LLM answer mode | Planned | `app/core/config.py` has `OPENAI_API_KEY`; `openai` dep exists | Do not add before retrieval/evaluation comparisons are useful. |
| End-to-end answer evaluation | Planned | none | Final eval phase after retrieval loop is stable. |
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
| Folder upload UI | Done | `frontend/src/App.tsx`, `frontend/src/api/client.ts` | Lets users select a folder and preserves browser relative paths. |
| Golden Questions tab | Done | `frontend/src/App.tsx` | Upload/list/delete JSONL questions. |
| Experiments tab | Done | `frontend/src/App.tsx` | Run selected strategy, list runs, view metrics. |
| Strategy selector | Done | `frontend/src/App.tsx` | Supports keyword/vector/hybrid. |
| Compare strategies UI | Done | `frontend/src/App.tsx` | Runs keyword/vector/hybrid comparison. |
| RAG config preset selector | Done | `frontend/src/App.tsx`, `frontend/src/api/client.ts` | Fetches workspace presets and runs experiments by config id. |
| RAG phase leaderboard UI | Done | `frontend/src/App.tsx`, `frontend/src/index.css` | Shows rank/config/metrics/score/status table. |
| Candidate pool summary UI | Done | `frontend/src/App.tsx` | Shows tested count, pool size, kept count, best/fastest/highest recall. |
| Latest phase artifact UI | Done | `frontend/src/App.tsx`, `frontend/src/api/client.ts` | Shows the latest persisted candidate pool after compare or workspace refresh. |
| Reports tab | Done | `frontend/src/App.tsx` | Shows selected Markdown report as preformatted text. |
| Playground tab | Done | `frontend/src/App.tsx` | Calls workspace RAG mock query and shows sources. |
| Per-question compare UI | Done | `frontend/src/App.tsx`, `frontend/src/index.css` | Shows question-level hit/miss, metrics, winner, and status filters. |
| RAG phase selector UI | Done | `frontend/src/App.tsx`, `frontend/src/api/client.ts` | Shows active chunking/retriever phases and planned disabled future phases. |
| Chunking evaluation UI | Done | `frontend/src/App.tsx` | Phase selector can run chunking candidates and leaderboard shows chunking params. |
| Report rendering polish | Partial | `frontend/src/App.tsx` | Currently raw Markdown in `<pre>`, not rich rendered. |

## Data Storage Status

Current MVP storage is local file storage.

Workspace data:

```text
data/workspaces/metadata.json
data/workspaces/{workspace_id}/metadata.json
data/workspaces/{workspace_id}/documents/
data/workspaces/{workspace_id}/eval_sets/golden_questions.jsonl
data/workspaces/{workspace_id}/experiments/run_*.json
data/workspaces/{workspace_id}/phase_artifacts/artifact_*.json
data/workspaces/{workspace_id}/reports/run_*.md
```

Important:

- Runtime data should generally not be committed.
- The current MVP intentionally avoids PostgreSQL/SQLite.
- Local JSON storage is acceptable until the evaluation loop is stable.
- Candidate pools are persisted as local phase artifact JSON files after compare.

## API Status

Primary workspace API:

```text
POST   /workspaces
GET    /workspaces
GET    /workspaces/{workspace_id}
PATCH  /workspaces/{workspace_id}
DELETE /workspaces/{workspace_id}

POST   /workspaces/{workspace_id}/documents/upload
POST   /workspaces/{workspace_id}/documents/upload-folder
GET    /workspaces/{workspace_id}/documents
GET    /workspaces/{workspace_id}/documents/{document_id}
DELETE /workspaces/{workspace_id}/documents/{document_id}

POST   /workspaces/{workspace_id}/research/retrieve
POST   /workspaces/{workspace_id}/research/query

GET    /workspaces/{workspace_id}/rag-configs
GET    /workspaces/{workspace_id}/rag-phases
GET    /workspaces/{workspace_id}/phase-artifacts
GET    /workspaces/{workspace_id}/phase-artifacts/latest
GET    /workspaces/{workspace_id}/phase-artifacts/{artifact_id}

POST   /workspaces/{workspace_id}/eval/questions/upload
GET    /workspaces/{workspace_id}/eval/questions
DELETE /workspaces/{workspace_id}/eval/questions/{question_id}

POST   /workspaces/{workspace_id}/experiments/run
POST   /workspaces/{workspace_id}/experiments/compare
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

- Chunking and baseline retriever phases are implemented.
- Future query transform, reranker, context builder, and answer phases are visible but disabled until their experiment logic exists.
- Retriever evaluation can consume the latest chunking phase artifact, but later phases do not consume retriever artifacts yet.
- `rag_config` presets are in-memory only; full config storage is not implemented yet.
- RAG answer generation is mock mode only.
- Reports are displayed as raw Markdown.
- There are no automated tests for the new experiment APIs yet.
- Some older project scaffold folders exist but are not active in the current MVP flow.
