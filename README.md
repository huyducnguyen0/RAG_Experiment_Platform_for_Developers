# RAG Experiment Platform for Developers

## 1. Giới thiệu

**RAG Experiment Platform for Developers** là một nền tảng giúp developer thử nghiệm, so sánh và đánh giá nhiều chiến lược RAG khác nhau trên cùng một bộ tài liệu và bộ câu hỏi kiểm thử.

Thay vì chỉ xây một chatbot RAG đơn giản, project này tập trung vào việc trả lời câu hỏi:

> Với bộ dữ liệu cụ thể của developer, chiến lược RAG nào cho kết quả tốt nhất?

Platform cho phép người dùng upload tài liệu, tạo workspace, truy vấn tài liệu, và trong các phase tiếp theo sẽ hỗ trợ chạy nhiều experiment để so sánh các chiến lược như:

- Keyword retrieval
- Vector search
- Hybrid search
- Different chunking strategies
- Query rewriting
- Query expansion
- Reranking
- Parent-child / hierarchical RAG
- GraphRAG
- Agentic RAG

Hiện tại project đang ở giai đoạn MVP nền tảng: đã có backend FastAPI, workspace, document upload, chunking cơ bản, retrieval baseline và frontend cơ bản.

---

## 2. Mục tiêu của project

Project hướng tới việc xây dựng một nền tảng đánh giá RAG theo dạng **modular pipeline**.

Pipeline tổng quát:

```text
Documents
→ Chunking / Indexing
→ Query Processing
→ Retrieval
→ Reranking
→ Context Building
→ Answer Generation
→ Evaluation
→ Leaderboard
```

Mỗi thành phần trong pipeline có thể được thay đổi để tạo ra một cấu hình RAG khác nhau.

Ví dụ:

```text
Config A = Recursive Chunking + Vector Search
Config B = Recursive Chunking + Hybrid Search
Config C = Parent-child Chunking + Hybrid Search + Reranking
Config D = Query Expansion + Hybrid Search + Reranking
```

Sau đó platform sẽ chạy các cấu hình này trên cùng một bộ câu hỏi test và trả về bảng so sánh metric.

---

## 3. Trạng thái hiện tại

Hiện tại project đã có các chức năng chính:

### Backend

- FastAPI backend
- Health check API
- Chat API thử nghiệm
- Workspace CRUD
- Upload tài liệu theo workspace
- Lưu danh sách documents
- Tự động chunk tài liệu `.txt` / `.md`
- Keyword retrieval baseline
- Mock RAG answer kèm source chunks
- API retrieve documents
- API query documents trong workspace

### Frontend

- Giao diện workspace cơ bản
- Tạo workspace
- Xem danh sách workspace
- Upload document
- Xem documents trong workspace
- Gửi query tới backend
- Hiển thị answer và sources

---

## 4. Flow người dùng hiện tại

Flow hiện tại của platform:

```text
1. User tạo workspace
2. User upload tài liệu vào workspace
3. Backend đọc file và chia thành chunks
4. User đặt câu hỏi trên workspace đó
5. Backend retrieve các chunks liên quan
6. Backend trả về câu trả lời mock + danh sách sources
```

Ví dụ:

```text
Workspace: AI Papers
Documents: rag_intro.md, vector_search.txt
Question: "RAG là gì?"
Output:
- Answer
- Source chunks liên quan
```

---

## 5. Flow mục tiêu sau khi hoàn thiện evaluation

Flow mục tiêu của project:

```text
1. User tạo workspace
2. User upload corpus tài liệu
3. User upload QA test set
4. User chọn nhiều RAG configs để benchmark
5. Platform chạy experiment
6. Platform tính metrics
7. Platform hiển thị leaderboard
8. User xem top configurations tốt nhất
```

Ví dụ output leaderboard:

| Rank | Config | Recall@3 | Recall@5 | MRR | Latency |
|---:|---|---:|---:|---:|---:|
| 1 | Hybrid + Rerank | 0.72 | 0.84 | 0.69 | 1800ms |
| 2 | Parent-child + Hybrid | 0.70 | 0.82 | 0.66 | 1400ms |
| 3 | Vector Baseline | 0.55 | 0.67 | 0.49 | 500ms |

---

## 6. Dataset đánh giá

Platform sẽ hỗ trợ nhiều format dataset khác nhau để người dùng không bị ép chuẩn bị dữ liệu quá phức tạp.

