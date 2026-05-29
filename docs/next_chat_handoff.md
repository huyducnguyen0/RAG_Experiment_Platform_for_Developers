# Next Chat Handoff

Use this file when starting a new chat/session.

## Short Context To Paste

```text
Project: RAG Experiment Platform for Developers

Read first:
- AGENTS.md
- docs/current_phase.md
- docs/codebase_status.md
- docs/feature_status.md
- docs/architecture_snapshot.md
- docs/restructure_plan.md
- docs/frontend_rebuild_plan.md

Current phase:
Phase Eval 4 is complete. The app can create workspaces, upload .txt/.md docs,
auto chunk documents, upload golden_questions.jsonl, run keyword baseline
experiments, save JSON/Markdown reports, and view them in the React frontend.

Next recommended phase:
Phase Vector 1 - Add vector retrieval strategy.

Rules:
- Do not remove keyword retrieval.
- Do not add auth/database/frontend rewrite.
- Keep local file storage.
- Implement vector retrieval as an additional strategy and compare against keyword.
- After code changes, run backend compile check and frontend build.
```

## Current Product Flow

```text
1. Start backend
2. Start frontend
3. Create workspace
4. Upload documents (.txt/.md)
5. Upload golden_questions.jsonl
6. Run keyword baseline from Experiments tab
7. Open report from Reports tab
8. Use Playground for manual RAG mock query
```

## Commands

Backend:

```powershell
cd D:\AI\projects\RAG_Experiment_Platform_for_Developers
.\.venv\Scripts\Activate.ps1
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

Implement Phase Vector 1 in the smallest usable way:

1. Add vector retrieval service.
2. Prefer existing dependencies already in `pyproject.toml`:
   - `sentence-transformers`
   - `chromadb`
   - `torch`
3. Keep fallback behavior if model/vector setup fails.
4. Extend experiment strategy validation from only `keyword` to:
   - `keyword`
   - `vector`
5. Update frontend Experiments tab to select strategy.
6. Run both strategies and compare metrics.

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
app/services/rag_service.py
app/schemas/experiment.py
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
docs/codebase_status.md
docs/feature_status.md
docs/architecture_snapshot.md
docs/restructure_plan.md
docs/frontend_rebuild_plan.md
docs/evaluation.md
```

## Known Worktree Warning

The worktree had unrelated dirty/untracked files when this handoff was written.
Do not revert them unless the user explicitly asks.

```text
M app/core/config.py
M data/metadata.json
D tests/test.py
M uv.lock
?? app/vectorstore/chroma_client.py
?? docs/checklist_agentic_research_os.docx
?? docs/fastapi.md
?? docs/prompt_for_learner
?? scripts/test.py
?? scripts/test_config.py
```
