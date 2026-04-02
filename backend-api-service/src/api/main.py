from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import load_settings
from api.deps import build_repositories
from api.guidance.router import router as guidance_router
from api.ingest.router import router as ingest_router
from api.realtime.router import router as realtime_router


def create_app(*, data_root: str | Path | None = None) -> FastAPI:
    settings = load_settings(data_root=data_root)
    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.state.repositories = build_repositories(settings.data_root)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz", tags=["ops"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(ingest_router, prefix=settings.api_prefix)
    app.include_router(guidance_router, prefix=settings.api_prefix)
    app.include_router(realtime_router, prefix=settings.api_prefix)
    return app


app = create_app()
