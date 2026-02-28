"""Info module - User and group information."""

from typing import Optional

from aiogram.types import User
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class InfoConfig(BaseModel):
    """Configuration for info module."""
    info_enabled: bool = True
    show_member_count: bool = True
    show_admin_list: bool = True


class InfoModule(NexusModule):
    """Information module."""

    name = "info"
    version = "1.0.0"
    author = "Nexus Team"
    description = "View user and group information"
    category = ModuleCategory.UTILITY

    config_schema = InfoConfig
    default_config = InfoConfig().dict()

    commands = [
        CommandDef(
            name="info",
            description="View user information",
            admin_only=False,
            args="[@user]",
        ),
        CommandDef(
            name="chatinfo",
            description="View group information",
            admin_only=False,
        ),
        CommandDef(
            name="id",
            description="Get user or chat ID",
            admin_only=False,
            args="[@user]",
        ),
        CommandDef(
            name="adminlist",
            description="List group admins",
            admin_only=False,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("info", self.cmd_info)
        self.register_command("chatinfo", self.cmd_chatinfo)
        self.register_command("id", self.cmd_id)
        self.register_command("adminlist", self.cmd_adminlist)

    def _get_target_user(self, ctx: NexusContext) -> Optional[User]:
        """Get target user from message."""
        # Try reply first
        if ctx.replied_to and ctx.replied_to.from_user:
            return ctx.replied_to.from_user

        # Try mention
        if ctx.message.entities:
            for entity in ctx.message.entities:
                if entity.type == "text_mention":
                    return entity.user

        # Try username in args
        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if args:
            username = args[0].lstrip("@")
            if username:
                # Search in cache/db
                pass  # Would implement DB lookup

        return ctx.message.from_user

    async def cmd_info(self, ctx: NexusContext):
        """View user information."""
        target = self._get_target_user(ctx)

        if not target:
            await ctx.reply(ctx.i18n.t("user_not_found"))
            return

        text = f"👤 **User Info**\n\n"
        text += f"**ID:** `{target.id}`\n"
        text += f"**First Name:** {target.first_name or 'N/A'}\n"
        text += f"**Last Name:** {target.last_name or 'N/A'}\n"
        text += f"**Username:** @{target.username or 'N/A'}\n"
        text += f"**Language:** {target.language_code or 'N/A'}\n"
        text += f"**Is Bot:** {'Yes' if target.is_bot else 'No'}\n"
        text += f"**Is Premium:** {'Yes' if target.is_premium else 'No'}\n"

        if ctx.db:
            from shared.models import Member
            result = ctx.db.execute(
                f"""
                SELECT m.*, u.telegram_id
                FROM members m
                JOIN users u ON m.user_id = u.id
                WHERE m.group_id = {ctx.group.id} AND u.telegram_id = {target.id}
                LIMIT 1
                """
            )
            row = result.fetchone()

            if row:
                text += f"\n📊 **Member Stats:**\n"
                text += f"**Role:** {row[9]}\n"
                text += f"**Trust Score:** {row[6]}/100\n"
                text += f"**XP:** {row[7]} (Level {row[8]})\n"
                text += f"**Messages:** {row[5]}\n"
                text += f"**Warnings:** {row[14]}\n"
                text += f"**Mutes:** {row[15]}\n"
                text += f"**Bans:** {row[17]}\n"
                text += f"**Joined:** {row[4].strftime('%Y-%m-%d %H:%M')}\n"
                text += f"**Is Approved:** {'Yes' if row[20] else 'No'}\n"
                text += f"**Is Whitelisted:** {'Yes' if row[21] else 'No'}\n"

        await ctx.reply(text, parse_mode="Markdown")

    async def cmd_chatinfo(self, ctx: NexusContext):
        """View group information."""
        chat = ctx.message.chat

        text = f"👥 **Group Info**\n\n"
        text += f"**ID:** `{chat.id}`\n"
        text += f"**Title:** {chat.title}\n"
        text += f"**Username:** @{chat.username or 'N/A'}\n"
        text += f"**Type:** {chat.type}\n"

        if chat.full_name:
            text += f"**Full Name:** {chat.full_name}\n"

        text += f"**Member Count:** {ctx.group.member_count}\n"
        text += f"**Language:** {ctx.group.language}\n"
        text += f"**Owner ID:** {ctx.group.owner_id or 'N/A'}\n"
        text += f"**Is Premium:** {'Yes' if ctx.group.is_premium else 'No'}\n"

        # Get enabled modules
        enabled_modules = ctx.group.enabled_modules
        text += f"\n🔧 **Enabled Modules ({len(enabled_modules)}):**\n"
        if enabled_modules:
            text += ", ".join(enabled_modules[:10])
            if len(enabled_modules) > 10:
                text += f" and {len(enabled_modules) - 10} more..."

        await ctx.reply(text, parse_mode="Markdown")

    async def cmd_id(self, ctx: NexusContext):
        """Get user or chat ID."""
        target = self._get_target_user(ctx)

        if not target:
            target = ctx.message.from_user

        chat = ctx.message.chat

        text = f"🆔 **IDs**\n\n"
        text += f"**User ID:** `{target.id}`\n"
        text += f"**Chat ID:** `{chat.id}`\n"
        text += f"**User Name:** {target.full_name}\n"
        text += f"**Username:** @{target.username or 'N/A'}\n"

        await ctx.reply(text, parse_mode="Markdown")

    async def cmd_adminlist(self, ctx: NexusContext):
        """List group admins."""
        try:
            admins = await ctx.bot.get_chat_administrators(ctx.group.telegram_id)

            if not admins:
                await ctx.reply("❌ Could not fetch admin list")
                return

            text = f"👑 **Admins** ({len(admins)}):\n\n"

            owner = None
            admins_list = []

            for admin in admins:
                if admin.status == "creator":
                    owner = admin
                else:
                    admins_list.append(admin)

            if owner:
                user = owner.user
                text += f"👑 **Owner:** {user.full_name}\n"
                text += f"   ID: `{user.id}`\n"
                text += f"   Username: @{user.username or 'N/A'}\n\n"

            if admins_list:
                text += f"👨‍💼 **Administrators:**\n"
                for admin in admins_list:
                    user = admin.user
                    text += f"• {user.full_name}"
                    if user.username:
                        text += f" (@{user.username})"
                    text += f"\n"

            if len(text) > 4096:
                text = f"👑 **Admins:** {len(admins)} total\n"
                text += f"Owner: {owner.user.full_name if owner else 'Unknown'}\n"
                text += f"Admins: {len(admins_list)}"

            await ctx.reply(text, parse_mode="Markdown")

        except Exception as e:
            await ctx.reply(f"❌ Error fetching admins: {e}")
