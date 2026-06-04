# Next Chat Handoff

Use this file when starting a new chat/session.

## Short Context To Paste

```text
Project: RAG Experiment Platform for Developers

Read first:
- AGENTS.md
- docs/current_phase.md
- docs/next_session_instructions.md
- docs/rag_experiment_product_plan.md
- docs/codebase_status.md
- docs/feature_status.md
- docs/architecture_snapshot.md

Current phase:
Phase 12 / RAG Evaluation. The app can create workspaces, upload .txt/.md docs,
auto chunk documents, upload golden_questions.jsonl, run retrieval experiments,
compare keyword/vector/hybrid, save JSON/Markdown reports, and view a leaderboard
table plus question-level comparison in the React frontend. Baseline strategies
are now exposed as first-class `rag_config` presets, and the Experiments tab has
a phase selector with future phases disabled. Compare also persists the candidate
pool as a phase artifact JSON. `chunking_evaluation` is now runnable and compares
fixed/paragraph/recursive runtime chunks against the uploaded golden set. The
Documents tab can upload nested corpus folders and preserve source path/doc type
metadata. `retriever_evaluation` now consumes the latest kept chunking artifact
and generates chunking + retriever candidate combinations.

Current product direction:
Each RAG phase evaluates one stage of the RAG pipeline. Do not cut to top 5 after
each small test. Keep a wider candidate pool, prune gradually, and export final
top 5 only at the end.

Current implemented comparison stages:
- `chunking_evaluation`: fixed, paragraph, and recursive runtime chunks, keyword retriever fixed, content-overlap evidence scoring, chunk statistics metrics.
- `retriever_evaluation`: latest kept chunking candidates combined with keyword, vector, and hybrid retrievers.

The compare response includes leaderboard output, `rag_config` metadata, and
side-by-side per-question analysis. The selected phase is sent as `stage`. Each
compare creates a phase artifact that can be listed or loaded as the latest artifact.

Next recommended step:
Start query transform evaluation foundation from the strongest retriever artifact.

Rules:
- Do not remove keyword retrieval.
- Do not jump to GraphRAG, Agentic RAG, auth, or production DB.
- Keep local file storage for now.
- Keep answer-level evaluation later; retrieval eval must be trustworthy first.
- After code changes, run backend compile check and frontend build.
```

## Current Product Flow

```text
1. Start backend
2. Start frontend
3. Create workspace
4. Upload documents or a nested corpus folder (.txt/.md)
5. Upload golden_questions.jsonl
6. Select the active RAG phase: chunking or retriever
7. Select a `rag_config` preset or compare all presets in that phase
8. Inspect leaderboard, candidate-pool status, and question-level failures
9. Inspect the latest persisted phase artifact
10. Open report from Reports tab
11. Use Playground for manual RAG mock query
```

## Multi-Phase RAG Experiment Direction

```text
Phase 0: Baseline sanity
Phase 1: Chunking evaluation
Phase 2: Retriever evaluation
Phase 3: Query transform evaluation
Phase 4: Reranker evaluation
Phase 5: Context builder evaluation
Phase 6: End-to-end answer evaluation
Final: export top 5 RAG configs
```

Candidate pool rule:

```text
initial configs: 30-60
after quick benchmark: keep top 20
after full retrieval benchmark: keep top 10
after final evaluation: export top 5
```

For the current MVP, chunking keeps top 3, then retriever evaluation combines those chunking candidates with keyword/vector/hybrid and keeps top 5.

## Commands

Backend:

```powershell
cd D:\AI\projects\RAG_Experiment_Platform_for_Developers
uv run uvicorn app.main:app --reload
```

Frontend:

```powershell
cd D:\AI\projects\RAG_Experiment_Platform_for_Developers\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Checks:

```powershell
uv run python -m compileall app
cd frontend
npm run build
```

## Good Next Step

Implement query transform evaluation foundation:

1. Read the latest `retriever_evaluation` artifact.
2. Keep the best retriever candidate pool.
3. Add no-transform vs simple query rewrite candidates.
4. Persist a new query transform artifact.
5. Keep answer evaluation disabled.

Current question-level output:

```text
Question | Expected | Keyword | Vector | Hybrid | Winner | Status
```

## Current Important Files

Backend:

```text
app/main.py
app/api/routes/workspaces.py
app/services/workspace_service.py
app/services/document_service.py
app/services/chunking_service.py
app/services/retrieval_service.py
app/services/evaluation_service.py
app/services/eval_question_service.py
app/services/experiment_service.py
app/services/phase_artifact_service.py
app/services/rag_config_service.py
app/services/rag_phase_service.py
app/services/rag_service.py
app/schemas/experiment.py
app/schemas/phase_artifact.py
app/schemas/rag_config.py
app/schemas/rag_phase.py
app/schemas/eval.py
app/schemas/research.py
```

Frontend:

```text
frontend/src/App.tsx
frontend/src/api/client.ts
frontend/src/types/api.ts
frontend/src/index.css
```

Docs:

```text
docs/current_phase.md
docs/rag_experiment_product_plan.md
docs/codebase_status.md
docs/feature_status.md
docs/architecture_snapshot.md
docs/restructure_plan.md
docs/frontend_rebuild_plan.md
docs/evaluation.md
```

## Known Limitation

The current comparison output has leaderboard, candidate-pool status, `rag_config` metadata, selected phase, side-by-side per-question failures, persisted phase artifacts, runnable chunking evaluation, and `chunking -> retriever` cross-phase candidate selection. Later phases do not yet consume retriever artifacts.
