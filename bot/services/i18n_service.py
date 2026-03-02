"""Internationalization (i18n) service for multi-language support."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Group, User


# Supported languages with their display names and native names
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native": "English", "flag": "🇬🇧"},
    "fr": {"name": "French", "native": "Français", "flag": "🇫🇷"},
    "it": {"name": "Italian", "native": "Italiano", "flag": "🇮🇹"},
    "es": {"name": "Spanish", "native": "Español", "flag": "🇪🇸"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "flag": "🇮🇳"},
}

# Language aliases for common variations
LANGUAGE_ALIASES = {
    # English variants
    "en-us": "en",
    "en-gb": "en",
    "en-au": "en",
    "en-ca": "en",
    # French variants
    "fr-fr": "fr",
    "fr-ca": "fr",
    "fr-be": "fr",
    "fr-ch": "fr",
    # Italian variants
    "it-it": "it",
    "it-ch": "it",
    # Spanish variants
    "es-es": "es",
    "es-mx": "es",
    "es-ar": "es",
    "es-co": "es",
    "es-cl": "es",
    "es-pe": "es",
    "es-ve": "es",
    # Hindi variants
    "hi-in": "hi",
    # Portuguese (not yet supported, fallback to Spanish)
    "pt": "es",
    "pt-br": "es",
    "pt-pt": "es",
    # German (not yet supported, fallback to English)
    "de": "en",
    "de-de": "en",
    "de-at": "en",
    # Other common languages (fallback to English)
    "ru": "en",
    "zh": "en",
    "ja": "en",
    "ko": "en",
    "ar": "en",
}


@dataclass
class LocaleData:
    """Container for locale data."""
    language: str
    translations: Dict[str, Any]
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a translation by dot-notation key."""
        parts = key.split(".")
        value = self.translations
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        
        return value if isinstance(value, str) else default