### 6.1. Simple QA format

Dạng đơn giản nhất:

```json
{
  "question": "Who won the IIOTY award in 2023?",
  "reference_answer": "Maxine Thompson won the IIOTY award in 2023."
}
```

### 6.2. QA + keywords

```json
{
  "question": "Who won the IIOTY award in 2023?",
  "reference_answer": "Maxine Thompson won the prestigious Insurellm Innovator of the Year award in 2023.",
  "keywords": ["Maxine", "Thompson", "IIOTY"],
  "category": "direct_fact"
}
```

### 6.3. QA + evidence text

```json
{
  "question": "Who won the IIOTY award in 2023?",
  "reference_answer": "Maxine Thompson won the prestigious Insurellm Innovator of the Year award in 2023.",
  "gold_evidence_text": "Maxine Thompson won the prestigious Insurellm Innovator of the Year award in 2023.",
  "category": "direct_fact"
}
```

### 6.4. Full retrieval evaluation format

```json
{
  "q_id": "q_001",
  "question": "Who won the IIOTY award in 2023?",
  "reference_answer": "Maxine Thompson won the prestigious Insurellm Innovator of the Year award in 2023.",
  "expected_chunk_ids": ["doc_001_chunk_003"],
  "keywords": ["Maxine", "Thompson", "IIOTY"],
  "category": "direct_fact"
}
```

### 6.5. JSONL format

Mỗi dòng là một JSON object độc lập:

```jsonl
{"q_id":"q_001","question":"Who won the IIOTY award in 2023?","reference_answer":"Maxine Thompson won the IIOTY award in 2023.","keywords":["Maxine","Thompson","IIOTY"],"category":"direct_fact"}
{"q_id":"q_002","question":"What is RAG?","reference_answer":"RAG combines retrieval with generation.","keywords":["retrieval","generation","RAG"],"category":"definition"}
```

Nếu user không cung cấp `q_id`, backend sẽ tự sinh.

Nếu user không cung cấp `expected_chunk_ids`, backend vẫn có thể đánh giá bằng `reference_answer`, `keywords`, hoặc `gold_evidence_text`.

---

## 7. Metrics dự kiến

Phase evaluation sẽ tập trung trước vào retrieval metrics.

### Recall@K

Đo xem chunk đúng có nằm trong top K kết quả retrieve không.

```text
Recall@5 = số câu hỏi có evidence đúng trong top 5 / tổng số câu hỏi
```

### Hit Rate@K

Đo xem ít nhất một kết quả đúng có xuất hiện trong top K không.

```text
Hit@5 = câu hỏi có ít nhất một chunk đúng trong top 5
```

### MRR

MRR đo vị trí xuất hiện đầu tiên của evidence đúng.

```text
Nếu chunk đúng ở rank 1 → score = 1
Nếu chunk đúng ở rank 2 → score = 1/2
Nếu chunk đúng ở rank 5 → score = 1/5
Nếu không tìm thấy → score = 0
```

### Latency

Đo thời gian chạy trung bình của từng config.

```text
avg_latency_ms
p95_latency_ms
```

---

## 8. Cấu trúc project

Cấu trúc tổng quan:

```text
RAG_Experiment_Platform_for_Developers/
│
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   │
│   ├── services/
│   │   ├── rag_service.py
│   │   ├── ingestion_service.py
│   │   └── ...
│   │
│   ├── vectorstore/
│   │   └── ...
│   │
│   └── ...
│
├── frontend/
│   └── ...
│
├── docs/
│   ├── project_checklist.md
│   ├── current_phase.md
│   └── ...
│
├── sample_data/
│   └── ...
│
├── scripts/
│   └── ...
│
├── pyproject.toml
├── README.md
└── uv.lock
```

---

## 9. Backend API hiện tại

### Health check

```http
GET /health
```

Dùng để kiểm tra backend có chạy không.

---

### Chat thử nghiệm

```http
POST /chat
```

Body:

```json
{
  "question": "What is RAG?"
}
```

---

### Workspaces

Tạo workspace:

```http
POST /workspaces
```

Lấy danh sách workspace:

```http
GET /workspaces
```

Lấy chi tiết workspace:

```http
GET /workspaces/{workspace_id}
```

Cập nhật workspace:

```http
PATCH /workspaces/{workspace_id}
```

