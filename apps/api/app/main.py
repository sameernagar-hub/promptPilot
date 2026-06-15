from fastapi import FastAPI

app = FastAPI(
    title="PromptPilot API",
    version="0.1.0",
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": "promptpilot-api",
        "status": "ok",
    }
