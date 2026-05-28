# RAG Experiment Roadmap

## Goal

Turn Agentic Research OS into a RAG experimentation platform that can compare retrieval and generation techniques with measurable results.

## Phase Order

```text
Phase Clean 0 - Repository cleanup
Phase Eval 1 - Golden dataset + keyword baseline metrics
Phase Eval 2 - Evaluation report export
Phase Vector 1 - Vector retrieval strategy
Phase Hybrid 1 - Hybrid retrieval strategy
Phase Rerank 1 - Reranking strategy
Phase RAG 2 - Real LLM answer mode
Phase Agent 1 - Agentic router
Phase Portfolio - README/CV/demo polish
```

## Core Evaluation Metrics

- Hit@k
- Recall@k
- Precision@k
- MRR
- Average latency

## Strategy Comparison Target

The project should eventually produce a report like:

```text
keyword baseline
vector retrieval
hybrid retrieval
hybrid + rerank
agentic router
```

Each strategy should be evaluated against the same golden question set.
