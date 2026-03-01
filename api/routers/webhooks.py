"""Webhook handlers for Telegram updates."""

import os
from typing import Any, Optional

from aiogram import Bot
from aiogram.types import Update
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks

from bot.core.middleware import pipeline
from bot.core.token_manager import token_manager

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN is not set in webhooks.py at module level")
else:
    print(f"DEBUG: BOT_TOKEN is set in webhooks.py (length: {len(BOT_TOKEN)})")

router = APIRouter()

# Cached bot instance and identity for shared bot
_shared_bot: Optional[Bot] = None
_shared_identity: Optional[Any] = None


async def get_shared_bot():
    """Get or create the cached shared bot instance."""
    global _shared_bot, _shared_identity
    
    if _shared_bot is None:
        if not BOT_TOKEN:
            raise ValueError("BOT_TOKEN not configured")
        
        _shared_bot = Bot(token=BOT_TOKEN)
        bot_info = await _shared_bot.get_me()
        
        from bot.core.context import BotIdentity
        _shared_identity = BotIdentity(
            bot_id=bot_info.id,
            username=bot_info.username,
            name=bot_info.first_name,
            token_hash="shared",
        )
    
    return _shared_bot, _shared_identity


async def process_update(bot: Bot, bot_identity: Any, update: Update):
    """Process a single update through the pipeline."""
    try:
        await pipeline.process_update(bot, bot_identity, update)
    except Exception as e:
        print(f"Error processing update: {e}")


@router.post("/shared")
async def shared_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Webhook endpoint for shared bot."""
    try:
        data = await request.json()
        update = Update(**data)

        if not BOT_TOKEN:
            raise HTTPException(status_code=500, detail="Bot token not configured")

        bot, identity = await get_shared_bot()

        # Process in background
        background_tasks.add_task(process_update, bot, identity, update)

        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
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
