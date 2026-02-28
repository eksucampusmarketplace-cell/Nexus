"""Identity module - XP, levels, achievements, badges, and profile system."""

import random
from datetime import datetime, timedelta, date
from typing import Optional, List
from dataclasses import dataclass

from aiogram.types import Message
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class IdentityConfig(BaseModel):
    """Configuration for identity module."""
    xp_per_message: int = 1
    xp_per_reaction: int = 2
    xp_per_voice_minute: int = 5
    xp_multiplier_weekend: float = 1.5
    xp_streak_bonus: int = 50
    level_up_announcement: bool = True
    achievement_announcement: bool = True
    max_level: int = 100
    xp_formula: str = "100 * level"  # XP needed for level


@dataclass
class UserStats:
    """User statistics."""
    messages_today: int
    reactions_today: int
    streak_days: int
    last_active: Optional[datetime]


class IdentityModule(NexusModule):
    """Identity system with XP, levels, achievements, and badges."""

    name = "identity"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Complete identity system with XP, levels, achievements, badges, and profiles"
    category = ModuleCategory.COMMUNITY

    config_schema = IdentityConfig
    default_config = IdentityConfig().dict()

    # Achievement definitions
    achievements = {
        "first_message": {"name": "First Steps", "emoji": "👋", "description": "Sent your first message"},
        "messages_100": {"name": "Chatty", "emoji": "💬", "description": "Sent 100 messages"},
        "messages_500": {"name": "Talkative", "emoji": "🗣️", "description": "Sent 500 messages"},
        "messages_1000": {"name": "Conversationalist", "emoji": "📢", "description": "Sent 1000 messages"},
        "messages_5000": {"name": "Message Master", "emoji": "🎤", "description": "Sent 5000 messages"},
        "level_5": {"name": "Rising Star", "emoji": "⭐", "description": "Reached level 5"},
        "level_10": {"name": "Celebrity", "emoji": "🌟", "description": "Reached level 10"},
        "level_25": {"name": "Superstar", "emoji": "💫", "description": "Reached level 25"},
        "level_50": {"name": "Legend", "emoji": "🏆", "description": "Reached level 50"},
        "streak_7": {"name": "Week Warrior", "emoji": "🔥", "description": "7-day streak"},
        "streak_30": {"name": "Monthly Champion", "emoji": "🔥🔥", "description": "30-day streak"},
        "reactions_100": {"name": "Reactive", "emoji": "❤️", "description": "Received 100 reactions"},
        "reactions_500": {"name": "Reaction Master", "emoji": "💕", "description": "Received 500 reactions"},
        "coins_1000": {"name": "Coin Collector", "emoji": "💰", "description": "Earned 1000 coins"},
        "coins_10000": {"name": "Coin Tycoon", "emoji": "💎", "description": "Earned 10000 coins"},
        "top_10": {"name": "Top 10", "emoji": "🏅", "description": "Reached top 10 in leaderboard"},
        "mod_actions_10": {"name": "Guardian", "emoji": "🛡️", "description": "Performed 10 moderation actions"},
        "mod_actions_100": {"name": "Peacekeeper", "emoji": "🕊️", "description": "Performed 100 moderation actions"},
        "early_member": {"name": "OG Member", "emoji": "👴", "description": "Joined within first week"},
        "year_active": {"name": "Veteran", "emoji": "🎖️", "description": "Active for 1 year"},
    }

    commands = [
        CommandDef(
            name="me",
            description="View your profile",
            admin_only=False,
            aliases=["profile", "myprofile"],
        ),
        CommandDef(
            name="profile",
            description="View user's profile",
            admin_only=False,
            aliases=["p"],
        ),
        CommandDef(
            name="rank",
            description="View user's rank and level",
            admin_only=False,
        ),
        CommandDef(
            name="level",
            description="View your level and XP",
            admin_only=False,
        ),
        CommandDef(
            name="xp",
            description="View your XP progress",
            admin_only=False,
        ),
        CommandDef(
            name="streak",
            description="View your activity streak",
            admin_only=False,
        ),
        CommandDef(
            name="badges",
            description="View your earned badges",
            admin_only=False,
            aliases=["achievements"],
        ),
        CommandDef(
            name="achievements",
            description="View all available achievements",
            admin_only=False,
        ),
        CommandDef(
            name="awardxp",
            description="Award XP to user (admin)",
            admin_only=True,
        ),
        CommandDef(
            name="awardachievement",
            description="Award achievement to user (admin)",
            admin_only=True,
        ),
        CommandDef(
            name="setlevel",
            description="Set user's level (admin)",
            admin_only=True,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("me", self.cmd_me)
        self.register_command("profile", self.cmd_profile)
        self.register_command("p", self.cmd_profile)
        self.register_command("rank", self.cmd_rank)
        self.register_command("level", self.cmd_level)
        self.register_command("xp", self.cmd_xp)
        self.register_command("streak", self.cmd_streak)
        self.register_command("badges", self.cmd_badges)
        self.register_command("achievements", self.cmd_achievements)
        self.register_command("awardxp", self.cmd_awardxp)
        self.register_command("awardachievement", self.cmd_awardachievement)
        self.register_command("setlevel", self.cmd_setlevel)

    async def on_message(self, ctx: NexusContext):
        """Award XP for messages."""
        config = IdentityConfig(**ctx.group.module_configs.get("identity", {}))

        # Calculate XP
        xp = config.xp_per_message

        # Weekend multiplier
        if datetime.utcnow().weekday() >= 5:  # Saturday or Sunday
            xp = int(xp * config.xp_multiplier_weekend)

        # Award XP
        await self._award_xp(ctx, xp, "message")

        # Check for messages achievements
        await self._check_achievements(ctx, "messages")

        # Update daily stats
        await self._update_daily_stats(ctx)

    async def on_callback_query(self, ctx: NexusContext):
        """Handle callback queries (reaction XP)."""
        if ctx.callback_query:
            # Check if it's a reaction
            if ctx.callback_query.data:
                config = IdentityConfig(**ctx.group.module_configs.get("identity", {}))
                xp = config.xp_per_reaction
                await self._award_xp(ctx, xp, "reaction")
                await self._check_achievements(ctx, "reactions")

    async def on_new_member(self, ctx: NexusContext):
        """Check for early member achievement."""
        # Get group creation date
        from shared.models import Group
        result = ctx.db.execute(
            f"SELECT created_at FROM groups WHERE id = {ctx.group.id} LIMIT 1"
        )
        row = result.fetchone()

        if row and row[0]:
            group_age = datetime.utcnow() - row[0]
            if group_age < timedelta(weeks=1):
                # Award early member achievement
                await self._award_achievement(ctx, ctx.user, "early_member")

    def _calculate_level(self, xp: int, config: IdentityConfig) -> int:
        """Calculate level from XP."""
        # Simple formula: level = floor(xp / 100)
        return min(xp // 100, config.max_level)

    def _calculate_xp_needed(self, level: int, config: IdentityConfig) -> int:
        """Calculate XP needed for a level."""
        return level * 100

    async def _award_xp(self, ctx: NexusContext, xp: int, reason: str):
        """Award XP to user."""
        if xp <= 0:
            return

        config = IdentityConfig(**ctx.group.module_configs.get("identity", {}))

        # Get current XP
        from shared.models import MemberProfile
        current_xp = ctx.user.xp
        current_level = self._calculate_level(current_xp, config)

        # Award XP
        await ctx.award_xp(ctx.user.user_id, xp, reason)

        # Check for level up
        new_level = self._calculate_level(current_xp + xp, config)
        if new_level > current_level:
            if config.level_up_announcement:
                await ctx.reply(
                    f"🎉 {ctx.user.mention} leveled up to level {new_level}!\n"
                    f"⭐ +{xp} XP"
                )

        # Check for level achievements
        for level in [5, 10, 25, 50]:
            if new_level >= level and current_level < level:
                await self._award_achievement(ctx, ctx.user, f"level_{level}")

    async def _award_achievement(self, ctx: NexusContext, user, achievement_id: str):
        """Award achievement to user."""
        if achievement_id not in self.achievements:
            return

        # Check if already earned
        from shared.models import MemberBadge

        result = ctx.db.execute(
            f"SELECT id FROM member_badges WHERE member_id = {user.member_id} AND badge_slug = '{achievement_id}' LIMIT 1"
        )
        row = result.fetchone()

        if row:
            return  # Already earned

        # Award achievement
        achievement = self.achievements[achievement_id]
        badge = MemberBadge(
            member_id=user.member_id,
            badge_slug=achievement_id,
            earned_at=datetime.utcnow(),
            metadata={},
        )
        ctx.db.add(badge)
        ctx.db.commit()

        config = IdentityConfig(**ctx.group.module_configs.get("identity", {}))

        if config.achievement_announcement:
            await ctx.reply(
                f"🏆 {user.mention} earned achievement: {achievement['emoji']} {achievement['name']}\n"
                f"📝 {achievement['description']}"
            )

    async def _check_achievements(self, ctx: NexusContext, category: str):
        """Check and award achievements based on category."""
        from shared.models import Wallet

        if category == "messages":
            # Get message count
            msg_count = ctx.user.message_count

            # Check message achievements
            achievements = [
                ("messages_100", 100),
                ("messages_500", 500),
                ("messages_1000", 1000),
                ("messages_5000", 5000),
            ]

            for achievement_id, threshold in achievements:
                if msg_count >= threshold:
                    await self._award_achievement(ctx, ctx.user, achievement_id)

        elif category == "reactions":
            # Get reaction count (from stats)
            # This would need a separate reaction tracking table
            pass

        elif category == "coins":
            # Get coin count
            result = ctx.db.execute(
                f"SELECT balance FROM wallets WHERE user_id = {ctx.user.user_id} AND group_id = {ctx.group.id} LIMIT 1"
            )
            row = result.fetchone()

            if row:
                coin_count = row[0]
                achievements = [
                    ("coins_1000", 1000),
                    ("coins_10000", 10000),
                ]

                for achievement_id, threshold in achievements:
                    if coin_count >= threshold:
                        await self._award_achievement(ctx, ctx.user, achievement_id)

    async def _update_daily_stats(self, ctx: NexusContext):
        """Update daily statistics for streak tracking."""
        from shared.models import Member

        today = datetime.utcnow().date()
        last_active = ctx.user.last_active

        if last_active and last_active.date() == today:
            # Active today, update streak
            pass
        elif last_active and (today - last_active.date()) > timedelta(days=1):
            # Missed a day, reset streak
            ctx.db.execute(
                f"UPDATE members SET streak_days = 0 WHERE id = {ctx.user.member_id}"
            )
            ctx.db.commit()
        else:
            # First message of the day, increment streak
            streak_days = ctx.user.streak_days + 1

            # Check for streak achievements
            if streak_days == 7:
                await self._award_achievement(ctx, ctx.user, "streak_7")
            elif streak_days == 30:
                await self._award_achievement(ctx, ctx.user, "streak_30")

    async def cmd_me(self, ctx: NexusContext):
        """View your profile."""
        await self.cmd_profile(ctx, str(ctx.user.telegram_id))

    async def cmd_profile(self, ctx: NexusContext):
        """View user's profile."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        # Parse user ID or username
        if args:
            user_id = self._get_user_id(ctx, args)
            if not user_id:
                await ctx.reply("❌ User not found")
                return
        else:
            user_id = ctx.user.telegram_id

        # Get user data
        from shared.models import User, MemberProfile, MemberBadge, Wallet

        user_result = ctx.db.execute(
            f"SELECT id, username, first_name, last_name, created_at FROM users WHERE telegram_id = {user_id} LIMIT 1"
        )
        user_row = user_result.fetchone()

        if not user_row:
            await ctx.reply("❌ User not found in database")
            return

        user_db_id = user_row[0]
        username = user_row[1]
        first_name = user_row[2]
        last_name = user_row[3]
        joined_at = user_row[4]

        # Get member data
        member_result = ctx.db.execute(
            f"""
            SELECT m.*, u.telegram_id
            FROM members m
            JOIN users u ON m.user_id = u.id
            WHERE m.group_id = {ctx.group.id} AND m.user_id = {user_db_id}
            LIMIT 1
            """
        )
        member_row = member_result.fetchone()

        if not member_row:
            await ctx.reply("❌ User is not a member of this group")
            return

        # Get badges
        badge_result = ctx.db.execute(
            f"""
            SELECT badge_slug, earned_at
            FROM member_badges
            WHERE member_id = {member_row[0]}
            ORDER BY earned_at DESC
            LIMIT 20
            """
        )
        badges = badge_result.fetchall()

        # Get wallet
        wallet_result = ctx.db.execute(
            f"SELECT balance, bank_balance FROM wallets WHERE user_id = {user_db_id} AND group_id = {ctx.group.id} LIMIT 1"
        )
        wallet_row = wallet_result.fetchone()

        config = IdentityConfig(**ctx.group.module_configs.get("identity", {}))
        level = self._calculate_level(member_row[7] or 0, config)
        xp_needed = self._calculate_xp_needed(level + 1, config) - (member_row[7] or 0)

        # Build profile
        name = f"{first_name} {last_name or ''}".strip()
        display_name = username or name

        text = f"👤 {display_name}\n\n"
        text += f"🏷️ ID: {user_id}\n"
        text += f"👑 Role: {member_row[9] or 'member'}\n"
        text += f"⭐ Level: {level}/{config.max_level}\n"
        text += f"✨ XP: {member_row[7] or 0} (need {xp_needed} for next level)\n"
        text += f"🔥 Streak: {member_row[9] or 0} days\n"
        text += f"💬 Messages: {member_row[5] or 0}\n"

        if wallet_row:
            text += f"💰 Coins: {wallet_row[0]:,}\n"
            text += f"🏦 Bank: {wallet_row[1]:,}\n"

        if badges:
            text += f"\n🏆 Badges ({len(badges)}):\n"
            for badge_slug, earned_at in badges[:10]:  # Show first 10
                achievement = self.achievements.get(badge_slug)
                if achievement:
                    text += f"{achievement['emoji']} {achievement['name']}\n"

        await ctx.reply(text)

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

    async def cmd_rank(self, ctx: NexusContext):
        """View user's rank and level."""
        config = IdentityConfig(**ctx.group.module_configs.get("identity", {}))

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        user_id = ctx.user.telegram_id

        if args:
            user_id = self._get_user_id(ctx, args)

        # Get user's XP
        from shared.models import MemberProfile
        user_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {user_id} LIMIT 1"
        )
        user_db_id = user_result.scalar()

        member_result = ctx.db.execute(
            f"SELECT xp FROM members WHERE user_id = {user_db_id} AND group_id = {ctx.group.id} LIMIT 1"
        )
        member_row = member_result.fetchone()

        if not member_row:
            await ctx.reply("❌ User not found")
            return

        xp = member_row[0] or 0
        level = self._calculate_level(xp, config)

        # Calculate rank
        result = ctx.db.execute(
            f"""
            SELECT COUNT(*) + 1
            FROM members
            WHERE group_id = {ctx.group.id}
              AND xp > {xp}
            """
        )
        rank = result.scalar()

        # Get total members
        result = ctx.db.execute(
            f"SELECT COUNT(*) FROM members WHERE group_id = {ctx.group.id}"
        )
        total = result.scalar()

        percentile = int((total - rank) / total * 100) if total > 0 else 0

        text = f"📊 {ctx.user.mention if user_id == ctx.user.telegram_id else 'User'}'s Rank\n\n"
        text += f"🏆 #{rank} / {total} (top {percentile}%)\n"
        text += f"⭐ Level {level}\n"
        text += f"✨ {xp:,} XP\n"

        await ctx.reply(text)

    async def cmd_level(self, ctx: NexusContext):
        """View your level and XP."""
        config = IdentityConfig(**ctx.group.module_configs.get("identity", {}))

        level = self._calculate_level(ctx.user.xp, config)
        xp_needed = self._calculate_xp_needed(level + 1, config) - ctx.user.xp

        progress = (ctx.user.xp % 100)

        text = f"⭐ {ctx.user.mention}'s Level\n\n"
        text += f"Level: {level}/{config.max_level}\n"
        text += f"XP: {ctx.user.xp:,}\n"
        text += f"Progress to next level: {progress}/100\n"

        if level < config.max_level:
            text += f"XP needed: {xp_needed:,}\n"

        await ctx.reply(text)

    async def cmd_xp(self, ctx: NexusContext):
        """View your XP progress."""
        config = IdentityConfig(**ctx.group.module_configs.get("identity", {}))

        level = self._calculate_level(ctx.user.xp, config)
        xp_needed = self._calculate_xp_needed(level + 1, config) - ctx.user.xp

        text = f"✨ {ctx.user.mention}'s XP\n\n"
        text += f"Total XP: {ctx.user.xp:,}\n"
        text += f"Level: {level}\n"
        text += f"Progress: {ctx.user.xp % 100}/100\n"
        text += f"XP needed for level {level + 1}: {xp_needed:,}\n"

        # Calculate XP to next milestones
        for milestone in [5, 10, 25, 50]:
            if level < milestone:
                xp_to_milestone = self._calculate_xp_needed(milestone, config) - ctx.user.xp
                text += f"\nTo level {milestone}: +{xp_to_milestone:,} XP"

        await ctx.reply(text)

    async def cmd_streak(self, ctx: NexusContext):
        """View your activity streak."""
        streak = ctx.user.streak_days or 0

        next_milestone = 7 if streak < 7 else 30 if streak < 30 else 90

        text = f"🔥 {ctx.user.mention}'s Activity Streak\n\n"
        text += f"Current Streak: {streak} days\n"

        if streak > 0:
            text += f"📅 Last Active: {ctx.user.last_active.strftime('%Y-%m-%d')}\n"

        if streak < next_milestone:
            text += f"\nNext Achievement: {next_milestone} days ({next_milestone - streak} more)\n"
        elif streak >= 7:
            text += f"\n🏆 Earned: Week Warrior (7 days)\n"
        if streak >= 30:
            text += f"🏆 Earned: Monthly Champion (30 days)\n"

        await ctx.reply(text)

    async def cmd_badges(self, ctx: NexusContext):
        """View your earned badges."""
        from shared.models import MemberBadge

        result = ctx.db.execute(
            f"""
            SELECT badge_slug, earned_at
            FROM member_badges
            WHERE member_id = {ctx.user.member_id}
            ORDER BY earned_at DESC
            LIMIT 50
            """
        )
        badges = result.fetchall()

        if not badges:
            await ctx.reply("❌ You haven't earned any badges yet!")
            await ctx.reply("Use /achievements to see available achievements")
            return

        text = f"🏆 {ctx.user.mention}'s Badges ({len(badges)}\n\n"

        for badge_slug, earned_at in badges:
            achievement = self.achievements.get(badge_slug)
            if achievement:
                date_str = earned_at.strftime('%Y-%m-%d')
                text += f"{achievement['emoji']} {achievement['name']}\n"
                text += f"   {achievement['description']}\n"
                text += f"   📅 {date_str}\n\n"

        await ctx.reply(text)

    async def cmd_achievements(self, ctx: NexusContext):
        """View all available achievements."""
        # Get user's earned achievements
        from shared.models import MemberBadge

        result = ctx.db.execute(
            f"SELECT badge_slug FROM member_badges WHERE member_id = {ctx.user.member_id}"
        )
        earned = set(row[0] for row in result.fetchall())

        text = f"🏆 Available Achievements\n\n"

        for achievement_id, achievement in sorted(self.achievements.items()):
            is_earned = achievement_id in earned
            status = "✅" if is_earned else "❌"

            text += f"{status} {achievement['emoji']} {achievement['name']}\n"
            text += f"   {achievement['description']}\n\n"

        await ctx.reply(text)

    async def cmd_awardxp(self, ctx: NexusContext):
        """Award XP to user (admin only)."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only")
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if len(args) < 2:
            await ctx.reply("❌ Usage: /awardxp <@user> <amount> [reason]")
            return

        user_id = self._get_user_id(ctx, args)
        if not user_id:
            await ctx.reply("❌ User not found")
            return

        try:
            amount = int(args[1])
        except ValueError:
            await ctx.reply("❌ Invalid amount")
            return

        if amount <= 0:
            await ctx.reply("❌ Amount must be positive")
            return

        # Get target user
        from shared.models import User

        result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {user_id} LIMIT 1"
        )
        user_db_id = result.scalar()

        if not user_db_id:
            await ctx.reply("❌ User not found")
            return

        # Award XP
        reason = " ".join(args[2:]) if len(args) > 2 else "admin award"
        await ctx.award_xp(user_db_id, amount, reason)

        await ctx.reply(
            f"✅ Awarded {amount:,} XP to user\n"
            f"Reason: {reason}"
        )

    async def cmd_awardachievement(self, ctx: NexusContext):
        """Award achievement to user (admin only)."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only")
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if len(args) < 2:
            await ctx.reply("❌ Usage: /awardachievement <@user> <achievement_id>")
            await ctx.reply("Available achievements: " + ", ".join(self.achievements.keys()))
            return

        user_id = self._get_user_id(ctx, args)
        if not user_id:
            await ctx.reply("❌ User not found")
            return

        achievement_id = args[1]

        if achievement_id not in self.achievements:
            await ctx.reply(f"❌ Invalid achievement. Available: " + ", ".join(self.achievements.keys()))
            return

        # Get target user
        from shared.models import User

        result = ctx.db.execute(
            f"SELECT id, telegram_id FROM users WHERE telegram_id = {user_id} LIMIT 1"
        )
        row = result.fetchone()

        if not row:
            await ctx.reply("❌ User not found")
            return

        user_db_id = row[0]

        # Create a fake user object
        from bot.core.context import MemberProfile
        target = MemberProfile(
            id=0,
            user_id=user_db_id,
            group_id=ctx.group.id,
            telegram_id=row[1],
            username="",
            first_name="",
            last_name="",
            role="",
            trust_score=0,
            xp=0,
            level=0,
            warn_count=0,
            is_muted=False,
            is_banned=False,
            is_approved=False,
            is_whitelisted=False,
            joined_at=datetime.utcnow(),
            message_count=0,
            custom_title="",
            member_id=user_db_id,
        )

        # Award achievement
        await self._award_achievement(ctx, target, achievement_id)

        await ctx.reply(f"✅ Awarded achievement: {achievement_id}")

    async def cmd_setlevel(self, ctx: NexusContext):
        """Set user's level (admin only)."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only")
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if len(args) < 2:
            await ctx.reply("❌ Usage: /setlevel <@user> <level>")
            return

        user_id = self._get_user_id(ctx, args)
        if not user_id:
            await ctx.reply("❌ User not found")
            return

        try:
            level = int(args[1])
        except ValueError:
            await ctx.reply("❌ Invalid level")
            return

        if level < 0 or level > 100:
            await ctx.reply("❌ Level must be between 0 and 100")
            return

        # Get target user
        from shared.models import User

        result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {user_id} LIMIT 1"
        )
        user_db_id = result.scalar()

        if not user_db_id:
            await ctx.reply("❌ User not found")
            return

        # Calculate XP for level
        xp = level * 100

        # Update member
        ctx.db.execute(
            f"UPDATE members SET xp = {xp}, level = {level} WHERE user_id = {user_db_id} AND group_id = {ctx.group.id}"
        )
        ctx.db.commit()

        await ctx.reply(f"✅ Set level to {level} ({xp:,} XP)")
