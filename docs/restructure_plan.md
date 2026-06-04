# Restructure Plan - RAG Experiment Platform

## Muc Tieu

Chuyen project tu huong chat/notebook clone sang RAG Experiment Platform for Developers voi quy trinh:

```text
documents + golden questions
-> run RAG phase experiment
-> compare metrics
-> keep candidate pool
-> inspect failures
-> move candidates to next RAG phase
-> export final top 5 configs
```

## Nguyen Tac

- Khong dap di lam lai mot lan.
- Refactor theo tung phase nho, moi phase deu chay duoc.
- Khong doi hanh vi endpoint dang on dinh neu phase do khong yeu cau.
- Uu tien kha nang demo va benchmark co so lieu.
- Khong cat top 5 qua som.
- Top 5 chi la output cuoi cua toan bo pipeline.
- Moi phase giu candidate pool rong hon, vi config yeu o phase rieng le co the manh khi ket hop voi module khac.

## Kien Truc Backend Huong Toi

```text
app/
├── main.py
├── api/
│   └── routes/
│       ├── health.py
│       ├── workspaces.py
│       ├── documents.py
│       ├── playground.py
│       ├── eval_questions.py
│       ├── experiments.py
│       └── reports.py
├── schemas/
│   ├── workspace.py
│   ├── document.py
│   ├── retrieval.py
│   ├── eval.py
│   ├── experiment.py
│   └── rag_config.py
├── services/
│   ├── workspace_service.py
│   ├── document_service.py
│   ├── chunking_service.py
│   ├── evaluation_service.py
│   ├── experiment_service.py
│   ├── rag_config_service.py
│   ├── metrics_service.py
│   ├── rag_service.py
│   └── retrieval/
│       ├── keyword_retriever.py
│       ├── vector_retriever.py
│       ├── hybrid_retriever.py
│       └── reranker.py
├── storage/
│   ├── repository.py
│   └── file_store.py
└── core/
    ├── config.py
    └── logging.py
```

Do not create all of this at once. Add pieces only when the feature needs them.

## Multi-Phase RAG Experiment Pipeline

```text
Phase 0 - Baseline sanity
Phase 1 - Chunking evaluation
Phase 2 - Retriever evaluation
Phase 3 - Query transform evaluation
Phase 4 - Reranker evaluation
Phase 5 - Context builder evaluation
Phase 6 - End-to-end answer evaluation
Final   - Export top 5 RAG configs
```

Current implemented baseline:

```text
retriever_evaluation with keyword, vector, hybrid
```

## Local Persistent Data Huong Toi

```text
data/
└── workspaces/
    └── {workspace_id}/
        ├── metadata.json
        ├── documents/
        ├── chunks/
        ├── eval_sets/
        │   └── golden_questions.jsonl
        ├── rag_configs/
        │   └── presets.json
        ├── experiments/
        │   └── run_*.json
        ├── candidate_pools/
        │   └── {stage}.json
        └── reports/
            └── run_*.md
```

Current data layout does not yet have `rag_configs/` or `candidate_pools/`.

## Mapping Tu Hien Trang Sang Cau Truc Moi

1. Route

- Giu cac route hien co dang chay.
- Tach ro route theo domain khi file `workspaces.py` qua lon.
- Them route cho `rag_configs` sau khi leaderboard/failure analysis on dinh.

2. Service

- `document_service`, `chunking_service`, `evaluation_service` giu va bo sung.
- `experiment_service` hien dang chua run/compare/leaderboard.
- Them `rag_config_service.py` khi bat dau phase chunking/query/rerank.
- Retrieval doi sang strategy package khi logic bat dau phinh to.

3. Storage

- Chua them production DB.
- Them repository/file store chi khi viec doc/ghi JSON bi lap lai nhieu.
- Candidate pool persistence la buoc sau, khong phai buoc dau.

4. Script

- Script prepare/upload/eval tiep tuc dung duoc trong luc migrate.
- Sau do goi chung qua service/repository.

## Ke Hoach Migrate Nho Theo Commit

1. Commit A - Product direction docs + current phase update
2. Commit B - Leaderboard output + candidate pool response
3. Commit C - Add stable question_id to experiment results
4. Commit D - Side-by-side per-question failure analysis
5. Commit E - First-class rag_config presets
6. Commit F - Chunking evaluation phase
7. Commit G - Query transform evaluation phase
8. Commit H - Reranker evaluation phase
9. Commit I - Candidate pool persistence
10. Commit J - Final answer evaluation foundation

## Definition Of Done Cho Giai Doan Restructure

- Luong upload docs -> upload eval set -> run eval -> xem leaderboard -> xem report chay tron.
- Co the so sanh it nhat 3 retrieval candidates.
- Leaderboard co rank, score, metrics, status.
- Candidate pool duoc the hien ro tren UI.
- Report/failure analysis giup debug tai sao candidate thang/thua.
- Frontend phuc vu workflow benchmark, khong chi chat playground.
