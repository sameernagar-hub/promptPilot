from dataclasses import dataclass, field
from functools import lru_cache
from os import getenv
from pathlib import Path

from dotenv import load_dotenv


APP_DIR = Path(__file__).resolve().parents[1]
load_dotenv(APP_DIR / ".env")


def _csv_env(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _runtime_environment() -> str:
    return getenv("APP_ENV") or ("production" if getenv("VERCEL") else "development")


def _is_local_reference(value: str) -> bool:
    lowered = value.lower()
    return any(
        marker in lowered
        for marker in ("localhost", "127.0.0.1", "0.0.0.0", "[::1]", "::1")
    )


@dataclass(frozen=True)
class Settings:
    app_env: str = field(default_factory=_runtime_environment)
    database_url: str = getenv(
        "DATABASE_URL",
        "postgresql://prompt_engine:prompt_engine@localhost:5432/prompt_engine",
    )
    llm_provider: str = getenv("LLM_PROVIDER", "ollama")
    ollama_base_url: str = getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_scorer_timeout_seconds: float = float(getenv("OLLAMA_SCORER_TIMEOUT_SECONDS", "12"))
    default_model: str = getenv("DEFAULT_MODEL", "ollama/llama3.1:8b")
    allowed_origins: tuple[str, ...] = _csv_env(
        getenv(
            "ALLOWED_ORIGINS",
            ",".join(
                [
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                ]
            ),
        )
    )

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def validate_runtime(self) -> None:
        if not self.is_production:
            return
        failures: list[str] = []
        if _is_local_reference(self.database_url):
            failures.append("DATABASE_URL must use a managed production database")
        if self.llm_provider == "ollama":
            failures.append("LLM_PROVIDER must use a hosted provider in production")
        if not self.allowed_origins:
            failures.append("ALLOWED_ORIGINS must include the production web origin")
        if any(_is_local_reference(origin) for origin in self.allowed_origins):
            failures.append("ALLOWED_ORIGINS must not include localhost in production")
        if failures:
            raise RuntimeError(
                "Invalid production configuration: " + "; ".join(failures)
            )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_runtime()
    return settings
