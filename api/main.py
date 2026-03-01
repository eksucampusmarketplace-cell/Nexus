"""FastAPI main application."""

import logging
import os
from contextlib import asynccontextmanager

from aiogram import Bot
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

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
    logger.info("=" * 50)
    logger.info("Nexus API Starting Up")
    logger.info("=" * 50)
    logger.info(f"Python Version: {os.sys.version}")
    logger.info(f"Working Directory: {os.getcwd()}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    # Startup
    logger.info("Initializing database...")
    await init_db()
    
    logger.info("Connecting to Redis...")
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
    
    # Check Mini App files
    dist_path = os.path.join(os.getcwd(), "mini-app", "dist")
    if os.path.exists(dist_path):
        logger.info(f"Mini App dist directory found at: {dist_path}")
        file_count = sum(1 for _, _, files in os.walk(dist_path) for _ in files)
        logger.info(f"Mini App contains {file_count} files")
    else:
        logger.warning(f"Mini App dist directory NOT found at: {dist_path}")
        logger.warning("Mini App will not be available via /mini-app endpoint")
    
    logger.info("Startup complete!")
    logger.info("=" * 50)

    yield

    # Shutdown
    logger.info("Shutting down Nexus API...")
    await module_registry.unload_all()
    await close_redis()
    logger.info("Shutdown complete")


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


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging."""
    try:
        logger.info(f"Request: {request.method} {request.url.path}")
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url.path} - Error: {e}")
        raise


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# Mount Mini App static files if dist exists
dist_path = os.path.join(os.getcwd(), "mini-app", "dist")
assets_path = os.path.join(dist_path, "assets")

if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    logger.info(f"Mini App assets mounted at /assets")


# Import and include routers
from api.routers import (
    advanced,
    analytics,
    auth,
    bot_builder,
    economy,
    federations,
    groups,
    members,
    modules,
    scheduled,
    toggles,
    webhooks,
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


@app.get("/mini-app", response_class=HTMLResponse, include_in_schema=False)
@app.get("/mini-app/", response_class=HTMLResponse, include_in_schema=False)
async def serve_mini_app():
    """Serve Mini App at /mini-app."""
    index_path = os.path.join(os.getcwd(), "mini-app", "dist", "index.html")
    
    if not os.path.exists(index_path):
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Nexus Mini App</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: #0f172a;
                        color: #fff;
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0;
                    }
                    .container {
                        text-align: center;
                        padding: 2rem;
                    }
                    h1 { color: #3b82f6; margin-bottom: 1rem; }
                    p { color: #94a3b8; margin-bottom: 0.5rem; }
                    code {
                        background: #1e293b;
                        padding: 0.5rem 1rem;
                        border-radius: 0.5rem;
                        display: inline-block;
                        margin-top: 1rem;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Nexus Mini App</h1>
                    <p>The Mini App is not available at this endpoint.</p>
                    <p>Access the Mini App from:</p>
                    <ul style="text-align: left; display: inline-block; color: #94a3b8;">
                        <li>Telegram: Open from a Telegram group with Nexus bot</li>
                        <li>Separate Service: <a href="https://nexus-mini-app.onrender.com" style="color: #3b82f6;">nexus-mini-app.onrender.com</a></li>
                    </ul>
                </div>
            </body>
            </html>
        """,
            status_code=200
        )
    
    with open(index_path, "r") as f:
        html_content = f.read()
    
    return HTMLResponse(content=html_content)


