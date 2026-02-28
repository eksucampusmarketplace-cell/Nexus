"""Economy-related tasks."""

import asyncio
from datetime import datetime

from sqlalchemy import select

from shared.database import AsyncSessionLocal
from shared.models import Member, Wallet
from worker.celery_app import celery_app


@celery_app.task
def process_daily_activity():
    """Process daily activity bonuses."""
    async def _process():
        async with AsyncSessionLocal() as session:
            # Get all active members
            result = await session.execute(
                select(Member).where(Member.last_active >= datetime.utcnow().replace(hour=0, minute=0, second=0))
            )
            members = result.scalars().all()

            processed = 0
            for member in members:
                # Award XP for daily activity
                member.xp += 5
                processed += 1

            await session.commit()
            return {"processed": processed}

    return asyncio.run(_process())


@celery_app.task
def award_daily_bonus(user_id: int, group_id: int):
    """Award daily bonus to a user."""
    async def _award():
        async with AsyncSessionLocal() as session:
            # Get or create wallet
            result = await session.execute(
                select(Wallet).where(
                    Wallet.user_id == user_id,
                    Wallet.group_id == group_id,
                )
            )
            wallet = result.scalar()

            if not wallet:
                wallet = Wallet(
                    user_id=user_id,
                    group_id=group_id,
                )
                session.add(wallet)

            # Get economy config for daily bonus amount
            from shared.models import EconomyConfig
            result = await session.execute(
                select(EconomyConfig).where(EconomyConfig.group_id == group_id)
            )
            config = result.scalar()

            daily_bonus = config.daily_bonus if config else 100

            wallet.balance += daily_bonus
            wallet.total_earned += daily_bonus

            await session.commit()
            return {"awarded": daily_bonus, "new_balance": wallet.balance}

    return asyncio.run(_award())


@celery_app.task
def process_xp_gain(user_id: int, group_id: int, amount: int):
    """Process XP gain and level up."""
    async def _process():
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Member).where(
                    Member.user_id == user_id,
                    Member.group_id == group_id,
                )
            )
            member = result.scalar()

            if not member:
                return {"error": "Member not found"}

            old_level = member.level
            member.xp += amount

            # Check for level up (simple formula: level * 100 XP needed)
            new_level = (member.xp // 100) + 1
            if new_level > old_level:
                member.level = new_level
                leveled_up = True
            else:
                leveled_up = False

            await session.commit()
            return {
                "xp_gained": amount,
                "total_xp": member.xp,
                "new_level": member.level,
                "leveled_up": leveled_up,
            }

    return asyncio.run(_process())
