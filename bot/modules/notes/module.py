"""Notes module - Saved notes system."""

from typing import Optional, List, Dict
from pydantic import BaseModel
from aiogram.types import Message

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule, EventType


class NotesConfig(BaseModel):
    """Configuration for notes module."""
    notes_enabled: bool = True
    private_notes_only: bool = False
    notes_per_page: int = 20


class NotesModule(NexusModule):
    """Saved notes system."""

    name = "notes"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Save and retrieve notes"
    category = ModuleCategory.UTILITY

    config_schema = NotesConfig
    default_config = NotesConfig().dict()

    commands = [
        CommandDef(
            name="save",
            description="Save a note",
            admin_only=True,
            args="<notename> <content>",
        ),
        CommandDef(
            name="get",
            description="Get a note",
            admin_only=False,
            args="<notename>",
        ),
        CommandDef(
            name="notes",
            description="List all notes",
            admin_only=False,
        ),
        CommandDef(
            name="clear",
            description="Delete a note",
            admin_only=True,
            args="<notename>",
        ),
        CommandDef(
            name="clearall",
            description="Delete all notes",
            admin_only=True,
        ),
    ]

    listeners = [
        EventType.MESSAGE,
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("save", self.cmd_save)
        self.register_command("get", self.cmd_get)
        self.register_command("notes", self.cmd_notes)
        self.register_command("clear", self.cmd_clear)
        self.register_command("clearall", self.cmd_clearall)

    async def on_message(self, ctx: NexusContext) -> bool:
        """Handle #notename triggers."""
        if not ctx.message or not ctx.message.text:
            return False

        text = ctx.message.text.strip()

        # Check if message starts with #
        if text.startswith("#"):
            notename = text[1:].split()[0]
            return await self._send_note(ctx, notename)

        # Check for /get trigger
        if text.startswith("/get "):
            notename = text[5:].split()[0]
            return await self._send_note(ctx, notename)

        return False

    async def _send_note(self, ctx: NexusContext, notename: str) -> bool:
        """Send a note by keyword."""
        if ctx.db:
            from shared.models import Note
            result = ctx.db.execute(
                f"""
                SELECT * FROM notes
                WHERE group_id = {ctx.group.id} AND keyword = '{notename}'
                LIMIT 1
                """
            )
            row = result.fetchone()

            if row:
                content = row[2]
                media_file_id = row[3]
                media_type = row[4]
                has_buttons = row[5]
                button_data = row[6]
                is_private = row[7]

                # Check if private and user is not creator
                if is_private and row[8] != ctx.user.user_id:
                    await ctx.reply("❌ This note is private")
                    return True

                # Send note
                if media_file_id:
                    await ctx.reply_media(media_file_id, media_type, caption=content)
                elif has_buttons and button_data:
                    buttons = self._parse_buttons(button_data)
                    await ctx.reply(content, buttons=buttons)
                else:
                    await ctx.reply(content)

                return True

        return False

    def _parse_buttons(self, button_data: Dict) -> Optional[List[List[Dict]]]:
        """Parse button data from JSON."""
        if not button_data or not isinstance(button_data, dict):
            return None

        try:
            rows = button_data.get("rows", [])
            buttons = []

            for row in rows:
                button_row = []
                for btn in row:
                    button = {
                        "text": btn.get("text", ""),
                        "url": btn.get("url"),
                        "callback_data": btn.get("callback_data"),
                    }
                    button_row.append(button)
                buttons.append(button_row)

            return buttons
        except Exception:
            return None

    async def cmd_save(self, ctx: NexusContext):
        """Save a note."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("❌ Usage: /save <notename> <content> or reply to media")
            return

        notename = args[0].lower()

        # Check if reply to media
        media_file_id = None
        media_type = None
        content = None

        if ctx.replied_to:
            if ctx.replied_to.photo:
                media_file_id = ctx.replied_to.photo[-1].file_id
                media_type = "photo"
                content = ctx.replied_to.caption or f"#{notename}"
            elif ctx.replied_to.video:
                media_file_id = ctx.replied_to.video.file_id
                media_type = "video"
                content = ctx.replied_to.caption or f"#{notename}"
            elif ctx.replied_to.animation:
                media_file_id = ctx.replied_to.animation.file_id
                media_type = "animation"
                content = ctx.replied_to.caption or f"#{notename}"
            elif ctx.replied_to.document:
                media_file_id = ctx.replied_to.document.file_id
                media_type = "document"
                content = ctx.replied_to.caption or f"#{notename}"
            elif ctx.replied_to.sticker:
                media_file_id = ctx.replied_to.sticker.file_id
                media_type = "sticker"
                content = f"#{notename}"
            elif ctx.replied_to.text:
                content = ctx.replied_to.text
                if len(args) > 1:
                    content = " ".join(args[1:])

        if not content:
            if len(args) > 1:
                content = " ".join(args[1:])

        if not content and not media_file_id:
            await ctx.reply("❌ Please provide content or reply to media")
            return

        # Save to database
        if ctx.db:
            from shared.models import Note
            existing = ctx.db.execute(
                f"""
                SELECT id FROM notes
                WHERE group_id = {ctx.group.id} AND keyword = '{notename}'
                LIMIT 1
                """
            ).fetchone()

            if existing:
                # Update existing note
                ctx.db.execute(
                    f"""
                    UPDATE notes
                    SET content = %s,
                        media_file_id = %s,
                        media_type = %s,
                        updated_at = NOW()
                    WHERE id = {existing[0]}
                    """,
                    (content, media_file_id, media_type)
                )
                await ctx.reply(f"✅ Note '{notename}' updated")
            else:
                # Create new note
                note = Note(
                    group_id=ctx.group.id,
                    keyword=notename,
                    content=content,
                    media_file_id=media_file_id,
                    media_type=media_type,
                    has_buttons=False,
                    created_by=ctx.user.user_id,
                )
                ctx.db.add(note)
                await ctx.reply(f"✅ Note '{notename}' saved")

    async def cmd_get(self, ctx: NexusContext):
        """Get a note."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("❌ Usage: /get <notename>")
            return

        notename = args[0].lower()
        await self._send_note(ctx, notename)

    async def cmd_notes(self, ctx: NexusContext):
        """List all notes."""
        if ctx.db:
            from shared.models import Note
            result = ctx.db.execute(
                f"""
                SELECT keyword, content, media_type, is_private, created_by
                FROM notes
                WHERE group_id = {ctx.group.id}
                ORDER BY keyword ASC
                """
            )

            notes = result.fetchall()

            if not notes:
                await ctx.reply("📝 No notes saved yet")
                return

            text = "📝 **Saved Notes:**\n\n"
            for row in notes:
                notename = row[0]
                has_media = row[2] is not None
                is_private = row[3]

                icon = "🔒" if is_private else "📄"
                media_icon = "📎" if has_media else ""

                text += f"{icon} **#{notename}** {media_icon}\n"

            await ctx.reply(text, parse_mode="Markdown")

    async def cmd_clear(self, ctx: NexusContext):
        """Delete a note."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("❌ Usage: /clear <notename>")
            return

        notename = args[0].lower()

        if ctx.db:
            from shared.models import Note
            result = ctx.db.execute(
                f"""
                DELETE FROM notes
                WHERE group_id = {ctx.group.id} AND keyword = '{notename}'
                """
            )

            await ctx.reply(f"✅ Note '{notename}' deleted")

    async def cmd_clearall(self, ctx: NexusContext):
        """Delete all notes."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        # Confirm
        # In a real implementation, we'd show a confirmation button

        if ctx.db:
            from shared.models import Note
            ctx.db.execute(
                f"""
                DELETE FROM notes
                WHERE group_id = {ctx.group.id}
                """
            )

            await ctx.reply("✅ All notes cleared")
