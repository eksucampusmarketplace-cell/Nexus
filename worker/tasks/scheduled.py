"""Scheduled message tasks."""

import asyncio
from datetime import datetime

import croniter
from aiogram import Bot
from sqlalchemy import select

from shared.database import AsyncSessionLocal
from shared.models import ScheduledMessage
from worker.celery_app import celery_app


@celery_app.task
def check_scheduled_messages():
    """Check and process due scheduled messages."""
    async def _check():
        async with AsyncSessionLocal() as session:
            now = datetime.utcnow()
            result = await session.execute(
                select(ScheduledMessage).where(
                    ScheduledMessage.is_enabled == True,
                    ScheduledMessage.next_run <= now,
                )
            )
            messages = result.scalars().all()

            sent = 0
            for msg in messages:
                try:
                    await send_scheduled_message(msg)
                    sent += 1

                    # Update message
                    msg.last_run = now
                    msg.run_count += 1

                    if msg.schedule_type == "once":
                        msg.is_enabled = False
                    elif msg.cron_expression:
                        # Calculate next run
                        itr = croniter.croniter(msg.cron_expression, now)
                        msg.next_run = itr.get_next(datetime)
                    elif msg.days_of_week and msg.time_slot:
                        # Calculate next run based on days and time
                        msg.next_run = calculate_next_weekly_run(
                            msg.days_of_week, msg.time_slot, now
                        )

                    # Check if max runs reached
                    if msg.max_runs and msg.run_count >= msg.max_runs:
                        msg.is_enabled = False

                    # Check if end date reached
                    if msg.end_date and now.date() > msg.end_date:
                        msg.is_enabled = False

                except Exception as e:
                    print(f"Error sending scheduled message {msg.id}: {e}")

            await session.commit()
            return {"checked": len(messages), "sent": sent}

    return asyncio.run(_check())


async def send_scheduled_message(msg: ScheduledMessage):
    """Send a single scheduled message."""
    from shared.models import Group, BotInstance
    from bot.core.token_manager import token_manager

    async with AsyncSessionLocal() as session:
        # Get group
        result = await session.execute(
            select(Group).where(Group.id == msg.group_id)
        )
        group = result.scalar()

        if not group:
            return

        # Get bot token
        bot = token_manager.get_bot_for_group(msg.group_id)
        if not bot:
            # Use shared bot
            import os
            bot = Bot(token=os.getenv("BOT_TOKEN"))
            shared = True
        else:
            shared = False

        try:
            # Build buttons if any
            reply_markup = None
            if msg.has_buttons and msg.button_data:
                from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = [
                    [
                        InlineKeyboardButton(
                            text=btn.get("text", ""),
                            url=btn.get("url"),
                            callback_data=btn.get("callback_data"),
                        )
                        for btn in row
                    ]
                    for row in msg.button_data.get("buttons", [])
                ]
                reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

            # Send message
            if msg.media_file_id and msg.media_type:
                if msg.media_type == "photo":
                    await bot.send_photo(
                        chat_id=group.telegram_id,
                        photo=msg.media_file_id,
                        caption=msg.content,
                        reply_markup=reply_markup,
                    )
                elif msg.media_type == "video":
                    await bot.send_video(
                        chat_id=group.telegram_id,
                        video=msg.media_file_id,
                        caption=msg.content,
                        reply_markup=reply_markup,
                    )
                elif msg.media_type == "animation":
                    await bot.send_animation(
                        chat_id=group.telegram_id,
                        animation=msg.media_file_id,
                        caption=msg.content,
                        reply_markup=reply_markup,
                    )
                elif msg.media_type == "document":
                    await bot.send_document(
                        chat_id=group.telegram_id,
                        document=msg.media_file_id,
                        caption=msg.content,
                        reply_markup=reply_markup,
                    )
            else:
                await bot.send_message(
                    chat_id=group.telegram_id,
                    text=msg.content,
                    reply_markup=reply_markup,
                    parse_mode="HTML",
                )

            # Schedule deletion if self-destruct is set
            if msg.self_destruct_after:
                from worker.tasks.messages import delete_message
                delete_message.apply_async(
                    args=[os.getenv("BOT_TOKEN"), group.telegram_id, None],
                    countdown=msg.self_destruct_after,
                )

        finally:
            if shared:
                await bot.session.close()


def calculate_next_weekly_run(days_of_week: list, time_slot: str, now: datetime) -> datetime:
    """Calculate the next run time for weekly scheduled message."""
    hour, minute = map(int, time_slot.split(":"))
    current_weekday = now.weekday()

    # Find next available day
    next_day = None
    days_ahead = 0

    for i in range(8):  # Check up to 8 days ahead
        check_day = (current_weekday + i) % 7
        if check_day + 1 in days_of_week:  # days_of_week is 1-indexed (Monday=1)
            if i == 0:
                # Today, check if time has passed
                if now.hour < hour or (now.hour == hour and now.minute < minute):
                    next_day = now.date()
                    days_ahead = 0
                    break
            else:
                next_day = now.date() + __import__('datetime').timedelta(days=i)
                days_ahead = i
                break

    if next_day is None:
        next_day = now.date() + __import__('datetime').timedelta(days=7)

    return datetime.combine(next_day, datetime.strptime(time_slot, "%H:%M").time())
