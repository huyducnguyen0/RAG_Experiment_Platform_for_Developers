# Current Phase

Current phase: Phase Clean 0 - Product Repositioning Alignment

Current goal:
Align architecture and frontend direction to the new product identity:
"RAG Experiment Platform for Developers".

Current constraints:
- Keep existing working APIs stable.
- Do not add vector/hybrid/rerank implementation in this phase.
- Keep local persistent storage (no production DB migration yet).
- Keep scope focused on planning + migration mapping.

Next task:
- Finalize restructure plan and frontend rebuild plan.
- Start Phase Eval 2 implementation next:
  - export evaluation reports to JSON/Markdown
  - timestamped run outputs for comparison

Expected behavior:
- Team has a clear migration map before heavy code changes.
- Next coding steps follow a stable, testable sequence.
