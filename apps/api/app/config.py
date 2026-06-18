from dataclasses import dataclass
from functools import lru_cache
from os import getenv
from pathlib import Path

from dotenv import load_dotenv


APP_DIR = Path(__file__).resolve().parents[1]
load_dotenv(APP_DIR / ".env")


def _csv_env(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    database_url: str = getenv(
        "DATABASE_URL",
        "postgresql://prompt_engine:prompt_engine@localhost:5432/prompt_engine",
    )
    llm_provider: str = getenv("LLM_PROVIDER", "ollama")
    ollama_base_url: str = getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    default_model: str = getenv("DEFAULT_MODEL", "ollama/llama3.1:8b")
    allowed_origins: tuple[str, ...] = _csv_env(
        getenv(
            "ALLOWED_ORIGINS",
            ",".join(
                [
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                    "http://localhost:3001",
                    "http://127.0.0.1:3001",
                ]
            ),
        )
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
