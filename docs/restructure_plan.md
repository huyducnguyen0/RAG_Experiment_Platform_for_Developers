# Restructure Plan - RAG Experiment Platform

## Muc tieu

Chuyen project tu huong "chat/notebook clone" sang "RAG Experiment Platform for Developers" voi quy trinh:

documents + golden questions -> run experiments -> compare metrics -> recommend strategy

## Nguyen tac

- Khong dap di lam lai 1 lan.
- Refactor theo tung phase nho, moi phase deu chay duoc.
- Khong doi hanh vi endpoint dang on dinh neu phase do khong yeu cau.
- Uu tien kha nang demo va benchmark co so lieu.

## Kien truc backend de huong toi

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
│   └── report.py
├── services/
│   ├── workspace_service.py
│   ├── document_service.py
│   ├── chunking_service.py
│   ├── evaluation_service.py
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

## Cau truc data local persistent

```text
data/
└── workspaces/
    └── {workspace_id}/
        ├── metadata.json
        ├── documents/
        ├── chunks/
        ├── eval_sets/
        │   └── golden_questions.jsonl
        ├── experiments/
        │   └── run_*.json
        └── reports/
            └── run_*.md
```

## Mapping tu hien trang sang cau truc moi

1. Route
- Giu cac route hien co dang chay.
- Tach ro route theo domain: workspace/document/playground/eval/experiment/report.

2. Service
- `document_service`, `chunking_service`, `evaluation_service` giu va bo sung.
- Retrieval doi sang strategy package (`services/retrieval/*`) de de benchmark.

3. Storage
- Them lop `storage/repository.py` de gom doc/ghi file JSON.
- Service khong truy cap file truc tiep nua sau khi migrate.

4. Script
- Script eval tiep tuc dung duoc trong luc migrate.
- Sau do goi chung qua service/repository.

## Ke hoach migrate nho theo commit

1. Commit A - Product direction docs + current phase update
2. Commit B - Eval report export (JSON + Markdown) hoan tat
3. Commit C - Eval question APIs trong workspace
4. Commit D - Experiment run/list/detail APIs
5. Commit E - Frontend tabs: Golden Questions / Experiments / Reports
6. Commit F - Vector strategy
7. Commit G - Hybrid strategy
8. Commit H - Rerank option
9. Commit I - Recommendation logic + portfolio polish

## Definition of Done cho giai doan restructure

- Luong "upload docs -> upload eval set -> run eval -> xem report" chay tron.
- Co the so sanh it nhat 2 strategies.
- Report co du metrics: hit@k, recall@k, precision@k, MRR, latency.
- Frontend phuc vu workflow benchmark, khong chi chat playground.
