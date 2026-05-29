# Architecture Snapshot

Last updated: 2026-05-29

## System Shape

The current app is a monorepo-style local MVP:

```text
FastAPI backend + local JSON/file storage + React/Vite frontend
```

The main product loop is:

```text
Create workspace
-> Upload documents
-> Auto chunk documents
-> Upload golden questions
-> Run keyword experiment
-> Store JSON run result
-> Store Markdown report
-> View results in frontend
```

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
- `workspaces.py`: primary product APIs, including workspace documents, eval questions, experiments, reports.

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
- `experiment.py`: experiment request, metrics, results, reports.
- `chat.py`: basic chat request/response.

### Services

Services live in:

```text
app/services/
```

Main service responsibilities:

- `workspace_service.py`: workspace index, create/list/get/rename/delete.
- `document_service.py`: upload, validate, persist document metadata/content.
- `chunking_service.py`: character chunking with overlap.
- `retrieval_service.py`: keyword retrieval.
- `rag_service.py`: retrieve context + build mock RAG response with sources.
- `ai_service.py`: mock answer text generation.
- `eval_question_service.py`: upload/list/delete JSONL golden questions.
- `evaluation_service.py`: compute retrieval metrics.
- `experiment_service.py`: run keyword baseline, save JSON and Markdown reports.

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
```

## Retrieval and Evaluation Details

Current retrieval:

```text
question -> lowercase alphanumeric keywords -> count keyword occurrences per chunk -> sort by score -> top_k
```

Current metrics:

- `hit_at_k`
- `recall_at_k`
- `precision_at_k`
- `mrr`
- `avg_latency_ms`

Current experiment strategy:

```text
keyword
```

Unsupported strategies currently return HTTP 400.

## Recommended Next Refactors

Keep these small and separate:

1. Split `workspaces.py` route file after vector strategy works.
2. Add retrieval strategy interface:

```text
retrieve(strategy, question, workspace_id, top_k)
```

3. Move keyword retriever into:

```text
app/services/retrieval/keyword_retriever.py
```

4. Add vector retriever without deleting keyword baseline.
5. Add compare UI after at least two strategies exist.

## Things To Avoid Next

- Do not jump to auth.
- Do not add production database yet.
- Do not remove keyword baseline.
- Do not make frontend the main complexity center before vector eval exists.
- Do not wire real LLM calls before retrieval/evaluation comparisons are useful.
