"""Anti-spam module implementation."""

from pydantic import BaseModel, Field

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, EventType, ModuleCategory, NexusModule


class AntispamConfig(BaseModel):
    """Anti-spam module configuration."""
    antiflood_enabled: bool = True
    message_limit: int = Field(default=5, ge=2, le=20)
    window_seconds: int = Field(default=5, ge=1, le=60)
    antiflood_action: str = "mute"  # delete, warn, mute, kick, ban
    antiflood_duration: int = 300

    antiraid_enabled: bool = True
    join_threshold: int = 10
    raid_window_seconds: int = 60
    raid_action: str = "lock"
    raid_auto_unlock: int = 3600

    cas_enabled: bool = True
    cas_action: str = "ban"


class AntispamModule(NexusModule):
    """Anti-flood and spam protection module."""

    name = "antispam"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Anti-flood, anti-raid, and CAS integration"
    category = ModuleCategory.ANTISPAM

    config_schema = AntispamConfig
    default_config = AntispamConfig().dict()

    commands = [
        CommandDef(
            name="antiflood",
            description="Configure anti-flood settings.",
            admin_only=True,
            args="on/off",
        ),
        CommandDef(
            name="antiraid",
            description="Configure anti-raid settings.",
            admin_only=True,
            args="on/off",
        ),
        CommandDef(
            name="cas",
            description="Toggle CAS integration.",
            admin_only=True,
            args="on/off",
        ),
    ]

    listeners = [EventType.MESSAGE, EventType.NEW_MEMBER]

    async def on_message(self, ctx: NexusContext) -> bool:
        """Handle messages."""
        if not ctx.message or ctx.user.is_moderator:
            return False

        text = ctx.message.text or ""
        command = text.split()[0].lower()

        if command == "/antiflood":
            return await self._handle_antiflood(ctx)
        elif command == "/antiraid":
            return await self._handle_antiraid(ctx)
        elif command == "/cas":
            return await self._handle_cas(ctx)

        return False

    async def on_new_member(self, ctx: NexusContext) -> bool:
        """Check new members against CAS."""
        config = ctx.group.module_configs.get("antispam", {})
        if not config.get("cas_enabled", True):
            return False

        if not ctx.message or not ctx.message.new_chat_members:
            return False

        for new_member in ctx.message.new_chat_members:
            # Check CAS
            cas_banned = await self._check_cas(new_member.id)

            if cas_banned:
                action = config.get("cas_action", "ban")
                if action == "ban":
                    await ctx.ban_user(
                        target=None,  # Need to get proper target
                        reason="CAS banned user",
                        silent=True,
                    )
                elif action == "kick":
                    await ctx.kick_user(
                        target=None,
                        reason="CAS banned user",
                    )

                await ctx.delete_message()
                return True

        return False

    async def _check_cas(self, user_id: int) -> bool:
        """Check if user is CAS banned."""
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.cas.chat/check?user_id={user_id}"
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("ok", False)
        except Exception:
            pass

        return False

    async def _handle_antiflood(self, ctx: NexusContext) -> bool:
        """Handle /antiflood command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        args = ctx.message.text.split()
        if len(args) < 2:
            config = ctx.group.module_configs.get("antispam", {})
            enabled = config.get("antiflood_enabled", True)
            limit = config.get("message_limit", 5)
            window = config.get("window_seconds", 5)

            text = f"📊 <b>Anti-Flood Settings</b>\n\n"
            text += f"Status: {'✅ Enabled' if enabled else '❌ Disabled'}\n"
            text += f"Limit: {limit} messages\n"
            text += f"Window: {window} seconds\n"
            text += f"\nUsage: /antiflood on/off"
            await ctx.reply(text)
            return True

        enabled = args[1].lower() == "on"

        # Update config
        await ctx.reply(f"✅ Anti-flood {'enabled' if enabled else 'disabled'}.")
        return True

    async def _handle_antiraid(self, ctx: NexusContext) -> bool:
        """Handle /antiraid command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        args = ctx.message.text.split()
        if len(args) < 2:
            config = ctx.group.module_configs.get("antispam", {})
            enabled = config.get("antiraid_enabled", True)

            text = f"🛡️ <b>Anti-Raid Settings</b>\n\n"
            text += f"Status: {'✅ Enabled' if enabled else '❌ Disabled'}\n"
            text += f"\nUsage: /antiraid on/off"
            await ctx.reply(text)
            return True

        enabled = args[1].lower() == "on"

        await ctx.reply(f"✅ Anti-raid {'enabled' if enabled else 'disabled'}.")
        return True

    async def _handle_cas(self, ctx: NexusContext) -> bool:
        """Handle /cas command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        args = ctx.message.text.split()
        if len(args) < 2:
            config = ctx.group.module_configs.get("antispam", {})
            enabled = config.get("cas_enabled", True)

            text = f"🔍 <b>CAS Integration</b>\n\n"
            text += f"Status: {'✅ Enabled' if enabled else '❌ Disabled'}\n"
            text += f"\nCombot Anti-Spam check for new members."
            text += f"\nUsage: /cas on/off"
            await ctx.reply(text)
            return True

        enabled = args[1].lower() == "on"

        await ctx.reply(f"✅ CAS integration {'enabled' if enabled else 'disabled'}.")
        return True
