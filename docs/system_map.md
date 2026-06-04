# System Map

Muc tieu cua file nay: cho phep nhin du an bang so do thay vi doc tung file.
No tap trung vao flow dang chay: workspace-first + retrieval comparison + leaderboard + candidate pool.

## 1) Product Loop Hien Tai

```mermaid
flowchart TD
  A[Create workspace] --> B[Upload documents or corpus folder .txt/.md]
  B --> C[Auto chunking]
  C --> D[Upload golden_questions.jsonl]
  D --> C1[Run chunking evaluation]
  D --> E[Run single strategy experiment]
  D --> F[Compare keyword/vector/hybrid]
  C1 --> I[Build leaderboard]
  C1 --> A1[Save phase artifact JSON]
  E --> G[Save run JSON]
  E --> H[Save report Markdown]
  F --> I[Build leaderboard]
  F --> J[Return candidate pool status]
  F --> A1[Save phase artifact JSON]
  G --> K[View in frontend]
  H --> K
  I --> K
  J --> K
  A1 --> K
  C --> L[Playground: query workspace]
  L --> K
```

## 2) Product Loop Huong Toi

```mermaid
flowchart TD
  A[Baseline sanity] --> B[Chunking evaluation]
  B --> C[Keep chunking candidate pool]
  C --> D[Retriever evaluation]
  D --> E[Keep retriever candidate pool]
  E --> F[Query transform evaluation]
  F --> G[Reranker evaluation]
  G --> H[Context builder evaluation]
  H --> I[End-to-end answer evaluation]
  I --> J[Export final top 5 RAG configs]
```

Nguyen tac:

```text
Top 5 chi la output cuoi.
Moi phase giu candidate pool rong roi prune dan co kiem soat.
```

## 3) Backend Request Flow

Quy uoc:

- Route: nhan HTTP request, validate schema
- Service: xu ly logic, doc/ghi file local
- Storage: hien tai nam trong `data/` (khong co DB)

```mermaid
flowchart LR
  FE[Frontend React] -->|HTTP JSON| API[FastAPI routes]
  API --> SCH[Schemas Pydantic]
  API --> SVC[Services]
  SVC --> FS[Local file storage data/workspaces/*]
```

## 4) Workspace API Map

File route chinh: `app/api/routes/workspaces.py`

```mermaid
flowchart TD
  subgraph WS[Workspaces Domain]
    W1[POST /workspaces] --> WSVC[workspace_service.create_workspace]
    W2[GET /workspaces] --> WSVC2[workspace_service.list_workspaces]
    W3[GET /workspaces/{id}] --> WSVC3[workspace_service.get_workspace]
    W4[PATCH /workspaces/{id}] --> WSVC4[workspace_service.rename_workspace]
    W5[DELETE /workspaces/{id}] --> WSVC5[workspace_service.delete_workspace]
  end

  subgraph DOCS[Workspace Documents]
    D1[POST /workspaces/{id}/documents/upload] --> DSVC[document_service.save_uploaded_document]
    D2[GET /workspaces/{id}/documents] --> DSVC2[document_service.list_documents]
    D3[GET /workspaces/{id}/documents/{doc_id}] --> DSVC3[document_service.get_document]
    D4[DELETE /workspaces/{id}/documents/{doc_id}] --> DSVC4[document_service.delete_document]
  end

  subgraph R[Workspace Research]
    R1[POST /workspaces/{id}/research/retrieve] --> RSVC[retrieval_service.retrieve_relevant_chunks]
    R2[POST /workspaces/{id}/research/query] --> RAGSVC[rag_service.answer_research_query]
  end

  subgraph EVAL[Golden Questions]
    Q1[POST /workspaces/{id}/eval/questions/upload] --> QSVC[eval_question_service.upload_eval_questions_file]
    Q2[GET /workspaces/{id}/eval/questions] --> QSVC2[eval_question_service.list_eval_questions]
    Q3[DELETE /workspaces/{id}/eval/questions/{q_id}] --> QSVC3[eval_question_service.delete_eval_question]
  end

  subgraph EXP[Experiments + Compare + Reports]
    X1[POST /workspaces/{id}/experiments/run] --> XSVC[experiment_service.run_workspace_experiment]
    X2[POST /workspaces/{id}/experiments/compare] --> XCOMP[experiment_service.run_workspace_experiment_comparison]
    X3[GET /workspaces/{id}/experiments] --> XSVC2[experiment_service.list_workspace_experiments]
    X4[GET /workspaces/{id}/experiments/{run_id}] --> XSVC3[experiment_service.get_workspace_experiment]
    X5[GET /workspaces/{id}/reports/{run_id}] --> XSVC4[experiment_service.get_workspace_report_markdown]
  end
```

## 5) Retrieval + Comparison

Current retrieval candidates:

```text
chunking_evaluation: fixed 500, fixed 800, fixed 1200, paragraph 1000, recursive 500/800/1000
retriever_evaluation:
keyword
vector
hybrid
```

```mermaid
flowchart TD
  U[Golden question] --> S{Strategy}
  S --> K[Keyword retrieval]
  S --> V[Vector retrieval]
  S --> H[Hybrid retrieval]
  K --> M[Compute metrics]
  V --> M
  H --> M
  M --> L[Leaderboard score]
  L --> C[Candidate pool status]
```

## 6) Local Data Layout

Workspace data:

```text
data/workspaces/metadata.json
data/workspaces/{workspace_id}/metadata.json
data/workspaces/{workspace_id}/documents/{doc_id}_{file_name}
data/workspaces/{workspace_id}/eval_sets/golden_questions.jsonl
data/workspaces/{workspace_id}/experiments/run_*.json
data/workspaces/{workspace_id}/phase_artifacts/artifact_*.json
data/workspaces/{workspace_id}/reports/run_*.md
```

Global legacy data:

```text
data/metadata.json
data/documents/*
```

## 7) Folders Co Nhung Chua Active Day Du

Nhung folder nay co the la scaffold/y tuong, chua duoc wired vao full multi-phase pipeline:

```text
app/ingestion/
app/embeddings/
app/retrieval/
app/generation/
app/evaluation/
app/database/
```

`app/vectorstore/` is now used by vector retrieval, but the future architecture should still move strategies into clearer modules once behavior is stable.
