# Codebase Status

Last updated: 2026-05-29

## Product Identity

Project name: RAG Experiment Platform for Developers

Current positioning:

```text
Developer-focused RAG experiment platform.

User uploads:
1. Workspace documents / corpus
2. Golden questions / evaluation set

System runs:
documents -> chunks -> retrieval strategy -> evaluation metrics -> report
```

This is no longer mainly a NotebookLM clone. The Notebook-style chat is now the
Playground tab, used for manual debugging.

## Current Phase

Current phase: Phase Eval 4 - Workspace Experiments and Reports

Completed in this phase:

- Workspace-level golden question upload/list/delete APIs.
- Keyword baseline evaluation metrics.
- Workspace experiment run/list/detail APIs.
- Markdown report retrieval API.
- Frontend tabs for Documents, Golden Questions, Experiments, Reports, Playground.

Next recommended phase:

```text
Phase Vector 1 - Add vector retrieval strategy
```

Goal of next phase:

- Add vector retrieval as a selectable strategy.
- Keep keyword as baseline.
- Run comparison reports: keyword vs vector.

## Current Git Milestone

Recent important commits:

```text
79a7bb7 feat(eval): add workspace experiment run history and report viewer
23edadd chore(project): rename local metadata and app titles to RAG Experiment Platform for Developers
aeebf79 feat(ui): rebuild frontend into workspace-first rag experiment flow
f58e0bd feat(eval): add workspace golden questions upload list and delete APIs
d5a24e6 feat(eval): export retrieval evaluation reports to json and markdown
99155d8 docs(plan): align architecture and frontend rebuild for RAG experiment platform
c0c44d9 feat(eval): add golden dataset and keyword baseline metrics
```

## Important Dirty/Untracked State

At the time of this snapshot, the worktree had unrelated dirty/untracked files:

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

Do not revert these automatically. Treat them as user/runtime/previous-session
changes unless the user explicitly asks to clean them.

## Runtime Commands

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

URLs:

```text
Backend API docs: http://127.0.0.1:8000/docs
Frontend app:     http://127.0.0.1:5173
```

## Verification Commands

Backend compile check:

```powershell
uv run python -m compileall app
```

Frontend build check:

```powershell
cd frontend
npm run build
```

Route smoke test:

```powershell
uv run python -c "from app.main import app; print(any(getattr(r,'path','') == '/workspaces/{workspace_id}/experiments/run' for r in app.routes))"
```

Expected route smoke output:

```text
True
```
