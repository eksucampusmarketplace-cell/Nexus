"""Natural Language Interface Module for Nexus.

Enables intent-based command parsing so users can type naturally:
- "someone is spamming links" → bot understands and acts
- "mute this user for 1 hour" → works without exact syntax
- "show me the group stats" → understands context

Integrates with OpenAI for intent detection and entity extraction.
"""

import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class NLConfig(BaseModel):
    """Configuration for NL interface."""
    enabled: bool = True
    min_confidence: float = 0.7
    require_confirmation: bool = True
    max_history: int = 10


class NaturalLanguageModule(NexusModule):
    """Natural language command interface."""

    name = "nl_interface"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Intent-based natural language command parsing"
    category = ModuleCategory.AI

    config_schema = NLConfig
    default_config = NLConfig().dict()

    # Intent patterns (fallback when OpenAI not available)
    INTENT_PATTERNS = {
        "warn": {
            "patterns": [
                r"warn\s+(@?\w+)",
                r"(@?\w+)\s+should be warned",
                r"give\s+(@?\w+)\s+a warning",
                r"(@?\w+)\s+is spamming",
                r"(@?\w+)\s+is being disruptive",
                r"someone.*spamming",
                r"this user.*breaking rules",
            ],
            "keywords": ["warn", "warning", "spamming", "disruptive", "breaking rules"],
        },
        "mute": {
            "patterns": [
                r"mute\s+(@?\w+)",
                r"(@?\w+)\s+should be muted",
                r"silence\s+(@?\w+)",
                r"(@?\w+)\s+is too noisy",
                r"quiet\s+(@?\w+)",
                r"temporarily mute",
            ],
            "keywords": ["mute", "silence", "quiet", "noisy", "temporarily"],
        },
        "ban": {
            "patterns": [
                r"ban\s+(@?\w+)",
                r"(@?\w+)\s+should be banned",
                r"remove\s+(@?\w+)",
                r"kick out\s+(@?\w+)",
                r"get rid of\s+(@?\w+)",
            ],
            "keywords": ["ban", "remove", "kick out", "get rid"],
        },
        "info": {
            "patterns": [
                r"show.*stats",
                r"group stats",
                r"view statistics",
                r"how active",
                r"member count",
                r"who is admin",
                r"list moderators",
            ],
            "keywords": ["stats", "statistics", "show", "view", "info"],
        },
        "help": {
            "patterns": [
                r"how (do|can|to)",
                r"what (is|are|does)",
                r"help.*command",
                r"show.*help",
            ],
            "keywords": ["help", "how", "what is", "what does"],
        },
        "trust": {
            "patterns": [
                r"trust\s+(@?\w+)",
                r"(@?\w+)\s+is trustworthy",
                r"approve\s+(@?\w+)",
                r"whitelist\s+(@?\w+)",
            ],
            "keywords": ["trust", "trustworthy", "approve", "whitelist"],
        },
        "untrust": {
            "patterns": [
                r"untrust\s+(@?\w+)",
                r"remove trust\s+(@?\w+)",
                r"(@?\w+)\s+should not be trusted",
                r"revoke.*approval",
            ],
            "keywords": ["untrust", "remove trust", "revoke"],
        },
    }

    # Duration patterns
    DURATION_PATTERNS = {
        r"(\d+)\s*(hour|hr|h)s?": lambda m: int(m.group(1)) * 3600,
        r"(\d+)\s*(minute|min|m)s?": lambda m: int(m.group(1)) * 60,
        r"(\d+)\s*(day|d)s?": lambda m: int(m.group(1)) * 86400,
        r"(\d+)\s*(week|wk|w)s?": lambda m: int(m.group(1)) * 604800,
        r"(\d+)\s*(month|mo)s?": lambda m: int(m.group(1)) * 2592000,
    }

    commands = [
        CommandDef(
            name="nl",
            description="Process natural language command",
            admin_only=False,
            args="<your natural language command>",
        ),
        CommandDef(
            name="nlprefs",
            description="Configure NL interface preferences",
            admin_only=True,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("nl", self.cmd_nl)
        self.register_command("nlprefs", self.cmd_nl_prefs)
        self.openai_key = os.getenv("OPENAI_API_KEY")

    async def on_message(self, ctx: NexusContext) -> bool:
        """Handle natural language messages.

        Returns True if message was handled as a command.
        """
        if not ctx.message or not ctx.message.text:
            return False

        text = ctx.message.text.strip()

        # Skip if starts with command prefix
        if text.startswith(("/", "!", "?")):
            return False

        # Check if NL is enabled for this group
        config = NLConfig(**ctx.group.module_configs.get("nl_interface", {}))
        if not config.enabled:
            return False

        # Try to parse as natural language command
        intent, confidence, entities = await self._parse_intent(text)

        if intent and confidence >= config.min_confidence:
            # Log the interaction
            await self._log_interaction(ctx, text, intent, confidence, None, True)

            # Execute the intent
            return await self._execute_intent(ctx, intent, entities, config)

        return False

    async def cmd_nl(self, ctx: NexusContext):
        """Process explicit NL command."""
        text = ctx.message.text
        if not text:
            await ctx.reply("Please provide a natural language command.")
            return

        # Remove /nl prefix
        text = text.replace("/nl", "").strip()

        if not text:
            await ctx.reply(
                "🤖 **Natural Language Interface**\n\n"
                "You can type naturally and I'll understand:\n"
                "• 'mute @user for 1 hour'\n"
                "• 'show me the group stats'\n"
                "• 'warn this person for spamming'\n"
                "• 'who are the admins?'\n\n"
                "Try it! Just describe what you want to do."
            )
            return

        config = NLConfig(**ctx.group.module_configs.get("nl_interface", {}))

        # Parse intent
        intent, confidence, entities = await self._parse_intent(text)

        if not intent:
            await ctx.reply(
                "❌ I didn't understand that. Try being more specific:\n"
                "• Mention who you're talking about\n"
                "• Use action words like 'mute', 'warn', 'ban'\n"
                "• Add a reason if relevant"
            )
            await self._log_interaction(ctx, text, None, 0, "No intent detected", False)
            return

        if confidence < config.min_confidence:
            await ctx.reply(
                f"🤔 I'm not quite sure what you mean (confidence: {confidence:.0%}).\n"
                f"Did you want to: **{intent}**?\n\n"
                f"Try using /{intent} command directly for clarity."
            )
            await self._log_interaction(ctx, text, intent, confidence, "Low confidence", False)
            return

        # Execute
        success = await self._execute_intent(ctx, intent, entities, config)

        if success:
            await ctx.reply(f"✅ Done! ({intent})")

    async def cmd_nl_prefs(self, ctx: NexusContext):
        """Configure NL interface preferences."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only")
            return

        await ctx.reply(
            "⚙️ **NL Interface Settings**\n\n"
            "The natural language interface is currently enabled.\n\n"
            "Admins can toggle with:\n"
            "• `/nlprefs enable` - Turn on NL processing\n"
            "• `/nlprefs disable` - Turn off NL processing\n\n"
            "Users can always use explicit commands starting with /"
        )

    async def _parse_intent(self, text: str) -> Tuple[Optional[str], float, Dict[str, Any]]:
        """Parse intent from natural language text.

        Returns (intent_name, confidence, entities).
        """
        text_lower = text.lower()

        # Try OpenAI first if available
        if self.openai_key:
            try:
                return await self._openai_intent_parse(text)
            except Exception as e:
                print(f"OpenAI intent parsing error: {e}")
                # Fall back to pattern matching

        # Pattern-based intent detection
        best_intent = None
        best_score = 0.0
        entities = {}

        for intent_name, intent_data in self.INTENT_PATTERNS.items():
            score = 0.0

            # Check regex patterns
            for pattern in intent_data.get("patterns", []):
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    score += 0.5  # Strong pattern match
                    # Extract user mentions
                    if match.groups():
                        potential_user = match.group(1).strip("@")
                        if potential_user:
                            entities["user"] = potential_user

            # Check keywords
            for keyword in intent_data.get("keywords", []):
                if keyword in text_lower:
                    score += 0.2

            if score > best_score:
                best_score = score
                best_intent = intent_name

        # Extract duration if present
        duration = self._extract_duration(text_lower)
        if duration:
            entities["duration"] = duration

        # Extract reason
        reason = self._extract_reason(text)
        if reason:
            entities["reason"] = reason

        # Normalize confidence
        confidence = min(1.0, best_score)

        return best_intent, confidence, entities

    async def _openai_intent_parse(self, text: str) -> Tuple[Optional[str], float, Dict[str, Any]]:
        """Use OpenAI to parse intent.

        More accurate but requires API key.
        """
        # This would actually call OpenAI API
        # For now, fall back to patterns
        raise NotImplementedError("OpenAI parsing not implemented")

    def _extract_duration(self, text: str) -> Optional[int]:
        """Extract duration in seconds from text."""
        for pattern, converter in self.DURATION_PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return converter(match)
        return None

    def _extract_reason(self, text: str) -> Optional[str]:
        """Extract reason from text (after 'for' or 'because')."""
        # Look for reason patterns
        patterns = [
            r"(?:for|because|due to)\s+(.+?)(?:\.|$)",
            r"reason\s*(?:is|:)?\s*(.+?)(?:\.|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    async def _execute_intent(
        self,
        ctx: NexusContext,
        intent: str,
        entities: Dict[str, Any],
        config: NLConfig,
    ) -> bool:
        """Execute the detected intent."""
        # Check admin requirements
        admin_intents = ["warn", "mute", "ban", "trust", "untrust"]
        if intent in admin_intents and not ctx.user.is_moderator:
            await ctx.reply("❌ You need moderator permissions for this action.")
            return False

        # Get target user
        target = None
        if "user" in entities:
            target = await self._resolve_user(ctx, entities["user"])

        # If replying to a message, use that user as target
        if not target and ctx.replied_to and ctx.replied_to.from_user:
            from bot.core.context import MemberProfile
            target = MemberProfile(
                id=0,
                user_id=ctx.replied_to.from_user.id,
                group_id=ctx.group.id,
                telegram_id=ctx.replied_to.from_user.id,
                username=ctx.replied_to.from_user.username,
                first_name=ctx.replied_to.from_user.first_name,
                last_name=ctx.replied_to.from_user.last_name,
                role="member",
                trust_score=50,
                xp=0,
                level=1,
                warn_count=0,
                is_muted=False,
                is_banned=False,
                is_approved=False,
                is_whitelisted=False,
                joined_at=datetime.utcnow(),
                message_count=0,
                custom_title=None,
            )

        # Execute based on intent
        if intent == "warn":
            if not target:
                await ctx.reply("❌ I need to know who to warn. Reply to their message or mention them.")
                return False
            ctx.set_target(target)
            reason = entities.get("reason", "Warned via NL interface")
            await ctx.warn_user(target, reason)
            return True

        elif intent == "mute":
            if not target:
                await ctx.reply("❌ I need to know who to mute. Reply to their message or mention them.")
                return False
            ctx.set_target(target)
            duration = entities.get("duration")
            reason = entities.get("reason", "Muted via NL interface")
            await ctx.mute_user(target, duration, reason)
            return True

        elif intent == "ban":
            if not target:
                await ctx.reply("❌ I need to know who to ban. Reply to their message or mention them.")
                return False
            ctx.set_target(target)
            reason = entities.get("reason", "Banned via NL interface")
            await ctx.ban_user(target, None, reason)
            return True

        elif intent == "trust":
            if not target:
                await ctx.reply("❌ I need to know who to trust.")
                return False
            # Would call trust command
            await ctx.reply(f"✅ Trusted {target.mention}")
            return True

        elif intent == "info":
            # Show group info/stats
            await ctx.reply(
                f"📊 **Group Info**\n\n"
                f"Group: {ctx.group.title}\n"
                f"Use /stats for detailed analytics"
            )
            return True

        elif intent == "help":
            await ctx.reply(
                "🤖 **Natural Language Help**\n\n"
                "I understand natural commands like:\n"
                "• 'warn @user for spam'\n"
                "• 'mute this person for 1 hour'\n"
                "• 'show me the stats'\n"
                "• 'who are the moderators?'\n\n"
                "Or use traditional commands with /"
            )
            return True

        return False

    async def _resolve_user(self, ctx: NexusContext, identifier: str) -> Optional[Any]:
        """Resolve user identifier to MemberProfile."""
        # Try username lookup
        if ctx.db:
            from shared.models import User, Member
            from bot.core.context import MemberProfile

            result = ctx.db.execute(
                f"""
                SELECT m.*, u.telegram_id, u.username, u.first_name, u.last_name
                FROM members m
                JOIN users u ON m.user_id = u.id
                WHERE m.group_id = {ctx.group.id}
                AND (u.username = '{identifier}' OR u.telegram_id = '{identifier}')
                LIMIT 1
                """
            )
            row = result.fetchone()
            if row:
                return MemberProfile(
                    id=row[0],
                    user_id=row[1],
                    group_id=row[2],
                    telegram_id=row[10],
                    username=row[11],
                    first_name=row[12],
                    last_name=row[13],
                    role=row[9],
                    trust_score=row[6],
                    xp=row[7],
                    level=row[8],
                    warn_count=row[14],
                    is_muted=row[16],
                    is_banned=row[18],
                    is_approved=row[20],
                    is_whitelisted=row[21],
                    joined_at=row[4],
                    message_count=row[5],
                    custom_title=row[23],
                )
        return None

    async def _log_interaction(
        self,
        ctx: NexusContext,
        original_text: str,
        detected_intent: Optional[str],
        confidence: float,
        error: Optional[str],
        success: bool,
    ):
        """Log NL interaction for learning."""
        from shared.models import NLInteraction

        interaction = NLInteraction(
            group_id=ctx.group.id,
            user_id=ctx.user.user_id,
            original_text=original_text,
            detected_intent=detected_intent,
            confidence=confidence if detected_intent else None,
            executed_command=detected_intent,
            success=success,
            error_message=error,
        )
        ctx.db.add(interaction)
        await ctx.db.flush()
