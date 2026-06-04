# Codebase Status

Last updated: 2026-06-04

## Product Identity

Project name: RAG Experiment Platform for Developers

Current positioning:

```text
Developer-focused RAG experiment platform.

User uploads:
1. Workspace documents / corpus
2. Golden questions / evaluation set

System runs:
documents -> chunks -> RAG candidate/config -> retrieval metrics -> leaderboard -> report
```

This is no longer mainly a NotebookLM clone. The Notebook-style chat is now the
Playground tab, used for manual debugging.

## Product Direction

The product direction is now multi-phase RAG experimentation:

```text
Phase 0: Baseline sanity
Phase 1: Chunking evaluation
Phase 2: Retriever evaluation
Phase 3: Query transform evaluation
Phase 4: Reranker evaluation
Phase 5: Context builder evaluation
Phase 6: End-to-end answer evaluation
```

Important rule:

```text
Top 5 is final output only.
During each phase, keep a wider candidate pool and prune gradually.
```

The current code implements a small baseline/retriever comparison MVP with:

- `keyword`
- `vector`
- `hybrid`

The comparison output now includes leaderboard rank, score, candidate-pool status,
side-by-side question-level failure analysis, baseline `rag_config` metadata, and
a persisted phase artifact for the candidate pool. The frontend also exposes a
phase selector; `chunking_evaluation` and `retriever_evaluation` are runnable,
while future phases are visible as planned.

Product plan file:

```text
docs/rag_experiment_product_plan.md
```

## Current Phase

Current phase: Phase 12 - RAG Evaluation / Multi-Phase Experiment Pipeline Foundation

Completed in this phase:

- Workspace-level golden question upload/list/delete APIs.
- Golden question validation and repair for missing expected chunk ids when possible.
- Retrieval metrics: hit@k, recall@k, precision@k, MRR, average latency.
- Workspace experiment run/list/detail APIs.
- Markdown report retrieval API.
- Keyword baseline retrieval.
- Vector retrieval with Chroma + sentence-transformers.
- Hybrid keyword + vector retrieval.
- Strategy comparison API: `POST /workspaces/{workspace_id}/experiments/compare`.
- Leaderboard output with rank, score, status, verdict, and candidate pool.
- First-class in-memory `rag_config` presets for keyword/vector/hybrid.
- Workspace API: `GET /workspaces/{workspace_id}/rag-configs`.
- Workspace API: `GET /workspaces/{workspace_id}/rag-phases`.
- Workspace API: `GET /workspaces/{workspace_id}/phase-artifacts`.
- Workspace API: `GET /workspaces/{workspace_id}/phase-artifacts/latest`.
- Workspace API: `GET /workspaces/{workspace_id}/phase-artifacts/{artifact_id}`.
- Phase selector UI with disabled planned phases.
- Chunking evaluation with fixed, paragraph, and recursive runtime chunk candidates.
- Recursive character chunking candidates using `langchain-text-splitters`.
- Folder/corpus upload for nested `.txt` and `.md` files.
- Source path, folder path, and doc type metadata on documents/chunks.
- Chunk statistics metrics: count, average/min/max size, and coverage ratio.
- Content-overlap relevance mode for chunking evaluation so existing golden chunk ids can still be used as evidence anchors.
- Retriever evaluation can read the latest kept chunking candidates and combine them with keyword/vector/hybrid retrievers.
- Retriever phase artifacts store their parent chunking artifact id.
- Query transform evaluation can read the latest kept retriever candidates and compare `none` vs simple rule-based `rewrite`.
- Query transform phase artifacts store their parent retriever artifact id.
- Reranker evaluation can read the latest kept query transform candidates and compare `none` vs simple lexical-overlap reranking.
- Reranker phase artifacts store their parent query transform artifact id.
- Context builder evaluation can read the latest kept reranker candidates and compare `plain_top_k` vs simple `document_window`.
- Context builder phase artifacts store their parent reranker artifact id.
- Answer evaluation can read the latest kept context builder candidates and compare grounded mock answer modes.
- Answer evaluation runs store generated answer text, `reference_answer`, answer presence rate, and simple lexical overlap scoring.
- Frontend run detail now includes a basic answer review panel for answer-evaluation runs.
- Stable `question_id` in experiment case results.
- Question-level comparison output for keyword/vector/hybrid wins and failures.
- Frontend tabs for Documents, Golden Questions, Experiments, Reports, Playground.
- Frontend config preset selector and compare table for the current `retriever_evaluation` baseline phase.
- Frontend question-level comparison table under the leaderboard.
- Frontend latest phase artifact card for the persisted candidate pool, including parent artifact metadata.

Next recommended phase:

```text
Phase Eval 8B - Answer quality refinement and review tooling
```

Goal of next phase:

- Improve answer metrics beyond simple lexical overlap.
- Add better review UX for generated answers, sources, and references.
- Keep real LLM answer mode and judge mode optional until the retrieval/eval pipeline remains stable.

## Current Git Milestone

Recent important commits:

```text
58dbac0 Add multi-strategy RAG evaluation
```

Current uncommitted milestone:

```text
Add RAG phase leaderboard, question-level comparison, rag_config presets, phase selector UI, persisted phase artifacts, and runnable chunking evaluation.
Update product direction docs.
```

## Runtime Commands

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

Compare endpoint smoke test:

```powershell
uv run python -c "from app.main import app; print(any(getattr(r,'path','') == '/workspaces/{workspace_id}/experiments/compare' for r in app.routes))"
```

Expected route smoke output:

```text
True
```
