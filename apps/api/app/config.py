from dataclasses import dataclass
from functools import lru_cache
from os import getenv
from pathlib import Path

from dotenv import load_dotenv


APP_DIR = Path(__file__).resolve().parents[1]
load_dotenv(APP_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    database_url: str = getenv(
        "DATABASE_URL",
        "postgresql://prompt_engine:prompt_engine@localhost:5432/prompt_engine",
    )
    llm_provider: str = getenv("LLM_PROVIDER", "ollama")
    ollama_base_url: str = getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    default_model: str = getenv("DEFAULT_MODEL", "ollama/llama3.1:8b")


@lru_cache
def get_settings() -> Settings:
    return Settings()
