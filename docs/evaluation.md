# Evaluation Guide

## Purpose

This guide explains the current evaluation system and the future multi-phase RAG experiment direction.

The current implemented comparison stages are:

```text
chunking_evaluation
retriever_evaluation
```

Current candidates:

```text
fixed chunking candidates
paragraph chunking candidate
recursive chunking candidates
keyword/vector/hybrid retrievers combined with kept chunking candidates
```

The product direction is not "run once and pick top 5". The direction is:

```text
evaluate one RAG phase
-> keep a candidate pool
-> move strong candidates into the next phase
-> export final top 5 only at the end
```

## Dataset Format

Golden questions are uploaded per workspace as `JSONL` or `CSV`.

The platform accepts flexible input formats and normalizes them into one internal schema.

User-friendly examples:

```json
{"question":"Who won the IIOTY award in 2023?","reference_answer":"Maxine Thompson won the prestigious IIOTY award in 2023.","keywords":["Maxine","Thompson","IIOTY"],"category":"direct_fact"}
{"question":"Who won the IIOTY award in 2023?","gold_evidence_text":"Maxine Thompson won the prestigious IIOTY award in 2023.","reference_answer":"Maxine Thompson won the prestigious IIOTY award in 2023."}
{"q_id":"q_001","question":"What is RAG?","top_k":5,"expected_chunk_ids":["doc_x_chunk_000"],"reference_answer":"RAG stands for Retrieval-Augmented Generation."}
```

CSV example:

```text
question,reference_answer,keywords,category
Who won the IIOTY award in 2023?,Maxine Thompson won the prestigious IIOTY award in 2023.,"Maxine;Thompson;IIOTY",direct_fact
```

Internal normalized fields:

- `id` or `q_id`: stable question id; backend auto-generates one if missing
- `question`: required
- `top_k`: defaults to `5`
- `expected_chunk_ids`: optional strong retrieval labels
- `gold_evidence_text`: optional evidence text for overlap-based retrieval scoring
- `reference_answer`: optional answer-level weak supervision
- `keywords`: optional retrieval hints or weak supervision
- `category`: optional metadata for grouping/debugging
- `notes`: optional free text

At least one supervision signal is required:

- `expected_chunk_ids`
- `gold_evidence_text`
- `reference_answer`
- `keywords`

## Current Compare API

Endpoint:

```text
POST /workspaces/{workspace_id}/experiments/compare
```

Request:

```json
{
  "strategies": ["keyword", "vector", "hybrid"],
  "top_k": 5,
  "stage": "retriever_evaluation",
  "candidate_pool_size": 5
}
```

Response includes:

- `summary`
- `phase_artifact`
- `leaderboard`
- `runs`

Leaderboard columns conceptually map to:

```text
Rank | Config | Hit@k | Recall | Precision | MRR | Latency | Score | Status
```

## Metrics

Current retrieval metrics:

- `Hit@k`: fraction of cases with at least one relevant retrieved chunk
- `Recall@k`: average relevant-retrieved / expected-relevant per case
- `Precision@k`: average relevant-retrieved / k per case
- `MRR`: mean reciprocal rank of first relevant chunk
- `Avg latency (ms)`: average retrieval latency per case

Current MVP leaderboard score:

```text
0.40 * hit_at_k
+ 0.30 * mrr
+ 0.20 * recall_at_k
+ 0.10 * precision_at_k
- 0.10 * normalized_latency
```

This score is intentionally simple. It is useful for ranking retrieval candidates, not final answer quality.

## Label Modes

The evaluator currently supports three supervision levels:

- `strong_chunk_ids`: direct chunk-id matching
- `evidence_text`: overlap-based scoring against `gold_evidence_text` or evidence reconstructed from chunk ids
- `weak_label`: soft scoring from `reference_answer` and/or `keywords`

Weak-label scoring is intentionally softer than chunk-id matching. It is designed to make the platform easier to use before a dataset has fully annotated chunk ids.

## Multi-Phase Evaluation Direction

The future phases are:

```text
Phase 0: Baseline sanity
Phase 1: Chunking evaluation
Phase 2: Retriever evaluation
Phase 3: Query transform evaluation
Phase 4: Reranker evaluation
Phase 5: Context builder evaluation
Phase 6: End-to-end answer evaluation
```

Candidate pool defaults:

```text
after quick benchmark: keep top 20
after full retrieval benchmark: keep top 10
after final evaluation: export top 5
```

## Current UI Output

After pressing compare/test in the Experiments tab, the UI should show:

- phase label
- tested count
- candidate pool size
- kept count
- best config
- fastest config
- highest recall config
- recommendation
- leaderboard table
- latest persisted phase artifact

## Phase Artifact

Each compare run saves the candidate pool as local JSON:

```text
data/workspaces/{workspace_id}/phase_artifacts/artifact_*.json
```

The artifact stores kept/pruned config ids, candidate rank, score, metrics, and the best current config. This is the bridge between one RAG phase and the next phase.

## Chunking Evaluation

`chunking_evaluation` lets the user upload long documents and golden questions once, then the platform tries several chunking strategies.

Current chunking candidates:

```text
cfg_chunk_fixed_500_50
cfg_chunk_fixed_800_100
cfg_chunk_fixed_1200_150
cfg_chunk_paragraph_1000
cfg_chunk_recursive_500_200
cfg_chunk_recursive_800_200
cfg_chunk_recursive_1000_250
```

Important detail:

Golden questions still use `expected_chunk_ids` from the uploaded/default chunks. During chunking evaluation, those expected chunks are treated as evidence text anchors. The runtime chunks are scored by content overlap, because new chunking strategies naturally produce different chunk ids and boundaries.

Chunking metrics include:

- `Hit@k`
- `Recall@k`
- `Precision@k`
- `MRR`
- `Avg latency`
- `Chunk count`
- `Avg/min/max chunk size`
- `Coverage ratio`

Default candidate pool rule:

```text
7 chunking configs -> keep top 3 -> pass to retriever evaluation later
```

## Retriever Evaluation

`retriever_evaluation` now reads the latest `chunking_evaluation` artifact and
uses its kept chunking candidates as input.

Default MVP rule:

```text
top 3 chunking configs x keyword/vector/hybrid -> 9 retriever candidates -> keep top 5
```

If no chunking artifact exists yet, retriever evaluation returns:

```text
Run chunking evaluation before retriever evaluation.
```

Retriever artifacts store:

- `parent_artifact_id`
- `parent_phase_id`

## Next Evaluation Feature

Use the strongest retriever artifact as the input candidate pool for query transform evaluation.

## Notes

- If workspace ids or chunk ids change after re-uploading files, update the dataset.
- Keep retrieval evaluation trustworthy before answer-level evaluation.
- Do not start LLM-as-judge until retrieval metrics and failure analysis are stable.
