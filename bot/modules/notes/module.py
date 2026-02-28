"""Notes module implementation."""

from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, EventType, ModuleCategory, NexusModule


class NotesConfig(BaseModel):
    """Notes module configuration."""
    max_notes: int = 100
    max_note_length: int = 4096


class NotesModule(NexusModule):
    """Saved notes module."""

    name = "notes"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Save and retrieve notes with #keyword"
    category = ModuleCategory.UTILITY

    config_schema = NotesConfig
    default_config = NotesConfig().dict()

    commands = [
        CommandDef(
            name="save",
            description="Save a note. Reply to text or use: /save notename content",
            admin_only=True,
            args="<keyword> <content>",
        ),
        CommandDef(
            name="get",
            description="Get a saved note.",
            args="<keyword>",
        ),
        CommandDef(
            name="notes",
            description="List all saved notes.",
            admin_only=True,
        ),
        CommandDef(
            name="clear",
            description="Delete a specific note.",
            admin_only=True,
            args="<keyword>",
        ),
        CommandDef(
            name="clearall",
            description="Delete all notes.",
            admin_only=True,
        ),
    ]

    listeners = [EventType.MESSAGE]

    async def on_message(self, ctx: NexusContext) -> bool:
        """Handle messages."""
        if not ctx.message or not ctx.message.text:
            return False

        text = ctx.message.text

        # Check for #keyword
        if text.startswith("#") and " " not in text:
            keyword = text[1:].lower()
            return await self._get_note(ctx, keyword)

        # Check for commands
        command = text.split()[0].lower()

        if command == "/save":
            return await self._handle_save(ctx)
        elif command == "/get":
            return await self._handle_get(ctx)
        elif command == "/notes":
            return await self._handle_list(ctx)
        elif command == "/clear":
            return await self._handle_clear(ctx)
        elif command == "/clearall":
            return await self._handle_clearall(ctx)

        return False

    async def _handle_save(self, ctx: NexusContext) -> bool:
        """Handle /save command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        text = ctx.message.text.split(maxsplit=1)
        if len(text) < 2:
            await ctx.reply("⚠️ Usage: /save <keyword> <content>")
            return True

        parts = text[1].split(maxsplit=1)
        if len(parts) < 2:
            await ctx.reply("⚠️ Usage: /save <keyword> <content>")
            return True

        keyword = parts[0].lower()
        content = parts[1]

        # Check if note exists
        if ctx.db:
            from shared.models import Note
            result = await ctx.db.execute(
                f"""
                INSERT INTO notes (group_id, keyword, content, created_by)
                VALUES ({ctx.group.id}, '{keyword}', '{content.replace(chr(39), chr(39)*2)}', {ctx.user.user_id})
                ON CONFLICT (group_id, keyword) DO UPDATE
                SET content = EXCLUDED.content, updated_at = NOW(), created_by = EXCLUDED.created_by
                RETURNING id
                """
            )
            await ctx.db.commit()

        await ctx.reply(f"✅ Note '#{keyword}' saved!")
        return True

    async def _get_note(self, ctx: NexusContext, keyword: str) -> bool:
        """Get a note by keyword."""
        if not ctx.db:
            return False

        from shared.models import Note
        result = await ctx.db.execute(
            f"""
            SELECT content, has_buttons, button_data FROM notes
            WHERE group_id = {ctx.group.id} AND keyword = '{keyword}'
            """
        )
        note = result.fetchone()

        if note:
            buttons = note[2] if note[1] else None
            await ctx.reply(note[0], buttons=buttons)
            return True

        return False

    async def _handle_get(self, ctx: NexusContext) -> bool:
        """Handle /get command."""
        text = ctx.message.text.split()
        if len(text) < 2:
            await ctx.reply("⚠️ Usage: /get <keyword>")
            return True

        keyword = text[1].lower()
        found = await self._get_note(ctx, keyword)

        if not found:
            await ctx.reply(f"❌ Note '#{keyword}' not found.")

        return True

    async def _handle_list(self, ctx: NexusContext) -> bool:
        """Handle /notes command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        if not ctx.db:
            return True

        from shared.models import Note
        result = await ctx.db.execute(
            f"""
            SELECT keyword FROM notes
            WHERE group_id = {ctx.group.id}
            ORDER BY keyword
            """
        )
        notes = [row[0] for row in result.fetchall()]

        if notes:
            text = "📋 <b>Saved Notes:</b>\n\n"
            text += "\n".join(f"  • #{note}" for note in notes)
        else:
            text = "📋 No notes saved yet.\n\nUse /save to create one."

        await ctx.reply(text)
        return True

    async def _handle_clear(self, ctx: NexusContext) -> bool:
        """Handle /clear command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        text = ctx.message.text.split()
        if len(text) < 2:
            await ctx.reply("⚠️ Usage: /clear <keyword>")
            return True

        keyword = text[1].lower()

        if ctx.db:
            await ctx.db.execute(
                f"""
                DELETE FROM notes
                WHERE group_id = {ctx.group.id} AND keyword = '{keyword}'
                """
            )
            await ctx.db.commit()

        await ctx.reply(f"✅ Note '#{keyword}' deleted.")
        return True

    async def _handle_clearall(self, ctx: NexusContext) -> bool:
        """Handle /clearall command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        if ctx.db:
            await ctx.db.execute(
                f"""
                DELETE FROM notes
                WHERE group_id = {ctx.group.id}
                """
            )
            await ctx.db.commit()

        await ctx.reply("✅ All notes deleted.")
        return True
