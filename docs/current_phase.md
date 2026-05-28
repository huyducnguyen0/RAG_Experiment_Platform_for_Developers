# Current Phase

Current phase: Phase Eval 2 - Evaluation Report Export

Current goal:
Export evaluation results into JSON/Markdown report files with timestamped outputs for comparison.

Current constraints:
- Keep keyword baseline as-is (no vector/hybrid/rerank yet).
- Keep workspace data local persistent storage.
- No production database migration.

Next task:
- Move to Phase Eval 3:
  - add golden question upload/list APIs per workspace
  - wire frontend Golden Questions tab to those APIs

Expected behavior:
- Running eval script prints metrics and writes:
  - reports/retrieval_eval_*.json
  - reports/retrieval_eval_*.md
