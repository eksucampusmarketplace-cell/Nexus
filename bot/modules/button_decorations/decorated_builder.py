"""Decorated keyboard builder with auto-decoration support."""

from typing import Any, Dict, Optional

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.modules.button_decorations.module import apply_button_decoration, get_decoration_module


class DecoratedInlineKeyboardBuilder(InlineKeyboardBuilder):
    """
    Enhanced InlineKeyboardBuilder that automatically applies button decorations.
    
    Usage:
        from bot.modules.button_decorations.decorated_builder import DecoratedInlineKeyboardBuilder
        
        builder = DecoratedInlineKeyboardBuilder(group_id=ctx.group_id)
        builder.button(text="Click Me", callback_data="clicked")
        markup = builder.as_markup()
        # Text becomes: "🌸 Click Me 🌺" if nature:flowers is set
    """
    
    def __init__(
        self,
        group_id: int,
        enabled: bool = True,
        apply_animation: bool = True,
        user_id: Optional[int] = None
    ):
        """
        Initialize the decorated keyboard builder.
        
        Args:
            group_id: The group ID for fetching decoration settings
            enabled: Whether to apply decorations (default: True)
            apply_animation: Whether to apply animations (default: True)
            user_id: Optional user ID for user-specific preferences
        """
        super().__init__()
        self.group_id = group_id
        self.enabled = enabled
        self.apply_animation = apply_animation
        self.user_id = user_id
    
    def button(
        self,
        text: str,
        callback_data: Optional[str] = None,
        url: Optional[str] = None,
        skip_decoration: bool = False,
        **kwargs: Any
    ) -> None:
        """
        Add a button with optional decoration.
        
        Args:
            text: Button text
            callback_data: Callback data
            url: URL for link buttons
            skip_decoration: If True, don't apply decoration to this button
            **kwargs: Additional aiogram button parameters
        """
        if self.enabled and not skip_decoration:
            text = apply_button_decoration(text, self.group_id, self.user_id)
            
            # Apply animation if enabled
            if self.apply_animation:
                module = get_decoration_module()
                if module:
                    text = module.apply_animation(text, self.group_id)
        
        super().button(
            text=text,
            callback_data=callback_data,
            url=url,
            **kwargs
        )
    
    def row(self, *buttons: Any, width: int = 3, **kwargs: Any) -> None:
        """Add buttons in a row."""
        super().row(*buttons, width=width, **kwargs)


class DecoratedKeyboardLayout:
    """
    High-level keyboard layout with decoration support.
    
    Provides a more declarative way to build keyboards.
    
    Usage:
        layout = DecoratedKeyboardLayout(group_id=ctx.group_id)
        
        layout.add_section("Actions")
        layout.add_button("Warn", callback="warn", icon="⚠️")
        layout.add_button("Mute", callback="mute", icon="🔇")
        layout.add_button("Ban", callback="ban", icon="🚫")
        
        layout.add_section("Options")
        layout.add_button("Cancel", callback="cancel", style="danger")
        
        markup = layout.build()
    """
    
    def __init__(self, group_id: int, enabled: bool = True):
        """Initialize the keyboard layout."""
        self.group_id = group_id
        self.enabled = enabled
        self.builder = InlineKeyboardBuilder()
        self._current_row = []
    
    def add_section(self, title: str) -> None:
        """Add a section header (as a disabled button)."""
        if self._current_row:
            self._flush_row()
        
        # Section header
        decorated_title = apply_button_decoration(f"─ {title} ─", self.group_id) if self.enabled else f"─ {title} ─"
        self.builder.button(text=decorated_title, callback_data=f"section_{title}")
        self._flush_row()
    
    def add_button(
        self,
        text: str,
        callback: str,
        icon: Optional[str] = None,
        style: str = "default",
        skip_decoration: bool = False,
        **kwargs: Any
    ) -> None:
        """
        Add a button to the layout.
        
        Args:
            text: Button text
            callback: Callback data
            icon: Optional icon to prepend (before decoration)
            style: Button style - "default", "danger", "success", "primary"
            skip_decoration: Skip decoration for this button
            **kwargs: Additional button parameters
        """
        if icon:
            text = f"{icon} {text}"
        
        if self.enabled and not skip_decoration:
            text = apply_button_decoration(text, self.group_id)
        
        self.builder.button(text=text, callback_data=callback, **kwargs)
    
    def add_url_button(
        self,
        text: str,
        url: str,
        icon: Optional[str] = None,
        skip_decoration: bool = False,
        **kwargs: Any
    ) -> None:
        """Add a URL button."""
        if icon:
            text = f"{icon} {text}"
        
        if self.enabled and not skip_decoration:
            text = apply_button_decoration(text, self.group_id)
        
        self.builder.button(text=text, url=url, **kwargs)
    
    def add_row(self) -> None:
        """Start a new row."""
        if self._current_row:
            self._flush_row()
    
    def _flush_row(self) -> None:
        """Flush current row to builder."""
        # InlineKeyboardBuilder handles rows automatically via button() calls
        pass
    
    def build(self) -> InlineKeyboardMarkup:
        """Build and return the keyboard markup."""
        return self.builder.as_markup()
    
    def as_markup(self) -> InlineKeyboardMarkup:
        """Alias for build()."""
        return self.build()


