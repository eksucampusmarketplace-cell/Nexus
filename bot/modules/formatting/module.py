"""Formatting module - Button generator and markdown helper."""

from typing import Optional
from aiogram.types import Message
from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class FormattingModule(NexusModule):
    """Button generator and markdown helper."""

    name = "formatting"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Button generator and markdown helper"
    category = ModuleCategory.UTILITY

    commands = [
        CommandDef(
            name="markdownhelp",
            description="Show markdown formatting help",
            admin_only=False,
        ),
        CommandDef(
            name="formattinghelp",
            description="Show formatting help",
            admin_only=False,
        ),
        CommandDef(
            name="bold",
            description="Format text as bold",
            admin_only=False,
            args="<text>",
        ),
        CommandDef(
            name="italic",
            description="Format text as italic",
            admin_only=False,
            args="<text>",
        ),
        CommandDef(
            name="underline",
            description="Format text as underlined",
            admin_only=False,
            args="<text>",
        ),
        CommandDef(
            name="strikethrough",
            description="Format text as strikethrough",
            admin_only=False,
            args="<text>",
        ),
        CommandDef(
            name="code",
            description="Format text as code",
            admin_only=False,
            args="<text>",
        ),
        CommandDef(
            name="pre",
            description="Format text as preformatted code block",
            admin_only=False,
            args="<text>",
        ),
        CommandDef(
            name="spoiler",
            description="Format text as spoiler",
            admin_only=False,
            args="<text>",
        ),
        CommandDef(
            name="link",
            description="Create a hyperlink",
            admin_only=False,
            args="<url> <text>",
        ),
        CommandDef(
            name="mention",
            description="Create a custom mention",
            admin_only=False,
            args="<user_id> <text>",
        ),
        CommandDef(
            name="emoji",
            description="Search for emoji",
            admin_only=False,
            args="<keyword>",
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("markdownhelp", self.cmd_markdownhelp)
        self.register_command("formattinghelp", self.cmd_formattinghelp)
        self.register_command("bold", self.cmd_bold)
        self.register_command("italic", self.cmd_italic)
        self.register_command("underline", self.cmd_underline)
        self.register_command("strikethrough", self.cmd_strikethrough)
        self.register_command("code", self.cmd_code)
        self.register_command("pre", self.cmd_pre)
        self.register_command("spoiler", self.cmd_spoiler)
        self.register_command("link", self.cmd_link)
        self.register_command("mention", self.cmd_mention)
        self.register_command("emoji", self.cmd_emoji)

    async def cmd_markdownhelp(self, ctx: NexusContext):
        """Show markdown formatting help."""
        help_text = (
            "📝 **Markdown Formatting Guide**\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "**Bold Text**\n"
            "• Input: `*Bold text*` or `__Bold text__`\n"
            "• Output: *Bold text*\n\n"
            "**Italic Text**\n"
            "• Input: `_Italic text_`\n"
            "• Output: _Italic text_\n\n"
            "**Bold + Italic**\n"
            "• Input: `*_Bold italic_*`\n"
            "• Output: *_Bold italic_*\n\n"
            "**Strikethrough**\n"
            "• Input: `~Strikethrough~`\n"
            "• Output: ~Strikethrough~\n\n"
            "**Underline**\n"
            "• Input: `__Underline__`\n"
            "• Output: __Underline__\n\n"
            "**Monospace (Code)**\n"
            "• Input: `` `Code` ``\n"
            "• Output: `Code`\n\n"
            "**Preformatted Block**\n"
            "• Input: ```Code block```\n"
            "• Output: Code block\n\n"
            "**Hyperlink**\n"
            "• Input: `[Link text](https://example.com)`\n"
            "• Output: Link text (clickable)\n\n"
            "**Mention by ID**\n"
            "• Input: `[Name](tg://user?id=123456789)`\n"
            "• Output: Name (mention)\n\n"
            "**Spoiler**\n"
            "• Input: `||Spoiler text||`\n"
            "• Output: Spoiler text (tap to reveal)\n\n"
            "**Button Link**\n"
            "• Input: `[Button text](https://example.com)`\n"
            "• Output: Button text (clickable button)\n\n"
            "**Button in Same Row**\n"
            "• Input: `[Button text](https://example.com:same)`\n"
            "• Output: Button text (same row)\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "💡 **Tip:** Use the formatting commands below for quick formatting!"
        )

        await ctx.reply(help_text, parse_mode="Markdown")

    async def cmd_formattinghelp(self, ctx: NexusContext):
        """Show formatting help."""
        help_text = (
            "📖 **Formatting Help**\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Nexus supports both Markdown and HTML formatting.\n\n"
            "**Quick Commands:**\n"
            "• `/bold <text>` - Bold\n"
            "• `/italic <text>` - Italic\n"
            "• `/underline <text>` - Underline\n"
            "• `/strikethrough <text>` - Strikethrough\n"
            "• `/code <text>` - Code\n"
            "• `/pre <text>` - Code block\n"
            "• `/spoiler <text>` - Spoiler\n"
            "• `/link <url> <text>` - Hyperlink\n"
            "• `/mention <user_id> <text>` - Custom mention\n"
            "• `/emoji <keyword>` - Search emoji\n\n"
            "**Button Syntax:**\n"
            "• `[Button Text](https://url)` - Link button\n"
            "• `[Button Text](https://url:same)` - Same row button\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📚 Use `/markdownhelp` for detailed markdown guide!"
        )

        await ctx.reply(help_text)

    async def cmd_bold(self, ctx: NexusContext):
        """Format text as bold."""
        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /bold <text>\n\nExample: /bold Hello World")
            return

        text = args[0]
        formatted = f"*{text}*"

        await ctx.message.delete()
        await ctx.reply(formatted, parse_mode="Markdown")

    async def cmd_italic(self, ctx: NexusContext):
        """Format text as italic."""
        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /italic <text>\n\nExample: /italic Hello World")
            return

        text = args[0]
        formatted = f"_{text}_"

        await ctx.message.delete()
        await ctx.reply(formatted, parse_mode="Markdown")

    async def cmd_underline(self, ctx: NexusContext):
        """Format text as underlined."""
        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /underline <text>\n\nExample: /underline Hello World")
            return

        text = args[0]
        formatted = f"__{text}__"

        await ctx.message.delete()
        await ctx.reply(formatted, parse_mode="Markdown")

    async def cmd_strikethrough(self, ctx: NexusContext):
        """Format text as strikethrough."""
        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /strikethrough <text>\n\nExample: /strikethrough Hello World")
            return

        text = args[0]
        formatted = f"~{text}~"

        await ctx.message.delete()
        await ctx.reply(formatted, parse_mode="Markdown")

    async def cmd_code(self, ctx: NexusContext):
        """Format text as code."""
        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /code <text>\n\nExample: /code print('Hello')")
            return

        text = args[0]
        formatted = f"`{text}`"

        await ctx.message.delete()
        await ctx.reply(formatted, parse_mode="Markdown")

    async def cmd_pre(self, ctx: NexusContext):
        """Format text as preformatted code block."""
        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /pre <text>\n\nExample: /pre def hello():\n    print('Hello')")
            return

        text = args[0]
        formatted = f"```{text}```"

        await ctx.message.delete()
        await ctx.reply(formatted, parse_mode="Markdown")

    async def cmd_spoiler(self, ctx: NexusContext):
        """Format text as spoiler."""
        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /spoiler <text>\n\nExample: /spoiler Darth Vader is Luke's father")
            return

        text = args[0]
        formatted = f"||{text}||"

        await ctx.message.delete()
        await ctx.reply(formatted, parse_mode="Markdown")

    async def cmd_link(self, ctx: NexusContext):
        """Create a hyperlink."""
        args = ctx.message.text.split(maxsplit=2)[1:] if ctx.message.text else []

        if len(args) < 2:
            await ctx.reply(
                "❌ Usage: /link <url> <text>\n\n"
                "Example: /link https://example.com Click Here"
            )
            return

        url = args[0]
        text = args[1]
        formatted = f"[{text}]({url})"

        await ctx.message.delete()
        await ctx.reply(formatted, parse_mode="Markdown", disable_web_page_preview=True)

    async def cmd_mention(self, ctx: NexusContext):
        """Create a custom mention."""
        args = ctx.message.text.split(maxsplit=2)[1:] if ctx.message.text else []

        if len(args) < 2:
            await ctx.reply(
                "❌ Usage: /mention <user_id> <text>\n\n"
                "Example: /mention 123456789 Click Here"
            )
            return

        user_id = args[0]
        text = args[1]
        formatted = f"[{text}](tg://user?id={user_id})"

        await ctx.message.delete()
        await ctx.reply(formatted, parse_mode="Markdown")

    async def cmd_emoji(self, ctx: NexusContext):
        """Search for emoji."""
        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /emoji <keyword>\n\nExample: /emoji heart")
            return

        keyword = args[0].lower()

        # Common emoji by category
        emoji_db = {
            "smile": ["😀", "😃", "😄", "😁", "😆", "😅", "🤣"],
            "love": ["❤️", "💕", "💖", "💗", "💓", "💞", "💝"],
            "heart": ["❤️", "💕", "💖", "💗", "💓", "💞"],
            "sad": ["😢", "😭", "😿", "😔", "😞", "😟"],
            "angry": ["😠", "😡", "😤", "😠", "👿"],
            "thumb": ["👍", "👎", "👌", "✌️", "🤏"],
            "fire": ["🔥", "💥", "💢", "🌟"],
            "star": ["⭐", "🌟", "✨", "💫", "🎇"],
            "money": ["💰", "💵", "💴", "💶", "💷", "💸"],
            "party": ["🎉", "🎊", "🎈", "🎆", "🎇", "🎋"],
            "animal": ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊"],
            "food": ["🍕", "🍔", "🍟", "🌭", "🍿", "🧂"],
            "drink": ["🍺", "🍷", "🥂", "☕", "🍵"],
            "music": ["🎵", "🎶", "🎼", "🎹", "🎸", "🎺"],
            "tech": ["📱", "💻", "🖥️", "⌨️", "🖱️", "💾"],
        }

        # Search for emoji
        results = []
        for cat, emojis in emoji_db.items():
            if keyword in cat:
                results.extend(emojis)

        if not results:
            await ctx.reply(
                f"❌ No emoji found for '{keyword}'.\n\n"
                f"Try: smile, love, heart, sad, angry, thumb, fire, star, "
                f"money, party, animal, food, drink, music, tech"
            )
            return

        text = f"✨ Emoji for '{keyword}':\n\n"
        text += " ".join(results[:10])  # Show first 10

        await ctx.reply(text)
