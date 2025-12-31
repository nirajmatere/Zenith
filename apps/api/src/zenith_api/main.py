from __future__ import annotations

from fastapi import FastAPI

from zenith_api.auth.router import router as auth_router
from zenith_api.routers.health import router as health_router
from zenith_api.routers.orgs import router as orgs_router

app = FastAPI(title="Zenith API")

app.include_router(health_router)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(orgs_router, prefix="/orgs", tags=["orgs"])
