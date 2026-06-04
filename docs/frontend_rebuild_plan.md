# Frontend Rebuild Plan - Developer UX

## Muc Tieu

Xay frontend theo huong cong cu benchmark RAG cho developer, khong dat chat UI lam trung tam.

Frontend phai giup user:

```text
upload corpus
-> upload golden questions
-> run RAG phase experiment
-> xem leaderboard
-> xem candidate pool
-> debug failure cases
-> tiep tuc phase ke tiep
```

## UX Flow Chinh

1. Man hinh dau:

- Danh sach workspace
- Tao workspace moi
- Xoa workspace

2. Khi vao mot workspace:

- Tabs:
  - Documents
  - Golden Questions
  - Experiments
  - Reports
  - Playground

## Scope Tab Theo MVP Hien Tai

### Documents

- Upload `.txt` / `.md`
- Upload nhieu file cung luc
- List documents
- View chunk count
- Delete document

### Golden Questions

- Upload `golden_questions.jsonl`
- List questions
- Delete question
- Hien warning neu question thieu `expected_chunk_ids`

### Experiments

Current MVP:

- Chon strategy: keyword/vector/hybrid
- Run single strategy evaluation
- Run comparison: keyword/vector/hybrid
- Hien RAG phase leaderboard
- Hien summary:
  - tested count
  - candidate pool size
  - kept count
  - best config
  - fastest config
  - highest recall config
  - recommendation

Future:

- Chon RAG phase:
  - chunking_evaluation
  - retriever_evaluation
  - query_transform_evaluation
  - reranker_evaluation
  - context_builder_evaluation
  - final_answer_evaluation
- Chon candidate pool size
- Chon `rag_config` presets
- Xem side-by-side per-question failure analysis

### Reports

- List run history
- Xem report Markdown
- Sau nay render Markdown dep hon

### Playground

- Hoi thu cong theo workspace
- Hien answer + sources
- Dung de debug thu cong, khong phai product center

## Output Sau Khi Bam Compare/Test

Leaderboard target:

```text
Rank | Config | Hit@k | Recall | Precision | MRR | Latency | Score | Status
```

Status:

```text
kept
pruned
```

Summary target:

- total configs tested
- candidate pool size
- kept count
- best config
- fastest config
- highest recall config
- recommendation

Failure analysis target:

```text
Question | Expected | Keyword | Vector | Hybrid | Winner
```

## Design Guideline

- UI kieu dashboard, toi gian, uu tien scan nhanh.
- Tranh bo cuc hero/marketing.
- Hanh dong chinh dat ro: upload, run, compare.
- Bang metric phai de scan.
- Khong cat top 5 o UI neu do chua phai final phase.
- O workspace list, card nho gon:
  - documents count
  - eval questions count
  - latest run
  - best strategy/config khi da co

## API Contract Can Canh

Workspace:

```text
POST /workspaces
GET  /workspaces
GET  /workspaces/{workspace_id}
DELETE /workspaces/{workspace_id}
```

Documents:

```text
POST /workspaces/{workspace_id}/documents/upload
GET  /workspaces/{workspace_id}/documents
```

Golden questions:

```text
POST /workspaces/{workspace_id}/eval/questions/upload
GET  /workspaces/{workspace_id}/eval/questions
DELETE /workspaces/{workspace_id}/eval/questions/{question_id}
```

Experiments:

```text
POST /workspaces/{workspace_id}/experiments/run
POST /workspaces/{workspace_id}/experiments/compare
GET  /workspaces/{workspace_id}/experiments
GET  /workspaces/{workspace_id}/experiments/{run_id}
```

Reports:

```text
GET /workspaces/{workspace_id}/reports/{run_id}
```

Playground:

```text
POST /workspaces/{workspace_id}/research/retrieve
POST /workspaces/{workspace_id}/research/query
```

## Rollout Frontend Theo Buoc Nho

1. FE-1: Chuan hoa workspace landing + create/delete
2. FE-2: Add tab Golden Questions + upload/list/delete
3. FE-3: Add tab Experiments + run keyword baseline
4. FE-4: Add strategy selector + compare keyword/vector/hybrid
5. FE-5: Add leaderboard + candidate pool summary
6. FE-6: Add side-by-side per-question failure table
7. FE-7: Add phase selector and `rag_config` presets
8. FE-8: Add richer report rendering

Moi buoc phai co:

- API call pass
- Loading state
- Error state
- Empty state

## Definition Of Done

- User moi co the tao workspace, upload docs, upload eval set.
- Chay duoc benchmark va xem leaderboard ngay tren UI.
- Biet candidate nao duoc giu lai cho phase tiep theo.
- Co du du lieu de chup screenshot va viet CV/bao cao.
