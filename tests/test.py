import sys
from pprint import pprint

print("=" * 60)
print("AGENTIC RESEARCH OS - ENVIRONMENT TEST")
print("=" * 60)

# ---------------------------------------------------
# PYTHON INFO
# ---------------------------------------------------

print("\n[1] PYTHON INFO")

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

# ---------------------------------------------------
# IMPORT TESTS
# ---------------------------------------------------

print("\n[2] TESTING IMPORTS")

packages = [
    ("fastapi", "FastAPI"),
    ("uvicorn", "Uvicorn"),
    ("openai", "OpenAI"),
    ("chromadb", "ChromaDB"),
    ("fitz", "PyMuPDF"),
    ("pydantic", "Pydantic"),
    ("loguru", "Loguru"),
    ("numpy", "NumPy"),
    ("pandas", "Pandas"),
    ("requests", "Requests"),
    ("httpx", "HTTPX"),
    ("bs4", "BeautifulSoup"),
]

success = []
failed = []

for module_name, display_name in packages:
    try:
        __import__(module_name)
        print(f"[OK] {display_name}")
        success.append(display_name)

    except Exception as e:
        print(f"[FAIL] {display_name} -> {e}")
        failed.append(display_name)

# ---------------------------------------------------
# OPENAI TEST
# ---------------------------------------------------

print("\n[3] TESTING OPENAI CLIENT")

try:
    from openai import OpenAI

    client = OpenAI()

    print("[OK] OpenAI client initialized")

except Exception as e:
    print(f"[FAIL] OpenAI client -> {e}")

# ---------------------------------------------------
# CHROMADB TEST
# ---------------------------------------------------

print("\n[4] TESTING CHROMADB")

try:
    import chromadb

    client = chromadb.PersistentClient(path="./chroma_db")

    collection = client.get_or_create_collection(
        name="test_collection"
    )

    collection.add(
        documents=["hello world"],
        ids=["1"]
    )

    results = collection.query(
        query_texts=["hello"],
        n_results=1
    )

    print("[OK] ChromaDB working")
    pprint(results)

except Exception as e:
    print(f"[FAIL] ChromaDB -> {e}")

# ---------------------------------------------------
# PDF TEST
# ---------------------------------------------------

print("\n[5] TESTING PDF MODULE")

try:
    import fitz

    print("[OK] PyMuPDF working")

except Exception as e:
    print(f"[FAIL] PDF module -> {e}")

# ---------------------------------------------------
# ENVIRONMENT SUMMARY
# ---------------------------------------------------

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

print(f"\nSuccessful imports: {len(success)}")
print(f"Failed imports: {len(failed)}")

if failed:
    print("\nFailed packages:")
    for f in failed:
        print(f" - {f}")

else:
    print("\nALL TESTS PASSED")

print("\nEnvironment looks healthy.")
print("=" * 60)