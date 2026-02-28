"""Blocklist module - Two separate banned word lists."""

from typing import Optional, List
from pydantic import BaseModel
import re

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule, EventType


class BlocklistConfig(BaseModel):
    """Configuration for blocklist module."""
    list1_enabled: bool = True
    list2_enabled: bool = False
    list1_action: str = "delete"
    list1_duration: Optional[int] = None
    list1_delete: bool = True
    list2_action: str = "delete"
    list2_duration: Optional[int] = None
    list2_delete: bool = True


class BlocklistModule(NexusModule):
    """Two separate banned word lists."""

    name = "blocklist"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Two separate banned word lists with independent configurations"
    category = ModuleCategory.MODERATION

    config_schema = BlocklistConfig
    default_config = BlocklistConfig().dict()

    commands = [
        CommandDef(
            name="blocklist",
            description="View blocked words list",
            admin_only=True,
            args="<list_number>",
        ),
        CommandDef(
            name="addblacklist",
            description="Add word to blocklist",
            admin_only=True,
            args="<word> <list_number> [regex]",
        ),
        CommandDef(
            name="rmblacklist",
            description="Remove word from blocklist",
            admin_only=True,
            args="<word>",
        ),
        CommandDef(
            name="blacklistmode",
            description="Set blocklist action mode",
            admin_only=True,
            args="<list_number> <action> [duration]",
        ),
        CommandDef(
            name="blacklistlist",
            description="List all blocked words",
            admin_only=False,
        ),
        CommandDef(
            name="blacklistclear",
            description="Clear a blocklist",
            admin_only=True,
            args="<list_number>",
        ),
    ]

    listeners = [
        EventType.MESSAGE,
        EventType.EDITED_MESSAGE,
        EventType.CALLBACK,
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("blocklist", self.cmd_blocklist)
        self.register_command("addblacklist", self.cmd_addblacklist)
        self.register_command("rmblacklist", self.cmd_rmblacklist)
        self.register_command("blacklistmode", self.cmd_blacklistmode)
        self.register_command("blacklistlist", self.cmd_blacklistlist)
        self.register_command("blacklistclear", self.cmd_blacklistclear)

    async def on_message(self, ctx: NexusContext) -> bool:
        """Check for blocked words in messages."""
        return await self._check_blocklist(ctx, ctx.message.text or "")

    async def on_edited_message(self, ctx: NexusContext) -> bool:
        """Check for blocked words in edited messages."""
        return await self._check_blocklist(ctx, ctx.message.text or "")

    async def on_callback_query(self, ctx: NexusContext) -> bool:
        """Check for blocked words in callback query data."""
        if ctx.callback_query and ctx.callback_query.message:
            return await self._check_blocklist(ctx, ctx.callback_query.message.text or "")
        return False

    async def _check_blocklist(self, ctx: NexusContext, text: str) -> bool:
        """Check if text contains blocked words."""
        if not text:
            return False

        config = ctx.group.module_configs.get("blocklist", {})

        # Check each list
        for list_num in [1, 2]:
            if not config.get(f"list{list_num}_enabled", False):
                continue

            action = config.get(f"list{list_num}_action", "delete")
            duration = config.get(f"list{list_num}_duration")
            delete_message = config.get(f"list{list_num}_delete", True)

            # Get blocked words for this list
            if ctx.db:
                from shared.models import BannedWord
                result = ctx.db.execute(
                    f"""
                    SELECT word, is_regex, is_enabled
                    FROM banned_words
                    WHERE group_id = {ctx.group.id} AND list_number = {list_num}
                    AND is_enabled = TRUE
                    ORDER BY word ASC
                    """
                )
                blocked_words = result.fetchall()

                for row in blocked_words:
                    word = row[0]
                    is_regex = row[1]

                    # Check match
                    if is_regex:
                        try:
                            pattern = re.compile(word, re.IGNORECASE)
                            if pattern.search(text):
                                return await self._take_action(ctx, list_num, word, action, duration, delete_message)
                        except re.error:
                            pass
                    else:
                        # Exact match (case-insensitive)
                        if word.lower() in text.lower():
                            return await self._take_action(ctx, list_num, word, action, duration, delete_message)

        return False

    async def _take_action(self, ctx: NexusContext, list_num: int, word: str, action: str, duration: Optional[int], delete_message: bool) -> bool:
        """Take blocklist action."""
        if action == "warn":
            await ctx.warn_user(reason=f"Blacklisted word (List {list_num}): {word}")
        elif action == "mute":
            await ctx.mute_user(duration=duration, reason=f"Blacklisted word (List {list_num}): {word}", silent=True)
        elif action == "kick":
            await ctx.kick_user(reason=f"Blacklisted word (List {list_num}): {word}")
        elif action == "ban":
            await ctx.ban_user(duration=duration, reason=f"Blacklisted word (List {list_num}): {word}", silent=True)
        elif action == "tban" and duration:
            await ctx.ban_user(duration=duration, reason=f"Blacklisted word (List {list_num}): {word}", silent=True)
        elif action == "tmute" and duration:
            await ctx.mute_user(duration=duration, reason=f"Blacklisted word (List {list_num}): {word}", silent=True)

        if delete_message:
            await ctx.delete_message()

        return True

    async def cmd_blocklist(self, ctx: NexusContext):
        """View blocked words list."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        list_num = int(args[0]) if args and args[0].isdigit() else 1

        if list_num not in [1, 2]:
            await ctx.reply("❌ Invalid list number. Use 1 or 2")
            return

        if ctx.db:
            from shared.models import BannedWord, BannedWordListConfig
            result = ctx.db.execute(
                f"""
                SELECT bw.*, bwc.action, bwc.action_duration, bwc.delete_message
                FROM banned_words bw
                LEFT JOIN banned_word_list_configs bwc ON bw.group_id = bwc.group_id AND bw.list_number = bwc.list_number
                WHERE bw.group_id = {ctx.group.id} AND bw.list_number = {list_num}
                AND bw.is_enabled = TRUE
                ORDER BY bw.word ASC
                LIMIT 50
                """
            )

            blocked_words = result.fetchall()

            if not blocked_words:
                await ctx.reply(f"📝 List {list_num} is empty")
                return

            # Get list config
            config_result = ctx.db.execute(
                f"""
                SELECT * FROM banned_word_list_configs
                WHERE group_id = {ctx.group.id} AND list_number = {list_num}
                LIMIT 1
                """
            )
            config_row = config_result.fetchone()

            action = config_row[3] if config_row else "delete"
            duration = config_row[4] if config_row else None
            delete_msg = config_row[5] if config_row else True

            text = f"📝 **Blacklist List {list_num}:**\n\n"
            text += f"**Action:** {action}\n"
            if duration:
                text += f"**Duration:** {ctx._format_duration(duration)}\n"
            text += f"**Delete Trigger:** {'Yes' if delete_msg else 'No'}\n\n"
            text += f"**Words ({len(blocked_words)}):**\n"

            for row in blocked_words:
                word = row[0]
                is_regex = row[1]
                regex_icon = "🔍" if is_regex else "📝"
                text += f"{regex_icon} `{word}`\n"

            await ctx.reply(text, parse_mode="Markdown")

    async def cmd_addblacklist(self, ctx: NexusContext):
        """Add word to blocklist."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("❌ Usage: /addblacklist <word> <list_number> [regex]")
            return

        word = args[0]
        list_num = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
        is_regex = len(args) > 2 and args[2].lower() == "regex"

        if list_num not in [1, 2]:
            await ctx.reply("❌ Invalid list number. Use 1 or 2")
            return

        # Save to database
        if ctx.db:
            from shared.models import BannedWord
            blocked_word = BannedWord(
                group_id=ctx.group.id,
                word=word,
                list_number=list_num,
                is_regex=is_regex,
                created_by=ctx.user.user_id,
            )
            ctx.db.add(blocked_word)

        regex_text = " (regex)" if is_regex else ""
        await ctx.reply(f"✅ Added `{word}`{regex_text} to blacklist {list_num}")

    async def cmd_rmblacklist(self, ctx: NexusContext):
        """Remove word from blocklist."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("❌ Usage: /rmblacklist <word>")
            return

        word = args[0]

        # Delete from database (all lists)
        if ctx.db:
            from shared.models import BannedWord
            ctx.db.execute(
                f"""
                DELETE FROM banned_words
                WHERE group_id = {ctx.group.id} AND word = '{word}'
                """
            )

        await ctx.reply(f"✅ Removed `{word}` from all blacklists")

    async def cmd_blacklistmode(self, ctx: NexusContext):
        """Set blocklist action mode."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if len(args) < 2:
            await ctx.reply("❌ Usage: /blacklistmode <list_number> <action> [duration]")
            await ctx.reply("\nActions: delete, warn, mute, kick, ban, tban, tmute")
            return

        list_num = int(args[0]) if args[0].isdigit() else 1
        action = args[1].lower()
        duration = ctx.parse_duration(args[2]) if len(args) > 2 else None

        if list_num not in [1, 2]:
            await ctx.reply("❌ Invalid list number. Use 1 or 2")
            return

        if action not in ["delete", "warn", "mute", "kick", "ban", "tban", "tmute"]:
            await ctx.reply("❌ Invalid action. Use: delete, warn, mute, kick, ban, tban, tmute")
            return

        # Update database
        if ctx.db:
            from shared.models import BannedWordListConfig
            result = ctx.db.execute(
                f"""
                SELECT * FROM banned_word_list_configs
                WHERE group_id = {ctx.group.id} AND list_number = {list_num}
                LIMIT 1
                """
            )

            if result.fetchone():
                ctx.db.execute(
                    f"""
                    UPDATE banned_word_list_configs
                    SET action = '{action}',
                        action_duration = {duration or 'NULL'}
                    WHERE group_id = {ctx.group.id} AND list_number = {list_num}
                    """
                )
            else:
                config = BannedWordListConfig(
                    group_id=ctx.group.id,
                    list_number=list_num,
                    action=action,
                    action_duration=duration,
                    delete_message=True,
                )
                ctx.db.add(config)

        duration_text = f" ({ctx._format_duration(duration)})" if duration else ""
        await ctx.reply(f"✅ List {list_num} mode set to: {action}{duration_text}")

    async def cmd_blacklistlist(self, ctx: NexusContext):
        """List all blocked words."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.db:
            from shared.models import BannedWord
            result = ctx.db.execute(
                f"""
                SELECT list_number, word, is_regex, is_enabled
                FROM banned_words
                WHERE group_id = {ctx.group.id}
                ORDER BY list_number ASC, word ASC
                LIMIT 100
                """
            )

            blocked_words = result.fetchall()

            if not blocked_words:
                await ctx.reply("📝 No blocked words set")
                return

            text = "📝 **All Blocked Words:**\n\n"

            current_list = None
            for row in blocked_words:
                list_num = row[0]
                word = row[1]
                is_regex = row[2]
                is_enabled = row[3]

                if list_num != current_list:
                    if current_list is not None:
                        text += "\n\n"
                    current_list = list_num
                    text += f"📝 **List {list_num}:**\n\n"

                regex_icon = "🔍" if is_regex else "📝"
                enabled_icon = "✅" if is_enabled else "🔴"

                text += f"{regex_icon}{enabled_icon} `{word}`\n"

            # Split into chunks if too long
            if len(text) > 4096:
                chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]
                for chunk in chunks:
                    await ctx.reply(chunk, parse_mode="Markdown")
            else:
                await ctx.reply(text, parse_mode="Markdown")

    async def cmd_blacklistclear(self, ctx: NexusContext):
        """Clear a blocklist."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args or not args[0].isdigit():
            await ctx.reply("❌ Usage: /blacklistclear <list_number>")
            return

        list_num = int(args[0])
        if list_num not in [1, 2]:
            await ctx.reply("❌ Invalid list number. Use 1 or 2")
            return

        # Delete all words from list
        if ctx.db:
            from shared.models import BannedWord
            ctx.db.execute(
                f"""
                DELETE FROM banned_words
                WHERE group_id = {ctx.group.id} AND list_number = {list_num}
                """
            )

        await ctx.reply(f"✅ List {list_num} cleared")
