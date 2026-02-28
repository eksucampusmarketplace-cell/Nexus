"""Community module - Member matching, interest groups, events, and social features."""

import random
from datetime import datetime, timedelta
from typing import Optional, List

from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class CommunityConfig(BaseModel):
    """Configuration for community module."""
    enable_matching: bool = True
    enable_events: bool = True
    enable_interest_groups: bool = True
    event_creation_cooldown: int = 3600  # 1 hour
    max_events_per_group: int = 10
    max_interest_groups: int = 20


class CommunityModule(NexusModule):
    """Community features with matching, events, and interest groups."""

    name = "community"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Community features: member matching, interest groups, events, celebrations"
    category = ModuleCategory.COMMUNITY

    config_schema = CommunityConfig
    default_config = CommunityConfig().dict()

    commands = [
        CommandDef(
            name="match",
            description="Find a matching member",
            admin_only=False,
            aliases=["findfriend", "matchme"],
        ),
        CommandDef(
            name="interestgroups",
            description="List all interest groups",
            admin_only=False,
            aliases=["interests", "groups", "communities"],
        ),
        CommandDef(
            name="joingroup",
            description="Join an interest group",
            admin_only=False,
            aliases=["joininterest", "joinig"],
        ),
        CommandDef(
            name="leavegroup",
            description="Leave an interest group",
            admin_only=False,
            aliases=["leaveinterest", "leaveig"],
        ),
        CommandDef(
            name="creategroup",
            description="Create an interest group",
            admin_only=False,
            aliases=["createig", "makegroup"],
        ),
        CommandDef(
            name="events",
            description="List all events",
            admin_only=False,
        ),
        CommandDef(
            name="createevent",
            description="Create a new event",
            admin_only=False,
            aliases=["addevent", "event"],
        ),
        CommandDef(
            name="rsvp",
            description="RSVP to an event",
            admin_only=False,
        ),
        CommandDef(
            name="myevents",
            description="View your event RSVPs",
            admin_only=False,
        ),
        CommandDef(
            name="topevents",
            description="View top events by RSVP",
            admin_only=False,
        ),
        CommandDef(
            name="celebrate",
            description="Celebrate a member milestone",
            admin_only=False,
        ),
        CommandDef(
            name="birthday",
            description="Set/view birthday",
            admin_only=False,
        ),
        CommandDef(
            name="birthdays",
            description="View upcoming birthdays",
            admin_only=False,
        ),
        CommandDef(
            name="bio",
            description="Set your bio",
            admin_only=False,
        ),
        CommandDef(
            name="membercount",
            description="Show member count milestone",
            admin_only=False,
            aliases=["members", "count"],
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("match", self.cmd_match)
        self.register_command("findfriend", self.cmd_match)
        self.register_command("matchme", self.cmd_match)
        self.register_command("interestgroups", self.cmd_interestgroups)
        self.register_command("interests", self.cmd_interestgroups)
        self.register_command("groups", self.cmd_interestgroups)
        self.register_command("communities", self.cmd_interestgroups)
        self.register_command("joingroup", self.cmd_joingroup)
        self.register_command("joininterest", self.cmd_joingroup)
        self.register_command("joinig", self.cmd_joingroup)
        self.register_command("leavegroup", self.cmd_leavegroup)
        self.register_command("leaveinterest", self.cmd_leavegroup)
        self.register_command("leaveig", self.cmd_leavegroup)
        self.register_command("creategroup", self.cmd_creategroup)
        self.register_command("createig", self.cmd_creategroup)
        self.register_command("makegroup", self.cmd_creategroup)
        self.register_command("events", self.cmd_events)
        self.register_command("createevent", self.cmd_createevent)
        self.register_command("addevent", self.cmd_createevent)
        self.register_command("event", self.cmd_createevent)
        self.register_command("rsvp", self.cmd_rsvp)
        self.register_command("myevents", self.cmd_myevents)
        self.register_command("topevents", self.cmd_topevents)
        self.register_command("celebrate", self.cmd_celebrate)
        self.register_command("birthday", self.cmd_birthday)
        self.register_command("birthdays", self.cmd_birthdays)
        self.register_command("bio", self.cmd_bio)
        self.register_command("membercount", self.cmd_membercount)
        self.register_command("members", self.cmd_membercount)
        self.register_command("count", self.cmd_membercount)

    async def cmd_match(self, ctx: NexusContext):
        """Find a matching member."""
        config = CommunityConfig(**ctx.group.module_configs.get("community", {}))

        if not config.enable_matching:
            await ctx.reply("❌ Member matching is disabled in this group")
            return

        # Get active members who haven't matched recently
        from shared.models import Member

        result = ctx.db.execute(
            f"""
            SELECT m.id, u.telegram_id, u.username, u.first_name, u.last_name,
                   m.message_count, m.trust_score, m.xp
            FROM members m
            JOIN users u ON m.user_id = u.id
            WHERE m.group_id = {ctx.group.id}
              AND m.id != {ctx.user.member_id}
              AND m.is_banned = FALSE
            ORDER BY RANDOM()
            LIMIT 5
            """
        )

        matches = result.fetchall()

        if not matches:
            await ctx.reply("❌ No matches found. Try again later!")
            return

        # Present matches
        text = f"👋 {ctx.user.mention}, here are some members you might connect with:\n\n"

        for i, row in enumerate(matches, 1):
            member_id = row[0]
            telegram_id = row[1]
            username = row[2]
            first_name = row[3]
            last_name = row[4]
            msg_count = row[5]
            trust_score = row[6]
            xp = row[7]

            name = f"{first_name} {last_name or ''}".strip()
            display_name = username or name

            text += f"{i}. {display_name}\n"
            text += f"   💬 {msg_count} messages | 🤝 {trust_score}/100 trust | ⭐ {xp} XP\n"

        text += f"\n💡 Tip: Message them to connect! Use /interestgroups to find people with similar interests."

        await ctx.reply(text)

    async def cmd_interestgroups(self, ctx: NexusContext):
        """List all interest groups."""
        config = CommunityConfig(**ctx.group.module_configs.get("community", {}))

        if not config.enable_interest_groups:
            await ctx.reply("❌ Interest groups are disabled in this group")
            return

        # Get interest groups
        # For now, we'll use a simple tag system
        # In production, this would be a dedicated table

        result = ctx.db.execute(
            f"""
            SELECT tag, COUNT(*) as member_count
            FROM member_profiles
            WHERE group_id = {ctx.group.id}
              AND tag IS NOT NULL
            GROUP BY tag
            ORDER BY member_count DESC
            LIMIT 20
            """
        )

        # Since we don't have member_profiles table yet, show placeholder
        text = "🏷️ Interest Groups\n\n"
        text += "Interest groups allow you to connect with like-minded members.\n\n"
        text += "How to create:\n"
        text += "/creategroup <name> <tags> <description>\n\n"
        text += "How to join:\n"
        text += "/joingroup <group_name>\n\n"
        text += "📝 Note: This feature uses tags in user profiles. Set your interests with /bio."

        await ctx.reply(text)

    async def cmd_joingroup(self, ctx: NexusContext):
        """Join an interest group."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /joingroup <group_name>")
            return

        group_name = " ".join(args)

        # For now, just notify that feature needs proper implementation
        await ctx.reply(
            f"📝 You want to join: {group_name}\n\n"
            f"ℹ️ This feature will be fully implemented with dedicated interest groups table.\n"
            f"💡 For now, use /bio to set your interests and find like-minded members!"
        )

    async def cmd_leavegroup(self, ctx: NexusContext):
        """Leave an interest group."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /leavegroup <group_name>")
            return

        group_name = " ".join(args)

        await ctx.reply(
            f"📝 You want to leave: {group_name}\n\n"
            f"ℹ️ This feature will be fully implemented with dedicated interest groups table."
        )

    async def cmd_creategroup(self, ctx: NexusContext):
        """Create an interest group."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if len(args) < 2:
            await ctx.reply(
                "❌ Usage: /creategroup <name> <description>\n\n"
                "Example: /creategroup Gamers People who love gaming and esports"
            )
            return

        group_name = args[0]
        description = " ".join(args[1:])

        # For now, just log the creation
        await ctx.reply(
            f"✅ Interest group created!\n\n"
            f"📝 Name: {group_name}\n"
            f"📄 Description: {description}\n"
            f"👤 Created by: {ctx.user.mention}\n\n"
            f"ℹ️ Full implementation will include:\n"
            f"• Dedicated interest groups table\n"
            f"• Member joining/leaving\n"
            f"• Interest group management\n"
            f"• Interest group announcements"
        )

    async def cmd_events(self, ctx: NexusContext):
        """List all events."""
        config = CommunityConfig(**ctx.group.module_configs.get("community", {}))

        if not config.enable_events:
            await ctx.reply("❌ Events are disabled in this group")
            return

        # Get events
        from shared.models import GroupEvent

        result = ctx.db.execute(
            f"""
            SELECT id, title, description, starts_at, ends_at, location,
                   status, created_by
            FROM group_events
            WHERE group_id = {ctx.group.id}
              AND status IN ('upcoming', 'active')
            ORDER BY starts_at ASC
            LIMIT 10
            """
        )

        events = result.fetchall()

        if not events:
            await ctx.reply(
                "📅 No upcoming events.\n\n"
                "Create one with: /createevent <title> <description> <date> <time> [location]"
            )
            return

        text = "📅 Upcoming Events\n\n"

        for row in events:
            event_id = row[0]
            title = row[1]
            description = row[2]
            starts_at = row[3]
            ends_at = row[4]
            location = row[5]
            status = row[6]

            status_emoji = "🟢" if status == "upcoming" else "🔴"
            date_str = starts_at.strftime("%Y-%m-%d %H:%M")

            text += f"{status_emoji} {title}\n"
            text += f"   📅 {date_str}\n"

            if location:
                text += f"   📍 {location}\n"

            text += f"   ID: {event_id}\n\n"

        text += f"💡 RSVP with: /rsvp <event_id> <going|maybe|not_going>"

        await ctx.reply(text)

    async def cmd_createevent(self, ctx: NexusContext):
        """Create a new event."""
        config = CommunityConfig(**ctx.group.module_configs.get("community", {}))

        if not config.enable_events:
            await ctx.reply("❌ Events are disabled in this group")
            return

        args = ctx.message.text.split(maxsplit=3)[1:] if ctx.message.text else []

        if len(args) < 1:
            await ctx.reply(
                "❌ Usage: /createevent <title> <description> <date> <time> [location]\n\n"
                "Example: /createevent Game Night Weekly gaming session 2024-12-25 20:00 Voice chat"
            )
            return

        title = args[0]
        description = args[1] if len(args) > 1 else ""
        date_str = args[2] if len(args) > 2 else ""
        location = args[3] if len(args) > 3 else ""

        # Parse date/time
        starts_at = None
        if date_str:
            try:
                # Try parsing various formats
                if len(date_str) > 10:  # YYYY-MM-DD HH:MM format
                    starts_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                else:
                    # Try just date
                    starts_at = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                    # Add default time
                    starts_at = starts_at.replace(hour=20, minute=0)
            except ValueError:
                await ctx.reply(f"❌ Invalid date format. Use YYYY-MM-DD HH:MM")
                return

        # Check cooldown
        if starts_at:
            result = ctx.db.execute(
                f"""
                SELECT COUNT(*)
                FROM group_events
                WHERE group_id = {ctx.group.id}
                  AND created_by = {ctx.user.user_id}
                  AND created_at > NOW() - INTERVAL '{config.event_creation_cooldown} seconds'
                """
            )
            count = result.scalar()

            if count > 0:
                await ctx.reply("❌ You're creating events too fast. Wait a bit.")
                return

        # Create event
        from shared.models import GroupEvent

        event = GroupEvent(
            group_id=ctx.group.id,
            title=title,
            description=description,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=2) if starts_at else None,
            location=location,
            created_by=ctx.user.user_id,
            status="upcoming",
            is_recurring=False,
        )

        ctx.db.add(event)
        ctx.db.commit()

        date_str_fmt = starts_at.strftime("%Y-%m-%d %H:%M") if starts_at else "TBD"

        await ctx.reply(
            f"✅ Event created!\n\n"
            f"📋 Title: {title}\n"
            f"📄 Description: {description or 'No description'}\n"
            f"📅 Date: {date_str_fmt}\n"
            f"📍 Location: {location or 'No location'}\n"
            f"👤 Created by: {ctx.user.mention}\n\n"
            f"💡 Members can RSVP with: /rsvp {event.id}"
        )

    async def cmd_rsvp(self, ctx: NexusContext):
        """RSVP to an event."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if len(args) < 2:
            await ctx.reply("❌ Usage: /rsvp <event_id> <going|maybe|not_going>")
            return

        try:
            event_id = int(args[0])
        except ValueError:
            await ctx.reply("❌ Invalid event ID")
            return

        status = args[1].lower()

        if status not in ["going", "maybe", "not_going"]:
            await ctx.reply("❌ Status must be: going, maybe, or not_going")
            return

        status_map = {
            "going": "going",
            "maybe": "maybe",
            "not_going": "not_going",
        }

        final_status = status_map[status]

        # Add or update RSVP
        from shared.models import EventRSVP

        # Check if already RSVP'd
        result = ctx.db.execute(
            f"""
            SELECT id
            FROM event_rsvps
            WHERE user_id = {ctx.user.user_id}
              AND event_id = {event_id}
            LIMIT 1
            """
        )
        row = result.fetchone()

        if row:
            # Update
            ctx.db.execute(
                f"UPDATE event_rsvps SET status = '{final_status}', rsvp_at = NOW() WHERE id = {row[0]}"
            )
        else:
            # Create
            rsvp = EventRSVP(
                user_id=ctx.user.user_id,
                event_id=event_id,
                status=final_status,
            )
            ctx.db.add(rsvp)

        ctx.db.commit()

        status_emoji = {"going": "✅", "maybe": "❓", "not_going": "❌"}
        await ctx.reply(f"{status_emoji[status]} You're {final_status} for event #{event_id}")

    async def cmd_myevents(self, ctx: NexusContext):
        """View your event RSVPs."""
        from shared.models import EventRSVP

        result = ctx.db.execute(
            f"""
            SELECT r.status, r.rsvp_at, e.id, e.title, e.starts_at, e.location
            FROM event_rsvps r
            JOIN group_events e ON r.event_id = e.id
            WHERE r.user_id = {ctx.user.user_id}
            ORDER BY r.rsvp_at DESC
            LIMIT 10
            """
        )

        rsvps = result.fetchall()

        if not rsvps:
            await ctx.reply(
                "❌ You haven't RSVP'd to any events yet.\n\n"
                "Use /events to see upcoming events and RSVP with /rsvp"
            )
            return

        text = "📅 Your Event RSVPs\n\n"

        for row in rsvps:
            status = row[0]
            rsvp_at = row[1]
            event_id = row[2]
            title = row[3]
            starts_at = row[4]
            location = row[5]

            status_emoji = {"going": "✅", "maybe": "❓", "not_going": "❌"}
            date_str = starts_at.strftime("%Y-%m-%d %H:%M") if starts_at else "TBD"

            text += f"{status_emoji[status]} {title}\n"
            text += f"   📅 {date_str}\n"
            text += f"   📍 {location or 'No location'}\n"
            text += f"   ID: {event_id}\n\n"

        await ctx.reply(text)

    async def cmd_topevents(self, ctx: NexusContext):
        """View top events by RSVP."""
        from shared.models import EventRSVP

        result = ctx.db.execute(
            f"""
            SELECT e.id, e.title, COUNT(*) as rsvp_count
            FROM event_rsvps r
            JOIN group_events e ON r.event_id = e.id
            WHERE e.group_id = {ctx.group.id}
              AND r.status = 'going'
            GROUP BY e.id, e.title
            ORDER BY rsvp_count DESC
            LIMIT 10
            """
        )

        events = result.fetchall()

        if not events:
            await ctx.reply("❌ No event RSVPs yet")
            return

        text = "🏆 Top Events by RSVP\n\n"

        for i, row in enumerate(events, 1):
            event_id = row[0]
            title = row[1]
            rsvp_count = row[2]

            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."

            text += f"{medal} {title}\n"
            text += f"   ✅ {rsvp_count} going\n"
            text += f"   ID: {event_id}\n\n"

        await ctx.reply(text)

    async def cmd_celebrate(self, ctx: NexusContext):
        """Celebrate a member milestone."""
        if not ctx.replied_to or not ctx.replied_to.from_user:
            await ctx.reply("❌ Reply to a member to celebrate them!")
            return

        target = ctx.replied_to.from_user
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /celebrate <reason>\n\nExample: /celebrate reached 1000 messages!")
            return

        reason = " ".join(args)

        # Send celebration message
        celebration_messages = [
            f"🎉 Let's celebrate {target.mention}!\n\n{reason}",
            f"🏆 Congratulations to {target.mention}!\n\n{reason}",
            f"👏 Big shoutout to {target.mention}!\n\n{reason}",
            f"⭐ {target.mention} deserves recognition!\n\n{reason}",
        ]

        message = random.choice(celebration_messages)

        await ctx.reply(message)

        # Create mod_action for tracking
        from shared.models import ModAction

        action = ModAction(
            group_id=ctx.group.id,
            target_user_id=target.id,
            actor_id=ctx.user.id,
            action_type="celebrate",
            reason=reason,
        )
        ctx.db.add(action)
        ctx.db.commit()

    async def cmd_birthday(self, ctx: NexusContext):
        """Set/view birthday."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            # View your birthday
            from shared.models import MemberProfile

            result = ctx.db.execute(
                f"SELECT birthday FROM member_profiles WHERE user_id = {ctx.user.user_id} AND group_id = {ctx.group.id} LIMIT 1"
            )
            row = result.fetchone()

            if row and row[0]:
                age = (datetime.utcnow() - row[0]).days // 365
                await ctx.reply(
                    f"🎂 Your Birthday: {row[0].strftime('%B %d, %Y')}\n"
                    f"🎈 Age: {age} years old"
                )
            else:
                await ctx.reply(
                    "🎂 You haven't set your birthday yet!\n\n"
                    "Set it with: /birthday YYYY-MM-DD"
                )
        else:
            # Set birthday
            try:
                birthday = datetime.strptime(args[0], "%Y-%m-%d").date()
            except ValueError:
                await ctx.reply("❌ Invalid date format. Use YYYY-MM-DD")
                return

            # Check if birthday is in future
            if birthday > datetime.utcnow().date():
                await ctx.reply("❌ Birthday cannot be in the future!")
                return

            # Store birthday
            from shared.models import MemberProfile

            result = ctx.db.execute(
                f"SELECT id FROM member_profiles WHERE user_id = {ctx.user.user_id} AND group_id = {ctx.group.id} LIMIT 1"
            )
            row = result.fetchone()

            if row:
                ctx.db.execute(
                    f"UPDATE member_profiles SET birthday = '{birthday}' WHERE id = {row[0]}"
                )
            else:
                # Create profile
                profile = MemberProfile(
                    user_id=ctx.user.user_id,
                    group_id=ctx.group.id,
                    birthday=birthday,
                    is_public=True,
                )
                ctx.db.add(profile)

            ctx.db.commit()

            await ctx.reply(f"✅ Birthday set to {birthday.strftime('%B %d, %Y')}")

    async def cmd_birthdays(self, ctx: NexusContext):
        """View upcoming birthdays."""
        from shared.models import MemberProfile

        result = ctx.db.execute(
            f"""
            SELECT mp.birthday, u.username, u.first_name, u.last_name, u.telegram_id
            FROM member_profiles mp
            JOIN users u ON mp.user_id = u.id
            WHERE mp.group_id = {ctx.group.id}
              AND mp.birthday IS NOT NULL
              AND DATE_PART('doy', mp.birthday) >= DATE_PART('doy', CURRENT_DATE)
              AND DATE_PART('doy', mp.birthday) < DATE_PART('doy', CURRENT_DATE) + 30
            ORDER BY DATE_PART('doy', mp.birthday)
            LIMIT 10
            """
        )

        # For now, show placeholder since we don't have full member_profiles
        text = "🎂 Upcoming Birthdays\n\n"
        text += "ℹ️ This feature tracks member birthdays.\n\n"
        text += "Set your birthday with: /birthday YYYY-MM-DD\n\n"
        text += "Members with upcoming birthdays will get special wishes! 🎉"

        await ctx.reply(text)

    async def cmd_bio(self, ctx: NexusContext):
        """Set your bio."""
        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not args:
            # View your bio
            from shared.models import MemberProfile

            result = ctx.db.execute(
                f"SELECT bio, tags FROM member_profiles WHERE user_id = {ctx.user.user_id} AND group_id = {ctx.group.id} LIMIT 1"
            )
            row = result.fetchone()

            if row and row[0]:
                text = f"📝 {ctx.user.mention}'s Profile\n\n"
                text += f"Bio: {row[0]}\n"
                if row[1]:
                    text += f"Interests: {row[1]}\n"
                await ctx.reply(text)
            else:
                await ctx.reply(
                    "📝 You haven't set your bio yet!\n\n"
                    "Set it with: /bio <your bio>\n\n"
                    "Example: /bio I love gaming, coding, and coffee! ☕🎮💻"
                )
        else:
            # Set bio
            bio = " ".join(args)

            if len(bio) > 280:
                await ctx.reply("❌ Bio too long (max 280 characters)")
                return

            # Store bio
            from shared.models import MemberProfile

            result = ctx.db.execute(
                f"SELECT id FROM member_profiles WHERE user_id = {ctx.user.user_id} AND group_id = {ctx.group.id} LIMIT 1"
            )
            row = result.fetchone()

            if row:
                ctx.db.execute(
                    f"UPDATE member_profiles SET bio = {repr(bio)} WHERE id = {row[0]}"
                )
            else:
                # Create profile
                profile = MemberProfile(
                    user_id=ctx.user.user_id,
                    group_id=ctx.group.id,
                    bio=bio,
                    is_public=True,
                )
                ctx.db.add(profile)

            ctx.db.commit()

            await ctx.reply(f"✅ Bio updated: {bio}")

    async def cmd_membercount(self, ctx: NexusContext):
        """Show member count milestone."""
        from shared.models import Group

        result = ctx.db.execute(
            f"SELECT member_count FROM groups WHERE id = {ctx.group.id} LIMIT 1"
        )
        row = result.fetchone()

        if not row:
            return

        member_count = row[0]

        # Milestone messages
        milestones = [
            (10, "🎉 First 10 members!"),
            (50, "🎊 50 members and growing!"),
            (100, "💯 We hit 100 members!"),
            (250, "🚀 250 members strong!"),
            (500, "🏆 500 members!"),
            (1000, "🎉 1000 members milestone!"),
            (5000, "🌟 5000 members!"),
            (10000, "💎 10,000 members!"),
        ]

        text = f"👥 {ctx.group.title}\n"
        text += f"👥 Members: {member_count:,}\n"

        for milestone, message in milestones:
            if member_count >= milestone:
                text += f"\n{message}"

        await ctx.reply(text)
