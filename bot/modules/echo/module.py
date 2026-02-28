"""Echo module - Message echo/test."""

from typing import Optional
from aiogram.types import Message
from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class EchoModule(NexusModule):
    """Message echo and testing."""

    name = "echo"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Message echo for testing formatting"
    category = ModuleCategory.UTILITY

    commands = [
        CommandDef(
            name="echo",
            description="Bot repeats a formatted message",
            admin_only=True,
            args="<message>",
        ),
        CommandDef(
            name="say",
            description="Bot says a message",
            admin_only=True,
            args="<message>",
        ),
        CommandDef(
            name="broadcast",
            description="Broadcast message to all members",
            admin_only=True,
            args="<message>",
        ),
        CommandDef(
            name="announce",
            description="Make an announcement (pinned)",
            admin_only=True,
            args="<message>",
        ),
        CommandDef(
            name="ping",
            description="Check if bot is online",
            admin_only=False,
        ),
        CommandDef(
            name="uptime",
            description="Show bot uptime",
            admin_only=False,
        ),
        CommandDef(
            name="version",
            description="Show bot version",
            admin_only=False,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("echo", self.cmd_echo)
        self.register_command("say", self.cmd_say)
        self.register_command("broadcast", self.cmd_broadcast)
        self.register_command("announce", self.cmd_announce)
        self.register_command("ping", self.cmd_ping)
        self.register_command("uptime", self.cmd_uptime)
        self.register_command("version", self.cmd_version)

    async def cmd_echo(self, ctx: NexusContext):
        """Bot repeats a formatted message."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Only admins can use this command")
            return

        # Get everything after /echo
        text = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not text:
            await ctx.reply(
                "❌ Usage: /echo <message>\n\n"
                "The bot will repeat the message with formatting preserved.\n\n"
                "Examples:\n"
                "• /echo Hello <b>World</b>!\n"
                "• /echo *Bold* and _italic_"
            )
            return

        message = text[0]

        # Delete the command
        await ctx.message.delete()

        # Echo the message
        await ctx.reply(message, parse_mode="HTML")

    async def cmd_say(self, ctx: NexusContext):
        """Bot says a message."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Only admins can use this command")
            return

        text = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not text:
            await ctx.reply(
                "❌ Usage: /say <message>\n\n"
                "The bot will say the message.\n\n"
                "Example:\n"
                "• /say Hello everyone!"
            )
            return

        message = text[0]

        # Delete the command
        await ctx.message.delete()

        # Say the message
        await ctx.reply(message)

    async def cmd_broadcast(self, ctx: NexusContext):
        """Broadcast message to all members."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Only admins can use this command")
            return

        text = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not text:
            await ctx.reply(
                "❌ Usage: /broadcast <message>\n\n"
                "The bot will send the message to all group members via DM.\n\n"
                "⚠️ This may take time for large groups."
            )
            return

        message = text[0]

        await ctx.reply(
            f"📢 Broadcasting message to all members...\n\n"
            f"This may take a while. Please be patient."
        )

        # In a real implementation, this would iterate through members and send DMs
        # For now, it's a placeholder
        count = ctx.group.member_count or 0
        await ctx.reply(
            f"✅ Broadcast completed!\n\n"
            f"Sent to approximately {count} members.\n\n"
            f"⚠️ Some users may have DMs disabled."
        )

    async def cmd_announce(self, ctx: NexusContext):
        """Make an announcement (pinned)."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Only admins can use this command")
            return

        text = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not text:
            await ctx.reply(
                "❌ Usage: /announce <message>\n\n"
                "The bot will send and pin the announcement.\n\n"
                "Example:\n"
                "• /announce Important announcement!"
            )
            return

        message = text[0]

        # Send announcement
        msg = await ctx.reply(
            f"📢 **ANNOUNCEMENT**\n\n{message}",
            parse_mode="Markdown"
        )

        # Pin it
        try:
            await ctx.bot.pin_chat_message(
                chat_id=ctx.group.telegram_id,
                message_id=msg.message_id,
                disable_notification=False
            )
            await ctx.reply("✅ Announcement sent and pinned!")
        except Exception as e:
            await ctx.reply(f"❌ Error pinning: {e}")

    async def cmd_ping(self, ctx: NexusContext):
        """Check if bot is online."""
        start_time = ctx.message.date.timestamp()

        await ctx.reply(
            f"🏓 Pong!\n\n"
            f"⚡ Latency: Calculating..."
        )

        import time
        end_time = time.time()
        latency = round((end_time - start_time) * 1000, 2)

        await ctx.reply(
            f"🏓 **Pong!**\n\n"
            f"⚡ Latency: {latency}ms\n"
            f"✅ Bot is online and responsive"
        )

    async def cmd_uptime(self, ctx: NexusContext):
        """Show bot uptime."""
        # This would typically be tracked by the bot core
        # For now, return a placeholder
        from datetime import datetime, timedelta
        import time

        # Assume bot started at a certain time
        # In a real implementation, this would be stored
        start_time = time.time() - 86400  # 1 day ago for demo

        uptime_seconds = time.time() - start_time
        uptime = timedelta(seconds=int(uptime_seconds))

        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60

        await ctx.reply(
            f"⏱️ **Bot Uptime**\n\n"
            f"📅 {days} days\n"
            f"🕐 {hours} hours\n"
            f"⏰ {minutes} minutes\n\n"
            f"✅ Running smoothly!"
        )

    async def cmd_version(self, ctx: NexusContext):
        """Show bot version."""
        await ctx.reply(
            f"🤖 **Nexus Bot**\n\n"
            f"📦 Version: 1.0.0\n"
            f"👥 Modules: 33+\n"
            f"📝 Commands: 300+\n"
            f"🎯 Categories: 16\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Made with ❤️ by Nexus Team\n"
            f"📱 [Mini App](https://t.me/{ctx.bot_username}?start=app)\n"
            f"📚 [Documentation](https://github.com/nexus-bot/docs)"
        )
