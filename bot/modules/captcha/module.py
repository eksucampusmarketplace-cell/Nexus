"""Captcha module - User verification."""

from typing import Optional, List, Dict
from pydantic import BaseModel
import random

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule, EventType


class CaptchaConfig(BaseModel):
    """Configuration for captcha module."""
    captcha_enabled: bool = True
    captcha_type: str = "button"
    timeout_seconds: int = 90
    action_on_fail: str = "kick"
    mute_on_join: bool = True
    custom_text: Optional[str] = None


class CaptchaModule(NexusModule):
    """CAPTCHA verification system."""

    name = "captcha"
    version = "1.0.0"
    author = "Nexus Team"
    description = "User verification with CAPTCHA"
    category = ModuleCategory.ANTISPAM

    config_schema = CaptchaConfig
    default_config = CaptchaConfig().dict()

    commands = [
        CommandDef(
            name="captcha",
            description="Set CAPTCHA type",
            admin_only=True,
            args="<type>",
        ),
        CommandDef(
            name="captchatimeout",
            description="Set CAPTCHA timeout",
            admin_only=True,
            args="<seconds>",
        ),
        CommandDef(
            name="captchaaction",
            description="Set action on CAPTCHA fail",
            admin_only=True,
            args="<action>",
        ),
        CommandDef(
            name="captchamute",
            description="Mute users on join until CAPTCHA",
            admin_only=True,
            args="[on|off]",
        ),
        CommandDef(
            name="captchatext",
            description="Set custom CAPTCHA message",
            admin_only=True,
            args="<text>",
        ),
        CommandDef(
            name="captchareset",
            description="Reset CAPTCHA settings",
            admin_only=True,
        ),
    ]

    listeners = [
        EventType.NEW_MEMBER,
        EventType.CALLBACK,
    ]

    # CAPTCHA types
    CAPTCHA_TYPES = ["button", "math", "quiz", "image", "emoji"]

    def __init__(self):
        super().__init__()
        self._challenges: Dict[int, Dict] = {}

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("captcha", self.cmd_captcha)
        self.register_command("captchatimeout", self.cmd_captchatimeout)
        self.register_command("captchaaction", self.cmd_captchaaction)
        self.register_command("captchamute", self.cmd_captchamute)
        self.register_command("captchatext", self.cmd_captchatext)
        self.register_command("captchareset", self.cmd_captchareset)

        # Clean up old challenges periodically
        pass  # Would use scheduler

    async def on_new_member(self, ctx: NexusContext) -> bool:
        """Handle new member join and show CAPTCHA."""
        if not ctx.message or not ctx.message.new_chat_members:
            return False

        config = ctx.group.module_configs.get("captcha", {})

        if not config.get("captcha_enabled", True):
            return False

        mute_on_join = config.get("mute_on_join", False)

        for member in ctx.message.new_chat_members:
            # Mute if enabled
            if mute_on_join:
                try:
                    await ctx.bot.restrict_chat_member(
                        chat_id=ctx.group.telegram_id,
                        user_id=member.id,
                        permissions={
                            "can_send_messages": False,
                            "can_send_media_messages": False,
                        },
                    )
                except Exception:
                    pass

            # Generate challenge
            challenge = self._generate_challenge(ctx, config)

            # Send CAPTCHA message
            keyboard = self._build_captcha_keyboard(member.id, challenge["correct_answer"])

            custom_text = config.get("custom_text", "")
            if custom_text:
                message_text = self._format_variables(custom_text, member)
            else:
                message_text = f"🔐 {member.first_name}, please verify you're human!"

            await ctx.bot.send_message(
                chat_id=ctx.group.telegram_id,
                text=message_text,
                reply_markup=keyboard,
            )

            # Store challenge
            self._challenges[member.id] = {
                "correct_answer": challenge["correct_answer"],
                "created_at": ctx.group.member_count,  # Use as timestamp proxy
                "timeout": config.get("timeout_seconds", 90),
            }

        return True

    async def on_callback_query(self, ctx: NexusContext) -> bool:
        """Handle CAPTCHA button click."""
        if not ctx.callback_query:
            return False

        try:
            # Extract user ID from callback data
            callback_data = ctx.callback_query.data
            if not callback_data.startswith("captcha_"):
                return False

            parts = callback_data.split("_")
            if len(parts) != 3:
                return False

            user_id = int(parts[1])
            answer = parts[2]

            # Check if user has pending challenge
            if user_id not in self._challenges:
                return False

            challenge = self._challenges[user_id]
            correct_answer = challenge["correct_answer"]

            if answer == correct_answer:
                # Correct! Unmute and delete CAPTCHA message
                await self._handle_success(ctx, user_id, ctx.callback_query.message.message_id)
                del self._challenges[user_id]

                await ctx.callback_query.answer("✅ Verification successful!", show_alert=True)
            else:
                # Wrong! Show alert
                await ctx.callback_query.answer("❌ Wrong answer! Try again.", show_alert=True)

        except Exception:
            return False

        return True

    def _generate_challenge(self, ctx: NexusContext, config: dict) -> Dict:
        """Generate a CAPTCHA challenge."""
        captcha_type = config.get("captcha_type", "button")

        if captcha_type == "button":
            answer = "verify"
            question_text = "Click the button below to verify"
            challenge_text = "Verify ✅"

        elif captcha_type == "math":
            num1 = random.randint(1, 10)
            num2 = random.randint(1, 10)
            operator = random.choice(["+", "-", "*"])
            if operator == "+":
                answer = num1 + num2
            elif operator == "-":
                answer = num1 - num2
            else:
                answer = num1 * num2
            question_text = f"Solve: {num1} {operator} {num2} = ?"
            challenge_text = f"{answer}"

        elif captcha_type == "quiz":
            questions = [
                {"q": "What is 2 + 2?", "a": "4"},
                {"q": "What is 3 * 3?", "a": "9"},
                {"q": "What is 10 / 2?", "a": "5"},
                {"q": "What is the color of the sky?", "a": "blue"},
                {"q": "What is the capital of France?", "a": "Paris"},
            ]
            q = random.choice(questions)
            answer = q["a"]
            question_text = q["q"]
            challenge_text = answer

        elif captcha_type == "image":
            # Generate simple numeric challenge (shown as text in message)
            answer = random.randint(1000, 9999)
            question_text = f"Type the number: {answer}"
            challenge_text = str(answer)

        elif captcha_type == "emoji":
            emojis = ["👍", "❤️", "😂", "👎", "😍", "😘", "🎉", "🔥", "💯"]
            correct_emoji = random.choice(emojis)
            question_text = f"Click the {correct_emoji} emoji below"
            challenge_text = correct_emoji

        else:
            # Default to button
            answer = "verify"
            question_text = "Click the button below to verify"
            challenge_text = "Verify ✅"

        return {
            "correct_answer": challenge_text,
            "question": question_text,
        }

    def _build_captcha_keyboard(self, user_id: int, answer: str) -> InlineKeyboardMarkup:
        """Build CAPTCHA verification keyboard."""
        if answer in ["verify", "Verify ✅"]:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Verify ✅", callback_data=f"captcha_{user_id}_verify")]
                ]
            )
        elif answer in ["👍", "❤️", "😂", "👎", "😍", "😘", "🎉", "🔥", "💯"]:
            buttons = []
            row = []
            for i, emoji in enumerate(["👍", "❤️", "😂", "👎", "😍", "😘", "🎉", "🔥", "💯"]):
                row.append(InlineKeyboardButton(text=emoji, callback_data=f"captcha_{user_id}_{emoji}"))
                if len(row) == 5:
                    buttons.append(row)
                    row = []
            if row:
                buttons.append(row)
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        else:
            # Numeric answer - multiple choice buttons
            buttons = []
            if len(answer) <= 4:
                for digit in answer:
                    buttons.append(InlineKeyboardButton(text=digit, callback_data=f"captcha_{user_id}_{digit}"))
                keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
            else:
                # For larger numbers, just ask to type
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="I'm ready", callback_data=f"captcha_{user_id}_ready")]
                    ]
                )

        return keyboard

    async def _handle_success(self, ctx: NexusContext, user_id: int, message_id: int):
        """Handle successful CAPTCHA verification."""
        # Unmute user
        try:
            await ctx.bot.restrict_chat_member(
                chat_id=ctx.group.telegram_id,
                user_id=user_id,
                permissions={
                    "can_send_messages": True,
                    "can_send_media_messages": True,
                    "can_send_polls": True,
                    "can_send_other_messages": True,
                    "can_add_web_page_previews": True,
                },
            )
        except Exception:
            pass

        # Delete CAPTCHA message
        try:
            await ctx.bot.delete_message(
                chat_id=ctx.group.telegram_id,
                message_id=message_id,
            )
        except Exception:
            pass

    async def _handle_failure(self, ctx: NexusContext, user_id: int):
        """Handle CAPTCHA timeout/failure."""
        config = ctx.group.module_configs.get("captcha", {})
        action = config.get("action_on_fail", "kick")

        if action == "kick":
            try:
                await ctx.bot.ban_chat_member(
                    chat_id=ctx.group.telegram_id,
                    user_id=user_id,
                    revoke_messages=True,
                )
            except Exception:
                pass

        elif action == "ban":
            try:
                await ctx.bot.ban_chat_member(
                    chat_id=ctx.group.telegram_id,
                    user_id=user_id,
                revoke_messages=True,
                )
            except Exception:
                pass

        elif action == "mute":
            try:
                await ctx.bot.restrict_chat_member(
                    chat_id=ctx.group.telegram_id,
                    user_id=user_id,
                    permissions={
                        "can_send_messages": False,
                        "can_send_media_messages": False,
                    },
                )
            except Exception:
                pass

    def _format_variables(self, text: str, member) -> str:
        """Format variables in CAPTCHA message."""
        return text.replace("{first}", member.first_name or "Friend")

    async def cmd_captcha(self, ctx: NexusContext):
        """Set CAPTCHA type."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            config = ctx.group.module_configs.get("captcha", {})
            current_type = config.get("captcha_type", "button")
            await ctx.reply(f"🔐 Current CAPTCHA type: {current_type}")
            return

        captcha_type = args[0].lower()

        if captcha_type not in self.CAPTCHA_TYPES:
            await ctx.reply(f"❌ Invalid type. Available: {', '.join(self.CAPTCHA_TYPES)}")
            return

        # Update config
        config = ctx.group.module_configs.get("captcha", {})
        config["captcha_type"] = captcha_type
        config["captcha_enabled"] = True

        await ctx.reply(f"✅ CAPTCHA type set to: {captcha_type}")

    async def cmd_captchatimeout(self, ctx: NexusContext):
        """Set CAPTCHA timeout."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args or not args[0].isdigit():
            await ctx.reply("❌ Usage: /captchatimeout <seconds>")
            return

        timeout = int(args[0])
        if timeout < 10 or timeout > 300:
            await ctx.reply("❌ Timeout must be between 10 and 300 seconds")
            return

        config = ctx.group.module_configs.get("captcha", {})
        config["timeout_seconds"] = timeout

        await ctx.reply(f"✅ CAPTCHA timeout set to: {timeout} seconds")

    async def cmd_captchaaction(self, ctx: NexusContext):
        """Set action on CAPTCHA fail."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            config = ctx.group.module_configs.get("captcha", {})
            current_action = config.get("action_on_fail", "kick")
            await ctx.reply(f"⚠️ Current action: {current_action}")
            await ctx.reply("Available: kick, ban, mute")
            return

        action = args[0].lower()

        if action not in ["kick", "ban", "mute"]:
            await ctx.reply("❌ Invalid action. Use: kick, ban, mute")
            return

        config = ctx.group.module_configs.get("captcha", {})
        config["action_on_fail"] = action

        await ctx.reply(f"✅ CAPTCHA action set to: {action}")

    async def cmd_captchamute(self, ctx: NexusContext):
        """Mute users on join until CAPTCHA."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            config = ctx.group.module_configs.get("captcha", {})
            current = config.get("mute_on_join", False)
            await ctx.reply(f"🔇 Mute on join: {'Yes' if current else 'No'}")
            return

        if args[0].lower() in ["on", "yes", "1"]:
            config = ctx.group.module_configs.get("captcha", {})
            config["mute_on_join"] = True
            await ctx.reply("✅ Mute on join: ON")
        elif args[0].lower() in ["off", "no", "0"]:
            config = ctx.group.module_configs.get("captcha", {})
            config["mute_on_join"] = False
            await ctx.reply("✅ Mute on join: OFF")
        else:
            await ctx.reply("❌ Usage: /captchamute [on|off]")

    async def cmd_captchatext(self, ctx: NexusContext):
        """Set custom CAPTCHA message."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []
        if not args:
            config = ctx.group.module_configs.get("captcha", {})
            custom_text = config.get("custom_text", "")
            if custom_text:
                await ctx.reply(f"📝 Custom text: {custom_text}")
            else:
                await ctx.reply("📝 No custom text set (using default)")
            return

        text = " ".join(args)

        config = ctx.group.module_configs.get("captcha", {})
        config["custom_text"] = text

        await ctx.reply(f"✅ Custom CAPTCHA text set")

    async def cmd_captchareset(self, ctx: NexusContext):
        """Reset CAPTCHA settings."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        config = ctx.group.module_configs.get("captcha", {})
        config["captcha_type"] = "button"
        config["timeout_seconds"] = 90
        config["action_on_fail"] = "kick"
        config["mute_on_join"] = True
        config["custom_text"] = None
        config["captcha_enabled"] = True

        await ctx.reply("✅ CAPTCHA settings reset to default")
