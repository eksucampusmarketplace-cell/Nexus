"""FastAPI main application."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.database import init_db
from shared.redis_client import close_redis, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_db()
    await get_redis()

    yield

    # Shutdown
    await close_redis()


app = FastAPI(
    title="Nexus API",
    description="REST API for Nexus - The Ultimate Telegram Bot Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# Import and include routers
from api.routers import (
    analytics,
    auth,
    economy,
    federations,
    groups,
    members,
    modules,
    scheduled,
    webhooks,
    bot_builder,
    advanced,
    toggles,
)

app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(groups.router, prefix="/api/v1", tags=["groups"])
app.include_router(members.router, prefix="/api/v1", tags=["members"])
app.include_router(modules.router, prefix="/api/v1", tags=["modules"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(economy.router, prefix="/api/v1", tags=["economy"])
app.include_router(federations.router, prefix="/api/v1", tags=["federations"])
app.include_router(scheduled.router, prefix="/api/v1", tags=["scheduled"])
app.include_router(bot_builder.router, prefix="/api/v1", tags=["Bot Builder"])
app.include_router(advanced.router, prefix="/api/v1", tags=["Advanced Features"])
app.include_router(toggles.router, prefix="/api/v1", tags=["toggles"])
app.include_router(webhooks.router, prefix="", tags=["webhooks"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Nexus API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
