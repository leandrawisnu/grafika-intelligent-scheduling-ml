import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-placeholder")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")
