# Current Phase

Current phase: Phase Eval 1 - Golden Dataset and Keyword Baseline Metrics

Current goal:
Create a small evaluation dataset and measure the current keyword retrieval baseline.

Current constraints:
- Do not add vector database yet.
- Do not add production database yet.
- Keep workspace data local for the MVP.
- Do not add real LLM calls yet.
- Evaluate the existing keyword retrieval before adding advanced strategies.

Next task:
Add evaluation foundation:
- eval/golden_questions.jsonl
- scripts/run_retrieval_eval.py
- app/services/evaluation_service.py if useful
- docs/evaluation.md

Expected behavior:
- A script can run keyword retrieval against golden questions.
- It prints Hit@k, Recall@k, Precision@k, MRR, and latency.
- Results can be used as the baseline before vector/hybrid/rerank phases.