@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables."""
    env_vars = {
        "BOT_TOKEN": bool(os.getenv("BOT_TOKEN")),
        "WEBHOOK_URL": os.getenv("WEBHOOK_URL"),
        "MINI_APP_URL": os.getenv("MINI_APP_URL"),
        "DATABASE_URL": bool(os.getenv("DATABASE_URL")),
        "REDIS_URL": bool(os.getenv("REDIS_URL")),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "unknown"),
        "PYTHONPATH": os.getenv("PYTHONPATH"),
    }
    return {
        "environment": env_vars,
        "all_env_keys": sorted([k for k in os.environ.keys() if not k.startswith("_")]),
    }


@app.get("/debug/mini-app-check")
async def debug_mini_app():
    """Debug endpoint to check Mini App availability."""
    import httpx
    import socket
    
    mini_app_url = os.getenv("MINI_APP_URL")
    if not mini_app_url:
        return {
            "error": "MINI_APP_URL not set",
            "suggestion": "Check render.yaml environment variables"
        }
    
    results = {
        "mini_app_url": mini_app_url,
        "dns_resolution": None,
        "http_response": None,
        "error": None,
    }
    
    # Check DNS resolution
    try:
        hostname = mini_app_url.replace("https://", "").replace("http://", "").split("/")[0]
        ip = socket.gethostbyname(hostname)
        results["dns_resolution"] = {"success": True, "hostname": hostname, "ip": ip}
    except Exception as e:
        results["dns_resolution"] = {"success": False, "error": str(e)}
    
    # Check HTTP response
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(mini_app_url)
            results["http_response"] = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_length": len(response.content),
                "content_preview": response.text[:200] if len(response.text) < 200 else response.text[:200] + "...",
            }
    except Exception as e:
        results["http_response"] = {"success": False, "error": str(e)}
        results["error"] = str(e)
    
    return results


@app.get("/debug/static-files")
async def debug_static_files():
    """Debug endpoint to check if static files exist."""
    dist_path_local = os.path.join(os.getcwd(), "mini-app", "dist")
    
    results = {
        "current_working_dir": os.getcwd(),
        "dist_path": dist_path_local,
        "dist_exists": os.path.exists(dist_path_local),
        "dist_is_dir": os.path.isdir(dist_path_local) if os.path.exists(dist_path_local) else None,
        "mini_app_exists": os.path.exists(os.path.join(os.getcwd(), "mini-app")),
    }
    
    if os.path.exists(dist_path_local) and os.path.isdir(dist_path_local):
        try:
            files = []
            for root, dirs, filenames in os.walk(dist_path_local):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    relpath = os.path.relpath(filepath, dist_path_local)
                    files.append({
                        "path": relpath,
                        "size": os.path.getsize(filepath),
                    })
            results["files"] = sorted(files, key=lambda x: x["path"])
            results["total_files"] = len(files)
        except Exception as e:
            results["file_list_error"] = str(e)
    
    return results


@app.get("/debug/summary")
async def debug_summary():
    """Comprehensive debug summary endpoint."""
    import httpx
    import socket
    
    dist_path_local = os.path.join(os.getcwd(), "mini-app", "dist")
    
    summary = {
        "api_status": {
            "service": "Nexus API",
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "working_dir": os.getcwd(),
        },
        "environment": {
            "BOT_TOKEN_set": bool(os.getenv("BOT_TOKEN")),
            "WEBHOOK_URL": os.getenv("WEBHOOK_URL"),
            "MINI_APP_URL": os.getenv("MINI_APP_URL"),
            "DATABASE_URL_set": bool(os.getenv("DATABASE_URL")),
            "REDIS_URL_set": bool(os.getenv("REDIS_URL")),
        },
        "mini_app_files": {
            "dist_path": dist_path_local,
            "exists": os.path.exists(dist_path_local),
            "is_directory": os.path.isdir(dist_path_local) if os.path.exists(dist_path_local) else None,
        },
        "mini_app_service": {},
        "recommendations": [],
    }
    
    # Check static files
    if os.path.exists(dist_path_local):
        try:
            files = []
            for root, dirs, filenames in os.walk(dist_path_local):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    relpath = os.path.relpath(filepath, dist_path_local)
                    files.append(relpath)
            summary["mini_app_files"]["file_count"] = len(files)
            summary["mini_app_files"]["sample_files"] = sorted(files)[:5]
        except Exception as e:
            summary["mini_app_files"]["error"] = str(e)
    
    # Check Mini App service
    mini_app_url = os.getenv("MINI_APP_URL")
    if mini_app_url:
        try:
            hostname = mini_app_url.replace("https://", "").replace("http://", "").split("/")[0]
            ip = socket.gethostbyname(hostname)
            summary["mini_app_service"]["dns"] = {"success": True, "ip": ip}
        except Exception as e:
            summary["mini_app_service"]["dns"] = {"success": False, "error": str(e)}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(mini_app_url)
                summary["mini_app_service"]["http"] = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                }
        except Exception as e:
            summary["mini_app_service"]["http"] = {"success": False, "error": str(e)}
    else:
        summary["mini_app_service"]["error"] = "MINI_APP_URL not set"
        summary["recommendations"].append("Set MINI_APP_URL environment variable")
    
    # Generate recommendations
    if not summary["mini_app_files"]["exists"]:
        summary["recommendations"].append("Mini App dist directory not found - run 'cd mini-app && bun run build'")
    
    if summary.get("mini_app_service", {}).get("http", {}).get("status_code") == 404:
        summary["recommendations"].append("Mini App service returns 404 - check Render static service deployment")
        summary["recommendations"].append("Verify staticPublishPath in render.yaml points to ./mini-app/dist")
        summary["recommendations"].append("Check Render build logs for nexus-mini-app service")
    
    if summary.get("mini_app_service", {}).get("http", {}).get("success") == False:
        summary["recommendations"].append("Mini App service unreachable - check service status on Render")
    
    return summary
