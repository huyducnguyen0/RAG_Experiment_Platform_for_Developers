# RAG Experiment Product Plan

## Product Direction

The platform should not pick top 5 after every small test round. Top 5 is the final output only. During evaluation, the system must keep a wider candidate pool so potentially strong configurations are not removed too early.

Correct flow:

```text
evaluate one RAG phase
-> keep a controlled candidate pool
-> combine or mutate the strongest candidates
-> rerun the next phase
-> export final top 5 only at the end
```

## RAG Evaluation Phases

### Phase 0 - Baseline Sanity

Goal: confirm the eval loop works.

Candidates:

- keyword baseline
- vector retrieval
- hybrid retrieval

Output:

- leaderboard
- best current candidate
- candidate pool kept for the next phase

### Phase 1 - Chunking Evaluation

Goal: find strong chunking strategies before testing more advanced modules.

Candidate examples:

- fixed chunk
- recursive chunk
- semantic chunk
- parent-child chunk

Output:

- top chunking candidates
- failure cases caused by bad chunk boundaries

### Phase 2 - Retriever Evaluation

Goal: compare retrieval methods using the best chunking candidates.

Candidate examples:

- BM25 or keyword
- vector
- hybrid

Output:

- top retriever candidates
- cases where lexical search beats semantic search
- cases where semantic search beats lexical search

### Phase 3 - Query Transform Evaluation

Goal: test whether query rewriting helps retrieval.

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

Goal: test whether reranking improves final top-k quality.

Candidate examples:

- no rerank
- rerank top 20 to top 5
- rerank top 50 to top 5

Output:

- top reranker candidates
- latency impact
- MRR improvement

### Phase 5 - Context Builder Evaluation

Goal: test how retrieved chunks are assembled into final context.

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

Goal: evaluate final answer quality only after retrieval is stable.

Metrics:

- retrieval metrics
- answer correctness
- faithfulness
- latency
- cost

Output:

- final top 5 RAG configurations
- recommendation report

## Candidate Pool Rules

Recommended default:

```text
initial configs: 30-60
after quick benchmark: keep top 20
after full retrieval benchmark: keep top 10
after final evaluation: export top 5
```

For the current MVP, the system starts smaller:

```text
baseline sanity: keyword, vector, hybrid
candidate_pool_size: 20
final kept candidates: all candidates if fewer than the pool size
```

## Leaderboard Output

After pressing Compare/Test, the UI should show:

```text
Rank | Config | Hit@k | Recall | Precision | MRR | Latency | Score | Status
```

The summary should show:

- total configs tested
- candidate pool size
- kept count
- best config
- fastest config
- highest recall config
- recommendation for the next phase

## Current Implementation Status

Implemented:

- baseline strategy comparison for keyword, vector, and hybrid
- backend comparison API
- leaderboard score
- candidate pool status
- first-class baseline rag_config presets
- phase selector UI with planned phases disabled
- stable question ids in experiment results
- side-by-side per-question comparison
- frontend leaderboard table
- frontend question-level comparison table
- persisted phase artifact JSON after compare
- frontend latest phase artifact card
- runnable chunking evaluation with fixed and paragraph candidates
- recursive character chunking candidates
- folder/corpus upload with source path and doc type metadata
- chunk count, chunk size, and coverage metrics
- content-overlap scoring for chunking candidates
- retriever candidates generated from kept chunking artifacts
- parent-linked retriever phase artifacts
- summary output

Not implemented yet:

- real rag_config storage
- query transform evaluation phase
- reranker evaluation phase
- context builder evaluation phase
- end-to-end answer evaluation
- cross-phase candidate mutation or combination after retriever evaluation

## Next Implementation Steps

1. Add query transform candidates that reuse the strongest retriever artifacts.
2. Add reranker candidates after retriever/query transform configs are stable.
3. Add context builder evaluation candidates.
4. Extend cross-phase candidate selection beyond `chunking -> retriever`.
5. Add end-to-end answer evaluation after retrieval evaluation is trustworthy.
