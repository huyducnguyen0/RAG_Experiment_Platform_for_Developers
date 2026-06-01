import csv
import hashlib
import json
import re
from pathlib import Path

from datasets import load_dataset

# =========================
# CONFIG
# =========================

NUM_SAMPLES = 120

OUTPUT_DIR = Path("sample_data/squad_eval_pack")
DOCS_DIR = OUTPUT_DIR / "documents"
EVAL_CSV = OUTPUT_DIR / "eval_questions.csv"
GOLDEN_TEMPLATE_JSONL = OUTPUT_DIR / "golden_questions_template.jsonl"
MAPPING_CSV = OUTPUT_DIR / "golden_questions_mapping.csv"
DOC_INDEX_JSON = OUTPUT_DIR / "documents_index.json"

DOCS_DIR.mkdir(parents=True, exist_ok=True)

# Remove old generated documents in this pack so each run is deterministic.
for old_file in DOCS_DIR.glob("doc_*.*"):
    if old_file.suffix.lower() in {".md", ".txt"}:
        old_file.unlink()


def clean_filename(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text[:40] or "document"


# =========================
# LOAD SQUAD DATASET
# =========================

dataset = load_dataset("rajpurkar/squad", split=f"train[:{NUM_SAMPLES}]")

docs_by_context: dict[str, dict] = {}
eval_rows: list[dict] = []

# =========================
# CONVERT DATA
# =========================

for row in dataset:
    title = row["title"]
    context = row["context"]
    question = row["question"]
    answers = row["answers"]["text"]

    if not answers:
        continue

    expected_answer = answers[0]

    context_hash = hashlib.md5(context.encode("utf-8")).hexdigest()[:8]
    safe_title = clean_filename(title)
    doc_key = f"{safe_title}_{context_hash}"
    doc_filename = f"doc_{doc_key}.md"

    if doc_key not in docs_by_context:
        docs_by_context[doc_key] = {
            "title": title,
            "context": context,
            "file_name": doc_filename,
        }

    eval_rows.append({
        "question": question,
        "expected_answer": expected_answer,
        "reference_doc": doc_filename,
        "reference_doc_key": doc_key,
        "question_type": "factual",
        "difficulty": "easy",
        "source": "squad",
    })

# =========================
# WRITE DOCUMENTS
# =========================

for doc in docs_by_context.values():
    file_path = DOCS_DIR / doc["file_name"]

    content = f"""# {doc["title"]}

{doc["context"]}
"""

    file_path.write_text(content, encoding="utf-8")

# =========================
# WRITE EVAL CSV
# =========================

with EVAL_CSV.open("w", newline="", encoding="utf-8") as csv_file:
    fieldnames = [
        "question",
        "expected_answer",
        "reference_doc",
        "reference_doc_key",
        "question_type",
        "difficulty",
        "source",
    ]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(eval_rows)

with DOC_INDEX_JSON.open("w", encoding="utf-8") as index_file:
    json.dump(
        [
            {
                "doc_key": doc_key,
                "file_name": payload["file_name"],
                "title": payload["title"],
            }
            for doc_key, payload in sorted(docs_by_context.items())
        ],
        index_file,
        ensure_ascii=False,
        indent=2,
    )

# This file is uploadable right away to /eval/questions/upload,
# but expected_chunk_ids is intentionally empty until you map chunk ids
# after uploading documents into a workspace.
with GOLDEN_TEMPLATE_JSONL.open("w", encoding="utf-8") as jsonl_file:
    for idx, row in enumerate(eval_rows, start=1):
        payload = {
            "id": f"q_{idx:04d}",
            "question": row["question"],
            "expected_chunk_ids": [],
            "top_k": 3,
            "notes": (
                f"source=squad; ref_doc={row['reference_doc']}; "
                f"expected_answer={row['expected_answer']}"
            ),
        }
        jsonl_file.write(json.dumps(payload, ensure_ascii=False) + "\n")

with MAPPING_CSV.open("w", newline="", encoding="utf-8") as mapping_file:
    fieldnames = [
        "question_id",
        "question",
        "reference_doc",
        "expected_answer",
        "expected_chunk_ids_after_upload",
    ]
    writer = csv.DictWriter(mapping_file, fieldnames=fieldnames)
    writer.writeheader()
    for idx, row in enumerate(eval_rows, start=1):
        writer.writerow(
            {
                "question_id": f"q_{idx:04d}",
                "question": row["question"],
                "reference_doc": row["reference_doc"],
                "expected_answer": row["expected_answer"],
                "expected_chunk_ids_after_upload": "",
            }
        )

print("DONE")
print(f"Documents folder: {DOCS_DIR}")
print(f"Eval CSV: {EVAL_CSV}")
print(f"Golden template JSONL: {GOLDEN_TEMPLATE_JSONL}")
print(f"Chunk-id mapping CSV: {MAPPING_CSV}")
print(f"Documents index JSON: {DOC_INDEX_JSON}")
print(f"Number of documents: {len(docs_by_context)}")
print(f"Number of eval questions: {len(eval_rows)}")
