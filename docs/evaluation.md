# Evaluation Guide

## Purpose

This guide explains how to evaluate the current keyword retrieval baseline.

The baseline uses:

```text
question -> keyword retrieval -> top-k chunk ids
```

## Dataset Format

Use `eval/golden_questions.jsonl` where each line is a JSON object.

Required fields:

- `question`: user question text
- `workspace_id`: workspace to search in
- `expected_chunk_ids`: list of chunk ids expected to be relevant

Optional fields:

- `top_k`: defaults to `3`
- `notes`: free text notes

Example:

```json
{"question":"What is RAG?","workspace_id":"ws_demo","top_k":3,"expected_chunk_ids":["doc_x_chunk_000"]}
```

## Run Evaluation

From project root:

```bash
uv run python scripts/run_retrieval_eval.py
```

After each run, the script also saves timestamped files:

- `reports/retrieval_eval_YYYYMMDD_HHMMSS.json`
- `reports/retrieval_eval_YYYYMMDD_HHMMSS.md`

## Metrics

The script prints:

- `Hit@k`: fraction of cases with at least one relevant retrieved chunk
- `Recall@k`: average relevant-retrieved / expected-relevant per case
- `Precision@k`: average relevant-retrieved / k per case
- `MRR`: mean reciprocal rank of first relevant chunk
- `Avg latency (ms)`: average retrieval latency per case

## Notes

- If workspace ids or chunk ids change after re-uploading files, update the dataset.
- Keep this as the baseline before adding vector, hybrid, or reranking strategies.
- You can compare historical runs by opening files in `reports/`.
