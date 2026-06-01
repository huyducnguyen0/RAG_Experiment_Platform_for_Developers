import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import Settings
settings = Settings()


print("APP_ENV:", settings.APP_ENV)
print("DEBUG:", settings.DEBUG)
print("CHROMA_DIR:", settings.CHROMA_DIR)
print("OPENAI_API_KEY exists:", bool(settings.OPENAI_API_KEY))
