"""FastAPI main application."""

import logging
import os
from contextlib import asynccontextmanager

from aiogram import Bot
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from bot.core.middleware import pipeline, setup_pipeline
from bot.core.module_registry import module_registry
from shared.database import init_db
from shared.redis_client import close_redis, get_redis

logger = logging.getLogger(__name__)


async def setup_telegram_webhook():
    """Set up Telegram webhook on startup."""
    bot_token = os.getenv("BOT_TOKEN")
    webhook_url = os.getenv("WEBHOOK_URL")
    
    if not bot_token:
        logger.error("BOT_TOKEN not set - webhook cannot be configured!")
        return
    
    if not webhook_url:
        logger.warning("WEBHOOK_URL not set - skipping webhook configuration")
        return
    
    try:
        # Construct the webhook endpoint URL
        base_url = webhook_url.split("/webhook")[0]
        shared_webhook = f"{base_url}/webhook/shared"
        
        if not shared_webhook.startswith("http"):
            shared_webhook = f"https://{shared_webhook}"
        
        logger.info(f"Setting Telegram webhook to: {shared_webhook}")
        
        bot = Bot(token=bot_token)
        
        # Delete any existing webhook first
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Set the new webhook
        await bot.set_webhook(
            url=shared_webhook,
            allowed_updates=[
                "message",
                "edited_message",
                "callback_query",
                "inline_query",
                "chat_member",
                "my_chat_member",
                "poll",
                "poll_answer",
                "chat_join_request",
                "message_reaction",
            ],
        )
        
        # Verify webhook is set
        info = await bot.get_webhook_info()
        logger.info(f"Webhook configured successfully: {info.url}")
        
        await bot.session.close()
        
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")


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

    # Set up Telegram webhook (critical for Render single-service deployment)
    logger.info("Setting up Telegram webhook...")
    await setup_telegram_webhook()
    logger.info("Startup complete!")

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
