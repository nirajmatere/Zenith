from __future__ import annotations

from fastapi import FastAPI

from zenith_api.routers.health import router as health_router

app = FastAPI(title="Zenith API")

app.include_router(health_router)
