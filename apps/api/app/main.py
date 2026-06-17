from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_database
from app.routers import health, imports, profile, prompts, sessions


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
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(imports.router)
app.include_router(profile.router)
app.include_router(sessions.router)
app.include_router(prompts.router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": "promptpilot-api",
        "status": "ok",
    }