Xóa workspace:

```http
DELETE /workspaces/{workspace_id}
```

---

### Documents trong workspace

Upload document vào workspace:

```http
POST /workspaces/{workspace_id}/documents/upload
```

Lấy danh sách documents:

```http
GET /workspaces/{workspace_id}/documents
```

Lấy chi tiết document:

```http
GET /workspaces/{workspace_id}/documents/{document_id}
```

Xóa document:

```http
DELETE /workspaces/{workspace_id}/documents/{document_id}
```

---

### Research / Retrieval

Retrieve chunks liên quan:

```http
POST /research/retrieve
```

Query tài liệu:

```http
POST /research/query
```

---

## 10. API dự kiến cho phase evaluation

### QA Sets

```http
POST /workspaces/{workspace_id}/qa-sets
GET /workspaces/{workspace_id}/qa-sets
GET /workspaces/{workspace_id}/qa-sets/{qa_set_id}
DELETE /workspaces/{workspace_id}/qa-sets/{qa_set_id}
```

Upload QA dataset:

```http
POST /workspaces/{workspace_id}/qa-sets/upload
```

---

### RAG Configs

```http
GET /workspaces/{workspace_id}/rag-configs
POST /workspaces/{workspace_id}/rag-configs
GET /workspaces/{workspace_id}/rag-configs/{config_id}
```

Preset configs:

```http
GET /rag-config-presets
```

---

### Experiment Runs

Tạo experiment:

```http
POST /workspaces/{workspace_id}/experiment-runs
```

Lấy danh sách experiment:

```http
GET /workspaces/{workspace_id}/experiment-runs
```

Xem chi tiết experiment:

```http
GET /workspaces/{workspace_id}/experiment-runs/{run_id}
```

Xem leaderboard:

```http
GET /workspaces/{workspace_id}/experiment-runs/{run_id}/leaderboard
```

---

## 11. RAG config dự kiến

Một config RAG có thể được biểu diễn như sau:

```json
{
  "name": "hybrid_recursive_rerank",
  "chunking_strategy": "recursive",
  "chunk_size": 500,
  "chunk_overlap": 100,
  "query_transform": "none",
  "retriever_type": "hybrid",
  "candidate_k": 30,
  "reranker_type": "cross_encoder",
  "top_k": 5,
  "context_builder": "top_k"
}
```

Một số preset config ban đầu:

```text
CFG_01: recursive + vector
CFG_02: recursive + BM25
CFG_03: recursive + hybrid
CFG_04: recursive + hybrid + rerank
CFG_05: semantic + vector
CFG_06: semantic + hybrid
CFG_07: parent-child + vector
CFG_08: parent-child + hybrid
CFG_09: query expansion + hybrid
CFG_10: multi-query + hybrid
CFG_11: query expansion + hybrid + rerank
CFG_12: parent-child + hybrid + rerank
```

---

## 12. Cách chạy project

### 12.1. Clone project

```bash
git clone <repo-url>
cd RAG_Experiment_Platform_for_Developers
```

---

### 12.2. Cài dependencies backend

Project dùng `uv`.

```bash
uv sync
```

Nếu chưa có `uv`, cài bằng:

```bash
pip install uv
```

---

### 12.3. Kích hoạt môi trường ảo trên Windows

```powershell
.venv\Scripts\Activate.ps1
```

Nếu bị lỗi execution policy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

---

### 12.4. Chạy backend

```bash
uv run uvicorn app.main:app --reload
```

Backend mặc định chạy tại:

```text
http://127.0.0.1:8000
```

Swagger docs:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

### 12.5. Chạy frontend

Vào thư mục frontend:

```bash
cd frontend
```

Cài dependencies:

```bash
npm install
```

Chạy dev server:

```bash
npm run dev
```

Frontend thường chạy tại:

```text
http://localhost:5173
```

---

## 13. Hướng dẫn sử dụng hiện tại

### Bước 1: Chạy backend

```bash
uv run uvicorn app.main:app --reload
```

Mở:

```text
http://127.0.0.1:8000/docs
```

Kiểm tra API `/health`.

---

### Bước 2: Chạy frontend

```bash
cd frontend
npm run dev
```

Mở frontend trên browser.

---

### Bước 3: Tạo workspace

Tạo một workspace mới, ví dụ:

```text
Name: AI Research Workspace
Description: Workspace for testing RAG documents
```

