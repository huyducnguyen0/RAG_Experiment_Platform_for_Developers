# Frontend Rebuild Plan - Developer UX

## Muc tieu

Xay lai frontend theo huong cong cu benchmark RAG cho developer, khong dat chat UI lam trung tam.

## UX flow chinh

1. Man hinh dau:
- Danh sach workspace
- Tao workspace moi
- Xoa workspace

2. Khi vao 1 workspace:
- Tabs:
  - Documents
  - Golden Questions
  - Experiments
  - Reports
  - Playground

## Scope tab theo MVP

### Documents
- Upload `.txt` / `.md`
- List documents
- View chunk count
- Delete document

### Golden Questions
- Upload `golden_questions.jsonl`
- List questions
- Kiem tra format invalid line

### Experiments
- Form chay eval:
  - strategy (ban dau: keyword)
  - top_k
- Nut run evaluation
- Hien metrics summary ngay sau khi chay

### Reports
- List run history
- Xem chi tiet report (json + markdown render)

### Playground
- Hoi thu cong theo workspace
- Hien answer + sources

## Design guideline

- UI kieu dashboard, toi gian, uu tien scan nhanh.
- Tranh bo cuc hero/marketing.
- Hanh dong chinh dat ro: upload, run, compare.
- O workspace list, card nho gon:
  - documents count
  - eval questions count
  - latest run
  - best strategy (khi da co)

## API contract can canh

- Workspace:
  - `POST /workspaces`
  - `GET /workspaces`
  - `GET /workspaces/{workspace_id}`
  - `DELETE /workspaces/{workspace_id}`

- Documents:
  - `POST /workspaces/{workspace_id}/documents/upload`
  - `GET /workspaces/{workspace_id}/documents`

- Golden questions:
  - `POST /workspaces/{workspace_id}/eval/questions/upload`
  - `GET /workspaces/{workspace_id}/eval/questions`

- Experiments:
  - `POST /workspaces/{workspace_id}/experiments/run`
  - `GET /workspaces/{workspace_id}/experiments`
  - `GET /workspaces/{workspace_id}/experiments/{run_id}`

- Reports:
  - `GET /workspaces/{workspace_id}/reports/{run_id}`

- Playground:
  - `POST /workspaces/{workspace_id}/research/retrieve`
  - `POST /workspaces/{workspace_id}/research/query`

## Rollout frontend theo buoc nho

1. FE-1: Chuan hoa workspace landing + create/delete
2. FE-2: Add tab Golden Questions + upload/list
3. FE-3: Add tab Experiments + run keyword baseline
4. FE-4: Add tab Reports + report detail
5. FE-5: Playground polish + source view

Moi buoc phai co:
- API call pass
- Loading state
- Error state
- Empty state

## Definition of Done

- User moi co the tu tao workspace, upload docs, upload eval set.
- Chay duoc benchmark va xem report ngay tren UI.
- Co du du lieu de chup screenshot va viet CV/bao cao.
