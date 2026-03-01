"""Webhook handlers for Telegram updates."""

import json
import logging
import os
from datetime import datetime
from typing import Any, Optional

from aiogram import Bot
from aiogram.types import Update
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks

from bot.core.middleware import pipeline
from bot.core.module_registry import module_registry
from bot.core.token_manager import token_manager

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN:
    logger.error("BOT_TOKEN is not set!")
else:
    logger.info(f"BOT_TOKEN is set (length: {len(BOT_TOKEN)})")

if WEBHOOK_URL:
    logger.info(f"WEBHOOK_URL is set: {WEBHOOK_URL}")
else:
    logger.warning("WEBHOOK_URL is not set - webhook mode may not work")

router = APIRouter()

# Cached bot instance and identity for shared bot
_shared_bot: Optional[Bot] = None
_shared_identity: Optional[Any] = None

# Debug stats
_webhook_count = 0
_last_update: Optional[dict] = None
_last_error: Optional[str] = None


async def get_shared_bot():
    """Get or create the cached shared bot instance."""
    global _shared_bot, _shared_identity
    
    if _shared_bot is None:
        if not BOT_TOKEN:
            raise ValueError("BOT_TOKEN not configured")
        
        logger.info("Creating new Bot instance...")
        _shared_bot = Bot(token=BOT_TOKEN)
        bot_info = await _shared_bot.get_me()
        
        from bot.core.context import BotIdentity
        _shared_identity = BotIdentity(
            bot_id=bot_info.id,
            username=bot_info.username,
            name=bot_info.first_name,
            token_hash="shared",
        )
        logger.info(f"Bot initialized: @{bot_info.username} (ID: {bot_info.id})")
    
    return _shared_bot, _shared_identity


async def process_update(bot: Bot, bot_identity: Any, update: Update):
    """Process a single update through the pipeline."""
    global _last_error
    
    try:
        # Log update type
        update_type = None
        if update.message:
            update_type = "message"
            if update.message.text:
                logger.info(f"Processing message: '{update.message.text[:50]}...' from chat {update.message.chat.id}")
        elif update.callback_query:
            update_type = "callback_query"
            logger.info(f"Processing callback from chat {update.callback_query.message.chat.id if update.callback_query.message else 'unknown'}")
        elif update.inline_query:
            update_type = "inline_query"
        elif update.edited_message:
            update_type = "edited_message"
        else:
            update_type = type(update).__name__
            logger.info(f"Processing update type: {update_type}")
        
        result = await pipeline.process_update(bot, bot_identity, update)
        logger.info(f"Pipeline result: {result}")
        
    except Exception as e:
        logger.exception(f"Error processing update: {e}")
        _last_error = f"{datetime.utcnow().isoformat()}: {str(e)}"


@router.post("/shared")
async def shared_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Webhook endpoint for shared bot."""
    global _webhook_count, _last_update
    
    try:
        data = await request.json()
        _last_update = data
        
        # Log incoming update
        logger.info(f"Received webhook update #{_webhook_count + 1}")
        
        update = Update(**data)

        if not BOT_TOKEN:
            logger.error("BOT_TOKEN not configured!")
            raise HTTPException(status_code=500, detail="Bot token not configured")

        bot, identity = await get_shared_bot()

        # Process in background
        background_tasks.add_task(process_update, bot, identity, update)
        _webhook_count += 1

        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{token_hash}")
async def custom_webhook(
    token_hash: str,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Webhook endpoint for custom bot tokens."""
    try:
        # Get bot instance for this token
        bot = token_manager.get_bot(token_hash)
        identity = token_manager.get_identity(token_hash)

        if not bot or not identity:
            raise HTTPException(status_code=404, detail="Bot not found")

        data = await request.json()
        update = Update(**data)

        # Process in background
        background_tasks.add_task(process_update, bot, identity, update)

        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/info")
async def webhook_info():
    """Get webhook information."""
    try:
        bot, _ = await get_shared_bot()
        info = await bot.get_webhook_info()
        return {
            "url": info.url,
            "has_custom_certificate": info.has_custom_certificate,
            "pending_update_count": info.pending_update_count,
            "ip_address": info.ip_address,
            "last_error_date": info.last_error_date,
            "last_error_message": info.last_error_message,
            "max_connections": info.max_connections,
            "allowed_updates": info.allowed_updates,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug")
async def debug_info():
    """Debug endpoint to diagnose webhook and command issues."""
    global _webhook_count, _last_update, _last_error, _shared_bot, _shared_identity
    
    # Get webhook info from Telegram
    webhook_info = None
    webhook_error = None
    try:
        if BOT_TOKEN:
            bot = Bot(token=BOT_TOKEN)
            info = await bot.get_webhook_info()
            webhook_info = {
                "url": info.url,
                "pending_update_count": info.pending_update_count,
                "last_error_date": info.last_error_date,
                "last_error_message": info.last_error_message,
                "allowed_updates": info.allowed_updates,
            }
            await bot.session.close()
    except Exception as e:
        webhook_error = str(e)
    
    # Get pipeline info
    pipeline_info = {
        "middleware_count": len(pipeline._middlewares),
        "module_count": len(pipeline._modules),
        "modules": [m.name for m in pipeline._modules] if pipeline._modules else [],
    }
    
    # Get module registry info
    registry_info = {
        "registered_modules": list(module_registry._modules.keys()),
        "module_count": len(module_registry._modules),
    }
    
    # Expected endpoint
    expected_webhook_url = None
    if WEBHOOK_URL:
        base_url = WEBHOOK_URL.split("/webhook")[0]
        expected_webhook_url = f"{base_url}/webhook/shared"
    
    return {
        "status": "debug",
        "timestamp": datetime.utcnow().isoformat(),
        "config": {
            "bot_token_set": bool(BOT_TOKEN),
            "webhook_url_set": bool(WEBHOOK_URL),
            "webhook_url": WEBHOOK_URL,
            "expected_webhook_endpoint": expected_webhook_url,
        },
        "cached_bot": {
            "initialized": _shared_bot is not None,
            "identity": {
                "bot_id": _shared_identity.bot_id if _shared_identity else None,
                "username": _shared_identity.username if _shared_identity else None,
            } if _shared_identity else None,
        },
        "webhook_stats": {
            "total_received": _webhook_count,
            "last_update": _last_update,
        },
        "telegram_webhook_info": webhook_info,
        "telegram_webhook_error": webhook_error,
        "pipeline": pipeline_info,
        "module_registry": registry_info,
        "last_error": _last_error,
    }


@router.post("/test")
async def test_webhook(request: Request):
    """Test endpoint to simulate a webhook update."""
    try:
        data = await request.json()
        logger.info(f"Test webhook received: {json.dumps(data, indent=2)}")
        
        # Check if we can process it
        if not BOT_TOKEN:
            return {"error": "BOT_TOKEN not configured"}
        
        bot, identity = await get_shared_bot()
        
        # Parse as Update
        update = Update(**data)
        
        # Process synchronously for testing
        result = await pipeline.process_update(bot, identity, update)
        
        return {
            "ok": True,
            "result": result,
            "message_received": update.message.text if update.message else None,
            "chat_id": update.message.chat.id if update.message else None,
            "chat_type": update.message.chat.type if update.message else None,
        }
    except Exception as e:
        logger.exception(f"Test webhook error: {e}")
        return {"error": str(e)}
