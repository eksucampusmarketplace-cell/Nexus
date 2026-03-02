"""Group Challenges Module for Nexus.

Manages collective group-wide goals:
- Message marathons
- Active member challenges
- Engagement competitions
- Tiered rewards based on contribution
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule
from bot.services.challenge_service import ChallengeService


class ChallengesConfig(BaseModel):
    """Configuration for challenges module."""
    enabled: bool = True
    max_concurrent: int = 3
    public_leaderboard: bool = True


class ChallengesModule(NexusModule):
    """Shared group challenges system."""

    name = "challenges"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Collective group-wide challenges with tiered rewards"
    category = ModuleCategory.COMMUNITY

    config_schema = ChallengesConfig
    default_config = ChallengesConfig().dict()

    commands = [
        CommandDef(
            name="challenges",
            description="View active challenges",
            admin_only=False,
            aliases=["challenge"],
        ),
        CommandDef(
            name="mychallenges",
            description="View your challenge progress",
            admin_only=False,
        ),
        CommandDef(
            name="createchallenge",
            description="Create a new challenge (admin)",
            admin_only=True,
            args="<title> <type> <target> <duration_days>",
        ),
        CommandDef(
            name="endchallenge",
            description="End a challenge (admin)",
            admin_only=True,
            args="<challenge_id>",
        ),
        CommandDef(
            name="claimreward",
            description="Claim challenge reward",
            admin_only=False,
            args="<challenge_id>",
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("challenges", self.cmd_challenges)
        self.register_command("challenge", self.cmd_challenges)
        self.register_command("mychallenges", self.cmd_mychallenges)
        self.register_command("createchallenge", self.cmd_create_challenge)
        self.register_command("endchallenge", self.cmd_end_challenge)
        self.register_command("claimreward", self.cmd_claim_reward)

    async def on_message(self, ctx: NexusContext) -> bool:
        """Track message contributions to challenges."""
        config = ChallengesConfig(**ctx.group.module_configs.get("challenges", {}))

        if not config.enabled:
            return False

        if not ctx.message:
            return False

        # Initialize challenge service
        service = ChallengeService(ctx.db)

        # Get active challenges
        active_challenges = await service.get_active_challenges(ctx.group.id)

        for challenge in active_challenges:
            if challenge["type"] == "messages":
                # Record message contribution
                await service.record_contribution(
                    challenge_id=challenge["id"],
                    user_id=ctx.user.user_id,
                    amount=1,
                )
            elif challenge["type"] == "active_members":
                # This would track unique active members
                pass

        return False

    async def cmd_challenges(self, ctx: NexusContext):
        """View active challenges."""
        config = ChallengesConfig(**ctx.group.module_configs.get("challenges", {}))

        if not config.enabled:
            await ctx.reply("❌ Challenges are not enabled in this group.")
            return

        service = ChallengeService(ctx.db)
        challenges = await service.get_active_challenges(ctx.group.id)

        if not challenges:
            await ctx.reply(
                "🎯 **Group Challenges**\n\n"
                "No active challenges right now.\n\n"
                "Admins can create challenges with:\n"
                "`/createchallenge <title> <type> <target> <days>`"
            )
            return

        text = "🎯 **Active Challenges**\n\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"

        for challenge in challenges:
            percent = challenge["percent_complete"]
            bar_filled = int(percent / 5)
            bar = "█" * bar_filled + "░" * (20 - bar_filled)

            text += (
                f"**{challenge['title']}**\n"
                f"{challenge['description'] or 'No description'}\n"
                f"Type: {challenge['type']}\n"
                f"Progress: [{bar}] {percent:.1f}%\n"
                f"{challenge['current_value']:,} / {challenge['target_value']:,}\n"
                f"Participants: {challenge['participant_count']}\n"
                f"Ends in: {challenge['time_remaining']}\n\n"
            )

        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "Use `/mychallenges` to see your progress!"

        await ctx.reply(text)

    async def cmd_mychallenges(self, ctx: NexusContext):
        """View your challenge progress."""
        config = ChallengesConfig(**ctx.group.module_configs.get("challenges", {}))

        if not config.enabled:
            await ctx.reply("❌ Challenges are not enabled.")
            return

        service = ChallengeService(ctx.db)
        user_challenges = await service.get_user_challenges(
            ctx.group.id, ctx.user.user_id
        )

        if not user_challenges:
            await ctx.reply(
                "🎯 **Your Challenges**\n\n"
                "You're not participating in any active challenges yet.\n\n"
                "Check `/challenges` to see what's available and start contributing!"
            )
            return

        text = "🎯 **Your Challenge Progress**\n\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"

        for uc in user_challenges:
            rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(uc["rank"], "🏅")

            percent = uc["percent_complete"]
            bar_filled = int(percent / 5)
            bar = "█" * bar_filled + "░" * (20 - bar_filled)

            text += (
                f"**{uc['title']}**\n"
                f"Contribution: {uc['contribution']:,}\n"
                f"Progress: [{bar}] {percent:.1f}%\n"
                f"Rank: {rank_emoji} #{uc['rank']}\n"
                f"Ends: {uc['end_date'][:10]}\n\n"
            )

        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "Keep contributing to climb the ranks! 🚀"

        await ctx.reply(text)

    async def cmd_create_challenge(self, ctx: NexusContext):
        """Create a new challenge."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        config = ChallengesConfig(**ctx.group.module_configs.get("challenges", {}))

        if not config.enabled:
            await ctx.reply("❌ Challenges are not enabled.")
            return

        args = ctx.message.text.split(maxsplit=4)[1:] if ctx.message.text else []

        if len(args) < 4:
            await ctx.reply(
                "❌ Usage: `/createchallenge <title> <type> <target> <duration_days>`\n\n"
                "Types: messages, active_members, engagement, reactions\n"
                "Example: `/createchallenge 'Message Marathon' messages 1000 7`"
            )
            return

        title = args[0]
        challenge_type = args[1]

        try:
            target = int(args[2])
            duration = int(args[3])
        except ValueError:
            await ctx.reply("❌ Target and duration must be numbers")
            return

        if challenge_type not in ChallengeService.CHALLENGE_TYPES:
            await ctx.reply(
                f"❌ Invalid challenge type. Available: {', '.join(ChallengeService.CHALLENGE_TYPES.keys())}"
            )
            return

        # Check max concurrent
        service = ChallengeService(ctx.db)
        active = await service.get_active_challenges(ctx.group.id)

        if len(active) >= config.max_concurrent:
            await ctx.reply(f"❌ Maximum {config.max_concurrent} concurrent challenges allowed.")
            return

        # Create challenge
        challenge = await service.create_challenge(
            group_id=ctx.group.id,
            title=title,
            description=f"Collective goal: {target} {challenge_type}",
            challenge_type=challenge_type,
            target_value=target,
            duration_days=duration,
            reward_type="xp",
            reward_config={
                "tiers": {
                    "gold": {"type": "xp", "amount": 500},
                    "silver": {"type": "xp", "amount": 300},
                    "bronze": {"type": "xp", "amount": 150},
                    "participant": {"type": "xp", "amount": 50},
                }
            },
            created_by=ctx.user.user_id,
        )

        await ctx.reply(
            f"✅ Challenge created!\n\n"
            f"**{title}**\n"
            f"Goal: {target:,} {challenge_type}\n"
            f"Duration: {duration} days\n"
            f"Challenge ID: {challenge.id}"
        )

    async def cmd_end_challenge(self, ctx: NexusContext):
        """End a challenge."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /endchallenge <challenge_id>")
            return

        try:
            challenge_id = int(args[0])
        except ValueError:
            await ctx.reply("❌ Challenge ID must be a number")
            return

        service = ChallengeService(ctx.db)

        try:
            await service.end_challenge(challenge_id, cancelled=False)
            await ctx.reply(f"✅ Challenge #{challenge_id} has been ended. Rewards can now be claimed!")
        except ValueError as e:
            await ctx.reply(f"❌ {e}")

    async def cmd_claim_reward(self, ctx: NexusContext):
        """Claim challenge reward."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /claimreward <challenge_id>")
            return

        try:
            challenge_id = int(args[0])
        except ValueError:
            await ctx.reply("❌ Challenge ID must be a number")
            return

        service = ChallengeService(ctx.db)

        try:
            reward = await service.claim_reward(challenge_id, ctx.user.user_id)

            tier_emoji = {
                "gold": "🥇",
                "silver": "🥈",
                "bronze": "🥉",
                "participant": "🏅",
            }.get(reward["tier"], "🏅")

            await ctx.reply(
                f"{tier_emoji} **Reward Claimed!**\n\n"
                f"Challenge contribution: {reward['contribution']:,}\n"
                f"Rank: #{reward['rank']}\n"
                f"Tier: **{reward['tier'].title()}**\n\n"
                f"🎁 Reward: {reward['reward']['amount']} {reward['reward']['type'].upper()}"
            )

        except ValueError as e:
            await ctx.reply(f"❌ {e}")
