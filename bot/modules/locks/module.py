"""Locks module - Content type locking."""

from typing import Optional
from pydantic import BaseModel
from aiogram.types import Message

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class LockConfig(BaseModel):
    """Configuration for locks module."""
    lock_mode: str = "delete"
    lock_duration: Optional[int] = None
    lock_warnings: bool = True


class LocksModule(NexusModule):
    """Content locking module."""

    name = "locks"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Lock specific content types"
    category = ModuleCategory.MODERATION

    config_schema = LockConfig
    default_config = LockConfig().dict()

    commands = [
        CommandDef(
            name="lock",
            description="Lock a content type",
            admin_only=True,
            args="<type> [mode] [duration]",
        ),
        CommandDef(
            name="unlock",
            description="Unlock a content type",
            admin_only=True,
            args="<type>",
        ),
        CommandDef(
            name="locks",
            description="List all active locks",
            admin_only=False,
        ),
        CommandDef(
            name="locktypes",
            description="List all available lock types",
            admin_only=False,
        ),
    ]

    listeners = [
        EventType.MESSAGE,
    ]

    # Available lock types
    LOCK_TYPES = [
        "audio", "bot", "button", "command", "contact", "document",
        "email", "forward", "forward_channel", "game", "gif", "inline",
        "invoice", "location", "phone", "photo", "poll", "rtl",
        "spoiler", "sticker", "url", "video", "video_note",
        "voice", "mention", "caption", "no_caption", "emoji_only",
        "unofficial_client", "arabic", "farsi", "links", "images",
    ]

    # Message type mappings
    MESSAGE_TYPE_MAP = {
        "audio": "audio",
        "bot": "new_chat_members",
        "button": None,
        "command": "text",
        "contact": "contact",
        "document": "document",
        "email": None,
        "forward": None,
        "forward_channel": None,
        "game": None,
        "gif": "animation",
        "inline": None,
        "invoice": None,
        "location": "location",
        "phone": None,
        "photo": "photo",
        "poll": "poll",
        "rtl": None,
        "spoiler": "has_media_spoiler",
        "sticker": "sticker",
        "url": "text",
        "video": "video",
        "video_note": "video_note",
        "voice": "voice",
        "mention": "text",
        "caption": "caption",
        "no_caption": None,
        "emoji_only": None,
        "unofficial_client": None,
        "arabic": "text",
        "farsi": "text",
        "links": "text",
        "images": "photo",
    }

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("lock", self.cmd_lock)
        self.register_command("unlock", self.cmd_unlock)
        self.register_command("locks", self.cmd_locks)
        self.register_command("locktypes", self.cmd_locktypes)

    def _is_locked(self, ctx: NexusContext, lock_type: str) -> bool:
        """Check if a lock type is active."""
        locks = ctx.group.module_configs.get("locks", {})
        active_locks = locks.get("active_locks", {})
        return active_locks.get(lock_type, False)

    def _get_message_types(self, message: Message) -> list:
        """Get all content types for a message."""
        types = []

        if message.audio:
            types.append("audio")
        if message.new_chat_members:
            types.append("bot")
        if message.contact:
            types.append("contact")
        if message.document:
            types.append("document")
        if message.animation:
            types.append("gif")
        if message.location:
            types.append("location")
        if message.photo:
            types.append("photo")
        if message.poll:
            types.append("poll")
        if message.sticker:
            types.append("sticker")
        if message.video:
            types.append("video")
        if message.video_note:
            types.append("video_note")
        if message.voice:
            types.append("voice")
        if message.text:
            types.append("text")

        return types

    async def on_message(self, ctx: NexusContext) -> bool:
        """Handle new message and check locks."""
        if not ctx.message:
            return False

        message = ctx.message
        message_types = self._get_message_types(message)
        config = ctx.group.module_configs.get("locks", {})
        active_locks = config.get("active_locks", {})

        # Check each message type against locks
        for msg_type in message_types:
            # Check direct lock
            if active_locks.get(msg_type, False):
                await self._apply_lock(ctx, msg_type)
                return True

            # Check pattern locks
            if msg_type == "text":
                # Check for links
                if active_locks.get("links", False):
                    if message.entities:
                        for entity in message.entities:
                            if entity.type in ["url", "text_link"]:
                                await self._apply_lock(ctx, "links")
                                return True

                if "http://" in message.text.lower() or "https://" in message.text.lower():
                    await self._apply_lock(ctx, "links")
                    return True

                # Check for mentions
                if active_locks.get("mention", False):
                    if message.entities:
                        for entity in message.entities:
                            if entity.type in ["mention", "text_mention"]:
                                await self._apply_lock(ctx, "mention")
                                return True

                if "@" in message.text:
                    await self._apply_lock(ctx, "mention")
                    return True

                # Check emoji only
                if active_locks.get("emoji_only", False):
                    # Check if message contains only emojis
                    import re
                    emoji_pattern = re.compile(r'^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U00002702-\U000027B0\U000024C2-\U0001F251]+$')
                    if emoji_pattern.fullmatch(message.text.strip()):
                        await self._apply_lock(ctx, "emoji_only")
                        return True

            # Check no caption
            if msg_type in ["photo", "video", "document", "animation"]:
                if active_locks.get("no_caption", False):
                    if not message.caption:
                        await self._apply_lock(ctx, "no_caption")
                        return True

            # Check caption
            if active_locks.get("caption", False):
                if message.caption and len(message.caption) > 0:
                    await self._apply_lock(ctx, "caption")
                    return True

        return False

    async def _apply_lock(self, ctx: NexusContext, lock_type: str):
        """Apply lock action."""
        config = ctx.group.module_configs.get("locks", {})
        lock_mode = config.get("lock_mode", "delete")

        if lock_mode == "delete":
            await ctx.delete_message()
        elif lock_mode == "warn":
            if ctx.target_user:
                from bot.core.context import MemberProfile
                # Create minimal profile for target
                target = MemberProfile(
                    id=0,
                    user_id=ctx.user.user_id,
                    group_id=ctx.group.id,
                    telegram_id=ctx.user.telegram_id,
                    username=ctx.user.username,
                    first_name=ctx.user.first_name,
                    last_name=ctx.user.last_name,
                    role=ctx.user.role,
                    trust_score=ctx.user.trust_score,
                    xp=ctx.user.xp,
                    level=ctx.user.level,
                    warn_count=ctx.user.warn_count,
                    is_muted=ctx.user.is_muted,
                    is_banned=ctx.user.is_banned,
                    is_approved=ctx.user.is_approved,
                    is_whitelisted=ctx.user.is_whitelisted,
                    joined_at=ctx.group.member_count,
                    message_count=ctx.user.message_count,
                    custom_title=ctx.user.custom_title,
                )
                ctx.set_target(target)
                await ctx.warn_user(target, f"Lock violation: {lock_type}")

    async def cmd_lock(self, ctx: NexusContext):
        """Lock a content type."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("❌ Usage: /lock <type> [mode] [duration]")
            await ctx.reply(f"\nAvailable types: {', '.join(self.LOCK_TYPES[:10])}...")
            return

        lock_type = args[0].lower()
        if lock_type not in self.LOCK_TYPES:
            await ctx.reply(f"❌ Unknown lock type. Use /locktypes to see all types.")
            return

        mode = args[1].lower() if len(args) > 1 else "delete"
        duration = ctx.parse_duration(args[2]) if len(args) > 2 else None

        if mode not in ["delete", "warn", "mute", "kick", "ban", "tban", "tmute"]:
            await ctx.reply("❌ Invalid mode. Use: delete, warn, mute, kick, ban, tban, tmute")
            return

        # Update config
        config = ctx.group.module_configs.get("locks", {})
        if "active_locks" not in config:
            config["active_locks"] = {}
        config["active_locks"][lock_type] = True
        config["lock_mode"] = mode
        if duration:
            config["lock_duration"] = duration

        # Save to database
        if ctx.db:
            from shared.models import Lock
            lock = ctx.db.execute(
                f"""
                SELECT * FROM locks
                WHERE group_id = {ctx.group.id} AND lock_type = '{lock_type}'
                LIMIT 1
                """
            ).fetchone()

            if lock:
                ctx.db.execute(
                    f"""
                    UPDATE locks
                    SET is_locked = TRUE,
                        mode = '{mode}',
                        mode_duration = {duration or 'NULL'}
                    WHERE id = {lock[0]}
                    """
                )
            else:
                lock = Lock(
                    group_id=ctx.group.id,
                    lock_type=lock_type,
                    is_locked=True,
                    mode=mode,
                    mode_duration=duration,
                )
                ctx.db.add(lock)

        duration_text = f" ({ctx._format_duration(duration)})" if duration else ""
        await ctx.reply(f"🔒 Locked: {lock_type} ({mode}{duration_text})")

    async def cmd_unlock(self, ctx: NexusContext):
        """Unlock a content type."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("❌ Usage: /unlock <type>")
            return

        lock_type = args[0].lower()
        if lock_type not in self.LOCK_TYPES:
            await ctx.reply(f"❌ Unknown lock type. Use /locktypes to see all types.")
            return

        # Update config
        config = ctx.group.module_configs.get("locks", {})
        if "active_locks" not in config:
            config["active_locks"] = {}
        config["active_locks"][lock_type] = False

        # Save to database
        if ctx.db:
            from shared.models import Lock
            ctx.db.execute(
                f"""
                UPDATE locks
                SET is_locked = FALSE
                WHERE group_id = {ctx.group.id} AND lock_type = '{lock_type}'
                """
            )

        await ctx.reply(f"🔓 Unlocked: {lock_type}")

    async def cmd_locks(self, ctx: NexusContext):
        """List all active locks."""
        config = ctx.group.module_configs.get("locks", {})
        active_locks = config.get("active_locks", {})

        active = [lock_type for lock_type, locked in active_locks.items() if locked]

        if not active:
            await ctx.reply("🔓 No active locks")
            return

        text = "🔒 **Active Locks:**\n\n"
        text += "\n".join([f"• {lock}" for lock in active])

        await ctx.reply(text, parse_mode="Markdown")

    async def cmd_locktypes(self, ctx: NexusContext):
        """List all available lock types."""
        text = "🔒 **Available Lock Types:**\n\n"
        text += "**Basic:**\n"
        text += "• audio, bot, command, contact, document, email, game\n"
        text += "• gif, image, invoice, location, phone, photo, poll\n"
        text += "• sticker, url, video, voice\n\n"
        text += "**Advanced:**\n"
        text += "• forward, forward_channel - Lock forwarded messages\n"
        text += "• link, links - Lock URLs\n"
        text += "• mention - Lock @mentions\n"
        text += "• caption, no_caption - Lock media captions\n"
        text += "• emoji_only - Allow only emoji messages\n"
        text += "• rtl - Lock right-to-left text\n"
        text += "• unofficial_client - Lock unofficial clients\n"
        text += "• arabic, farsi - Lock specific scripts\n\n"
        text += "**Modes:**\n"
        text += "• delete - Delete the message\n"
        text += "• warn - Warn the user\n"
        text += "• mute - Mute the user\n"
        text += "• kick - Kick the user\n"
        text += "• ban - Ban the user\n"
        text += "• tban - Temporary ban\n"
        text += "• tmute - Temporary mute\n\n"
        text += "**Usage:**\n"
        text += "/lock <type> [mode] [duration]\n"
        text += "/unlock <type>\n"
        text += "/locks - View active locks"

        await ctx.reply(text, parse_mode="Markdown")
