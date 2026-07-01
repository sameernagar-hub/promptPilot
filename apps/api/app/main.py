from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_database
from app.routers import health, imports, intelligence, profile, prompts, sessions
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    del app
    init_database()
    yield


app = FastAPI(
    title="PromptPilot API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(imports.router)
app.include_router(intelligence.router)
app.include_router(profile.router)
app.include_router(sessions.router)
app.include_router(prompts.router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": "promptpilot-api",
        "status": "ok",
    }
