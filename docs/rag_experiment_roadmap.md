# RAG Experiment Roadmap

## Goal

Turn the project into a RAG experimentation platform that can evaluate each stage of a RAG system with measurable results, keep candidate pools across phases, and only export final top 5 configurations at the end.

## Core Product Rule

Do not run one benchmark and immediately cut everything down to top 5.

Correct approach:

```text
evaluate a RAG stage
-> keep candidate pool
-> combine or mutate strong candidates
-> run the next stage
-> prune gradually
-> export final top 5 at the end
```

## Current Implemented Baseline

The current MVP implements baseline `retriever_evaluation` with:

- keyword retrieval
- vector retrieval
- hybrid retrieval

Current output:

- leaderboard
- score
- rank
- candidate-pool status
- best/fastest/highest-recall summary

## Phase Order

### Phase 0 - Baseline Sanity

Purpose:

- Prove that upload -> golden questions -> experiment -> leaderboard works.

Candidates:

- keyword
- vector
- hybrid

Status:

```text
Partial / implemented as current MVP.
```

### Phase 1 - Chunking Evaluation

Purpose:

- Find chunking strategies that preserve evidence well.

Candidate examples:

- fixed chunk
- recursive chunk
- semantic chunk
- parent-child chunk

Output:

- top chunking candidates
- chunk-boundary failure cases

### Phase 2 - Retriever Evaluation

Purpose:

- Compare retrievers using the strongest chunking candidates.

Candidate examples:

- BM25 / keyword
- vector
- hybrid

Output:

- top retriever candidates
- lexical-vs-semantic failure analysis

### Phase 3 - Query Transform Evaluation

Purpose:

- Test whether query rewriting improves retrieval.

Candidate examples:

- no transform
- query rewrite
- query expansion
- multi-query
- HyDE

Output:

- top query transform candidates
- cases where transform improves recall
- cases where transform adds noise

### Phase 4 - Reranker Evaluation

Purpose:

- Test whether reranking improves final top-k quality.

Candidate examples:

- no rerank
- rerank top 20 to 5
- rerank top 50 to 5

Output:

- top reranker candidates
- latency impact
- MRR improvement

### Phase 5 - Context Builder Evaluation

Purpose:

- Test how retrieved chunks are assembled into final context.

Candidate examples:

- plain top-k context
- parent context
- window-expanded context
- section-title boosted context

Output:

- top context builder candidates
- context token usage
- answer-readiness of context

### Phase 6 - End-To-End Answer Evaluation

Purpose:

- Evaluate whether final RAG configs answer well, not just retrieve well.

Metrics:

- retrieval metrics
- answer correctness
- faithfulness
- latency
- cost

Output:

- final top 5 RAG configs
- recommendation report

## Core Retrieval Metrics

- Hit@k
- Recall@k
- Precision@k
- MRR
- Average latency
- P95 latency later

## Leaderboard Target

The project should produce phase-specific leaderboards like:

```text
Rank | Config | Stage | Hit@k | Recall@k | MRR | Latency | Score | Status
```

Candidate status:

```text
kept
pruned
```

## Near-Term Roadmap

1. Add stable `question_id` to experiment results.
2. Add side-by-side per-question comparison.
3. Add `rag_config` presets.
4. Persist candidate pools per phase.
5. Add chunking evaluation phase.
6. Add query transform and reranker phases after retriever failure analysis is useful.