---

### Bước 4: Upload documents

Upload file `.txt` hoặc `.md`.

Ví dụ:

```text
rag_intro.md
vector_search.md
reranking_notes.txt
```

Sau khi upload, backend sẽ đọc nội dung và chia thành chunks.

---

### Bước 5: Query document

Nhập câu hỏi vào giao diện query.

Ví dụ:

```text
What is Retrieval Augmented Generation?
```

Backend sẽ retrieve chunks liên quan và trả về answer kèm sources.

---

## 14. Hướng dẫn sử dụng phase evaluation sau khi hoàn thiện

### Bước 1: Upload documents

Người dùng upload corpus tài liệu.

---

### Bước 2: Upload QA dataset

Ví dụ file `golden_questions.jsonl`:

```jsonl
{"question":"Who won the IIOTY award in 2023?","reference_answer":"Maxine Thompson won the IIOTY award in 2023.","keywords":["Maxine","Thompson","IIOTY"],"category":"direct_fact"}
{"question":"What is RAG?","reference_answer":"RAG combines retrieval with generation.","keywords":["retrieval","generation","RAG"],"category":"definition"}
```

---

### Bước 3: Chọn RAG configs

Ví dụ chọn:

```text
recursive + vector
recursive + hybrid
recursive + hybrid + rerank
parent-child + hybrid
query expansion + hybrid
```

---

### Bước 4: Run experiment

Platform chạy toàn bộ config trên cùng một bộ câu hỏi.

---

### Bước 5: Xem leaderboard

Kết quả hiển thị:

```text
Rank
Config name
Recall@3
Recall@5
MRR
Latency
Score
```

---

### Bước 6: Debug câu fail

Người dùng có thể xem từng câu hỏi:

```text
Question
Gold answer
Retrieved chunks
Expected evidence
Hit / Miss
Rank of correct chunk
```

---

## 15. Candidate pool strategy

Project không chọn top 5 ngay từ đầu.

Thay vào đó dùng chiến lược candidate pool:

```text
Initial configs: 30–60 configs
Quick benchmark: giữ top 20
Full retrieval benchmark: giữ top 10
Final evaluation: xuất top 5
```

Top 5 chỉ là output cuối cùng, không phải cách lọc ngay từ đầu.

Flow:

```text
Generate configs
→ Quick benchmark
→ Candidate pool top 20
→ Full benchmark
→ Candidate pool top 10
→ Final benchmark
→ Top 5 final configs
```

---

## 16. Roadmap

### Phase 1: Modular RAG Evaluation Leaderboard

Mục tiêu:

- Upload QA dataset
- Normalize nhiều schema dataset khác nhau
- Tạo RAG config presets
- Chạy retrieval-only evaluation
- Tính Recall@K, Hit@K, MRR, latency
- Hiển thị leaderboard
- Giữ candidate pool thay vì chỉ top 5 ngay từ đầu

---

### Phase 2: Advanced Retrieval Strategies

Mục tiêu:

- Query rewriting
- Query expansion
- Multi-query retrieval
- Reranking
- Parent-child retrieval
- Hierarchical retrieval
- Semantic chunking

---

### Phase 3: GraphRAG

Mục tiêu:

- Entity extraction
- Relationship extraction
- Knowledge graph construction
- Graph-based retrieval
- Community / document-level summary
- Global question answering

---

### Phase 4: Agentic RAG

Mục tiêu:

- Query decomposition
- Planner
- Iterative retrieval
- Self-checking
- Tool routing
- Multi-step reasoning
- Agent trace logging

---

### Phase 5: Report Export & Developer UX

Mục tiêu:

- Export experiment report
- Compare config side-by-side
- Cost / latency dashboard
- Failure analysis
- Recommendation system cho best RAG config

---

## 17. Tầm nhìn cuối cùng

Project hướng tới trở thành một nền tảng giúp developer:

```text
Upload documents
Upload test questions
Run multiple RAG strategies
Compare metrics
Find best RAG configuration
Export report
```

Thay vì đoán cấu hình RAG nào tốt, developer có thể benchmark thực tế trên dữ liệu của chính họ.

Mục tiêu cuối cùng:

> Build a developer-focused RAG evaluation platform that benchmarks different RAG pipeline configurations and recommends the best-performing setup based on retrieval quality, answer quality, latency, and cost.
