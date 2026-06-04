# RAG Experiment Platform - Implementation Plan

## Goal

Build a portfolio-ready RAG Experiment Platform for Developers.

The product should let users:

```text
upload corpus
-> upload golden questions
-> evaluate RAG candidates
-> compare metrics in a leaderboard
-> keep candidate pools across phases
-> inspect failures
-> export final top 5 RAG configurations
```

## Current Product Direction

The evaluation flow is multi-phase. Each phase evaluates one stage of the RAG pipeline.

```text
Phase 0: Baseline sanity
Phase 1: Chunking evaluation
Phase 2: Retriever evaluation
Phase 3: Query transform evaluation
Phase 4: Reranker evaluation
Phase 5: Context builder evaluation
Phase 6: End-to-end answer evaluation
```

Rule:

```text
Do not cut to top 5 after every test.
Keep a wider candidate pool and prune gradually.
Top 5 is final output only.
```

## Current Priority

Stabilize the retrieval evaluation loop before adding answer-level evaluation.

Current implemented baseline:

```text
retriever_evaluation:
- keyword
- vector
- hybrid
```

Current output:

- leaderboard
- score
- candidate-pool status
- summary
- saved run JSON
- saved Markdown report

## Strict Rules

- Do not over-engineer.
- Do not jump phases.
- Do not add auth.
- Do not add production database yet.
- Do not start GraphRAG or Agentic RAG before the eval pipeline is stable.
- Do not call real LLM evaluator until retrieval evaluation is trustworthy.
- Do not remove keyword baseline.
- Keep mock mode working without external API keys.
- After each implementation phase, explain what changed and how to test it.

## Current MVP Features

- Workspace CRUD
- Document upload/list/detail/delete
- Automatic chunking
- Golden question upload/list/delete
- Keyword retrieval
- Vector retrieval
- Hybrid retrieval
- Retrieval metrics
- Single strategy experiment runs
- Strategy comparison
- Leaderboard output
- Candidate pool status
- JSON run storage
- Markdown report storage
- React dashboard frontend
- Playground mock RAG query

## Immediate Implementation Order

### Step 1 - Stable Question IDs

Goal:

- Every experiment result must know which golden question it came from.

Tasks:

- Add `question_id` to `RetrievalEvalCase`.
- Add `question_id` to `RetrievalEvalCaseResult`.
- Save `question_id` into run JSON.
- Add frontend type support.

Done when:

- Experiment detail contains stable question IDs.

### Step 2 - Side-By-Side Failure Analysis

Goal:

- Show which candidate wins/fails per question.

Tasks:

- Group comparison results by `question_id`.
- Return per-question comparison rows.
- Show table in frontend.

Target output:

```text
Question | Expected | Keyword | Vector | Hybrid | Winner
```

Done when:

- User can inspect why one strategy beats another.

### Step 3 - First-Class RAG Config Presets

Goal:

- Move from simple strategy strings to configurable RAG candidates.

Tasks:

- Add `rag_config` schema.
- Add preset configs.
- Add API to list presets.
- Update compare request to accept config ids later.

Initial presets:

```text
keyword_baseline
vector_baseline
hybrid_baseline
```

Done when:

- UI can display candidate config names independent of strategy names.

### Step 4 - Candidate Pool Persistence

Goal:

- Store which candidates survive each phase.

Tasks:

- Add local JSON storage for candidate pools.
- Save stage name, candidate ids, rank, score, status.
- Allow next phase to use kept candidates.

Done when:

- Candidate pool survives page refresh.

### Step 5 - Chunking Evaluation Phase

Goal:

- Evaluate chunking strategies separately.

Candidate examples:

- fixed chunk
- recursive chunk
- semantic chunk
- parent-child chunk

Done when:

- User can compare chunking candidates in a leaderboard.

### Step 6 - Query Transform And Reranker Phases

Goal:

- Add more RAG modules after retrieval failure analysis is useful.

Candidate examples:

- no transform
- query expansion
- multi-query
- no rerank
- rerank top 20 to 5
- rerank top 50 to 5

Done when:

- These modules can be benchmarked without exploding combinations.

### Step 7 - End-To-End Answer Evaluation

Goal:

- Evaluate answer quality after retrieval is stable.

Metrics:

- answer correctness
- faithfulness
- latency
- cost

Done when:

- Final top 5 RAG configs can be exported with retrieval and answer-quality metrics.

## Historical MVP Phases

These older phases are already effectively covered by the current app:

- Backend skeleton
- Chat mock
- Document upload
- Document chunking
- Simple keyword retrieval
- RAG query with sources
- Workspace-first frontend
- Golden questions
- Experiment reports

They are no longer the active roadmap.
