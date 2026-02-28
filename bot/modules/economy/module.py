"""Economy module implementation."""

from pydantic import BaseModel, Field

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, EventType, ModuleCategory, NexusModule


class EconomyConfig(BaseModel):
    """Economy module configuration."""
    currency_name: str = "coins"
    currency_emoji: str = "🪙"
    earn_per_message: int = Field(default=1, ge=0)
    earn_per_reaction: int = Field(default=2, ge=0)
    daily_bonus: int = Field(default=100, ge=0)
    xp_to_coin_enabled: bool = False
    xp_to_coin_rate: float = 0.1


class EconomyModule(NexusModule):
    """Virtual currency module."""

    name = "economy"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Virtual currency and transactions"
    category = ModuleCategory.COMMUNITY

    config_schema = EconomyConfig
    default_config = EconomyConfig().dict()

    commands = [
        CommandDef(
            name="balance",
            description="Check your wallet balance.",
            aliases=["wallet", "bal"],
        ),
        CommandDef(
            name="daily",
            description="Claim your daily bonus.",
        ),
        CommandDef(
            name="give",
            description="Give coins to another user.",
            args="@user <amount>",
        ),
        CommandDef(
            name="leaderboard",
            description="Show top earners.",
            aliases=["top", "rich"],
        ),
        CommandDef(
            name="transactions",
            description="View your transaction history.",
        ),
    ]

    listeners = [EventType.MESSAGE]

    async def on_message(self, ctx: NexusContext) -> bool:
        """Handle messages."""
        if not ctx.message or not ctx.message.text:
            return False

        text = ctx.message.text
        command = text.split()[0].lower()

        if command in ["/balance", "/wallet", "/bal"]:
            return await self._handle_balance(ctx)
        elif command == "/daily":
            return await self._handle_daily(ctx)
        elif command == "/give":
            return await self._handle_give(ctx)
        elif command in ["/leaderboard", "/top", "/rich"]:
            return await self._handle_leaderboard(ctx)

        # Award XP for messages
        await self._award_message_xp(ctx)
        return False

    async def _handle_balance(self, ctx: NexusContext) -> bool:
        """Handle /balance command."""
        if not ctx.db:
            return True

        from shared.models import Wallet
        result = await ctx.db.execute(
            f"""
            SELECT balance, total_earned, total_spent FROM wallets
            WHERE user_id = {ctx.user.user_id} AND group_id = {ctx.group.id}
            """
        )
        wallet = result.fetchone()

        config = ctx.group.module_configs.get("economy", {})
        emoji = config.get("currency_emoji", "🪙")
        name = config.get("currency_name", "coins")

        if wallet:
            text = f"💰 <b>Your Wallet</b>\n\n"
            text += f"Balance: {wallet[0]:,} {emoji}\n"
            text += f"Total Earned: {wallet[1]:,} {emoji}\n"
            text += f"Total Spent: {wallet[2]:,} {emoji}"
        else:
            text = f"💰 <b>Your Wallet</b>\n\nBalance: 0 {emoji}\n\nStart chatting to earn {name}!"

        await ctx.reply(text)
        return True

    async def _handle_daily(self, ctx: NexusContext) -> bool:
        """Handle /daily command."""
        if not ctx.db:
            return True

        config = ctx.group.module_configs.get("economy", {})
        bonus = config.get("daily_bonus", 100)
        emoji = config.get("currency_emoji", "🪙")

        # Check if already claimed today
        from shared.models import Wallet
        # Simplified - in production check last_daily_claim

        # Award daily bonus
        await ctx.db.execute(
            f"""
            INSERT INTO wallets (user_id, group_id, balance, total_earned)
            VALUES ({ctx.user.user_id}, {ctx.group.id}, {bonus}, {bonus})
            ON CONFLICT (user_id, group_id) DO UPDATE
            SET balance = wallets.balance + {bonus},
                total_earned = wallets.total_earned + {bonus}
            """
        )
        await ctx.db.commit()

        await ctx.reply(f"🎁 <b>Daily Bonus Claimed!</b>\n\nYou received {bonus:,} {emoji}")
        return True

    async def _handle_leaderboard(self, ctx: NexusContext) -> bool:
        """Handle /leaderboard command."""
        if not ctx.db:
            return True

        from shared.models import Wallet, User
        result = await ctx.db.execute(
            f"""
            SELECT w.balance, u.username, u.first_name, u.id
            FROM wallets w
            JOIN users u ON w.user_id = u.id
            WHERE w.group_id = {ctx.group.id}
            ORDER BY w.balance DESC
            LIMIT 10
            """
        )
        top_users = result.fetchall()

        config = ctx.group.module_configs.get("economy", {})
        emoji = config.get("currency_emoji", "🪙")

        text = f"🏆 <b>Top 10 Richest Users</b>\n\n"
        for i, (balance, username, first_name, user_id) in enumerate(top_users, 1):
            name = first_name or username or f"User {user_id}"
            text += f"{i}. {name}: {balance:,} {emoji}\n"

        if not top_users:
            text += "No transactions yet!"

        await ctx.reply(text)
        return True

    async def _handle_give(self, ctx: NexusContext) -> bool:
        """Handle /give command."""
        await ctx.reply("💸 Use the Mini App to send coins to other users!")
        return True

    async def _award_message_xp(self, ctx: NexusContext) -> None:
        """Award XP/coins for messages."""
        if not ctx.db or ctx.user.is_bot:
            return

        config = ctx.group.module_configs.get("economy", {})
        earn_per_message = config.get("earn_per_message", 1)

        if earn_per_message <= 0:
            return

        # Award XP
        await ctx.award_xp(ctx.user.user_id, 1, "Sent a message")

        # Award coins (throttled)
        # In production, use Redis to throttle this
