"""Scheduler module - Message scheduling and automation with cron support."""

import re
from datetime import datetime, timedelta
from typing import Optional

from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class SchedulerConfig(BaseModel):
    """Configuration for scheduler module."""
    max_scheduled_messages: int = 50
    max_recurring_messages: int = 10
    default_delete_after: int = 0
    allow_member_scheduling: bool = True


class SchedulerModule(NexusModule):
    """Message scheduling and automation system."""

    name = "scheduler"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Schedule messages for future delivery or recurring automation"
    category = ModuleCategory.UTILITY

    config_schema = SchedulerConfig
    default_config = SchedulerConfig().dict()

    commands = [
        CommandDef(
            name="schedule",
            description="Schedule a message for future delivery",
            admin_only=False,
            aliases=["sched", "delay"],
        ),
        CommandDef(
            name="recurring",
            description="Create a recurring message schedule",
            admin_only=False,
            aliases=["recur", "cron"],
        ),
        CommandDef(
            name="listscheduled",
            description="List all scheduled messages",
            admin_only=True,
            aliases=["schedlist", "ls"],
        ),
        CommandDef(
            name="cancelschedule",
            description="Cancel a scheduled message",
            admin_only=True,
            aliases=["cancelsched", "cs"],
        ),
        CommandDef(
            name="clearschedule",
            description="Clear all scheduled messages",
            admin_only=True,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("schedule", self.cmd_schedule)
        self.register_command("sched", self.cmd_schedule)
        self.register_command("delay", self.cmd_schedule)
        self.register_command("recurring", self.cmd_recurring)
        self.register_command("recur", self.cmd_recurring)
        self.register_command("cron", self.cmd_recurring)
        self.register_command("listscheduled", self.cmd_listscheduled)
        self.register_command("schedlist", self.cmd_listscheduled)
        self.register_command("ls", self.cmd_listscheduled)
        self.register_command("cancelschedule", self.cmd_cancelschedule)
        self.register_command("cancelsched", self.cmd_cancelschedule)
        self.register_command("cs", self.cmd_cancelschedule)
        self.register_command("clearschedule", self.cmd_clearschedule)

    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """Parse time string to datetime."""
        now = datetime.utcnow()

        # Relative time patterns
        patterns = {
            r"(\d+)s": lambda m: now + timedelta(seconds=int(m.group(1))),
            r"(\d+)m": lambda m: now + timedelta(minutes=int(m.group(1))),
            r"(\d+)h": lambda m: now + timedelta(hours=int(m.group(1))),
            r"(\d+)d": lambda m: now + timedelta(days=int(m.group(1))),
            r"(\d+)w": lambda m: now + timedelta(weeks=int(m.group(1))),
            r"(\d+)mo": lambda m: now + timedelta(days=int(m.group(1)) * 30),
            r"tomorrow": lambda m: now + timedelta(days=1),
            r"next week": lambda m: now + timedelta(weeks=1),
            r"next month": lambda m: now + timedelta(days=30),
        }

        for pattern, handler in patterns.items():
            match = re.search(pattern, time_str.lower())
            if match:
                return handler(match)

        # Specific time (HH:MM)
        time_match = re.search(r"(\d{1,2}):(\d{2})", time_str)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if scheduled < now:
                scheduled += timedelta(days=1)
            return scheduled

        # Date format (YYYY-MM-DD HH:MM)
        date_match = re.search(r"(\d{4})-(\d{2})-(\d{2}) (\d{1,2}):(\d{2})", time_str)
        if date_match:
            year, month, day, hour, minute = map(int, date_match.groups())
            try:
                return datetime(year, month, day, hour, minute)
            except ValueError:
                pass

        return None

    def _parse_days(self, days_str: str) -> list:
        """Parse days of week from string."""
        day_map = {
            "mon": 0, "monday": 0,
            "tue": 1, "tuesday": 1,
            "wed": 2, "wednesday": 2,
            "thu": 3, "thursday": 3,
            "fri": 4, "friday": 4,
            "sat": 5, "saturday": 5,
            "sun": 6, "sunday": 6,
        }

        days = []
        parts = days_str.lower().split(",")
        for part in parts:
            part = part.strip()
            if part in day_map:
                days.append(day_map[part])
            elif "-" in part:  # Range like "mon-fri"
                start, end = part.split("-")
                if start in day_map and end in day_map:
                    start_day = day_map[start]
                    end_day = day_map[end]
                    if start_day <= end_day:
                        days.extend(range(start_day, end_day + 1))
                    else:  # Wrap around
                        days.extend(range(start_day, 7))
                        days.extend(range(0, end_day + 1))

        return list(set(days))

    def _parse_cron(self, cron_str: str) -> Optional[dict]:
        """Parse cron expression."""
        parts = cron_str.split()
        if len(parts) != 5:
            return None

        minute, hour, day, month, weekday = parts

        return {
            "minute": minute,
            "hour": hour,
            "day": day,
            "month": month,
            "weekday": weekday,
        }

    async def cmd_schedule(self, ctx: NexusContext):
        """Schedule a message for future delivery."""
        config = SchedulerConfig(**ctx.group.module_configs.get("scheduler", {}))

        if not config.allow_member_scheduling and not ctx.user.is_admin:
            await ctx.reply("❌ Only admins can schedule messages in this group")
            return

        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []
        if not args:
            await ctx.reply(
                "❌ Usage: /schedule <time> <message>\n"
                "Time formats:\n"
                "• Relative: 30s, 5m, 2h, 1d, 1w\n"
                "• Specific: 14:30, 2024-12-25 14:30\n"
                "• Natural: tomorrow, next week\n\n"
                "Examples:\n"
                "/schedule 30s Don't forget the meeting!\n"
                "/schedule 1h Good morning everyone!\n"
                "/schedule tomorrow Daily reminder"
            )
            return

        # Parse time
        time_match = re.match(r"^(\S+)\s+(.+)$", " ".join(args))
        if not time_match:
            await ctx.reply("❌ Invalid format. Use: /schedule <time> <message>")
            return

        time_str, message = time_match.groups()
        scheduled_time = self._parse_time(time_str)

        if not scheduled_time:
            await ctx.reply(
                f"❌ Invalid time format: {time_str}\n"
                "Use: 30s, 5m, 2h, 1d, 1w, 14:30, tomorrow, etc."
            )
            return

        # Check limit
        from shared.models import ScheduledMessage

        result = ctx.db.execute(
            f"""
            SELECT COUNT(*)
            FROM scheduled_messages
            WHERE group_id = {ctx.group.id}
              AND schedule_type = 'once'
              AND is_enabled = TRUE
            """
        )
        count = result.scalar()

        if count >= config.max_scheduled_messages:
            await ctx.reply(
                f"❌ Maximum scheduled messages reached ({config.max_scheduled_messages})"
            )
            return

        # Store message
        from shared.models import User

        user_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
        )
        user_id = user_result.scalar()

        scheduled_msg = ScheduledMessage(
            group_id=ctx.group.id,
            content=message,
            schedule_type="once",
            run_at=scheduled_time,
            created_by=user_id,
            is_enabled=True,
        )

        # Parse delete_after
        delete_match = re.search(r"delete_after[=:](\d+)([smhd])", message.lower())
        if delete_match:
            amount = int(delete_match.group(1))
            unit = delete_match.group(2)
            unit_map = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}
            scheduled_msg.delete_after = f"{amount} {unit_map[unit]}"

        ctx.db.add(scheduled_msg)
        ctx.db.commit()

        # Format time for display
        time_until = scheduled_time - datetime.utcnow()
        if time_until.total_seconds() < 60:
            time_str_fmt = f"{int(time_until.total_seconds())} seconds"
        elif time_until.total_seconds() < 3600:
            time_str_fmt = f"{int(time_until.total_seconds() / 60)} minutes"
        elif time_until.total_seconds() < 86400:
            time_str_fmt = f"{int(time_until.total_seconds() / 3600)} hours"
        else:
            time_str_fmt = f"{int(time_until.total_seconds() / 86400)} days"

        await ctx.reply(
            f"✅ Message scheduled!\n\n"
            f"⏰ Will send in {time_str_fmt}\n"
            f"📝 Content: {message}\n\n"
            f"🆔 ID: {scheduled_msg.id}"
        )

    async def cmd_recurring(self, ctx: NexusContext):
        """Create a recurring message schedule."""
        config = SchedulerConfig(**ctx.group.module_configs.get("scheduler", {}))

        if not config.allow_member_scheduling and not ctx.user.is_admin:
            await ctx.reply("❌ Only admins can create recurring schedules in this group")
            return

        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []
        if not args:
            await ctx.reply(
                "❌ Usage: /recurring <schedule> <message>\n"
                "Schedule formats:\n"
                "• Cron: '0 9 * * *' (9 AM daily)\n"
                "• Every X hours: 'every 2h'\n"
                "• Days of week: 'Mon,Wed,Fri 9:00'\n\n"
                "Examples:\n"
                "/recurring '0 9 * * *' Good morning!\n"
                "/recurring 'every 2h' Check the status\n"
                "/recurring 'Mon,Fri 14:00' Meeting reminder"
            )
            return

        # Parse schedule
        schedule_match = re.match(r"^['\"](.+)['\"]\s+(.+)$", " ".join(args))
        if not schedule_match:
            # Try simpler format
            schedule_match = re.match(r"^(\S+)\s+(.+)$", " ".join(args))

        if not schedule_match:
            await ctx.reply("❌ Invalid format")
            return

        schedule_str, message = schedule_match.groups()
        cron_expr = None
        days_of_week = []
        time_slot = None

        # Check for cron
        cron_data = self._parse_cron(schedule_str)
        if cron_data:
            cron_expr = schedule_str
        # Check for "every X"
        elif schedule_str.lower().startswith("every "):
            interval_match = re.match(r"every (\d+)([hm])", schedule_str.lower())
            if interval_match:
                amount = int(interval_match.group(1))
                unit = interval_match.group(2)
                if unit == "h":
                    cron_expr = f"0 */{amount} * * *"
                else:  # minutes
                    cron_expr = f"*/{amount} * * * *"
        # Check for days of week with time
        else:
            parts = schedule_str.split()
            if len(parts) >= 2:
                days_str = parts[0]
                time_str = " ".join(parts[1:])
                days_of_week = self._parse_days(days_str)
                time_slot = self._parse_time(time_str)

                if days_of_week and time_slot:
                    # Build cron from days and time
                    weekday_str = ",".join(map(str, days_of_week))
                    cron_expr = f"{time_slot.minute} {time_slot.hour} * * {weekday_str}"

        if not cron_expr:
            await ctx.reply(
                f"❌ Invalid schedule format: {schedule_str}\n"
                "Use cron format, 'every Xh', or 'Day,Day HH:MM'"
            )
            return

        # Check limit
        from shared.models import ScheduledMessage

        result = ctx.db.execute(
            f"""
            SELECT COUNT(*)
            FROM scheduled_messages
            WHERE group_id = {ctx.group.id}
              AND schedule_type = 'recurring'
              AND is_enabled = TRUE
            """
        )
        count = result.scalar()

        if count >= config.max_recurring_messages:
            await ctx.reply(
                f"❌ Maximum recurring messages reached ({config.max_recurring_messages})"
            )
            return

        # Store message
        from shared.models import User

        user_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
        )
        user_id = user_result.scalar()

        scheduled_msg = ScheduledMessage(
            group_id=ctx.group.id,
            content=message,
            schedule_type="recurring",
            cron_expression=cron_expr,
            created_by=user_id,
            is_enabled=True,
        )

        if days_of_week:
            scheduled_msg.days_of_week = days_of_week

        if time_slot:
            scheduled_msg.time_slot = time_slot.strftime("%H:%M")

        ctx.db.add(scheduled_msg)
        ctx.db.commit()

        await ctx.reply(
            f"✅ Recurring message created!\n\n"
            f"🔄 Schedule: {cron_expr}\n"
            f"📝 Content: {message}\n\n"
            f"🆔 ID: {scheduled_msg.id}"
        )

    async def cmd_listscheduled(self, ctx: NexusContext):
        """List all scheduled messages."""
        from shared.models import ScheduledMessage, User

        result = ctx.db.execute(
            f"""
            SELECT sm.id, sm.content, sm.schedule_type, sm.run_at, sm.cron_expression,
                   sm.is_enabled, sm.last_run, sm.next_run, sm.run_count,
                   u.username, u.first_name, u.last_name
            FROM scheduled_messages sm
            JOIN users u ON sm.created_by = u.id
            WHERE sm.group_id = {ctx.group.id}
            ORDER BY sm.next_run ASC NULLS LAST
            LIMIT 20
            """
        )

        messages = result.fetchall()
        if not messages:
            await ctx.reply("✅ No scheduled messages")
            return

        text = "📅 Scheduled Messages\n\n"

        for row in messages:
            msg_id = row[0]
            content = row[1][:50] + "..." if len(row[1]) > 50 else row[1]
            sched_type = row[2]
            run_at = row[3]
            cron = row[4]
            enabled = row[5]
            last_run = row[6]
            next_run = row[7]
            run_count = row[8]
            creator = row[9] or f"{row[10]} {row[11] or ''}".strip()

            status = "✅" if enabled else "❌"
            text += f"{status} [{msg_id}] {sched_type}\n"
            text += f"📝 {content}\n"
            text += f"👤 By: {creator}\n"

            if sched_type == "once":
                if run_at:
                    time_until = (run_at - datetime.utcnow()).total_seconds()
                    if time_until > 0:
                        hours = int(time_until // 3600)
                        minutes = int((time_until % 3600) // 60)
                        text += f"⏰ In {hours}h {minutes}m\n"
            else:
                text += f"🔄 {cron}\n"
                text += f"📊 Run count: {run_count}\n"

            text += "\n"

        await ctx.reply(
            text,
            buttons=[[{"text": "Clear All", "callback_data": "sched_clear_all"}]]
        )

    async def cmd_cancelschedule(self, ctx: NexusContext):
        """Cancel a scheduled message."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /cancelschedule <message_id>")
            return

        try:
            msg_id = int(args[0])
        except ValueError:
            await ctx.reply("❌ Invalid message ID")
            return

        from shared.models import ScheduledMessage

        result = ctx.db.execute(
            f"""
            SELECT id
            FROM scheduled_messages
            WHERE id = {msg_id} AND group_id = {ctx.group.id}
            LIMIT 1
            """
        )
        row = result.fetchone()

        if not row:
            await ctx.reply("❌ Message not found")
            return

        ctx.db.execute(f"DELETE FROM scheduled_messages WHERE id = {msg_id}")
        ctx.db.commit()

        await ctx.reply(f"✅ Scheduled message #{msg_id} cancelled")

    async def cmd_clearschedule(self, ctx: NexusContext):
        """Clear all scheduled messages."""
        from shared.models import ScheduledMessage

        result = ctx.db.execute(
            f"""
            SELECT COUNT(*)
            FROM scheduled_messages
            WHERE group_id = {ctx.group.id}
            """
        )
        count = result.scalar()

        if count == 0:
            await ctx.reply("✅ No scheduled messages to clear")
            return

        ctx.db.execute(
            f"DELETE FROM scheduled_messages WHERE group_id = {ctx.group.id}"
        )
        ctx.db.commit()

        await ctx.reply(f"✅ Cleared {count} scheduled message(s)")