class I18nService:
    """Service for handling internationalization and translations."""
    
    def __init__(self, locales_dir: Optional[str] = None):
        """Initialize the i18n service.
        
        Args:
            locales_dir: Directory containing locale JSON files.
                        Defaults to 'locales' in project root.
        """
        if locales_dir is None:
            # Find locales directory relative to this file
            project_root = Path(__file__).parent.parent.parent
            locales_dir = project_root / "locales"
        
        self.locales_dir = Path(locales_dir)
        self._cache: Dict[str, LocaleData] = {}
        self._loaded = False
    
    def load_locales(self) -> None:
        """Load all locale files from disk."""
        if self._loaded:
            return
        
        if not self.locales_dir.exists():
            self._loaded = True
            return
        
        for locale_file in self.locales_dir.glob("*.json"):
            lang_code = locale_file.stem
            try:
                with open(locale_file, "r", encoding="utf-8") as f:
                    translations = json.load(f)
                self._cache[lang_code] = LocaleData(
                    language=lang_code,
                    translations=translations
                )
            except (json.JSONDecodeError, IOError) as e:
                # Log error but continue
                print(f"Warning: Failed to load locale {lang_code}: {e}")
        
        self._loaded = True
    
    def reload_locales(self) -> None:
        """Force reload all locales from disk."""
        self._cache.clear()
        self._loaded = False
        self.load_locales()
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages with metadata."""
        return [
            {
                "code": code,
                "name": data["name"],
                "native": data["native"],
                "flag": data["flag"],
            }
            for code, data in SUPPORTED_LANGUAGES.items()
        ]
    
    def is_language_supported(self, language: str) -> bool:
        """Check if a language code is supported."""
        normalized = self._normalize_language_code(language)
        return normalized in SUPPORTED_LANGUAGES
    
    def _normalize_language_code(self, language: str) -> str:
        """Normalize a language code to our supported format."""
        if not language:
            return "en"
        
        # Convert to lowercase
        code = language.lower().strip()
        
        # Check aliases first
        if code in LANGUAGE_ALIASES:
            return LANGUAGE_ALIASES[code]
        
        # Check if directly supported
        if code in SUPPORTED_LANGUAGES:
            return code
        
        # Try base language code (e.g., "en-US" -> "en")
        base_code = code.split("-")[0]
        if base_code in LANGUAGE_ALIASES:
            return LANGUAGE_ALIASES[base_code]
        
        if base_code in SUPPORTED_LANGUAGES:
            return base_code
        
        # Fallback to English
        return "en"
    
    def get_locale(self, language: str) -> LocaleData:
        """Get locale data for a language."""
        if not self._loaded:
            self.load_locales()
        
        normalized = self._normalize_language_code(language)
        
        if normalized in self._cache:
            return self._cache[normalized]
        
        # Fallback to English
        if "en" in self._cache:
            return self._cache["en"]
        
        # Return empty locale if nothing available
        return LocaleData(language="en", translations={})
    
    def translate(
        self,
        key: str,
        language: str = "en",
        **kwargs: Any,
    ) -> str:
        """Translate a key with optional variable substitution.
        
        Args:
            key: Translation key in dot notation (e.g., "common.hello")
            language: Language code
            **kwargs: Variables to substitute in the translation
            
        Returns:
            Translated and substituted string
        """
        locale = self.get_locale(language)
        template = locale.get(key)
        
        if template is None:
            # Return the key as fallback
            return f"[{key}]"
        
        # Substitute variables
        try:
            return template.format(**kwargs)
        except KeyError as e:
            # Missing variable, return template as-is
            return template
    
    def t(
        self,
        key: str,
        language: str = "en",
        **kwargs: Any,
    ) -> str:
        """Shorthand for translate()."""
        return self.translate(key, language, **kwargs)
    
    def get_translations_for_category(
        self,
        category: str,
        language: str = "en",
    ) -> Dict[str, str]:
        """Get all translations for a category.
        
        Args:
            category: Category name (e.g., "moderation", "common")
            language: Language code
            
        Returns:
            Dictionary of key -> translation mappings
        """
        locale = self.get_locale(language)
        category_data = locale.translations.get(category, {})
        
        if not isinstance(category_data, dict):
            return {}
        
        return category_data
    
    async def get_user_language(
        self,
        db: AsyncSession,
        user_id: int,
        group_id: Optional[int] = None,
    ) -> str:
        """Get the preferred language for a user.
        
        Priority:
        1. User's stored preference
        2. Group's language setting
        3. User's Telegram language_code
        4. Default (English)
        """
        # Try to get user's stored preference
        result = await db.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Check if user has a custom language preference stored
            # (could be added as a field to User model)
            # For now, use their Telegram language_code
            if user.language_code:
                return self._normalize_language_code(user.language_code)
        
        # Fall back to group language if group_id provided
        if group_id:
            group_result = await db.execute(
                select(Group).where(Group.telegram_id == group_id)
            )
            group = group_result.scalar_one_or_none()
            if group and group.language:
                return self._normalize_language_code(group.language)
        
        # Default to English
        return "en"
    
    async def get_group_language(
        self,
        db: AsyncSession,
        group_id: int,
    ) -> str:
        """Get the language setting for a group."""
        result = await db.execute(
            select(Group).where(Group.telegram_id == group_id)
        )
        group = result.scalar_one_or_none()
        
        if group and group.language:
            return self._normalize_language_code(group.language)
        
        return "en"
    
    async def set_group_language(
        self,
        db: AsyncSession,
        group_id: int,
        language: str,
    ) -> Tuple[bool, str]:
        """Set the language for a group.
        
        Returns:
            Tuple of (success, message)
        """
        normalized = self._normalize_language_code(language)
        
        if normalized not in SUPPORTED_LANGUAGES:
            supported = ", ".join(SUPPORTED_LANGUAGES.keys())
            return False, f"Unsupported language. Supported: {supported}"
        
        result = await db.execute(
            select(Group).where(Group.telegram_id == group_id)
        )
        group = result.scalar_one_or_none()
        
        if not group:
            return False, "Group not found"
        
        group.language = normalized
        await db.flush()
        
        lang_info = SUPPORTED_LANGUAGES[normalized]
        return True, f"Language set to {lang_info['native']} ({lang_info['flag']})"


# Global instance
_i18n_service: Optional[I18nService] = None


def get_i18n_service() -> I18nService:
    """Get or create the global i18n service instance."""
    global _i18n_service
    if _i18n_service is None:
        _i18n_service = I18nService()
    return _i18n_service


def t(key: str, language: str = "en", **kwargs: Any) -> str:
    """Convenience function for translations."""
    return get_i18n_service().translate(key, language, **kwargs)
