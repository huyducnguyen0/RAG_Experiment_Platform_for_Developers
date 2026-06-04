import chromadb
from app.core.config import settings

def get_chroma_client():
    return chromadb.PersistentClient(path=settings.CHROMA_DIR)