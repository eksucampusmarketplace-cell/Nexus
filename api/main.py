"""FastAPI main application."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from bot.core.middleware import pipeline, setup_pipeline
from bot.core.module_registry import module_registry
from shared.database import init_db
from shared.redis_client import close_redis, get_redis

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_db()
    await get_redis()

    # Set up middleware pipeline
    logger.info("Setting up middleware pipeline...")
    setup_pipeline()

    # Load bot modules for webhook processing
    logger.info("Loading bot modules...")
    try:
        await module_registry.load_all()
        
        # Check dependencies and conflicts
        missing_deps = module_registry.check_dependencies()
        if missing_deps:
            for name, deps in missing_deps.items():
                logger.warning(f"Module {name} missing dependencies: {deps}")

        conflicts = module_registry.check_conflicts()
        if conflicts:
            for name, confs in conflicts.items():
                logger.warning(f"Module {name} conflicts with: {confs}")

        # Register modules with pipeline
        for module in module_registry.get_all_modules():
            pipeline.add_module(module)

        logger.info(f"Loaded {len(module_registry.get_all_modules())} modules")
    except Exception as e:
        logger.warning(f"Module loading skipped (DB unavailable): {e}")

    yield

    # Shutdown
    await module_registry.unload_all()
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
app.include_router(webhooks.router, prefix="/webhook", tags=["webhooks"])


@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    """Root endpoint."""
    return {
        "name": "Nexus API",
        "version": "1.0.0",
        "status": "running",
    }


@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
