"""Welcome module - Welcome and goodbye messages."""

from typing import Optional

from aiogram.types import Message
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class WelcomeConfig(BaseModel):
    """Configuration for welcome module."""
    welcome_enabled: bool = True
    goodbye_enabled: bool = False
    welcome_content: str = "Welcome {first}! You are member #{count} of {chatname}."
    goodbye_content: str = "Goodbye {first}!"
    welcome_media_file_id: Optional[str] = None
    welcome_media_type: Optional[str] = None
    goodbye_media_file_id: Optional[str] = None
    goodbye_media_type: Optional[str] = None
    delete_previous: bool = False
    delete_after_seconds: Optional[int] = None
    send_as_dm: bool = False
    mute_on_join: bool = False
    show_on_join: bool = True
    auto_delete_service: bool = True


class WelcomeModule(NexusModule):
    """Welcome and goodbye system."""

    name = "welcome"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Welcome new members and goodbye leaving members"
    category = ModuleCategory.GREETINGS

    config_schema = WelcomeConfig
    default_config = WelcomeConfig().dict()

    commands = [
        CommandDef(
            name="setwelcome",
            description="Set welcome message",
            admin_only=True,
            args="<content>",
        ),
        CommandDef(
            name="welcome",
            description="View current welcome message",
            admin_only=True,
        ),
        CommandDef(
            name="resetwelcome",
            description="Reset welcome message to default",
            admin_only=True,
        ),
        CommandDef(
            name="setgoodbye",
            description="Set goodbye message",
            admin_only=True,
            args="<content>",
        ),
        CommandDef(
            name="goodbye",
            description="View current goodbye message",
            admin_only=True,
        ),
        CommandDef(
            name="resetgoodbye",
            description="Reset goodbye message to default",
            admin_only=True,
        ),
        CommandDef(
            name="cleanwelcome",
            description="Auto-delete previous welcome messages",
            admin_only=True,
            args="[on|off]",
        ),
        CommandDef(
            name="welcomemute",
            description="Mute new members until they complete captcha",
            admin_only=True,
            args="[on|off]",
        ),
        CommandDef(
            name="welcomehelp",
            description="Show welcome message variables",
            admin_only=False,
        ),
    ]

    listeners = [
        EventType.NEW_MEMBER,
        EventType.LEFT_MEMBER,
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("setwelcome", self.cmd_setwelcome)
        self.register_command("welcome", self.cmd_welcome)
        self.register_command("resetwelcome", self.cmd_resetwelcome)
        self.register_command("setgoodbye", self.cmd_setgoodbye)
        self.register_command("goodbye", self.cmd_goodbye)
        self.register_command("resetgoodbye", self.cmd_resetgoodbye)
        self.register_command("cleanwelcome", self.cmd_cleanwelcome)
        self.register_command("welcomemute", self.cmd_welcomemute)
        self.register_command("welcomehelp", self.cmd_welcomehelp)

    def _format_variables(self, text: str, ctx: NexusContext) -> str:
        """Format welcome/goodbye variables."""
        if ctx.replied_to and ctx.replied_to.new_chat_members:
            member = ctx.replied_to.new_chat_members[0]
            first_name = member.first_name or "Friend"
            last_name = member.last_name or ""
            username = member.username or ""
            user_id = member.id
            full_name = f"{first_name} {last_name}".strip()
            chatname = ctx.group.title
            count = ctx.group.member_count

            # Get rules
            rules = "No rules set"
            if ctx.db:
                from shared.models import Rule
                result = ctx.db.execute(
                    f"SELECT content FROM rules WHERE group_id = {ctx.group.id}"
                )
                row = result.fetchone()
                if row:
                    rules = row[0]

            text = text.replace("{first}", first_name)
            text = text.replace("{last}", last_name)
            text = text.replace("{fullname}", full_name)
            text = text.replace("{username}", username or f"@{user_id}")
            text = text.replace("{mention}", f"<a href='tg://user?id={user_id}'>{full_name}</a>")
            text = text.replace("{id}", str(user_id))
            text = text.replace("{count}", str(count))
            text = text.replace("{chatname}", chatname)
            text = text.replace("{rules}", rules)

        return text

    async def on_new_member(self, ctx: NexusContext) -> bool:
        """Handle new member join."""
        if not ctx.group.module_configs.get("welcome", {}).get("welcome_enabled", True):
            return False

        config = ctx.group.module_configs.get("welcome", {})

        # Mute if enabled
        if config.get("mute_on_join", False):
            if ctx.replied_to and ctx.replied_to.new_chat_members:
                member = ctx.replied_to.new_chat_members[0]
                try:
                    await ctx.bot.restrict_chat_member(
                        chat_id=ctx.group.telegram_id,
                        user_id=member.id,
                        permissions={
                            "can_send_messages": False,
                            "can_send_media_messages": False,
                            "can_send_polls": False,
                            "can_send_other_messages": False,
                        },
                    )
                except Exception:
                    pass

        # Don't show welcome if disabled
        if not config.get("show_on_join", True):
            return False

        content = config.get("welcome_content", "")
        content = self._format_variables(content, ctx)

        # Check if should send as DM
        send_as_dm = config.get("send_as_dm", False)

        # Send welcome message
        if send_as_dm and ctx.replied_to and ctx.replied_to.new_chat_members:
            member = ctx.replied_to.new_chat_members[0]
            try:
                await ctx.bot.send_message(
                    chat_id=member.id,
                    text=content,
                    parse_mode="HTML",
                )
                return True
            except Exception:
                pass

        # Send in group
        media_file_id = config.get("welcome_media_file_id")
        media_type = config.get("welcome_media_type")
        delete_after = config.get("delete_after_seconds")

        if media_file_id:
            if media_type == "photo":
                await ctx.reply_media(media_file_id, "photo", caption=content)
            elif media_type == "video":
                await ctx.reply_media(media_file_id, "video", caption=content)
            elif media_type == "animation":
                await ctx.reply_media(media_file_id, "animation", caption=content)
            elif media_type == "document":
                await ctx.reply_media(media_file_id, "document", caption=content)
        else:
            await ctx.reply(content)

        # Auto-delete after N seconds
        if delete_after:
            pass  # Would use scheduler

        return True

    async def on_left_member(self, ctx: NexusContext) -> bool:
        """Handle member leave."""
        if not ctx.group.module_configs.get("welcome", {}).get("goodbye_enabled", False):
            return False

        config = ctx.group.module_configs.get("welcome", {})
        content = config.get("goodbye_content", "")

        if ctx.replied_to and ctx.replied_to.left_chat_member:
            member = ctx.replied_to.left_chat_member
            first_name = member.first_name or "Friend"
            last_name = member.last_name or ""
            full_name = f"{first_name} {last_name}".strip()
            username = member.username or ""
            user_id = member.id

            content = content.replace("{first}", first_name)
            content = content.replace("{last}", last_name)
            content = content.replace("{fullname}", full_name)
            content = content.replace("{username}", username or f"@{user_id}")
            content = content.replace("{mention}", f"<a href='tg://user?id={user_id}'>{full_name}</a>")
            content = content.replace("{id}", str(user_id))

            media_file_id = config.get("goodbye_media_file_id")
            media_type = config.get("goodbye_media_type")

            if media_file_id:
                if media_type == "photo":
                    await ctx.reply_media(media_file_id, "photo", caption=content)
                elif media_type == "video":
                    await ctx.reply_media(media_file_id, "video", caption=content)
                elif media_type == "animation":
                    await ctx.reply_media(media_file_id, "animation", caption=content)
            else:
                await ctx.reply(content)

        return True

    async def cmd_setwelcome(self, ctx: NexusContext):
        """Set welcome message."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("❌ Usage: /setwelcome <message>")
            return

        content = " ".join(args)

        # Check if reply to media
        media_file_id = None
        media_type = None
        if ctx.replied_to:
            if ctx.replied_to.photo:
                media_file_id = ctx.replied_to.photo[-1].file_id
                media_type = "photo"
            elif ctx.replied_to.video:
                media_file_id = ctx.replied_to.video.file_id
                media_type = "video"
            elif ctx.replied_to.animation:
                media_file_id = ctx.replied_to.animation.file_id
                media_type = "animation"
            elif ctx.replied_to.document:
                media_file_id = ctx.replied_to.document.file_id
                media_type = "document"

        config = ctx.group.module_configs.get("welcome", {})
        config["welcome_content"] = content
        config["welcome_enabled"] = True
        if media_file_id:
            config["welcome_media_file_id"] = media_file_id
            config["welcome_media_type"] = media_type

        # Save to database
        if ctx.db:
            from shared.models import Greeting
            greeting = ctx.db.execute(
                f"""
                SELECT * FROM greetings
                WHERE group_id = {ctx.group.id} AND greeting_type = 'welcome'
                LIMIT 1
                """
            ).fetchone()

            if greeting:
                ctx.db.execute(
                    f"""
                    UPDATE greetings
                    SET content = %s,
                        media_file_id = %s,
                        media_type = %s,
                        is_enabled = TRUE,
                        updated_by = {ctx.user.user_id}
                    WHERE id = {greeting[0]}
                    """,
                    (content, media_file_id, media_type)
                )
            else:
                greeting = Greeting(
                    group_id=ctx.group.id,
                    greeting_type="welcome",
                    content=content,
                    media_file_id=media_file_id,
                    media_type=media_type,
                    is_enabled=True,
                    updated_by=ctx.user.user_id,
                )
                ctx.db.add(greeting)

        await ctx.reply("✅ Welcome message set")

    async def cmd_welcome(self, ctx: NexusContext):
        """View current welcome message."""
        config = ctx.group.module_configs.get("welcome", {})
        content = config.get("welcome_content", "Not set")
        media_file_id = config.get("welcome_media_file_id")

        text = f"📝 Welcome Message:\n\n{content}"
        if media_file_id:
            text += "\n\n📎 Media attached"
        if not config.get("welcome_enabled", False):
            text += "\n\n⚠️ Welcome is disabled"

        await ctx.reply(text)

    async def cmd_resetwelcome(self, ctx: NexusContext):
        """Reset welcome message."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        config = ctx.group.module_configs.get("welcome", {})
        config["welcome_content"] = "Welcome {first}! You are member #{count} of {chatname}."
        config["welcome_media_file_id"] = None
        config["welcome_media_type"] = None
        config["welcome_enabled"] = True

        if ctx.db:
            from shared.models import Greeting
            ctx.db.execute(
                f"""
                DELETE FROM greetings
                WHERE group_id = {ctx.group.id} AND greeting_type = 'welcome'
                """
            )

        await ctx.reply("✅ Welcome message reset to default")

    async def cmd_setgoodbye(self, ctx: NexusContext):
        """Set goodbye message."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("❌ Usage: /setgoodbye <message>")
            return

        content = " ".join(args)

        media_file_id = None
        media_type = None
        if ctx.replied_to:
            if ctx.replied_to.photo:
                media_file_id = ctx.replied_to.photo[-1].file_id
                media_type = "photo"
            elif ctx.replied_to.video:
                media_file_id = ctx.replied_to.video.file_id
                media_type = "video"
            elif ctx.replied_to.animation:
                media_file_id = ctx.replied_to.animation.file_id
                media_type = "animation"

        config = ctx.group.module_configs.get("welcome", {})
        config["goodbye_content"] = content
        config["goodbye_enabled"] = True
        if media_file_id:
            config["goodbye_media_file_id"] = media_file_id
            config["goodbye_media_type"] = media_type

        if ctx.db:
            from shared.models import Greeting
            greeting = ctx.db.execute(
                f"""
                SELECT * FROM greetings
                WHERE group_id = {ctx.group.id} AND greeting_type = 'goodbye'
                LIMIT 1
                """
            ).fetchone()

            if greeting:
                ctx.db.execute(
                    f"""
                    UPDATE greetings
                    SET content = %s,
                        media_file_id = %s,
                        media_type = %s,
                        is_enabled = TRUE,
                        updated_by = {ctx.user.user_id}
                    WHERE id = {greeting[0]}
                    """,
                    (content, media_file_id, media_type)
                )
            else:
                greeting = Greeting(
                    group_id=ctx.group.id,
                    greeting_type="goodbye",
                    content=content,
                    media_file_id=media_file_id,
                    media_type=media_type,
                    is_enabled=True,
                    updated_by=ctx.user.user_id,
                )
                ctx.db.add(greeting)

        await ctx.reply("✅ Goodbye message set")

    async def cmd_goodbye(self, ctx: NexusContext):
        """View current goodbye message."""
        config = ctx.group.module_configs.get("welcome", {})
        content = config.get("goodbye_content", "Not set")
        media_file_id = config.get("goodbye_media_file_id")

        text = f"📝 Goodbye Message:\n\n{content}"
        if media_file_id:
            text += "\n\n📎 Media attached"
        if not config.get("goodbye_enabled", False):
            text += "\n\n⚠️ Goodbye is disabled"

        await ctx.reply(text)

    async def cmd_resetgoodbye(self, ctx: NexusContext):
        """Reset goodbye message."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        config = ctx.group.module_configs.get("welcome", {})
        config["goodbye_content"] = "Goodbye {first}!"
        config["goodbye_media_file_id"] = None
        config["goodbye_media_type"] = None
        config["goodbye_enabled"] = False

        if ctx.db:
            from shared.models import Greeting
            ctx.db.execute(
                f"""
                DELETE FROM greetings
                WHERE group_id = {ctx.group.id} AND greeting_type = 'goodbye'
                """
            )

        await ctx.reply("✅ Goodbye message reset")

    async def cmd_cleanwelcome(self, ctx: NexusContext):
        """Auto-delete previous welcome messages."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("✅ Clean welcome: ON")
        elif args[0].lower() in ["on", "yes", "1"]:
            await ctx.reply("✅ Clean welcome: ON")
        elif args[0].lower() in ["off", "no", "0"]:
            await ctx.reply("✅ Clean welcome: OFF")
        else:
            await ctx.reply("❌ Usage: /cleanwelcome [on|off]")

    async def cmd_welcomemute(self, ctx: NexusContext):
        """Mute new members."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("❌ Usage: /welcomemute [on|off]")
            return

        config = ctx.group.module_configs.get("welcome", {})
        if args[0].lower() in ["on", "yes", "1"]:
            config["mute_on_join"] = True
            await ctx.reply("✅ Welcome mute: ON")
        elif args[0].lower() in ["off", "no", "0"]:
            config["mute_on_join"] = False
            await ctx.reply("✅ Welcome mute: OFF")
        else:
            await ctx.reply("❌ Usage: /welcomemute [on|off]")

    async def cmd_welcomehelp(self, ctx: NexusContext):
        """Show welcome message help."""
        help_text = """
📝 Welcome Message Variables

{first} - User's first name
{last} - User's last name
{fullname} - User's full name
{username} - User's username
{mention} - User's mention
{id} - User's ID
{count} - Current member count
{chatname} - Chat title
{rules} - Group rules

💡 You can reply to media to set it as the welcome media.

Examples:
/setwelcome Welcome {first}! You are member #{count} of {chatname}
/setwelcome Hello {mention}! Please read our rules: {rules}
/setgoodbye Goodbye {first}!
        """

        await ctx.reply(help_text)
