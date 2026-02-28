"""Antispam module - Anti-flood and anti-raid protection."""

from datetime import datetime, timedelta
from typing import Optional, Dict
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule, EventType


class AntispamConfig(BaseModel):
    """Configuration for antispam module."""
    antiflood_enabled: bool = True
    message_limit: int = 5
    window_seconds: int = 5
    flood_action: str = "mute"
    flood_duration: int = 300
    media_flood_enabled: bool = True
    media_limit: int = 3

    antiraid_enabled: bool = True
    join_threshold: int = 10
    raid_window: int = 60
    raid_action: str = "lock"
    auto_unlock_after: int = 3600
    notify_admins: bool = True


class AntispamModule(NexusModule):
    """Anti-flood and anti-raid protection."""

    name = "antispam"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Anti-flood and anti-raid protection"
    category = ModuleCategory.ANTISPAM

    config_schema = AntispamConfig
    default_config = AntispamConfig().dict()

    commands = [
        CommandDef(
            name="antiflood",
            description="Configure anti-flood",
            admin_only=True,
            args="[limit] [window] [action]",
        ),
        CommandDef(
            name="antifloodmedia",
            description="Configure media flood",
            admin_only=True,
            args="[limit]",
        ),
        CommandDef(
            name="antiraidthreshold",
            description="Set raid threshold",
            admin_only=True,
            args="<number>",
        ),
        CommandDef(
            name="antiraidaction",
            description="Set raid action",
            admin_only=True,
            args="<action>",
        ),
        CommandDef(
            name="antifloodaction",
            description="Set flood action",
            admin_only=True,
            args="<action>",
        ),
    ]

    listeners = [
        EventType.MESSAGE,
        EventType.NEW_MEMBER,
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("antiflood", self.cmd_antiflood)
        self.register_command("antifloodmedia", self.cmd_antifloodmedia)
        self.register_command("antiraidthreshold", self.cmd_antiraidthreshold)
        self.register_command("antiraidaction", self.cmd_antiraidaction)
        self.register_command("antifloodaction", self.cmd_antifloodaction)

        # Initialize flood tracking in Redis
        self._flood_tracking: Dict[str, list] = {}

    async def on_message(self, ctx: NexusContext) -> bool:
        """Check for flood and take action."""
        if not ctx.message:
            return False

        config = ctx.group.module_configs.get("antispam", {})

        # Check flood
        if config.get("antiflood_enabled", True):
            is_flood = await self._check_flood(ctx, config)
            if is_flood:
                return True

        # Check media flood
        if config.get("media_flood_enabled", True):
            is_media_flood = await self._check_media_flood(ctx, config)
            if is_media_flood:
                return True

        return False

    async def on_new_member(self, ctx: NexusContext) -> bool:
        """Check for raid and take action."""
        config = ctx.group.module_configs.get("antispam", {})

        if not config.get("antiraid_enabled", True):
            return False

        is_raid = await self._check_raid(ctx, config)
        if is_raid:
            return True

        return False

    async def _check_flood(self, ctx: NexusContext, config: dict) -> bool:
        """Check if user is flooding."""
        message_limit = config.get("message_limit", 5)
        window = config.get("window_seconds", 5)
        action = config.get("flood_action", "mute")
        duration = config.get("flood_duration", 300)

        user_id = ctx.user.telegram_id
        group_id = ctx.group.id
        key = f"flood:{group_id}:{user_id}"

        # Get message history from Redis
        if ctx.cache:
            messages = await ctx.cache.get_json(key) or []

            # Add current message
            now = datetime.utcnow().timestamp()
            messages.append(now)

            # Filter old messages outside window
            messages = [m for m in messages if now - m < window]

            # Check if limit exceeded
            if len(messages) > message_limit:
                # Take action
                if action == "mute":
                    await ctx.mute_user(ctx.user, duration, "Anti-flood: Too many messages", silent=True)
                elif action == "kick":
                    await ctx.kick_user(ctx.user, "Anti-flood: Too many messages")
                elif action == "ban":
                    await ctx.ban_user(ctx.user, duration, "Anti-flood: Too many messages", silent=True)

                # Notify admins
                await ctx.notify_admins(
                    f"🚨 Flood detected!\n\n"
                    f"User: {ctx.user.mention}\n"
                    f"Group: {ctx.group.title}\n"
                    f"Messages: {len(messages)} in {window}s",
                    action_type="flood",
                )

                return True

            # Save back to Redis
            await ctx.cache.set_json(key, messages, expire=window)

        return False

    async def _check_media_flood(self, ctx: NexusContext, config: dict) -> bool:
        """Check if user is flooding with media."""
        media_limit = config.get("media_limit", 3)

        if not ctx.message:
            return False

        # Check if message has media
        has_media = bool(
            ctx.message.photo or
            ctx.message.video or
            ctx.message.document or
            ctx.message.audio or
            ctx.message.voice or
            ctx.message.animation or
            ctx.message.sticker
        )

        if not has_media:
            return False

        user_id = ctx.user.telegram_id
        group_id = ctx.group.id
        key = f"media_flood:{group_id}:{user_id}"

        # Get media history from Redis
        if ctx.cache:
            media_count = await ctx.cache.get(key) or 0

            media_count += 1

            if media_count > media_limit:
                # Take action
                action = config.get("flood_action", "mute")
                duration = config.get("flood_duration", 300)

                if action == "mute":
                    await ctx.mute_user(ctx.user, duration, "Anti-media-flood: Too many media", silent=True)
                elif action == "kick":
                    await ctx.kick_user(ctx.user, "Anti-media-flood: Too many media")
                elif action == "ban":
                    await ctx.ban_user(ctx.user, duration, "Anti-media-flood: Too many media", silent=True)

                # Notify admins
                await ctx.notify_admins(
                    f"🚨 Media flood detected!\n\n"
                    f"User: {ctx.user.mention}\n"
                    f"Group: {ctx.group.title}\n"
                    f"Media items: {media_count}",
                    action_type="media_flood",
                )

                return True

            # Save to Redis with short expiration
            await ctx.cache.set(key, media_count, expire=60)

        return False

    async def _check_raid(self, ctx: NexusContext, config: dict) -> bool:
        """Check if group is being raided."""
        threshold = config.get("join_threshold", 10)
        window = config.get("raid_window", 60)
        action = config.get("raid_action", "lock")
        auto_unlock = config.get("auto_unlock_after", 3600)

        group_id = ctx.group.id
        key = f"raid:{group_id}"

        # Track joins
        if ctx.cache:
            joins = await ctx.cache.get_json(key) or []

            # Add current join
            now = datetime.utcnow().timestamp()
            joins.append({
                "timestamp": now,
                "user_id": ctx.user.telegram_id,
            })

            # Filter old joins outside window
            joins = [j for j in joins if now - j["timestamp"] < window]

            # Check if threshold exceeded
            if len(joins) > threshold:
                # Take action
                if action == "lock":
                    # Lock all common content types
                    await self._apply_raid_lock(ctx)
                elif action == "restrict":
                    for join in joins:
                        try:
                            await ctx.bot.restrict_chat_member(
                                chat_id=ctx.group.telegram_id,
                                user_id=join["user_id"],
                                permissions={
                                    "can_send_messages": False,
                                    "can_send_media_messages": False,
                                },
                            )
                        except Exception:
                            pass
                elif action == "ban":
                    for join in joins:
                        try:
                            await ctx.bot.ban_chat_member(
                                chat_id=ctx.group.telegram_id,
                                user_id=join["user_id"],
                            )
                        except Exception:
                            pass

                # Notify admins
                await ctx.notify_admins(
                    f"🚨 RAID DETECTED!\n\n"
                    f"Group: {ctx.group.title}\n"
                    f"Joins: {len(joins)} in {window}s\n"
                    f"Action taken: {action}",
                    action_type="raid",
                )

                # Schedule auto-unlock
                if auto_unlock > 0 and action == "lock":
                    await ctx.scheduler.schedule_recurring(
                        chat_id=ctx.group.telegram_id,
                        text="🔓 Auto-unlock after raid protection",
                        cron=f"*/1 * * * *",
                    )

                return True

            # Save to Redis
            await ctx.cache.set_json(key, joins, expire=window)

        return False

    async def _apply_raid_lock(self, ctx: NexusContext):
        """Apply raid lock."""
        lock_types = ["links", "images", "sticker", "gif", "video", "audio", "document", "poll"]

        config = ctx.group.module_configs.get("locks", {})
        if "active_locks" not in config:
            config["active_locks"] = {}

        for lock_type in lock_types:
            config["active_locks"][lock_type] = True

    async def cmd_antiflood(self, ctx: NexusContext):
        """Configure anti-flood."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            config = ctx.group.module_configs.get("antispam", {})
            text = "🌊 **Anti-Flood Settings**\n\n"
            text += f"**Enabled:** {'Yes' if config.get('antiflood_enabled') else 'No'}\n"
            text += f"**Limit:** {config.get('message_limit', 5)} messages\n"
            text += f"**Window:** {config.get('window_seconds', 5)} seconds\n"
            text += f"**Action:** {config.get('flood_action', 'mute')}\n"
            text += f"**Duration:** {ctx._format_duration(config.get('flood_duration', 300))}\n"
            await ctx.reply(text, parse_mode="Markdown")
            return

        limit = int(args[0]) if args[0].isdigit() else None
        window = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
        action = args[2].lower() if len(args) > 2 else None

        config = ctx.group.module_configs.get("antispam", {})

        if limit:
            config["message_limit"] = limit
        if window:
            config["window_seconds"] = window
        if action in ["delete", "mute", "kick", "ban"]:
            config["flood_action"] = action

        await ctx.reply(f"✅ Anti-flood updated")

    async def cmd_antifloodmedia(self, ctx: NexusContext):
        """Configure media flood."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            config = ctx.group.module_configs.get("antispam", {})
            text = f"📎 **Media Flood Settings**\n\n"
            text += f"**Enabled:** {'Yes' if config.get('media_flood_enabled') else 'No'}\n"
            text += f"**Limit:** {config.get('media_limit', 3)} media\n"
            await ctx.reply(text, parse_mode="Markdown")
            return

        limit = int(args[0]) if args[0].isdigit() else None
        config = ctx.group.module_configs.get("antispam", {})

        if limit is not None:
            config["media_limit"] = limit
        config["media_flood_enabled"] = True

        await ctx.reply(f"✅ Media flood updated")

    async def cmd_antiraidthreshold(self, ctx: NexusContext):
        """Set raid threshold."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args or not args[0].isdigit():
            await ctx.reply("❌ Usage: /antiraidthreshold <number>")
            return

        threshold = int(args[0])
        config = ctx.group.module_configs.get("antispam", {})
        config["join_threshold"] = threshold

        await ctx.reply(f"✅ Raid threshold set to {threshold} joins")

    async def cmd_antiraidaction(self, ctx: NexusContext):
        """Set raid action."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args or args[0] not in ["lock", "restrict", "ban"]:
            await ctx.reply("❌ Usage: /antiraidaction <lock|restrict|ban>")
            return

        action = args[0]
        config = ctx.group.module_configs.get("antispam", {})
        config["raid_action"] = action

        await ctx.reply(f"✅ Raid action set to: {action}")

    async def cmd_antifloodaction(self, ctx: NexusContext):
        """Set flood action."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args or args[0] not in ["delete", "mute", "kick", "ban"]:
            await ctx.reply("❌ Usage: /antifloodaction <delete|mute|kick|ban>")
            return

        action = args[0]
        config = ctx.group.module_configs.get("antispam", {})
        config["flood_action"] = action

        await ctx.reply(f"✅ Flood action set to: {action}")
