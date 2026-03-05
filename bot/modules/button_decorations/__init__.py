"""Button Decorations Module - Customize inline keyboard button styles."""

from .module import (
    ButtonDecorationsModule,
    ButtonDecorationsConfig,
    apply_button_decoration,
    DECORATION_CATEGORIES,
    get_decoration_module,
    set_decoration_module,
)

from .decorated_builder import (
    DecoratedInlineKeyboardBuilder,
    DecoratedKeyboardLayout,
    create_button_set,
    decorate_buttons,
    decorate_button,
    BUTTON_SETS,
)

__all__ = [
    # Main module
    "ButtonDecorationsModule",
    "ButtonDecorationsConfig",
    "apply_button_decoration",
    "DECORATION_CATEGORIES",
    "get_decoration_module",
    "set_decoration_module",
    # Builder utilities
    "DecoratedInlineKeyboardBuilder",
    "DecoratedKeyboardLayout",
    "create_button_set",
    "decorate_buttons",
    "decorate_button",
    "BUTTON_SETS",
]
