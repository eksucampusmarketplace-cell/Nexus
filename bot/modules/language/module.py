"""Language management module - Configure bot language per group."""

from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule
from bot.services.i18n_service import SUPPORTED_LANGUAGES, get_i18n_service
from shared.models import Group


class LanguageConfig(BaseModel):
    """Configuration for language module."""
    default_language: str = "en"
    allow_user_override: bool = True


class LanguageModule(NexusModule):
    """Language management module for multi-language support."""

    name = "language"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Manage bot language settings with support for English, French, Italian, Spanish, and Hindi"
    category = ModuleCategory.UTILITY

    config_schema = LanguageConfig
    default_config = LanguageConfig().dict()

    commands = [
        CommandDef(
            name="language",
            description="Set or view the bot language for this group",
            admin_only=True,
            aliases=["lang", "setlang"],
            args="[language_code]",
        ),
        CommandDef(
            name="languages",
            description="List all supported languages",
            admin_only=False,
            aliases=["langs"],
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("language", self.cmd_language)
        self.register_command("lang", self.cmd_language)
        self.register_command("setlang", self.cmd_language)
        self.register_command("languages", self.cmd_languages)
        self.register_command("langs", self.cmd_languages)

    async def cmd_languages(self, ctx: NexusContext):
        """List all supported languages."""
        i18n = get_i18n_service()
        languages = i18n.get_supported_languages()
        
        lines = ["🌐 <b>Supported Languages</b>\n"]
        for lang in languages:
            lines.append(f"{lang['flag']} <b>{lang['native']}</b> ({lang['name']})")
            lines.append(f"   └ Code: <code>{lang['code']}</code>")
        
        lines.append("\n💡 Use <code>/language [code]</code> to set the language.")
        
        await ctx.reply("\n".join(lines), parse_mode="HTML")

    async def cmd_language(self, ctx: NexusContext):
        """Set or view the current language."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("errors.not_admin"))
            return
        
        args = (ctx.message.text or "").split()[1:] if ctx.message.text else []
        i18n = get_i18n_service()
        
        # If no args, show current language and interactive selection
        if not args:
            await self._show_language_menu(ctx, i18n)
            return
        
        # Parse language code
        lang_code = args[0].lower().strip()
        
        # Validate and set language
        success, message = await self._set_group_language(ctx.db, ctx.group.telegram_id, lang_code)
        
        if success:
            # Update context's i18n client
            ctx.i18n.set_language(lang_code)
            
            # Get language info for message
            normalized = i18n._normalize_language_code(lang_code)
            if normalized in SUPPORTED_LANGUAGES:
                lang_info = SUPPORTED_LANGUAGES[normalized]
                await ctx.reply(
                    f"✅ {lang_info['flag']} Language set to <b>{lang_info['native']}</b>",
                    parse_mode="HTML"
                )
            else:
                await ctx.reply(f"✅ {message}")
        else:
            await ctx.reply(f"❌ {message}")

    async def _show_language_menu(self, ctx: NexusContext, i18n):
        """Show interactive language selection menu."""
        languages = i18n.get_supported_languages()
        current_lang = ctx.group.language if ctx.group else "en"
        
        # Build keyboard
        buttons = []
        for lang in languages:
            marker = " ✓" if lang["code"] == current_lang else ""
            buttons.append([{
                "text": f"{lang['flag']} {lang['native']}{marker}",
                "callback_data": f"lang_set:{lang['code']}"
            }])
        
        text = (
            f"🌐 <b>Language Settings</b>\n\n"
            f"Current: {SUPPORTED_LANGUAGES.get(current_lang, {}).get('flag', '🌐')} "
            f"{SUPPORTED_LANGUAGES.get(current_lang, {}).get('native', current_lang)}\n\n"
            f"Select a language below:"
        )
        
        await ctx.reply(text, buttons=buttons, parse_mode="HTML")

    async def _set_group_language(
        self,
        db: Optional[AsyncSession],
        group_telegram_id: int,
        language: str,
    ) -> tuple[bool, str]:
        """Set the language for a group in the database."""
        if not db:
            return False, "Database not available"
        
        i18n = get_i18n_service()
        normalized = i18n._normalize_language_code(language)
        
        if normalized not in SUPPORTED_LANGUAGES:
            supported = ", ".join(f"`{code}`" for code in SUPPORTED_LANGUAGES.keys())
            return False, f"Unsupported language. Supported: {supported}"
        
        result = await db.execute(
            select(Group).where(Group.telegram_id == group_telegram_id)
        )
        group = result.scalar_one_or_none()
        
        if not group:
            return False, "Group not found"
        
        group.language = normalized
        await db.flush()
        
        lang_info = SUPPORTED_LANGUAGES[normalized]
        return True, f"Language set to {lang_info['native']}"

    async def on_callback_query(self, ctx: NexusContext) -> bool:
        """Handle language selection callbacks."""
        if not ctx.callback_query or not ctx.callback_query.data:
            return False
        
        data = ctx.callback_query.data
        
        if not data.startswith("lang_set:"):
            return False
        
        # Check admin permission
        if not ctx.user.is_admin:
            await ctx.callback_query.answer(
                "❌ Only admins can change language settings",
                show_alert=True
            )
            return True
        
        # Extract language code
        lang_code = data.split(":")[1]
        
        # Set language
        success, message = await self._set_group_language(ctx.db, ctx.group.telegram_id, lang_code)
        
        if success:
            ctx.i18n.set_language(lang_code)
            lang_info = SUPPORTED_LANGUAGES.get(lang_code, {})
            await ctx.callback_query.answer(
                f"✅ Language set to {lang_info.get('native', lang_code)}",
                show_alert=True
            )
            # Update the menu
            await self._show_language_menu(ctx, get_i18n_service())
        else:
            await ctx.callback_query.answer(f"❌ {message}", show_alert=True)
        
        return True