# Decorator for easy button creation
def decorate_button(group_id: int):
    """
    Decorator factory for creating decorated buttons.
    
    Usage:
        @decorate_button(ctx.group_id)
        def create_button(text: str) -> str:
            return text  # Will be decorated automatically
        
        decorated_text = create_button("Click Me")
    """
    def decorator(func):
        def wrapper(text: str, skip_decoration: bool = False, *args, **kwargs):
            result = func(text, *args, **kwargs)
            if not skip_decoration:
                return apply_button_decoration(result, group_id)
            return result
        return wrapper
    return decorator


# Predefined button sets with decorations
BUTTON_SETS = {
    "moderation": {
        "name": "Moderation Actions",
        "buttons": [
            {"text": "Warn", "callback": "warn", "icon": "⚠️"},
            {"text": "Mute", "callback": "mute", "icon": "🔇"},
            {"text": "Unmute", "callback": "unmute", "icon": "🔊"},
            {"text": "Ban", "callback": "ban", "icon": "🚫"},
            {"text": "Unban", "callback": "unban", "icon": "✅"},
            {"text": "Kick", "callback": "kick", "icon": "👢"},
        ]
    },
    "confirmation": {
        "name": "Confirmation",
        "buttons": [
            {"text": "Yes", "callback": "yes", "icon": "✅"},
            {"text": "No", "callback": "no", "icon": "❌"},
        ]
    },
    "navigation": {
        "name": "Navigation",
        "buttons": [
            {"text": "Back", "callback": "back", "icon": "◀️"},
            {"text": "Next", "callback": "next", "icon": "▶️"},
            {"text": "Close", "callback": "close", "icon": "❌"},
        ]
    }
}


def create_button_set(group_id: int, set_name: str, **kwargs: Any) -> InlineKeyboardMarkup:
    """
    Create a predefined button set with decorations.
    
    Args:
        group_id: Group ID for decoration settings
        set_name: Name of button set ("moderation", "confirmation", "navigation")
        **kwargs: Additional arguments for layout
        
    Returns:
        InlineKeyboardMarkup with decorated buttons
    """
    if set_name not in BUTTON_SETS:
        raise ValueError(f"Unknown button set: {set_name}")
    
    button_set = BUTTON_SETS[set_name]
    layout = DecoratedKeyboardLayout(group_id=group_id, **kwargs)
    
    for btn in button_set["buttons"]:
        layout.add_button(
            text=btn["text"],
            callback=btn["callback"],
            icon=btn.get("icon")
        )
    
    return layout.build()


# Helper function to decorate multiple buttons at once
def decorate_buttons(buttons: list, group_id: int) -> list:
    """
    Decorate multiple button texts.
    
    Args:
        buttons: List of button dicts with 'text' key
        group_id: Group ID for decoration settings
        
    Returns:
        List of decorated button dicts
    """
    decorated = []
    for btn in buttons:
        btn_copy = btn.copy()
        btn_copy["text"] = apply_button_decoration(btn["text"], group_id)
        decorated.append(btn_copy)
    return decorated
