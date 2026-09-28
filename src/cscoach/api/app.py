"""FastAPI service (M10.2). Run: uvicorn cscoach.api.app:app"""

from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI
except ImportError:  # pragma: no cover
    FastAPI = None

app: Any = FastAPI(title="cscoach") if FastAPI else None

if app is not None:

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}
