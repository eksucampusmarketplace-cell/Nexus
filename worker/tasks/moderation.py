"""Moderation-related tasks."""

import asyncio
from datetime import datetime

from sqlalchemy import select, update

from shared.database import AsyncSessionLocal
from shared.models import Member, Warning
from worker.celery_app import celery_app


@celery_app.task
def cleanup_expired_warnings():
    """Clean up expired warnings."""
    async def _cleanup():
        async with AsyncSessionLocal() as session:
            now = datetime.utcnow()
            result = await session.execute(
                select(Warning).where(
                    Warning.expires_at <= now,
                    Warning.deleted_at.is_(None),
                )
            )
            warnings = result.scalars().all()

            for warning in warnings:
                warning.deleted_at = now

                # Decrement warn count
                await session.execute(
                    update(Member)
                    .where(Member.id == warning.user_id)
                    .values(warn_count=Member.warn_count - 1)
                )

            await session.commit()
            return {"cleaned": len(warnings)}

    return asyncio.run(_cleanup())


@celery_app.task
def auto_unmute_users():
    """Auto-unmute users whose mute has expired."""
    async def _unmute():
        async with AsyncSessionLocal() as session:
            now = datetime.utcnow()
            result = await session.execute(
                select(Member).where(
                    Member.is_muted == True,
                    Member.mute_until <= now,
                )
            )
            members = result.scalars().all()

            for member in members:
                member.is_muted = False
                member.mute_until = None

            await session.commit()
            return {"unmuted": len(members)}

    return asyncio.run(_unmute())


@celery_app.task
def auto_unban_users():
    """Auto-unban users whose ban has expired."""
    async def _unban():
        async with AsyncSessionLocal() as session:
            now = datetime.utcnow()
            result = await session.execute(
                select(Member).where(
                    Member.is_banned == True,
                    Member.ban_until <= now,
                )
            )
            members = result.scalars().all()

            for member in members:
                member.is_banned = False
                member.ban_until = None

            await session.commit()
            return {"unbanned": len(members)}

    return asyncio.run(_unban())
