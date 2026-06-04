# Architecture Snapshot

Last updated: 2026-06-03

## System Shape

The current app is a monorepo-style local MVP:

```text
FastAPI backend + local JSON/file storage + React/Vite frontend
```

The main product loop is:

```text
Create workspace
-> Upload documents or corpus folder
-> Auto chunk documents
-> Upload golden questions
-> Run retrieval experiments
-> Compare candidates in a leaderboard
-> Keep candidate pool
-> Persist phase artifact
-> Inspect reports and failure cases
```

The long-term product loop is multi-phase:

```text
Baseline sanity
-> Chunking evaluation
-> Retriever evaluation
-> Query transform evaluation
-> Reranker evaluation
-> Context builder evaluation
-> End-to-end answer evaluation
-> Final top 5 RAG configs
```

Top 5 is final output only. During the intermediate phases, the system should keep a wider candidate pool and prune gradually.

## Backend Layers

### App entrypoint

File: `app/main.py`

Responsibilities:

- Create FastAPI app.
- Configure CORS for frontend dev server.
- Include routers:
  - health
  - chat
  - documents
  - research
  - workspaces

### Routes

Routes live in:

```text
app/api/routes/
```

Current route organization:

- `health.py`: backend health.
- `chat.py`: mock chat.
- `documents.py`: legacy/global document APIs.
- `research.py`: legacy/global retrieve/query APIs.
- `workspaces.py`: primary product APIs, including workspace documents, eval questions, experiments, compare, reports.

Important note:

`workspaces.py` is currently large because it contains several workspace-scoped
domains. A future cleanup can split it into:

```text
workspaces.py
workspace_documents.py
workspace_eval_questions.py
workspace_experiments.py
workspace_reports.py
```

Do this only after behavior is stable.

### Schemas

Schemas live in:

```text
app/schemas/
```

Important schemas:

- `workspace.py`: workspace create/update/detail/summary.
- `document.py`: document summary/detail/chunk.
- `research.py`: retrieve/query response and sources.
- `eval.py`: golden question upload/list/delete responses.
- `experiment.py`: experiment request, metrics, results, reports, comparison summary, leaderboard rows.
- `phase_artifact.py`: persisted candidate-pool artifact for a RAG phase.
- `chat.py`: basic chat request/response.

### Services

Services live in:

```text
app/services/
```

Main service responsibilities:

- `workspace_service.py`: workspace index, create/list/get/rename/delete.
- `document_service.py`: upload files/folders, validate, infer corpus metadata, persist document metadata/content.
- `chunking_service.py`: fixed, paragraph, and recursive character chunking.
- `retrieval_service.py`: keyword, vector, and hybrid retrieval.
- `rag_service.py`: retrieve context + build mock RAG response with sources.
- `ai_service.py`: mock answer text generation.
- `eval_question_service.py`: upload/list/delete JSONL golden questions and repair missing ids when possible.
- `evaluation_service.py`: compute retrieval metrics.
- `experiment_service.py`: run experiments, save JSON/Markdown reports, build comparison leaderboard.
- `phase_artifact_service.py`: save/list/load candidate pools as phase artifacts.
- `chunking_service.py`: default upload chunking plus runtime chunking candidates for chunking evaluation.

## Frontend Architecture

Frontend stack:

```text
React + TypeScript + Vite + lucide-react
```

Main files:

- `frontend/src/App.tsx`: current single-file app shell and tab views.
- `frontend/src/api/client.ts`: typed API calls.
- `frontend/src/types/api.ts`: TypeScript response/request types.
- `frontend/src/index.css`: dashboard styling.

Current tabs:

- Documents
- Golden Questions
- Experiments
- Reports
- Playground

The Experiments tab now supports:

- single strategy run
- keyword/vector/hybrid comparison
- fixed/paragraph/recursive chunking comparison
- RAG phase leaderboard table
- candidate pool summary
- latest persisted phase artifact

The Documents tab now supports:

- single file upload
- nested folder/corpus upload
- source path, folder path, and doc type metadata display

Frontend API base:

```text
import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"
```

## Data Model

Conceptual model:

```text
Workspace
- id
- name
- created_at

Document
- id
- workspace_id
- title
- file_name
- file_type
- source_path
- relative_path
- folder_path
- doc_type
- content_length
- chunk_count
- chunks
- created_at
- stored_file_name

Chunk
- chunk_id
- document_id
- chunk_index
- content
- original_text
- headline
- summary
- source_path
- doc_type
- chunking_strategy
- start_index
- end_index
- content_length

EvalQuestion
- id
- workspace_id
- question
- expected_chunk_ids
- top_k
- notes

ExperimentRun
- run_id
- workspace_id
- strategy
- top_k
- created_at
- metrics
- results
- report_markdown_path

ExperimentComparison
- workspace_id
- stage
- top_k
- best_strategy
- summary
- phase_artifact
- leaderboard
- runs

LeaderboardRow
- rank
- config_id
- config_name
- rag_stage
- strategy
- metrics
- score
- status
- verdict

PhaseArtifact
- artifact_id
- workspace_id
- phase_id
- candidate_pool_size
- kept_config_ids
- pruned_config_ids
- candidates
```

## Retrieval and Evaluation Details

Current retrieval strategies:

```text
keyword
vector
hybrid
```

Current comparison stages:

```text
chunking_evaluation
retriever_evaluation
```

Current metrics:

- `hit_at_k`
- `recall_at_k`
- `precision_at_k`
- `mrr`
- `avg_latency_ms`

Current leaderboard score is a simple weighted retrieval score:

```text
0.40 * hit_at_k
+ 0.30 * mrr
+ 0.20 * recall_at_k
+ 0.10 * precision_at_k
- 0.10 * normalized_latency
```

This score is for MVP ranking only. It can be revised when more RAG phases exist.

## Recommended Next Refactors

Keep these small and separate:

1. Add chunking evaluation phase candidates.
2. Add cross-phase candidate selection from phase artifacts.
3. Split `workspaces.py` route file after behavior is stable.
4. Move retrieval strategies into a package after the interfaces settle.

## Things To Avoid Next

- Do not jump to auth.
- Do not add production database yet.
- Do not remove keyword baseline.
- Do not cut directly to top 5 in intermediate phases.
- Do not wire real LLM calls before retrieval/evaluation comparisons are useful.
- Do not start GraphRAG or Agentic RAG before the multi-phase eval pipeline is stable.
