"""Message-related tasks."""

import asyncio

from aiogram import Bot

from worker.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def send_scheduled_message(self, bot_token: str, chat_id: int, text: str, **kwargs):
    """Send a scheduled message."""
    async def _send():
        bot = Bot(token=bot_token)
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                **kwargs
            )
        finally:
            await bot.session.close()

    try:
        asyncio.run(_send())
        return {"success": True}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def delete_message(self, bot_token: str, chat_id: int, message_id: int):
    """Delete a message."""
    async def _delete():
        bot = Bot(token=bot_token)
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        finally:
            await bot.session.close()

    try:
        asyncio.run(_delete())
        return {"success": True}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def pin_message(self, bot_token: str, chat_id: int, message_id: int, notify: bool = True):
    """Pin a message."""
    async def _pin():
        bot = Bot(token=bot_token)
        try:
            await bot.pin_chat_message(
                chat_id=chat_id,
                message_id=message_id,
                disable_notification=not notify,
            )
        finally:
            await bot.session.close()

    try:
        asyncio.run(_pin())
        return {"success": True}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
