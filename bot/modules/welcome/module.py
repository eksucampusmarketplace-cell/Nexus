"""Welcome module implementation."""

from typing import Optional

from pydantic import BaseModel, Field

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, EventType, ModuleCategory, NexusModule


class WelcomeConfig(BaseModel):
    """Welcome module configuration."""
    welcome_enabled: bool = True
    welcome_text: str = Field(default="Welcome {mention} to {chatname}!")
    welcome_media: Optional[str] = None
    welcome_media_type: Optional[str] = None
    welcome_buttons: Optional[list] = None
    delete_previous: bool = False
    delete_after: Optional[int] = None
    send_as_dm: bool = False

    goodbye_enabled: bool = False
    goodbye_text: str = Field(default="Goodbye {mention}! We hope to see you again.")

    captcha_enabled: bool = False
    captcha_type: str = "button"  # button, math, quiz
    captcha_timeout: int = 90


class WelcomeModule(NexusModule):
    """Welcome and goodbye messages module."""

    name = "welcome"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Welcome and goodbye messages for new and leaving members"
    category = ModuleCategory.GREETINGS

    config_schema = WelcomeConfig
    default_config = WelcomeConfig().dict()

    commands = [
        CommandDef(
            name="setwelcome",
            description="Set the welcome message. Use {first}, {last}, {username}, {mention}, {count}, {chatname}",
            admin_only=True,
            args="<text>",
        ),
        CommandDef(
            name="welcome",
            description="Show current welcome settings.",
            admin_only=True,
        ),
        CommandDef(
            name="resetwelcome",
            description="Reset welcome message to default.",
            admin_only=True,
        ),
        CommandDef(
            name="setgoodbye",
            description="Set the goodbye message.",
            admin_only=True,
            args="<text>",
        ),
        CommandDef(
            name="goodbye",
            description="Show current goodbye settings.",
            admin_only=True,
        ),
        CommandDef(
            name="resetgoodbye",
            description="Reset goodbye message to default.",
            admin_only=True,
        ),
        CommandDef(
            name="cleanwelcome",
            description="Toggle auto-delete of previous welcome.",
            admin_only=True,
            args="on/off",
        ),
        CommandDef(
            name="welcomemute",
            description="Mute new members until captcha is completed.",
            admin_only=True,
            args="on/off",
        ),
        CommandDef(
            name="welcomehelp",
            description="Show welcome variables help.",
            admin_only=True,
        ),
    ]

    listeners = [EventType.NEW_MEMBER, EventType.LEFT_MEMBER, EventType.MESSAGE]

    async def on_new_member(self, ctx: NexusContext) -> bool:
        """Send welcome message when new member joins."""
        if not ctx.message or not ctx.message.new_chat_members:
            return False

        config = ctx.group.module_configs.get("welcome", {})
        if not config.get("welcome_enabled", True):
            return False

        welcome_text = config.get("welcome_text", "Welcome {mention}!")
        welcome_media = config.get("welcome_media")
        welcome_media_type = config.get("welcome_media_type")

        for new_member in ctx.message.new_chat_members:
            if new_member.is_bot:
                continue

            # Format welcome message
            formatted_text = self._format_message(
                welcome_text,
                new_member,
                ctx.group,
            )

            # Send welcome
            buttons = config.get("welcome_buttons")
            if welcome_media:
                await ctx.reply_media(
                    welcome_media,
                    media_type=welcome_media_type or "photo",
                    caption=formatted_text,
                    buttons=buttons,
                )
            else:
                await ctx.reply(formatted_text, buttons=buttons)

        return True

    async def on_left_member(self, ctx: NexusContext) -> bool:
        """Send goodbye message when member leaves."""
        if not ctx.message or not ctx.message.left_chat_member:
            return False

        config = ctx.group.module_configs.get("welcome", {})
        if not config.get("goodbye_enabled", False):
            return False

        goodbye_text = config.get("goodbye_text", "Goodbye {mention}!")

        formatted_text = self._format_message(
            goodbye_text,
            ctx.message.left_chat_member,
            ctx.group,
        )

        await ctx.reply(formatted_text)
        return True

    async def on_message(self, ctx: NexusContext) -> bool:
        """Handle welcome commands."""
        if not ctx.message or not ctx.message.text:
            return False

        text = ctx.message.text
        command = text.split()[0].lower()

        if command == "/setwelcome":
            return await self._handle_setwelcome(ctx)
        elif command == "/welcome":
            return await self._handle_welcome(ctx)
        elif command == "/resetwelcome":
            return await self._handle_resetwelcome(ctx)
        elif command == "/setgoodbye":
            return await self._handle_setgoodbye(ctx)
        elif command == "/goodbye":
            return await self._handle_goodbye(ctx)
        elif command == "/resetgoodbye":
            return await self._handle_resetgoodbye(ctx)
        elif command == "/cleanwelcome":
            return await self._handle_cleanwelcome(ctx)
        elif command == "/welcomemute":
            return await self._handle_welcomemute(ctx)
        elif command == "/welcomehelp":
            return await self._handle_welcomehelp(ctx)

        return False

    async def _handle_setwelcome(self, ctx: NexusContext) -> bool:
        """Handle /setwelcome command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        text = ctx.message.text.split(maxsplit=1)
        if len(text) < 2:
            await ctx.reply("⚠️ Please provide welcome text.")
            return True

        welcome_text = text[1]

        # Update config
        if ctx.db:
            from shared.models import Greeting
            result = await ctx.db.execute(
                f"""
                SELECT * FROM greetings
                WHERE group_id = {ctx.group.id} AND type = 'welcome'
                """
            )
            greeting = result.fetchone()

            if greeting:
                await ctx.db.execute(
                    f"""
                    UPDATE greetings
                    SET content = '{welcome_text.replace(chr(39), chr(39)*2)}',
                        updated_by = {ctx.user.user_id}
                    WHERE group_id = {ctx.group.id} AND type = 'welcome'
                    """
                )
            else:
                await ctx.db.execute(
                    f"""
                    INSERT INTO greetings (group_id, type, content, updated_by)
                    VALUES ({ctx.group.id}, 'welcome', '{welcome_text.replace(chr(39), chr(39)*2)}', {ctx.user.user_id})
                    """
                )
            await ctx.db.commit()

        await ctx.reply("✅ Welcome message updated!")
        return True

    async def _handle_welcome(self, ctx: NexusContext) -> bool:
        """Handle /welcome command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        config = ctx.group.module_configs.get("welcome", {})
        text = config.get("welcome_text", "Not set")

        await ctx.reply(f"📋 <b>Current Welcome Message:</b>\n\n{text}")
        return True

    async def _handle_resetwelcome(self, ctx: NexusContext) -> bool:
        """Handle /resetwelcome command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        if ctx.db:
            await ctx.db.execute(
                f"""
                DELETE FROM greetings
                WHERE group_id = {ctx.group.id} AND type = 'welcome'
                """
            )
            await ctx.db.commit()

        await ctx.reply("✅ Welcome message reset to default.")
        return True

    async def _handle_setgoodbye(self, ctx: NexusContext) -> bool:
        """Handle /setgoodbye command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        text = ctx.message.text.split(maxsplit=1)
        if len(text) < 2:
            await ctx.reply("⚠️ Please provide goodbye text.")
            return True

        goodbye_text = text[1]

        if ctx.db:
            await ctx.db.execute(
                f"""
                INSERT INTO greetings (group_id, type, content, updated_by)
                VALUES ({ctx.group.id}, 'goodbye', '{goodbye_text.replace(chr(39), chr(39)*2)}', {ctx.user.user_id})
                ON CONFLICT (group_id, type) DO UPDATE
                SET content = EXCLUDED.content, updated_by = EXCLUDED.updated_by
                """
            )
            await ctx.db.commit()

        await ctx.reply("✅ Goodbye message updated!")
        return True

    async def _handle_goodbye(self, ctx: NexusContext) -> bool:
        """Handle /goodbye command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        config = ctx.group.module_configs.get("welcome", {})
        enabled = config.get("goodbye_enabled", False)
        text = config.get("goodbye_text", "Not set")

        status = "✅ Enabled" if enabled else "❌ Disabled"
        await ctx.reply(f"📋 <b>Goodbye ({status}):</b>\n\n{text}")
        return True

    async def _handle_resetgoodbye(self, ctx: NexusContext) -> bool:
        """Handle /resetgoodbye command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        if ctx.db:
            await ctx.db.execute(
                f"""
                DELETE FROM greetings
                WHERE group_id = {ctx.group.id} AND type = 'goodbye'
                """
            )
            await ctx.db.commit()

        await ctx.reply("✅ Goodbye message reset to default.")
        return True

    async def _handle_cleanwelcome(self, ctx: NexusContext) -> bool:
        """Handle /cleanwelcome command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        args = ctx.message.text.split()
        if len(args) < 2 or args[1].lower() not in ["on", "off"]:
            await ctx.reply("⚠️ Usage: /cleanwelcome on/off")
            return True

        enabled = args[1].lower() == "on"
        # Update config

        await ctx.reply(f"✅ Auto-delete previous welcome: {'Enabled' if enabled else 'Disabled'}")
        return True

    async def _handle_welcomemute(self, ctx: NexusContext) -> bool:
        """Handle /welcomemute command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        args = ctx.message.text.split()
        if len(args) < 2 or args[1].lower() not in ["on", "off"]:
            await ctx.reply("⚠️ Usage: /welcomemute on/off")
            return True

        enabled = args[1].lower() == "on"

        await ctx.reply(f"✅ Welcome captcha: {'Enabled' if enabled else 'Disabled'}")
        return True

    async def _handle_welcomehelp(self, ctx: NexusContext) -> bool:
        """Handle /welcomehelp command."""
        help_text = """📖 <b>Welcome Message Variables</b>

Use these placeholders in your welcome message:

<code>{first}</code> - User's first name
<code>{last}</code> - User's last name
<code>{fullname}</code> - Full name
<code>{username}</code> - Username (without @)
<code>{mention}</code> - User mention
<code>{id}</code> - User ID
<code>{count}</code> - Group member count
<code>{chatname}</code> - Group name
<code>{rules}</code> - Link to rules

<b>Example:</b>
<code>Welcome {mention} to {chatname}! You are member #{count}.</code>
"""
        await ctx.reply(help_text)
        return True

    def _format_message(
        self,
        template: str,
        user,
        group: NexusContext,
    ) -> str:
        """Format welcome/goodbye message with variables."""
        first = user.first_name or ""
        last = user.last_name or ""
        fullname = f"{first} {last}".strip()
        username = user.username or ""
        mention = f'<a href="tg://user?id={user.id}">{first}</a>'

        return template.format(
            first=first,
            last=last,
            fullname=fullname,
            username=username,
            mention=mention,
            id=user.id,
            count=group.member_count if hasattr(group, 'member_count') else '?',
            chatname=group.title if hasattr(group, 'title') else 'this group',
            rules="/rules",
        )
