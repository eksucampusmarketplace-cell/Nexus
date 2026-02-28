"""Polls module - Advanced polling and voting system."""

from typing import List, Optional
from datetime import datetime, timedelta
from aiogram.types import Message, Poll
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class PollsConfig(BaseModel):
    """Configuration for polls module."""
    enabled: bool = True
    allow_anonymous: bool = False
    allow_multiple: bool = False
    default_close_time: int = 3600


class PollsModule(NexusModule):
    """Advanced polling and voting system."""

    name = "polls"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Advanced polls with multiple options and voting"
    category = ModuleCategory.COMMUNITY

    config_schema = PollsConfig
    default_config = PollsConfig().dict()

    commands = [
        CommandDef(
            name="poll",
            description="Create a poll",
            admin_only=False,
            args="<question> [options...]",
        ),
        CommandDef(
            name="strawpoll",
            description="Create a quick straw poll",
            admin_only=False,
            args="<question> [options...]",
        ),
        CommandDef(
            name="quizpoll",
            description="Create a quiz poll (one correct answer)",
            admin_only=False,
            args="<question> <correct> [wrong...]",
        ),
        CommandDef(
            name="closepoll",
            description="Close a poll",
            admin_only=True,
        ),
        CommandDef(
            name="vote",
            description="Vote in a poll (via callback)",
            admin_only=False,
        ),
        CommandDef(
            name="pollresults",
            description="View poll results",
            admin_only=False,
        ),
        CommandDef(
            name="anonymouspoll",
            description="Create an anonymous poll",
            admin_only=False,
            args="<question> [options...]",
        ),
        CommandDef(
            name="multiplepoll",
            description="Create a multi-select poll",
            admin_only=False,
            args="<question> [options...]",
        ),
        CommandDef(
            name="scheduledpoll",
            description="Schedule a poll for later",
            admin_only=True,
            args="<time> <question> [options...]",
        ),
        CommandDef(
            name="pollhistory",
            description="View poll history",
            admin_only=True,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("poll", self.cmd_poll)
        self.register_command("strawpoll", self.cmd_strawpoll)
        self.register_command("quizpoll", self.cmd_quizpoll)
        self.register_command("closepoll", self.cmd_closepoll)
        self.register_command("pollresults", self.cmd_pollresults)
        self.register_command("anonymouspoll", self.cmd_anonymouspoll)
        self.register_command("multiplepoll", self.cmd_multiplepoll)
        self.register_command("scheduledpoll", self.cmd_scheduledpoll)
        self.register_command("pollhistory", self.cmd_pollhistory)

    async def cmd_poll(self, ctx: NexusContext):
        """Create a poll."""
        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not args:
            await ctx.reply(
                "❌ Usage: `/poll <question> [options...]`\n\n"
                "Examples:\n"
                "• `/poll What's your favorite color? Red Blue Green Yellow`\n"
                "• `/poll Should we have a weekly event? Yes No Maybe`"
            )
            return

        text = args[0]
        options = text.split() if len(args) > 1 else ["Yes", "No"]

        # Parse options after question
        if len(args) > 1:
            parts = args[1].split()
            if len(parts) >= 2:
                options = parts

        config = ctx.group.module_configs.get("polls", {})

        poll = Poll(
            id=f"poll_{ctx.message.message_id}",
            question=text,
            options=options[:10],  # Max 10 options
            type="regular",
            allows_multiple_answers=config.get("allow_multiple", False),
            is_anonymous=config.get("allow_anonymous", False),
            is_closed=False
        )

        try:
            message = await ctx.bot.send_poll(
                chat_id=ctx.chat_id,
                question=poll.question,
                options=poll.options,
                type=poll.type,
                allows_multiple_answers=poll.allows_multiple_answers,
                is_anonymous=poll.is_anonymous
            )

            # Store poll in database
            if ctx.db:
                from shared.models import Poll
                poll_data = Poll(
                    group_id=ctx.group.id,
                    question=text,
                    options=pool.options,
                    is_anonymous=poll.is_anonymous,
                    allows_multiple=poll.allows_multiple_answers,
                    message_id=message.message_id,
                    created_by=ctx.user.user_id
                )
                ctx.db.add(poll_data)

            await ctx.reply("📊 Poll created successfully!")

        except Exception as e:
            await ctx.reply(f"❌ Error creating poll: {e}")

    async def cmd_strawpoll(self, ctx: NexusContext):
        """Create a quick straw poll."""
        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not args:
            await ctx.reply(
                "❌ Usage: `/strawpoll <question> [options...]`\n\n"
                "Example: `/strawpoll What should we eat? Pizza Burger Tacos`"
            )
            return

        text = args[0]
        options = args[1].split() if len(args) > 1 else ["👍", "👎"]

        try:
            await ctx.bot.send_poll(
                chat_id=ctx.chat_id,
                question=f"🗳️ {text}",
                options=options[:10],
                type="regular",
                allows_multiple_answers=False,
                is_anonymous=True
            )
        except Exception as e:
            await ctx.reply(f"❌ Error: {e}")

    async def cmd_quizpoll(self, ctx: NexusContext):
        """Create a quiz poll."""
        args = ctx.message.text.split(maxsplit=2)[1:] if ctx.message.text else []

        if len(args) < 2:
            await ctx.reply(
                "❌ Usage: `/quizpoll <question> <correct_answer> [wrong_answer1] [wrong_answer2]...`\n\n"
                "Example: `/quizpoll What is 2+2? 4 3 5 6`"
            )
            return

        question = args[0]
        correct = args[1]
        wrong = args[2].split() if len(args) > 2 else []

        options = [correct] + wrong
        # Shuffle wrong answers
        import random
        random.shuffle(options)
        correct_index = options.index(correct)

        try:
            message = await ctx.bot.send_poll(
                chat_id=ctx.chat_id,
                question=f"❓ {question}",
                options=options[:10],
                type="quiz",
                correct_option_id=correct_index,
                is_anonymous=False,
                explanation=f"The correct answer is: {correct}"
            )

            await ctx.reply("🎯 Quiz poll created!")
        except Exception as e:
            await ctx.reply(f"❌ Error: {e}")

    async def cmd_closepoll(self, ctx: NexusContext):
        """Close a poll."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if not ctx.replied_to:
            await ctx.reply("❌ Reply to a poll to close it")
            return

        try:
            await ctx.bot.stop_poll(
                chat_id=ctx.chat_id,
                message_id=ctx.replied_to.message_id
            )
            await ctx.reply("📊 Poll closed!")
        except Exception as e:
            await ctx.reply(f"❌ Error: {e}")

    async def cmd_pollresults(self, ctx: NexusContext):
        """View poll results."""
        if not ctx.replied_to:
            await ctx.reply("❌ Reply to a poll to see results")
            return

        # Results are shown when poll stops
        await ctx.reply("📊 Click 'Show Results' on the poll to see results")

    async def cmd_anonymouspoll(self, ctx: NexusContext):
        """Create an anonymous poll."""
        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not args:
            await ctx.reply(
                "❌ Usage: `/anonymouspoll <question> [options...]`\n\n"
                "Example: `/anonymouspoll Who should win? Alice Bob Charlie`"
            )
            return

        text = args[0]
        options = args[1].split() if len(args) > 1 else ["Yes", "No"]

        try:
            await ctx.bot.send_poll(
                chat_id=ctx.chat_id,
                question=f"🔒 {text}",
                options=options[:10],
                type="regular",
                allows_multiple_answers=False,
                is_anonymous=True
            )
        except Exception as e:
            await ctx.reply(f"❌ Error: {e}")

    async def cmd_multiplepoll(self, ctx: NexusContext):
        """Create a multi-select poll."""
        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not args:
            await ctx.reply(
                "❌ Usage: `/multiplepoll <question> [options...]`\n\n"
                "Example: `/multiplepoll Which games do you like? Chess Cards Dice Board`"
            )
            return

        text = args[0]
        options = args[1].split() if len(args) > 1 else ["Option 1", "Option 2", "Option 3"]

        try:
            await ctx.bot.send_poll(
                chat_id=ctx.chat_id,
                question=f"✅ {text}",
                options=options[:10],
                type="regular",
                allows_multiple_answers=True,
                is_anonymous=False
            )
        except Exception as e:
            await ctx.reply(f"❌ Error: {e}")

    async def cmd_scheduledpoll(self, ctx: NexusContext):
        """Schedule a poll for later."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split(maxsplit=2)[1:] if ctx.message.text else []

        if len(args) < 2:
            await ctx.reply(
                "❌ Usage: `/scheduledpoll <time> <question> [options...]`\n\n"
                "Examples:\n"
                "• `/scheduledpoll 18:00 What should we watch? Movie Series Documentary`\n"
                "• `/scheduledpoll tomorrow 9am Morning or Evening?`"
            )
            return

        time_str = args[0]
        question = args[1]
        options = args[2].split() if len(args) > 2 else ["Yes", "No"]

        # Parse time (simple implementation)
        try:
            if ":" in time_str:
                hours, minutes = map(int, time_str.split(":"))
                scheduled_time = datetime.now().replace(hour=hours, minute=minutes)
            elif time_str.lower() == "tomorrow":
                scheduled_time = datetime.now() + timedelta(days=1)
            else:
                await ctx.reply("❌ Invalid time format. Use HH:MM or 'tomorrow'")
                return

            # Schedule the poll (would use Celery in production)
            await ctx.reply(
                f"📅 Poll scheduled for:\n"
                f"⏰ {scheduled_time.strftime('%Y-%m-%d %H:%M')}\n"
                f"❓ {question}\n\n"
                f"✅ Will be created automatically!"
            )

            # Store in database
            if ctx.db:
                from shared.models import ScheduledMessage
                scheduled = ScheduledMessage(
                    group_id=ctx.group.id,
                    content=f"POLL:{question}|{','.join(options)}",
                    schedule_type="poll",
                    run_at=scheduled_time,
                    created_by=ctx.user.user_id
                )
                ctx.db.add(scheduled)

        except Exception as e:
            await ctx.reply(f"❌ Error scheduling poll: {e}")

    async def cmd_pollhistory(self, ctx: NexusContext):
        """View poll history."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.db:
            from shared.models import Poll
            result = ctx.db.execute(
                f"""
                SELECT p.id, p.question, p.options, p.is_anonymous,
                       p.allows_multiple, p.created_at,
                       u.username, u.first_name
                FROM polls p
                JOIN users u ON p.created_by = u.id
                WHERE p.group_id = {ctx.group.id}
                ORDER BY p.created_at DESC
                LIMIT 10
                """
            )

            polls = result.fetchall()
            if not polls:
                await ctx.reply("❌ No polls created yet")
                return

            text = "📊 **Poll History**\n\n"
            for row in polls:
                poll_id = row[0]
                question = row[1]
                options = eval(row[2]) if isinstance(row[2], str) else row[2]
                creator = row[6] or row[7]
                created = row[5].strftime("%Y-%m-%d %H:%M")

                text += f"━━━━━━━━━━\n"
                text += f"Poll #{poll_id}\n"
                text += f"❓ {question}\n"
                text += f"📝 Options: {', '.join(options[:3])}{'...' if len(options) > 3 else ''}\n"
                text += f"👤 Created by: {creator}\n"
                text += f"🕐 {created}\n\n"

            await ctx.reply(text)
