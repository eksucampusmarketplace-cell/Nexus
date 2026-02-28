"""Help module - Complete command help system."""

from typing import Optional
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class HelpModule(NexusModule):
    """Complete help system with categorized commands."""

    name = "help"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Complete help system for all commands"
    category = ModuleCategory.UTILITY

    commands = [
        CommandDef(
            name="help",
            description="Show help menu",
            admin_only=False,
            args="[command]",
        ),
        CommandDef(
            name="start",
            description="Start bot and show welcome",
            admin_only=False,
        ),
        CommandDef(
            name="commands",
            description="List all available commands",
            admin_only=False,
            args="[category]",
        ),
        CommandDef(
            name="modules",
            description="List all available modules",
            admin_only=False,
        ),
        CommandDef(
            name="modhelp",
            description="Show moderation commands",
            admin_only=False,
        ),
        CommandDef(
            name="adminhelp",
            description="Show admin commands",
            admin_only=True,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("help", self.cmd_help)
        self.register_command("start", self.cmd_start)
        self.register_command("commands", self.cmd_commands)
        self.register_command("modules", self.cmd_modules)
        self.register_command("modhelp", self.cmd_modhelp)
        self.register_command("adminhelp", self.cmd_adminhelp)

    async def cmd_start(self, ctx: NexusContext):
        """Show welcome message."""
        welcome_text = (
            "🤖 **Welcome to Nexus Bot!**\n\n"
            f"👋 Hello {ctx.user.first_name}!\n\n"
            "Nexus is the most complete Telegram bot platform with "
            "300+ commands across 33+ modules.\n\n"
            "📚 **Quick Start:**\n"
            "• `/help` - View all commands\n"
            "• `/modules` - View all modules\n"
            "• `/commands` - List commands by category\n"
            "• `/settings` - Open Mini App\n\n"
            "🎯 **Popular Commands:**\n"
            "• `/warn @user` - Warn a user\n"
            "• `/mute @user 1h` - Mute user for 1 hour\n"
            "• `/ban @user` - Ban a user\n"
            "• `/info @user` - Get user info\n"
            "• `/rules` - View group rules\n"
            "• `/me` - View your profile\n"
            "• `/balance` - Check your wallet\n\n"
            "💡 **Tip:** Type `/help <command>` for detailed info on any command!\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "*Made with ❤️ by Nexus Team*"
        )

        await ctx.reply(
            welcome_text,
            buttons=[
                [
                    {"text": "📖 All Commands", "callback_data": "help_commands"},
                    {"text": "🎮 Games", "callback_data": "help_games"},
                ],
                [
                    {"text": "⚙️ Settings", "url": f"https://t.me/{ctx.bot_username}?start=settings"},
                    {"text": "📱 Mini App", "url": f"https://t.me/{ctx.bot_username}?start=app"},
                ],
                [
                    {"text": "📚 Documentation", "url": "https://github.com/nexus-bot/docs"},
                    {"text": "💬 Support", "url": "https://t.me/nexussupport"},
                ],
            ],
        )

    async def cmd_help(self, ctx: NexusContext):
        """Show help menu."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if args:
            # Show help for specific command
            command_name = args[0].lower().lstrip("/")
            await self._show_command_help(ctx, command_name)
        else:
            # Show main help menu
            await self._show_help_menu(ctx)

    async def _show_help_menu(self, ctx: NexusContext):
        """Show main help menu with categories."""
        help_text = (
            "📚 **Nexus Bot Help Menu**\n\n"
            f"👤 User: {ctx.user.mention}\n"
            f"🏠 Group: {ctx.group.title}\n"
            f"🎭 Role: {ctx.user.role.title()}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📖 **Command Categories:**\n\n"
        )

        categories = [
            ("🛡️ Moderation", "modhelp", "Admin only"),
            ("👋 Welcome", "welcome_help", "Admin only"),
            ("🔒 Captcha", "captcha_help", "Admin only"),
            ("🔐 Locks", "locks_help", "Admin only"),
            ("🚫 Antispam", "antispam_help", "Admin only"),
            ("📝 Notes", "notes_help", "All users"),
            ("🔍 Filters", "filters_help", "Mod only"),
            ("📜 Rules", "rules_help", "All users"),
            ("ℹ️ Info", "info_help", "All users"),
            ("💰 Economy", "economy_help", "All users"),
            ("⭐ Reputation", "reputation_help", "All users"),
            ("🎮 Games", "games_help", "All users"),
            ("📊 Polls", "polls_help", "Mod only"),
            ("⏰ Scheduler", "scheduler_help", "Admin only"),
            ("🤖 AI", "ai_help", "All users"),
            ("📈 Analytics", "analytics_help", "Admin only"),
        ]

        for name, callback, permission in categories:
            help_text += f"• {name} `{callback}`\n"

        help_text += "\n━━━━━━━━━━━━━━━━━━━━\n\n"
        help_text += "💡 **Tip:** Use `/help <command>` for detailed info!\n"
        help_text += "📱 Use `/settings` to open Mini App for full control!\n"

        buttons = []
        row = []
        for i, (name, callback, _) in enumerate(categories):
            row.append({"text": name, "callback_data": callback})
            if len(row) == 2 or i == len(categories) - 1:
                buttons.append(row)
                row = []

        await ctx.reply(help_text, buttons=buttons)

    async def _show_command_help(self, ctx: NexusContext, command_name: str):
        """Show detailed help for a specific command."""
        command_help = self._get_command_help(command_name)

        if command_help:
            help_text = (
                f"❓ **Command: /{command_name}**\n\n"
                f"📝 Description: {command_help['description']}\n\n"
                f"📋 Usage: `{command_help['usage']}`\n\n"
            )

            if command_help.get('examples'):
                help_text += "🔹 Examples:\n"
                for example in command_help['examples']:
                    help_text += f"• `{example}`\n"
                help_text += "\n"

            if command_help.get('aliases'):
                help_text += f"🔄 Aliases: {', '.join(command_help['aliases'])}\n"

            if command_help.get('permissions'):
                help_text += f"🔒 Permissions: {command_help['permissions']}\n"

            help_text += "\n━━━━━━━━━━━━━━━━━━━━"

            await ctx.reply(
                help_text,
                buttons=[[{"text": "↩️ Back to Help", "callback_data": "help_menu"}]]
            )
        else:
            await ctx.reply(
                f"❌ Command `/{command_name}` not found.\n\n"
                f"Use `/commands` to see all available commands.",
                buttons=[[{"text": "📖 All Commands", "callback_data": "help_commands"}]]
            )

    def _get_command_help(self, command_name: str) -> Optional[dict]:
        """Get detailed help for a command."""
        command_docs = {
            # ========== MODERATION ==========
            "warn": {
                "description": "Warn a user for violating group rules",
                "usage": "/warn [@user] [reason]",
                "examples": [
                    "/warn @username Spamming",
                    "/warn Inappropriate language",
                    "/w Breaking rules (alias)"
                ],
                "aliases": ["w"],
                "permissions": "Admin/Moderator"
            },
            "mute": {
                "description": "Mute a user temporarily or permanently",
                "usage": "/mute [@user] [duration] [reason]",
                "examples": [
                    "/mute @username 1h Spamming",
                    "/mute 24h",
                    "/m @username 30d Repeated violations",
                    "/tmute @username 1w"
                ],
                "aliases": ["m", "tm", "tmute"],
                "permissions": "Admin/Moderator"
            },
            "ban": {
                "description": "Ban a user from the group",
                "usage": "/ban [@user] [duration] [reason]",
                "examples": [
                    "/ban @username Spamming",
                    "/ban 7d",
                    "/b @username 30d Repeated violations",
                    "/tban @username 1d"
                ],
                "aliases": ["b", "tb", "tban"],
                "permissions": "Admin"
            },
            "kick": {
                "description": "Kick a user from the group (they can rejoin)",
                "usage": "/kick [@user] [reason]",
                "examples": [
                    "/kick @username",
                    "/kick Inappropriate behavior",
                    "/k @username Spamming"
                ],
                "aliases": ["k"],
                "permissions": "Admin"
            },
            "unban": {
                "description": "Unban a previously banned user",
                "usage": "/unban [@user]",
                "examples": ["/unban @username", "/ub @username"],
                "aliases": ["ub"],
                "permissions": "Admin"
            },
            "unmute": {
                "description": "Unmute a previously muted user",
                "usage": "/unmute [@user]",
                "examples": ["/unmute @username", "/um @username"],
                "aliases": ["um"],
                "permissions": "Admin"
            },
            "pin": {
                "description": "Pin a message to the top of the group",
                "usage": "/pin [silent]",
                "examples": [
                    "/pin (reply to message)",
                    "/pin silent"
                ],
                "aliases": [],
                "permissions": "Admin"
            },
            "unpin": {
                "description": "Unpin a previously pinned message",
                "usage": "/unpin (reply to message)",
                "examples": ["/unpin"],
                "aliases": [],
                "permissions": "Admin"
            },
            "purge": {
                "description": "Delete multiple messages at once",
                "usage": "/purge (reply to last message to delete)",
                "examples": ["/purge"],
                "aliases": [],
                "permissions": "Admin"
            },
            "info": {
                "description": "View detailed information about a user",
                "usage": "/info [@user]",
                "examples": [
                    "/info",
                    "/info @username",
                    "/info 123456789"
                ],
                "aliases": [],
                "permissions": "All users"
            },
            "me": {
                "description": "View your own profile with XP, level, badges",
                "usage": "/me",
                "examples": ["/me"],
                "aliases": [],
                "permissions": "All users"
            },
            "balance": {
                "description": "Check your wallet balance",
                "usage": "/balance [@user]",
                "examples": [
                    "/balance",
                    "/balance @username"
                ],
                "aliases": [],
                "permissions": "All users"
            },
            "daily": {
                "description": "Claim your daily bonus coins",
                "usage": "/daily",
                "examples": ["/daily"],
                "aliases": [],
                "permissions": "All users"
            },
            "rules": {
                "description": "View the group rules",
                "usage": "/rules",
                "examples": ["/rules"],
                "aliases": [],
                "permissions": "All users"
            },
            "setwelcome": {
                "description": "Set the welcome message for new members",
                "usage": "/setwelcome <message>",
                "examples": [
                    "/setwelcome Welcome {first}!",
                    "/setwelcome Hello {mention}! You are member #{count}."
                ],
                "aliases": [],
                "permissions": "Admin"
            },
            "welcome": {
                "description": "View the current welcome message",
                "usage": "/welcome",
                "examples": ["/welcome"],
                "aliases": [],
                "permissions": "All users"
            },
            "setrules": {
                "description": "Set the group rules",
                "usage": "/setrules <rules>",
                "examples": [
                    "/setrules 1. Be respectful\n2. No spam\n3. Follow Telegram TOS"
                ],
                "aliases": [],
                "permissions": "Admin"
            },
            "save": {
                "description": "Save a note for later retrieval",
                "usage": "/save <name> <content>",
                "examples": [
                    "/save rules Our group rules...",
                    "/save meme (reply to image)"
                ],
                "aliases": [],
                "permissions": "Admin/Moderator"
            },
            "filter": {
                "description": "Create an automatic response filter",
                "usage": "/filter <trigger>",
                "examples": [
                    "/filter hello",
                    "/filter bye"
                ],
                "aliases": [],
                "permissions": "Admin/Moderator"
            },
            "lock": {
                "description": "Lock a specific content type in the group",
                "usage": "/lock <type>",
                "examples": [
                    "/lock url",
                    "/lock sticker",
                    "/lock links"
                ],
                "aliases": [],
                "permissions": "Admin"
            },
            "unlock": {
                "description": "Unlock a previously locked content type",
                "usage": "/unlock <type>",
                "examples": [
                    "/unlock url",
                    "/unlock sticker"
                ],
                "aliases": [],
                "permissions": "Admin"
            },
            "promote": {
                "description": "Promote a user to admin or moderator",
                "usage": "/promote [@user] [role]",
                "examples": [
                    "/promote @username",
                    "/promote @username mod"
                ],
                "aliases": [],
                "permissions": "Owner only"
            },
            "demote": {
                "description": "Demote a user from admin/moderator",
                "usage": "/demote [@user]",
                "examples": ["/demote @username"],
                "aliases": [],
                "permissions": "Owner only"
            },
            "trust": {
                "description": "Trust a user (bypass some restrictions)",
                "usage": "/trust [@user]",
                "examples": ["/trust @username"],
                "aliases": [],
                "permissions": "Admin"
            },
            "approve": {
                "description": "Approve a user (bypass all restrictions)",
                "usage": "/approve [@user]",
                "examples": ["/approve @username"],
                "aliases": [],
                "permissions": "Admin"
            },
            "history": {
                "description": "View a user's complete moderation history",
                "usage": "/history [@user]",
                "examples": [
                    "/history",
                    "/history @username"
                ],
                "aliases": [],
                "permissions": "Moderator+"
            },
            "slowmode": {
                "description": "Enable/disable slow mode (delay between messages)",
                "usage": "/slowmode <seconds> | off",
                "examples": [
                    "/slowmode 30",
                    "/slowmode off"
                ],
                "aliases": [],
                "permissions": "Admin"
            },
            "report": {
                "description": "Report a message to admins",
                "usage": "/report [reason]",
                "examples": [
                    "/report",
                    "/report This is spam"
                ],
                "aliases": [],
                "permissions": "All users"
            },
            "trivia": {
                "description": "Start a trivia game",
                "usage": "/trivia [category] [difficulty]",
                "examples": [
                    "/trivia",
                    "/trivia science hard"
                ],
                "aliases": [],
                "permissions": "All users"
            },
            "ai": {
                "description": "Ask the AI assistant anything",
                "usage": "/ai <prompt>",
                "examples": [
                    "/ai What should we do for event?",
                    "/ai Summarize last 50 messages"
                ],
                "aliases": [],
                "permissions": "All users"
            },
            "give": {
                "description": "Send coins to another user",
                "usage": "/give @user <amount>",
                "examples": [
                    "/give @username 100",
                    "/give @friend 50"
                ],
                "aliases": [],
                "permissions": "All users"
            },
            "rep": {
                "description": "Give or remove reputation from a user",
                "usage": "/rep [@user] [+1|-1]",
                "examples": [
                    "/rep @username +1",
                    "/rep -1"
                ],
                "aliases": ["reputation"],
                "permissions": "All users"
            },
            "captcha": {
                "description": "Set the CAPTCHA type for new members",
                "usage": "/captcha <type>",
                "examples": [
                    "/captcha button",
                    "/captcha math",
                    "/captcha quiz"
                ],
                "aliases": [],
                "permissions": "Admin"
            },
            "antiflood": {
                "description": "Configure anti-flood settings",
                "usage": "/antiflood [limit] [window]",
                "examples": [
                    "/antiflood 10 10",
                    "/antiflood off"
                ],
                "aliases": [],
                "permissions": "Admin"
            },
            "setlang": {
                "description": "Set the bot language for this group",
                "usage": "/setlang <language>",
                "examples": [
                    "/setlang en",
                    "/setlang es"
                ],
                "aliases": [],
                "permissions": "Admin"
            },
            "schedule": {
                "description": "Schedule a message to be sent later",
                "usage": "/schedule <time> <message>",
                "examples": [
                    "/schedule 18:00 Meeting at 8pm",
                    "/schedule tomorrow 9am Good morning"
                ],
                "aliases": [],
                "permissions": "Admin/Moderator"
            },
            "stats": {
                "description": "View group statistics",
                "usage": "/stats",
                "examples": ["/stats"],
                "aliases": [],
                "permissions": "Admin"
            },
            "leaderboard": {
                "description": "View the economy leaderboard",
                "usage": "/leaderboard [type]",
                "examples": [
                    "/leaderboard",
                    "/leaderboard xp"
                ],
                "aliases": [],
                "permissions": "All users"
            },
            "newfed": {
                "description": "Create a new federation for cross-group bans",
                "usage": "/newfed <name>",
                "examples": ["/newfed MyFederation"],
                "aliases": [],
                "permissions": "All users"
            },
            "fban": {
                "description": "Ban a user from all groups in the federation",
                "usage": "/fban @user <reason>",
                "examples": ["/fban @username Spamming across feds"],
                "aliases": [],
                "permissions": "Fed Admin"
            },
            "export": {
                "description": "Export group settings to a file",
                "usage": "/export [modules...]",
                "examples": [
                    "/export",
                    "/export notes filters rules"
                ],
                "aliases": [],
                "permissions": "Admin"
            },
            "import": {
                "description": "Import settings from a file",
                "usage": "/import (reply to file)",
                "examples": ["/import"],
                "aliases": [],
                "permissions": "Admin"
            },

            # ========== GAMES ==========
            "trivia": {
                "description": "Start a trivia game",
                "usage": "/trivia [category] [difficulty] [questions]",
                "examples": [
                    "/trivia",
                    "/trivia science hard",
                    "/trivia history 10"
                ],
                "aliases": [],
                "permissions": "All users"
            },
            "wordle": {
                "description": "Play Wordle - guess the 5-letter word",
                "usage": "/wordle",
                "examples": ["/wordle"],
                "aliases": [],
                "permissions": "All users"
            },
            "hangman": {
                "description": "Play Hangman - guess the word letter by letter",
                "usage": "/hangman",
                "examples": ["/hangman"],
                "aliases": [],
                "permissions": "All users"
            },
            "rps": {
                "description": "Play Rock Paper Scissors",
                "usage": "/rps [rock|paper|scissors]",
                "examples": [
                    "/rps rock",
                    "/rps paper",
                    "/rps scissors"
                ],
                "aliases": [],
                "permissions": "All users"
            },
            "8ball": {
                "description": "Magic 8-Ball prediction",
                "usage": "/8ball <question>",
                "examples": ["/8ball Will I win?"],
                "aliases": [],
                "permissions": "All users"
            },
            "dice": {
                "description": "Roll dice",
                "usage": "/dice [sides]",
                "examples": [
                    "/dice",
                    "/dice 20"
                ],
                "aliases": [],
                "permissions": "All users"
            },
            "coinflip": {
                "description": "Flip a coin",
                "usage": "/coinflip",
                "examples": ["/coinflip"],
                "aliases": [],
                "permissions": "All users"
            },
            "guessnumber": {
                "description": "Guess the number game",
                "usage": "/guessnumber [min] [max]",
                "examples": [
                    "/guessnumber",
                    "/guessnumber 1 100"
                ],
                "aliases": [],
                "permissions": "All users"
            },

            # ========== POLLS ==========
            "poll": {
                "description": "Create a poll",
                "usage": "/poll <question> [options...]",
                "examples": [
                    "/poll What should we eat? Pizza Burger Tacos",
                    "/poll Should we have an event? Yes No Maybe"
                ],
                "aliases": [],
                "permissions": "All users"
            },
            "quizpoll": {
                "description": "Create a quiz poll (one correct answer)",
                "usage": "/quizpoll <question> <correct> [wrong...]",
                "examples": [
                    "/quizpoll What is 2+2? 4 3 5 6"
                ],
                "aliases": [],
                "permissions": "All users"
            },
            "closepoll": {
                "description": "Close a poll",
                "usage": "/closepoll (reply to poll)",
                "examples": ["/closepoll"],
                "aliases": [],
                "permissions": "Admin"
            },

            # ========== AI ASSISTANT ==========
            "ai": {
                "description": "Ask AI anything",
                "usage": "/ai <prompt>",
                "examples": [
                    "/ai What should we do for our event?",
                    "/ai Explain quantum physics simply"
                ],
                "aliases": [],
                "permissions": "All users"
            },
            "summarize": {
                "description": "Summarize last N messages",
                "usage": "/summarize [count]",
                "examples": [
                    "/summarize",
                    "/summarize 50"
                ],
                "aliases": [],
                "permissions": "All users"
            },
            "translate": {
                "description": "Translate text",
                "usage": "/translate <text> [language]",
                "examples": [
                    "/translate Hello es",
                    "/translate Bonjour English"
                ],
                "aliases": [],
                "permissions": "All users"
            },
            "factcheck": {
                "description": "Fact-check a claim",
                "usage": "/factcheck <claim>",
                "examples": [
                    "/factcheck The moon is made of cheese"
                ],
                "aliases": [],
                "permissions": "All users"
            },
            "explain": {
                "description": "Explain a concept",
                "usage": "/explain <concept>",
                "examples": [
                    "/explain blockchain",
                    "/explain quantum entanglement"
                ],
                "aliases": [],
                "permissions": "All users"
            },

            # ========== ANALYTICS ==========
            "stats": {
                "description": "View group statistics",
                "usage": "/stats",
                "examples": ["/stats"],
                "aliases": [],
                "permissions": "Admin"
            },
            "activity": {
                "description": "View activity metrics",
                "usage": "/activity [day|week|month]",
                "examples": [
                    "/activity day",
                    "/activity week"
                ],
                "aliases": [],
                "permissions": "Admin"
            },
            "members": {
                "description": "View member statistics",
                "usage": "/members",
                "examples": ["/members"],
                "aliases": [],
                "permissions": "Admin"
            },
            "top": {
                "description": "View top members",
                "usage": "/top [messages|xp|level|trust]",
                "examples": [
                    "/top messages",
                    "/top xp"
                ],
                "aliases": [],
                "permissions": "Admin"
            },
        }

        return command_docs.get(command_name)

    async def cmd_commands(self, ctx: NexusContext):
        """List all available commands."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if args:
            category = args[0].lower()
            await self._show_category_commands(ctx, category)
        else:
            await self._show_all_commands(ctx)

    async def _show_all_commands(self, ctx: NexusContext):
        """Show all commands categorized."""
        commands_text = "📚 **All Commands**\n\n━━━━━━━━━━━━━━━━━━━━\n\n"

        commands_text += "🛡️ **Moderation:**\n"
        commands_text += "/warn, /mute, /ban, /kick, /unban, /unmute, /pin, /unpin, /purge, /del, /history, /trust, /approve, /promote, /demote, /restrict\n\n"

        commands_text += "👋 **Welcome & Greetings:**\n"
        commands_text += "/setwelcome, /welcome, /resetwelcome, /setgoodbye, /goodbye\n\n"

        commands_text += "🔒 **Captcha:**\n"
        commands_text += "/captcha, /captchatimeout, /captchaaction\n\n"

        commands_text += "🔐 **Locks:**\n"
        commands_text += "/lock, /unlock, /locks, /locktypes\n\n"

        commands_text += "🚫 **Antispam:**\n"
        commands_text += "/antiflood, /antifloodmedia, /antiraidthreshold\n\n"

        commands_text += "📝 **Notes:**\n"
        commands_text += "/save, #notename, /notes, /clear, /clearall\n\n"

        commands_text += "🔍 **Filters:**\n"
        commands_text += "/filter, /stop, /stopall, /filters\n\n"

        commands_text += "📜 **Rules:**\n"
        commands_text += "/setrules, /rules, /resetrules\n\n"

        commands_text += "ℹ️ **Info:**\n"
        commands_text += "/info, /chatinfo, /id, /adminlist\n\n"

        commands_text += "💰 **Economy:**\n"
        commands_text += "/balance, /daily, /give, /leaderboard, /gamble, /slots, /shop, /inventory\n\n"

        commands_text += "⭐ **Reputation:**\n"
        commands_text += "/rep, /reputation, /repleaderboard\n\n"

        commands_text += "🎮 **Games:**\n"
        commands_text += "/trivia, /wordle, /hangman, /chess, /tictactoe, /rps, /8ball, /dice, /coinflip, /wheel, /memory, /guessnumber, /unscramble, /connect4, /battleship, /minesweeper, /sudoku, /mastermind, /riddle\n\n"

        commands_text += "📊 **Polls:**\n"
        commands_text += "/poll, /strawpoll, /quizpoll, /closepoll, /anonymouspoll, /multiplepoll, /scheduledpoll\n\n"

        commands_text += "⏰ **Scheduler:**\n"
        commands_text += "/schedule, /recurring, /unschedule, /listschedules\n\n"

        commands_text += "🤖 **AI Assistant:**\n"
        commands_text += "/ai, /summarize, /translate, /factcheck, /scam, /draft, /recommend, /sentiment, /explain, /rewrite, /analyze\n\n"

        commands_text += "📈 **Analytics:**\n"
        commands_text += "/stats, /activity, /members, /growth, /heatmap, /top, /trends, /commands, /moderation, /engagement\n\n"

        commands_text += "🌐 **Federations:**\n"
        commands_text += "/newfed, /joinfed, /fban, /unfban, /fedinfo, /fedbans\n\n"

        commands_text += "🔗 **Connections:**\n"
        commands_text += "/connect, /disconnect, /connected\n\n"

        commands_text += "🌍 **Languages:**\n"
        commands_text += "/setlang, /lang, /languages\n\n"

        commands_text += "📤 **Portability:**\n"
        commands_text += "/export, /import, /exportall, /importall\n\n"

        commands_text += "👤 **Identity:**\n"
        commands_text += "/me, /profile, /level, /xp, /badges, /setbio, /setbirthday\n\n"

        commands_text += "🎉 **Community:**\n"
        commands_text += "/event, /events, /digest, /spotlight, /milestone\n\n"

        commands_text += "🎙️ **Silent Mode:**\n"
        commands_text += "Add `!` to any mod command: /ban!, /mute!, /warn!\n\n"

        commands_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        commands_text += "💡 Use `/help <command>` for detailed info!"

        await ctx.reply(
            commands_text,
            buttons=[
                [
                    {"text": "🛡️ Moderation", "callback_data": "help_moderation"},
                    {"text": "🎮 Games", "callback_data": "help_games"},
                ],
                [
                    {"text": "💰 Economy", "callback_data": "help_economy"},
                    {"text": "🤖 AI", "callback_data": "help_ai"},
                ],
                [
                    {"text": "📱 Settings", "url": f"https://t.me/{ctx.bot_username}?start=settings"},
                    {"text": "📚 Docs", "url": "https://github.com/nexus-bot/docs"},
                ],
            ]
        )

    async def _show_category_commands(self, ctx: NexusContext, category: str):
        """Show commands for a specific category."""
        category_commands = {
            "moderation": {
                "title": "🛡️ Moderation Commands",
                "commands": [
                    "/warn - Warn a user",
                    "/mute - Mute a user",
                    "/ban - Ban a user",
                    "/kick - Kick a user",
                    "/unban - Unban a user",
                    "/unmute - Unmute a user",
                    "/pin - Pin a message",
                    "/unpin - Unpin a message",
                    "/purge - Delete messages",
                    "/del - Delete a message",
                    "/history - View history",
                    "/trust - Trust a user",
                    "/approve - Approve a user",
                    "/promote - Promote to admin",
                    "/demote - Demote from admin",
                    "/restrict - Restrict permissions",
                    "/slowmode - Enable slow mode",
                ]
            },
            "games": {
                "title": "🎮 Games Commands",
                "commands": [
                    "/trivia - Start trivia",
                    "/quiz - Start quiz",
                    "/wordle - Play Wordle",
                    "/hangman - Play Hangman",
                    "/chess - Play chess",
                    "/tictactoe - Play Tic Tac Toe",
                    "/rps - Rock Paper Scissors",
                    "/8ball - Magic 8-Ball",
                    "/dice - Roll dice",
                    "/coinflip - Flip a coin",
                    "/wheel - Spin the wheel",
                    "/memory - Memory game",
                    "/guessnumber - Guess number",
                    "/unscramble - Unscramble word",
                    "/connect4 - Connect Four",
                    "/battleship - Play Battleship",
                    "/minesweeper - Play Minesweeper",
                    "/sudoku - Play Sudoku",
                    "/mastermind - Mastermind code-breaking",
                    "/riddle - Solve a riddle",
                ]
            },
            "polls": {
                "title": "📊 Polls Commands",
                "commands": [
                    "/poll - Create a poll",
                    "/strawpoll - Quick straw poll",
                    "/quizpoll - Create quiz poll",
                    "/closepoll - Close a poll",
                    "/anonymouspoll - Anonymous poll",
                    "/multiplepoll - Multi-select poll",
                    "/scheduledpoll - Schedule a poll",
                ]
            },
            "analytics": {
                "title": "📈 Analytics Commands",
                "commands": [
                    "/stats - Group statistics",
                    "/activity - Activity metrics",
                    "/members - Member statistics",
                    "/growth - Member growth",
                    "/heatmap - Activity heatmap",
                    "/top - Top members",
                    "/trends - Message trends",
                    "/commands - Command usage",
                    "/moderation - Moderation stats",
                    "/engagement - Engagement metrics",
                ]
            },
            "economy": {
                "title": "💰 Economy Commands",
                "commands": [
                    "/balance - Check balance",
                    "/daily - Claim daily bonus",
                    "/give - Send coins",
                    "/leaderboard - View leaderboard",
                    "/gamble - Gamble coins",
                    "/slots - Play slots",
                    "/roulette - Play roulette",
                    "/shop - View shop",
                    "/buy - Buy item",
                    "/sell - Sell item",
                    "/inventory - View inventory",
                ]
            },
            "ai": {
                "title": "🤖 AI Commands",
                "commands": [
                    "/ai - Ask AI anything",
                    "/summarize - Summarize messages",
                    "/translate - Translate text",
                    "/factcheck - Fact check claims",
                    "/scam - Check for scams",
                    "/draft - AI draft announcement",
                    "/recommend - Get AI recommendations",
                    "/sentiment - Analyze sentiment",
                    "/explain - Explain concepts",
                    "/rewrite - Improve text",
                    "/analyze - Analyze user behavior",
                ]
            },
        }

        cat = category_commands.get(category.lower())

        if cat:
            text = f"**{cat['title']}**\n\n━━━━━━━━━━━━━━━━━━━━\n\n"
            for cmd in cat['commands']:
                text += f"• {cmd}\n"

            await ctx.reply(
                text,
                buttons=[[{"text": "↩️ Back to All Commands", "callback_data": "help_commands"}]]
            )
        else:
            await ctx.reply(
                f"❌ Category '{category}' not found.\n\n"
                f"Available categories: moderation, games, economy, polls, ai, analytics",
                buttons=[[{"text": "📖 All Commands", "callback_data": "help_commands"}]]
            )

    async def cmd_modules(self, ctx: NexusContext):
        """List all available modules."""
        modules_text = "📦 **Available Modules**\n\n━━━━━━━━━━━━━━━━━━━━\n\n"

        modules = [
            ("🛡️ Moderation", "Core moderation tools", "Enabled"),
            ("👋 Welcome", "Welcome & goodbye messages", "Enabled"),
            ("🔒 Captcha", "Anti-bot verification", "Enabled"),
            ("🔐 Locks", "Content type locking", "Enabled"),
            ("🚫 Antispam", "Flood & raid protection", "Enabled"),
            ("📝 Notes", "Saved notes system", "Enabled"),
            ("🔍 Filters", "Keyword auto-responses", "Enabled"),
            ("📜 Rules", "Group rules management", "Enabled"),
            ("💰 Economy", "Virtual currency system", "Enabled"),
            ("⭐ Reputation", "Member reputation", "Enabled"),
            ("🎮 Games", "Game suite", "Enabled"),
            ("📊 Polls", "Advanced polls", "Enabled"),
            ("⏰ Scheduler", "Message scheduling", "Enabled"),
            ("🤖 AI Assistant", "GPT-4 powered assistant", "Enabled"),
            ("📈 Analytics", "Group insights", "Enabled"),
            ("🌐 Federations", "Cross-group ban sync", "Enabled"),
            ("🔗 Connections", "Multi-group management", "Enabled"),
            ("✅ Approvals", "Approved users", "Enabled"),
            ("🧹 Cleaning", "Clean bot messages", "Enabled"),
            ("📌 Pins", "Pin management", "Enabled"),
            ("🌍 Languages", "Internationalization", "Enabled"),
            ("📤 Portability", "Settings import/export", "Enabled"),
            ("👤 Identity", "Member profiles", "Enabled"),
            ("🎉 Community", "Group events & more", "Enabled"),
        ]

        for name, desc, status in modules:
            status_emoji = "✅" if status == "Enabled" else "❌"
            modules_text += f"{status_emoji} **{name}**\n   {desc}\n\n"

        modules_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        modules_text += f"📊 **Total: {len(modules)} modules**\n"
        modules_text += f"📱 Use `/settings` to configure modules in Mini App"

        await ctx.reply(
            modules_text,
            buttons=[
                [
                    {"text": "📖 Commands", "callback_data": "help_commands"},
                    {"text": "⚙️ Settings", "url": f"https://t.me/{ctx.bot_username}?start=settings"},
                ]
            ]
        )

    async def cmd_modhelp(self, ctx: NexusContext):
        """Show moderation commands."""
        await self._show_category_commands(ctx, "moderation")

    async def cmd_adminhelp(self, ctx: NexusContext):
        """Show admin commands."""
        admin_text = "👑 **Admin Commands**\n\n━━━━━━━━━━━━━━━━━━━━\n\n"

        admin_text += "🛡️ **Moderation:**\n"
        admin_text += "/warn, /mute, /ban, /kick, /promote, /demote\n\n"

        admin_text += "👋 **Welcome:**\n"
        admin_text += "/setwelcome, /setgoodbye, /cleanwelcome\n\n"

        admin_text += "🔒 **Captcha:**\n"
        admin_text += "/captcha, /captchatimeout, /captchaaction\n\n"

        admin_text += "🔐 **Locks:**\n"
        admin_text += "/lock, /unlock, /locktype\n\n"

        admin_text += "🚫 **Antispam:**\n"
        admin_text += "/antiflood, /antiraidthreshold, /antifloodaction\n\n"

        admin_text += "📝 **Notes:**\n"
        admin_text += "/save, /clear, /clearall\n\n"

        admin_text += "🔍 **Filters:**\n"
        admin_text += "/filter, /stop, /stopall\n\n"

        admin_text += "📜 **Rules:**\n"
        admin_text += "/setrules, /resetrules\n\n"

        admin_text += "⏰ **Scheduler:**\n"
        admin_text += "/schedule, /recurring, /unschedule\n\n"

        admin_text += "🌐 **Federations:**\n"
        admin_text += "/newfed, /joinfed, /fban\n\n"

        admin_text += "📈 **Analytics:**\n"
        admin_text += "/stats, /activity, /members, /growth\n\n"

        admin_text += "📤 **Portability:**\n"
        admin_text += "/export, /import\n\n"

        admin_text += "🧹 **Cleaning:**\n"
        admin_text += "/cleanservice, /cleancommands, /clean\n\n"

        admin_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        admin_text += "💡 Use `/help <command>` for detailed info!"

        await ctx.reply(
            admin_text,
            buttons=[
                [
                    {"text": "📖 All Commands", "callback_data": "help_commands"},
                    {"text": "⚙️ Settings", "url": f"https://t.me/{ctx.bot_username}?start=settings"},
                ]
            ]
        )
