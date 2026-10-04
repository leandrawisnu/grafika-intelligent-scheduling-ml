import os

from dotenv import load_dotenv

# Muat .env untuk dev lokal; di container env sudah disuntik docker compose
# (load_dotenv tidak menimpa env yang sudah ada).
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-placeholder")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")

# AI Import dokumen (ingest): LlamaParse untuk parsing universal, OpenRouter
# (Gemini) untuk klasifikasi, ekstraksi, dan pemetaan ke master GIS.
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY", "")
LLAMA_PARSE_TIER = os.getenv("LLAMA_PARSE_TIER", "agentic")
LLAMA_PARSE_TIMEOUT_SECONDS = float(os.getenv("LLAMA_PARSE_TIMEOUT_SECONDS", "300"))
LLAMA_OCR_LANGUAGES = os.getenv("LLAMA_OCR_LANGUAGES", "id,en")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
INGEST_MODEL = os.getenv("INGEST_MODEL", "google/gemini-2.5-flash")
INGEST_TIMEOUT_SECONDS = float(os.getenv("INGEST_TIMEOUT_SECONDS", "180"))
INGEST_MAX_OUTPUT_TOKENS = int(os.getenv("INGEST_MAX_OUTPUT_TOKENS", "60000"))
INGEST_MAX_TEKS = int(os.getenv("INGEST_MAX_TEKS", "400000"))
