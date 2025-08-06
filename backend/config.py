"""App settings, read from environment variables (see .env.example)."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# .env.local is still read so older setups keep working.
for candidate in (".env", ".env.local"):
    env_path = BASE_DIR / candidate
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)


def _get_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_list(name: str, default: str) -> list[str]:
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# MongoDB. The db name is separate so Atlas URIs without a path also work.
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "Annapoorna")

# Chat model: "gemini", "ollama" or "openai" (any OpenAI-compatible API).
# If empty, the first configured one is used, in that order.
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "").strip().lower()

LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.8"))
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "2048"))
LLM_TIMEOUT_SECONDS = float(os.environ.get("LLM_TIMEOUT_SECONDS", "60"))

# No default model name, Google retires them over time.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "")
# Optional. 0 turns off "thinking" on models that support it.
GEMINI_THINKING_BUDGET = os.environ.get("GEMINI_THINKING_BUDGET", "").strip()

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "")

LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "EMPTY")
LLM_MODEL = os.environ.get("LLM_MODEL", "unsloth-llama-3-2-3b-instruct")

# Google Earth Engine. Locally, `earthengine authenticate` is enough; on a
# server set GEE_SERVICE_ACCOUNT_KEY to a service account JSON key.
GEE_PROJECT_ID = os.environ.get("PROJECT_ID", "")
GEE_SERVICE_ACCOUNT_KEY = os.environ.get("GEE_SERVICE_ACCOUNT_KEY", "")

# Weather. Open-Meteo is used when there's no Tomorrow.io key (no key needed).
TOMORROW_API_KEY = os.environ.get("TOMORROW_API_KEY", "")
TOMORROW_API_URL = os.environ.get(
    "TOMORROW_API_URL", "https://api.tomorrow.io/v4/weather/realtime"
)
OPEN_METEO_API_URL = os.environ.get(
    "OPEN_METEO_API_URL", "https://api.open-meteo.com/v1/forecast"
)
WEATHER_TIMEOUT_SECONDS = float(os.environ.get("WEATHER_TIMEOUT_SECONDS", "10"))

# Vector store (only used by docCrud)
CHROMA_HOST = os.environ.get("CHROMA_HOST", "")
EMBEDDINGS_API_URL = os.environ.get("EMBEDDINGS_API_URL", "")
EMBEDDINGS_MODEL = os.environ.get("EMBEDDINGS_MODEL", "openai/clip-vit-base-patch32")

# Disease classifier
MODEL_PATH = Path(
    os.environ.get("MODEL_PATH", str(BASE_DIR / "crop_disease_cnn_model.h5"))
)
MODEL_IMAGE_SIZE = int(os.environ.get("MODEL_IMAGE_SIZE", "224"))

# Whisper. "medium" is a ~1.4GB download, "base" starts much faster.
WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "medium")

# Daily report time (server local time)
REPORT_CRON_HOUR = int(os.environ.get("REPORT_CRON_HOUR", "5"))
REPORT_CRON_MINUTE = int(os.environ.get("REPORT_CRON_MINUTE", "0"))

CORS_ALLOW_ORIGINS = _get_list(
    "CORS_ALLOW_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
)
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))

# Turns off every network call. Used by the tests.
OFFLINE_MODE = _get_bool("OFFLINE_MODE", False)

# When a service isn't configured, fall back instead of failing: Open-Meteo for
# weather, an in-memory store for MongoDB, built-in advice instead of the LLM.
ALLOW_KEYLESS_FALLBACKS = _get_bool("ALLOW_KEYLESS_FALLBACKS", True)

# Demo farmer, so the dashboard can be opened without registering.
DEMO_MODE = _get_bool("DEMO_MODE", True)
DEMO_USER_ID = os.environ.get("DEMO_USER_ID", "000000000000000000000001")
