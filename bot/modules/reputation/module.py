"""Reputation module - User reputation system with +rep and -rep."""

from datetime import datetime, timedelta
from typing import Optional

from aiogram.types import Message
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class ReputationConfig(BaseModel):
    """Configuration for reputation module."""
    cooldown: int = 300  # 5 minutes
    daily_limit: int = 10
    max_rep: int = 100
    min_rep: int = -100


class ReputationModule(NexusModule):
    """Reputation system with +rep and -rep."""

    name = "reputation"
    version = "1.0.0"
    author = "Nexus Team"
    description = "User reputation system with positive and negative reputation"
    category = ModuleCategory.COMMUNITY

    config_schema = ReputationConfig
    default_config = ReputationConfig().dict()

    commands = [
        CommandDef(
            name="rep",
            description="Give reputation to a user",
            admin_only=False,
        ),
        CommandDef(
            name="+rep",
            description="Give positive reputation",
            admin_only=False,
        ),
        CommandDef(
            name="-rep",
            description="Give negative reputation",
            admin_only=False,
        ),
        CommandDef(
            name="reputation",
            description="View user's reputation",
            admin_only=False,
            aliases=["repcheck"],
        ),
        CommandDef(
            name="repleaderboard",
            description="View reputation leaderboard",
            admin_only=False,
            aliases=["replb"],
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("rep", self.cmd_rep)
        self.register_command("+rep", self.cmd_rep)
        self.register_command("-rep", self.cmd_rep)
        self.register_command("reputation", self.cmd_reputation)
        self.register_command("repcheck", self.cmd_reputation)
        self.register_command("repleaderboard", self.cmd_repleaderboard)
        self.register_command("replb", self.cmd_repleaderboard)

    def _get_user_id(self, ctx: NexusContext, args: list) -> Optional[int]:
        """Extract user ID from message or args."""
        # Try reply first
        if ctx.replied_to and ctx.replied_to.from_user:
            return ctx.replied_to.from_user.id

        # Try mention
        if ctx.message.entities:
            for entity in ctx.message.entities:
                if entity.type == "text_mention":
                    return entity.user.id

        # Try username
        text = ctx.message.text or ""
        if args:
            username = args[0].lstrip("@")
            if username:
                if ctx.db:
                    from shared.models import User
                    result = ctx.db.execute(
                        f"SELECT telegram_id FROM users WHERE username = '{username}' LIMIT 1"
                    )
                    row = result.fetchone()
                    if row:
                        return row[0]

        return None

    async def _get_reputation(self, ctx: NexusContext, user_id: int) -> Optional[int]:
        """Get user's reputation score."""
        from shared.models import Reputation

        result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {user_id} LIMIT 1"
        )
        user_db_id = result.scalar()

        if not user_db_id:
            return None

        result = ctx.db.execute(
            f"""
            SELECT score
            FROM reputation
            WHERE user_id = {user_db_id} AND group_id = {ctx.group.id}
            LIMIT 1
            """
        )
        row = result.fetchone()

        return row[0] if row else 0

    async def _check_cooldown(self, ctx: NexusContext, user_id: int, to_user_id: int) -> Optional[int]:
        """Check if user is on cooldown for giving reputation."""
        from shared.models import ReputationLog

        result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {user_id} LIMIT 1"
        )
        from_db_id = result.scalar()

        result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {to_user_id} LIMIT 1"
        )
        to_db_id = result.scalar()

        config = ReputationConfig(**ctx.group.module_configs.get("reputation", {}))

        # Check cooldown
        result = ctx.db.execute(
            f"""
            SELECT last_given_at
            FROM reputation_logs
            WHERE from_user_id = {from_db_id}
              AND to_user_id = {to_db_id}
              AND group_id = {ctx.group.id}
            ORDER BY last_given_at DESC
            LIMIT 1
            """
        )
        row = result.fetchone()

        if row:
            last_given = row[0]
            elapsed = (datetime.utcnow() - last_given).total_seconds()
            if elapsed < config.cooldown:
                return int(config.cooldown - elapsed)

        # Check daily limit
        result = ctx.db.execute(
            f"""
            SELECT COUNT(*)
            FROM reputation_logs
            WHERE from_user_id = {from_db_id}
              AND group_id = {ctx.group.id}
              AND DATE(last_given_at) = CURRENT_DATE
            """
        )
        count = result.scalar()

        if count >= config.daily_limit:
            return -1  # Daily limit reached

        return None

    async def cmd_rep(self, ctx: NexusContext):
        """Give reputation to a user."""
        config = ReputationConfig(**ctx.group.module_configs.get("reputation", {}))

        text = ctx.message.text or ""
        is_positive = not text.startswith("/-rep")

        target_id = self._get_user_id(ctx, [])

        if not target_id:
            await ctx.reply("❌ Reply to a message or mention a user to give reputation")
            return

        if target_id == ctx.user.telegram_id:
            await ctx.reply("❌ You can't give reputation to yourself!")
            return

        # Check cooldown
        cooldown = await self._check_cooldown(ctx, ctx.user.telegram_id, target_id)
        if cooldown:
            if cooldown == -1:
                await ctx.reply(f"❌ You've reached your daily limit of {config.daily_limit} reputation points!")
            else:
                minutes = cooldown // 60
                seconds = cooldown % 60
                await ctx.reply(
                    f"⏰ You can't give reputation yet!\n"
                    f"Wait {minutes}m {seconds}s"
                )
            return

        # Get current reputation
        current_rep = await self._get_reputation(ctx, target_id) or 0

        # Calculate new reputation
        delta = 1 if is_positive else -1
        new_rep = current_rep + delta

        # Enforce limits
        if new_rep > config.max_rep:
            await ctx.reply(f"❌ User has reached maximum reputation ({config.max_rep})")
            return

        if new_rep < config.min_rep:
            await ctx.reply(f"❌ User has reached minimum reputation ({config.min_rep})")
            return

        # Update reputation
        from shared.models import Reputation, ReputationLog

        from_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
        )
        from_db_id = from_result.scalar()

        to_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {target_id} LIMIT 1"
        )
        to_db_id = to_result.scalar()

        # Update or create reputation
        result = ctx.db.execute(
            f"""
            SELECT id
            FROM reputation
            WHERE user_id = {to_db_id} AND group_id = {ctx.group.id}
            LIMIT 1
            """
        )
        row = result.fetchone()

        if row:
            ctx.db.execute(
                f"""
                UPDATE reputation
                SET score = {new_rep},
                    last_given_at = NOW()
                WHERE id = {row[0]}
                """
            )
        else:
            rep = Reputation(
                user_id=to_db_id,
                group_id=ctx.group.id,
                score=new_rep,
            )
            ctx.db.add(rep)

        # Add log
        log = ReputationLog(
            group_id=ctx.group.id,
            from_user_id=from_db_id,
            to_user_id=to_db_id,
            delta=delta,
            reason="manual" if text.startswith("/rep") else "quick",
        )
        ctx.db.add(log)
        ctx.db.commit()

        # Send notification
        icon = "👍" if is_positive else "👎"
        action = "gave" if is_positive else "took away"

        await ctx.reply(
            f"{icon} {ctx.user.mention} {action} 1 reputation point\n"
            f"📊 {new_rep} reputation"
        )

    async def cmd_reputation(self, ctx: NexusContext):
        """View user's reputation."""
        config = ReputationConfig(**ctx.group.module_configs.get("reputation", {}))
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        target_id = ctx.user.telegram_id
        if args:
            user_id = self._get_user_id(ctx, args)
            if user_id:
                target_id = user_id

        # Get reputation
        rep = await self._get_reputation(ctx, target_id) or 0

        # Get user info
        from shared.models import User
        result = ctx.db.execute(
            f"SELECT username, first_name, last_name FROM users WHERE telegram_id = {target_id} LIMIT 1"
        )
        row = result.fetchone()

        if row:
            username = row[0]
            name = f"{row[1]} {row[2] or ''}".strip()
            display_name = username or name

        # Get reputation history
        from shared.models import ReputationLog

        result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {target_id} LIMIT 1"
        )
        user_db_id = result.scalar()

        result = ctx.db.execute(
            f"""
            SELECT SUM(CASE WHEN delta > 0 THEN 1 ELSE 0 END) as positive,
                   SUM(CASE WHEN delta < 0 THEN 1 ELSE 0 END) as negative,
                   COUNT(*) as total
            FROM reputation_logs
            WHERE to_user_id = {user_db_id} AND group_id = {ctx.group.id}
            """
        )
        row = result.fetchone()

        positive = row[0] or 0
        negative = row[1] or 0
        total = row[2] or 0

        # Get rank
        result = ctx.db.execute(
            f"""
            SELECT COUNT(*) + 1
            FROM reputation
            WHERE group_id = {ctx.group.id}
              AND score > {rep}
            """
        )
        rank = result.scalar()

        text = f"📊 Reputation: {display_name}\n\n"
        text += f"🏆 Score: {rep} (#{rank})\n"
        text += f"👍 Positive: {positive}\n"
        text += f"👎 Negative: {negative}\n"
        text += f"📈 Total: {total}\n\n"

        # Trend
        if rep > 50:
            text += "🌟 Excellent reputation!"
        elif rep > 20:
            text += "😊 Good reputation!"
        elif rep > 0:
            text += "😐 Neutral reputation"
        elif rep > -20:
            text += "😔 Poor reputation"
        else:
            text += "💀 Terrible reputation!"

        await ctx.reply(text)

    async def cmd_repleaderboard(self, ctx: NexusContext):
        """View reputation leaderboard."""
        config = ReputationConfig(**ctx.group.module_configs.get("reputation", {}))

        from shared.models import Reputation, User

        result = ctx.db.execute(
            f"""
            SELECT u.username, u.first_name, u.last_name, r.score
            FROM reputation r
            JOIN users u ON r.user_id = u.id
            WHERE r.group_id = {ctx.group.id}
            ORDER BY r.score DESC
            LIMIT 10
            """
        )

        leaders = result.fetchall()
        if not leaders:
            await ctx.reply("❌ No reputation data yet")
            return

        text = f"🏆 Reputation Leaderboard\n\n"
        for i, row in enumerate(leaders, 1):
            username = row[0]
            name = f"{row[1]} {row[2] or ''}".strip()
            display_name = username or name
            score = row[3]

            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} {display_name}: {score} rep\n"

        await ctx.reply(text)
