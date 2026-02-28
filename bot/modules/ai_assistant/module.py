"""AI Assistant module - GPT-4 powered intelligent assistant."""

import re
from typing import Optional, List
from aiogram.types import Message
from pydantic import BaseModel
import httpx

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class AIConfig(BaseModel):
    """Configuration for AI module."""
    enabled: bool = True
    api_key: str = ""
    model: str = "gpt-4o"
    max_tokens: int = 1000
    temperature: float = 0.7


class AIModule(NexusModule):
    """AI-powered assistant with GPT-4."""

    name = "ai_assistant"
    version = "1.0.0"
    author = "Nexus Team"
    description = "GPT-4 powered AI assistant for moderation, insights, and help"
    category = ModuleCategory.AI

    config_schema = AIConfig
    default_config = AIConfig().dict()

    commands = [
        CommandDef(
            name="ai",
            description="Ask AI anything",
            admin_only=False,
            args="<prompt>",
        ),
        CommandDef(
            name="summarize",
            description="Summarize last N messages",
            admin_only=False,
            args="[count]",
        ),
        CommandDef(
            name="translate",
            description="Translate text",
            admin_only=False,
            args="<text> [language]",
        ),
        CommandDef(
            name="factcheck",
            description="Fact-check a claim",
            admin_only=False,
            args="<claim>",
        ),
        CommandDef(
            name="scam",
            description="Check if a link/message is a scam",
            admin_only=False,
            args="<link or message>",
        ),
        CommandDef(
            name="draft",
            description="AI draft an announcement",
            admin_only=True,
            args="<topic>",
        ),
        CommandDef(
            name="recommend",
            description="Get AI recommendations",
            admin_only=False,
            args="<topic>",
        ),
        CommandDef(
            name="sentiment",
            description="Analyze sentiment of message",
            admin_only=False,
            args="<message>",
        ),
        CommandDef(
            name="explain",
            description="Explain a concept",
            admin_only=False,
            args="<concept>",
        ),
        CommandDef(
            name="rewrite",
            description="Rewrite/improve text",
            admin_only=False,
            args="<text>",
        ),
        CommandDef(
            name="analyze",
            description="Analyze user behavior",
            admin_only=True,
            args="[@user]",
        ),
        CommandDef(
            name="moderation",
            description="Get AI moderation suggestions",
            admin_only=True,
        ),
        CommandDef(
            name="report",
            description="Generate AI report",
            admin_only=True,
            args="[daily|weekly]",
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("ai", self.cmd_ai)
        self.register_command("summarize", self.cmd_summarize)
        self.register_command("translate", self.cmd_translate)
        self.register_command("factcheck", self.cmd_factcheck)
        self.register_command("scam", self.cmd_scam)
        self.register_command("draft", self.cmd_draft)
        self.register_command("recommend", self.cmd_recommend)
        self.register_command("sentiment", self.cmd_sentiment)
        self.register_command("explain", self.cmd_explain)
        self.register_command("rewrite", self.cmd_rewrite)
        self.register_command("analyze", self.cmd_analyze)
        self.register_command("moderation", self.cmd_moderation)
        self.register_command("report", self.cmd_report)

    async def _call_openai(self, messages: List[dict], ctx: NexusContext) -> str:
        """Call OpenAI API."""
        config = ctx.group.module_configs.get("ai_assistant", {})
        api_key = config.get("api_key", "")

        if not api_key:
            return "❌ OpenAI API key not configured. Ask admin to set it up."

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": config.get("model", "gpt-4o"),
                        "messages": messages,
                        "max_tokens": config.get("max_tokens", 1000),
                        "temperature": config.get("temperature", 0.7)
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"❌ API Error: {response.status_code}"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def cmd_ai(self, ctx: NexusContext):
        """Ask AI anything."""
        prompt = " ".join(ctx.message.text.split()[1:]) if ctx.message.text else ""

        if not prompt:
            await ctx.reply(
                "❌ Usage: `/ai <prompt>`\n\n"
                "Examples:\n"
                "• `/ai What should we do for our event?`\n"
                "• `/ai Explain quantum physics simply`\n"
                "• `/ai Write a poem about this group`"
            )
            return

        await ctx.reply("🤖 Thinking...", delete_after=2)

        messages = [
            {"role": "system", "content": "You are a helpful AI assistant for a Telegram group. Be concise and friendly."},
            {"role": "user", "content": prompt}
        ]

        response = await self._call_openai(messages, ctx)

        await ctx.reply(
            f"🤖 **AI Response**\n\n"
            f"{response}"
        )

    async def cmd_summarize(self, ctx: NexusContext):
        """Summarize messages."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []
        count = int(args[0]) if args and args[0].isdigit() else 50

        # Get recent messages from database
        if ctx.db:
            from shared.models import Message as Msg
            result = ctx.db.execute(
                f"""
                SELECT m.text, u.username, u.first_name, m.created_at
                FROM messages m
                JOIN users u ON m.user_id = u.id
                WHERE m.group_id = {ctx.group.id}
                ORDER BY m.created_at DESC
                LIMIT {count}
                """
            )

            messages = result.fetchall()
            if not messages:
                await ctx.reply("❌ No messages to summarize")
                return

            # Build messages text
            messages_text = ""
            for msg in reversed(messages):
                user = msg[1] or msg[2]
                text = msg[0] or "[media]"
                messages_text += f"{user}: {text}\n"

            messages_text = messages_text[-4000:]  # Limit length

            await ctx.reply("🤖 Summarizing...")

            messages_openai = [
                {"role": "system", "content": "Summarize these Telegram messages concisely."},
                {"role": "user", "content": messages_text}
            ]

            response = await self._call_openai(messages_openai, ctx)

            await ctx.reply(
                f"📝 **Summary of last {count} messages**\n\n"
                f"{response}"
            )

    async def cmd_translate(self, ctx: NexusContext):
        """Translate text."""
        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []

        if not args:
            await ctx.reply(
                "❌ Usage: `/translate <text> [language]`\n\n"
                "Examples:\n"
                "• `/translate Hello es`\n"
                "• `/translate Bonjour English`"
            )
            return

        text = args[0]
        target_lang = args[1] if len(args) > 1 else "English"

        await ctx.reply("🌍 Translating...")

        messages = [
            {"role": "system", "content": f"You are a translator. Translate to {target_lang}."},
            {"role": "user", "content": text}
        ]

        response = await self._call_openai(messages, ctx)

        await ctx.reply(
            f"🌍 **Translation** ({target_lang})\n\n"
            f"Original: {text}\n\n"
            f"Translation: {response}"
        )

    async def cmd_factcheck(self, ctx: NexusContext):
        """Fact-check a claim."""
        claim = " ".join(ctx.message.text.split()[1:]) if ctx.message.text else ""

        if not claim:
            await ctx.reply(
                "❌ Usage: `/factcheck <claim>`\n\n"
                "Example: `/factcheck The moon is made of cheese`"
            )
            return

        await ctx.reply("🔍 Fact-checking...")

        messages = [
            {"role": "system", "content": "You are a fact-checker. Analyze claims and provide accurate information with sources."},
            {"role": "user", "content": f"Fact-check this claim: {claim}"}
        ]

        response = await self._call_openai(messages, ctx)

        await ctx.reply(
            f"🔍 **Fact Check**\n\n"
            f"❓ Claim: {claim}\n\n"
            f"✅ Analysis:\n{response}"
        )

    async def cmd_scam(self, ctx: NexusContext):
        """Check for scam."""
        content = " ".join(ctx.message.text.split()[1:]) if ctx.message.text else ""

        if not content:
            await ctx.reply(
                "❌ Usage: `/scam <link or message>`\n\n"
                "Example: `/scam https://suspicious-link.com`"
            )
            return

        await ctx.reply("🔎 Analyzing...")

        messages = [
            {"role": "system", "content": "You are a scam detector. Analyze messages and links for phishing, scam, or fraud indicators."},
            {"role": "user", "content": f"Is this a scam? {content}"}
        ]

        response = await self._call_openai(messages, ctx)

        await ctx.reply(
            f"🔎 **Scam Analysis**\n\n"
            f"🔗 Input: {content}\n\n"
            f"🛡️ Analysis:\n{response}"
        )

    async def cmd_draft(self, ctx: NexusContext):
        """Draft an announcement."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        topic = " ".join(ctx.message.text.split()[1:]) if ctx.message.text else ""

        if not topic:
            await ctx.reply(
                "❌ Usage: `/draft <topic>`\n\n"
                "Examples:\n"
                "• `/draft Weekly meeting announcement`\n"
                "• `/draft New member welcome`"
            )
            return

        await ctx.reply("✍️ Drafting announcement...")

        messages = [
            {"role": "system", "content": "You are a professional announcement writer. Write engaging, clear Telegram announcements."},
            {"role": "user", "content": f"Draft an announcement about: {topic}"}
        ]

        response = await self._call_openai(messages, ctx)

        await ctx.reply(
            f"✍️ **Drafted Announcement**\n\n"
            f"{response}\n\n"
            f"💡 You can edit and send this announcement!"
        )

    async def cmd_recommend(self, ctx: NexusContext):
        """Get recommendations."""
        topic = " ".join(ctx.message.text.split()[1:]) if ctx.message.text else ""

        if not topic:
            await ctx.reply(
                "❌ Usage: `/recommend <topic>`\n\n"
                "Examples:\n"
                "• `/recommend games for the group`\n"
                "• `/recommend ways to increase engagement`"
            )
            return

        await ctx.reply("💡 Getting recommendations...")

        messages = [
            {"role": "system", "content": "You are a helpful assistant. Provide practical recommendations."},
            {"role": "user", "content": f"Recommendations for: {topic}"}
        ]

        response = await self._call_openai(messages, ctx)

        await ctx.reply(
            f"💡 **Recommendations**\n\n"
            f"{response}"
        )

    async def cmd_sentiment(self, ctx: NexusContext):
        """Analyze sentiment."""
        text = " ".join(ctx.message.text.split()[1:]) if ctx.message.text else ""

        if not text:
            await ctx.reply(
                "❌ Usage: `/sentiment <message>`\n\n"
                "Example: `/sentiment This is the best group ever!`"
            )
            return

        await ctx.reply("📊 Analyzing sentiment...")

        messages = [
            {"role": "system", "content": "You are a sentiment analyzer. Analyze the emotion and tone of messages."},
            {"role": "user", "content": f"Analyze sentiment: {text}"}
        ]

        response = await self._call_openai(messages, ctx)

        await ctx.reply(
            f"📊 **Sentiment Analysis**\n\n"
            f"💬 Text: {text}\n\n"
            f"🎭 Analysis:\n{response}"
        )

    async def cmd_explain(self, ctx: NexusContext):
        """Explain a concept."""
        concept = " ".join(ctx.message.text.split()[1:]) if ctx.message.text else ""

        if not concept:
            await ctx.reply(
                "❌ Usage: `/explain <concept>`\n\n"
                "Examples:\n"
                "• `/explain blockchain`\n"
                "• `/explain quantum entanglement`"
            )
            return

        await ctx.reply("📚 Explaining...")

        messages = [
            {"role": "system", "content": "You are a teacher. Explain complex concepts simply and clearly."},
            {"role": "user", "content": f"Explain: {concept}"}
        ]

        response = await self._call_openai(messages, ctx)

        await ctx.reply(
            f"📚 **Explanation**\n\n"
            f"{response}"
        )

    async def cmd_rewrite(self, ctx: NexusContext):
        """Rewrite text."""
        text = " ".join(ctx.message.text.split(maxsplit=1)[1:]) if ctx.message.text else ""

        if not text:
            await ctx.reply(
                "❌ Usage: `/rewrite <text>`\n\n"
                "Example: `/rewrite Make this sound more professional...`"
            )
            return

        await ctx.reply("✏️ Rewriting...")

        messages = [
            {"role": "system", "content": "You are a professional editor. Improve clarity, grammar, and style."},
            {"role": "user", "content": f"Rewrite and improve: {text}"}
        ]

        response = await self._call_openai(messages, ctx)

        await ctx.reply(
            f"✏️ **Rewritten Text**\n\n"
            f"{response}"
        )

    async def cmd_analyze(self, ctx: NexusContext):
        """Analyze user behavior."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        # Extract user from reply or mention
        target_id = None
        if ctx.replied_to and ctx.replied_to.from_user:
            target_id = ctx.replied_to.from_user.id

        if not target_id:
            await ctx.reply("❌ Reply to a user's message to analyze their behavior")
            return

        await ctx.reply("📊 Analyzing user behavior...")

        # Get user's recent messages
        if ctx.db:
            from shared.models import Message
            result = ctx.db.execute(
                f"""
                SELECT text, created_at
                FROM messages
                WHERE user_id = (SELECT id FROM users WHERE telegram_id = {target_id})
                AND group_id = {ctx.group.id}
                ORDER BY created_at DESC
                LIMIT 100
                """
            )

            messages = result.fetchall()
            if not messages:
                await ctx.reply("❌ No messages from this user")
                return

            messages_text = ""
            for msg in messages:
                messages_text += f"{msg[0] or '[media]'}\n"

            messages_text = messages_text[-3000:]

            messages = [
                {"role": "system", "content": "You are a behavior analyst. Analyze user patterns for signs of spam, toxicity, or helpfulness."},
                {"role": "user", "content": f"Analyze this user's behavior based on their recent messages:\n{messages_text}"}
            ]

            response = await self._call_openai(messages, ctx)

            await ctx.reply(
                f"📊 **Behavior Analysis**\n\n"
                f"{response}"
            )

    async def cmd_moderation(self, ctx: NexusContext):
        """Get AI moderation suggestions."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        await ctx.reply("🤖 Analyzing recent activity...")

        # Get recent flagged content
        messages = [
            {"role": "system", "content": "You are a moderation assistant. Suggest actions based on community activity."},
            {"role": "user", "content": "Provide moderation recommendations for a busy Telegram group. Focus on: spam prevention, conflict resolution, and community engagement."}
        ]

        response = await self._call_openai(messages, ctx)

        await ctx.reply(
            f"🤖 **AI Moderation Suggestions**\n\n"
            f"{response}"
        )

    async def cmd_report(self, ctx: NexusContext):
        """Generate AI report."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        report_type = args[0].lower() if args else "daily"

        await ctx.reply("📊 Generating report...")

        if report_type == "daily":
            prompt = "Generate a daily group report summary including: message activity, most active users, and any notable events."
        elif report_type == "weekly":
            prompt = "Generate a weekly group report summary including: message activity trends, member growth, top contributors, and community health."
        else:
            prompt = "Generate a group report summary."

        messages = [
            {"role": "system", "content": "You are a community analyst. Generate clear, actionable group reports."},
            {"role": "user", "content": prompt}
        ]

        response = await self._call_openai(messages, ctx)

        await ctx.reply(
            f"📊 **{report_type.title()} Report**\n\n"
            f"{response}"
        )
