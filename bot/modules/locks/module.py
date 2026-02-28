"""Locks module implementation."""

from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, EventType, ModuleCategory, NexusModule


LOCK_TYPES = [
    "audio", "bot", "button", "command", "contact", "document", "email",
    "forward", "forward_channel", "game", "gif", "inline", "invoice",
    "location", "phone", "photo", "poll", "rtl", "spoiler", "sticker",
    "url", "video", "video_note", "voice", "mention", "caption",
    "no_caption", "emoji_only", "unofficial_client", "arabic", "farsi",
]


class LocksConfig(BaseModel):
    """Locks module configuration."""
    pass  # Individual locks are stored in the database


class LocksModule(NexusModule):
    """Content type locks module."""

    name = "locks"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Lock specific content types like links, stickers, forwards"
    category = ModuleCategory.ANTISPAM

    config_schema = LocksConfig
    default_config = {}

    commands = [
        CommandDef(
            name="lock",
            description="Lock a content type.",
            admin_only=True,
            args="<type>",
        ),
        CommandDef(
            name="unlock",
            description="Unlock a content type.",
            admin_only=True,
            args="<type>",
        ),
        CommandDef(
            name="locktypes",
            description="List all available lock types.",
            admin_only=True,
        ),
        CommandDef(
            name="locks",
            description="Show current locks.",
            admin_only=True,
        ),
    ]

    listeners = [EventType.MESSAGE]

    async def on_message(self, ctx: NexusContext) -> bool:
        """Handle messages and commands."""
        if not ctx.message:
            return False

        # Check for commands
        if ctx.message.text:
            text = ctx.message.text.split()[0].lower()

            if text == "/lock":
                return await self._handle_lock(ctx)
            elif text == "/unlock":
                return await self._handle_unlock(ctx)
            elif text == "/locktypes":
                return await self._handle_locktypes(ctx)
            elif text == "/locks":
                return await self._handle_locks(ctx)

        # Check content locks
        return await self._check_content_locks(ctx)

    async def _handle_lock(self, ctx: NexusContext) -> bool:
        """Handle /lock command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        text = ctx.message.text.split()
        if len(text) < 2:
            await ctx.reply("⚠️ Usage: /lock <type>. Use /locktypes to see available types.")
            return True

        lock_type = text[1].lower()
        if lock_type not in LOCK_TYPES:
            await ctx.reply(f"❌ Unknown lock type: {lock_type}. Use /locktypes to see available types.")
            return True

        if ctx.db:
            from shared.models import Lock
            await ctx.db.execute(
                f"""
                INSERT INTO locks (group_id, lock_type, is_locked)
                VALUES ({ctx.group.id}, '{lock_type}', TRUE)
                ON CONFLICT (group_id, lock_type) DO UPDATE
                SET is_locked = TRUE
                """
            )
            await ctx.db.commit()

        await ctx.reply(f"🔒 {lock_type} has been locked.")
        return True

    async def _handle_unlock(self, ctx: NexusContext) -> bool:
        """Handle /unlock command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        text = ctx.message.text.split()
        if len(text) < 2:
            await ctx.reply("⚠️ Usage: /unlock <type>")
            return True

        lock_type = text[1].lower()

        if ctx.db:
            from shared.models import Lock
            await ctx.db.execute(
                f"""
                UPDATE locks
                SET is_locked = FALSE
                WHERE group_id = {ctx.group.id} AND lock_type = '{lock_type}'
                """
            )
            await ctx.db.commit()

        await ctx.reply(f"🔓 {lock_type} has been unlocked.")
        return True

    async def _handle_locktypes(self, ctx: NexusContext) -> bool:
        """Handle /locktypes command."""
        text = "📋 <b>Available Lock Types:</b>\n\n"
        text += ", ".join(LOCK_TYPES)
        text += "\n\n<b>Usage:</b> /lock <type> or /unlock <type>"

        await ctx.reply(text)
        return True

    async def _handle_locks(self, ctx: NexusContext) -> bool:
        """Handle /locks command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        if ctx.db:
            from shared.models import Lock
            result = await ctx.db.execute(
                f"""
                SELECT lock_type FROM locks
                WHERE group_id = {ctx.group.id} AND is_locked = TRUE
                """
            )
            locked = [row[0] for row in result.fetchall()]

            if locked:
                text = "🔒 <b>Currently Locked:</b>\n\n"
                text += "\n".join(f"  • {lt}" for lt in locked)
            else:
                text = "🔓 No content types are currently locked."

            await ctx.reply(text)

        return True

    async def _check_content_locks(self, ctx: NexusContext) -> bool:
        """Check if message violates any content locks."""
        if not ctx.message or ctx.user.is_moderator:
            return False

        if ctx.db:
            from shared.models import Lock
            result = await ctx.db.execute(
                f"""
                SELECT lock_type, mode FROM locks
                WHERE group_id = {ctx.group.id} AND is_locked = TRUE
                """
            )
            locks = {row[0]: row[1] for row in result.fetchall()}

            if not locks:
                return False

            msg = ctx.message

            # Check different lock types
            lock_triggers = {
                "url": msg.entities and any(e.type in ["url", "text_link"] for e in msg.entities),
                "forward": msg.forward_from or msg.forward_from_chat,
                "photo": msg.photo,
                "video": msg.video,
                "audio": msg.audio or msg.voice,
                "document": msg.document,
                "sticker": msg.sticker,
                "gif": msg.animation,
                "poll": msg.poll,
                "location": msg.location or msg.venue,
                "contact": msg.contact,
                "game": msg.game,
                "command": msg.text and msg.text.startswith("/"),
            }

            for lock_type, triggered in lock_triggers.items():
                if lock_type in locks and triggered:
                    mode = locks.get(lock_type, "delete")

                    if mode == "delete":
                        await ctx.delete_message()
                    elif mode == "warn":
                        await ctx.delete_message()
                        await ctx.warn_user(ctx.user, f"Locked content: {lock_type}", silent=True)
                    elif mode == "mute":
                        await ctx.delete_message()
                        await ctx.mute_user(ctx.user, 300, f"Locked content: {lock_type}", silent=True)
                    elif mode == "kick":
                        await ctx.delete_message()
                        await ctx.kick_user(ctx.user, f"Locked content: {lock_type}")

                    return True

        return False
