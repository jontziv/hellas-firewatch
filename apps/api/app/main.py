from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .db import init_db, get_session
from .seed import seed_if_empty
from .routes import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(title="Hellas Firewatch", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    web_dir = Path(__file__).resolve().parents[2] / "web" / "static"
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")

    @app.on_event("startup")
    def _startup() -> None:
        init_db()
        with get_session() as s:
            seed_if_empty(s)

    return app


app = create_app()
