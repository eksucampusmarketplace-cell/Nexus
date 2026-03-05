"""Button Decorations Module - Customize inline keyboard button styles with emoji decorations."""

from typing import Dict, List, Optional
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


# Decoration categories with emoji options
DECORATION_CATEGORIES = {
    "nature": {
        "name": "Nature",
        "icon": "🌿",
        "decorations": {
            "flowers": {"name": "Flowers", "prefix": "🌸", "suffix": "🌺"},
            "trees": {"name": "Trees", "prefix": "🌳", "suffix": "🌴"},
            "plants": {"name": "Plants", "prefix": "🌵", "suffix": "🌱"},
            "leaves": {"name": "Leaves", "prefix": "🍃", "suffix": "🍂"},
            "seasonal": {"name": "Seasonal", "prefix": "🌸", "suffix": "🍁"},
        }
    },
    "animals": {
        "name": "Animals",
        "icon": "🦁",
        "decorations": {
            "lions": {"name": "Lions", "prefix": "🦁", "suffix": "🐾"},
            "cats": {"name": "Cats", "prefix": "🐱", "suffix": "😺"},
            "dogs": {"name": "Dogs", "prefix": "🐕", "suffix": "🐶"},
            "birds": {"name": "Birds", "prefix": "🦅", "suffix": "🐦"},
            "ocean": {"name": "Ocean", "prefix": "🐬", "suffix": "🦈"},
            "wild": {"name": "Wild", "prefix": "🦊", "suffix": "🐻"},
        }
    },
    "objects": {
        "name": "Objects",
        "icon": "✨",
        "decorations": {
            "stars": {"name": "Stars", "prefix": "⭐", "suffix": "🌟"},
            "hearts": {"name": "Hearts", "prefix": "❤️", "suffix": "💕"},
            "gems": {"name": "Gems", "prefix": "💎", "suffix": "💠"},
            "crowns": {"name": "Crowns", "prefix": "👑", "suffix": "🏆"},
            "sparkles": {"name": "Sparkles", "prefix": "✨", "suffix": "💫"},
            "fire": {"name": "Fire", "prefix": "🔥", "suffix": "💥"},
        }
    },
    "symbols": {
        "name": "Symbols",
        "icon": "🔷",
        "decorations": {
            "arrows": {"name": "Arrows", "prefix": "➡️", "suffix": "⬅️"},
            "checkmarks": {"name": "Checkmarks", "prefix": "✅", "suffix": "☑️"},
            "bullets": {"name": "Bullets", "prefix": "•", "suffix": "•"},
            "diamonds": {"name": "Diamonds", "prefix": "🔷", "suffix": "🔶"},
            "squares": {"name": "Squares", "prefix": "⬛", "suffix": "⬜"},
        }
    },
    "food": {
        "name": "Food",
        "icon": "🍔",
        "decorations": {
            "fruits": {"name": "Fruits", "prefix": "🍎", "suffix": "🍊"},
            "drinks": {"name": "Drinks", "prefix": "🥤", "suffix": "🍹"},
            "candy": {"name": "Candy", "prefix": "🍬", "suffix": "🍭"},
            "fastfood": {"name": "Fast Food", "prefix": "🍔", "suffix": "🍟"},
        }
    },
    "minimal": {
        "name": "Minimal",
        "icon": "⚪",
        "decorations": {
            "none": {"name": "None", "prefix": "", "suffix": ""},
            "simple": {"name": "Simple", "prefix": "▫️", "suffix": "▫️"},
            "dots": {"name": "Dots", "prefix": "•", "suffix": "•"},
            "clean": {"name": "Clean", "prefix": " ", "suffix": ""},
        }
    }
}


class ButtonDecorationsConfig(BaseModel):
    """Configuration for button decorations module."""
    
    # Global decoration setting
    enabled: bool = False
    
    # Default decoration (category:decoration format, e.g., "nature:flowers")
    default_decoration: str = "minimal:none"
    
    # Per-message-type decorations
    message_type_decorations: Dict[str, str] = {}
    
    # Apply to all buttons or only specific types
    apply_to_all: bool = False
    apply_to_admin_only: bool = False
    apply_to_commands_only: bool = False
    
    # Decoration position
    position: str = "both"  # "prefix", "suffix", "both"
    
    # Custom decorations (user-defined)
    custom_decorations: Dict[str, Dict[str, str]] = {}


class ButtonDecorationsModule(NexusModule):
    """Customize inline keyboard button styles with emoji decorations."""

    name = "button_decorations"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Add beautiful emoji decorations to inline keyboard buttons"
    category = ModuleCategory.UTILITY

    config_schema = ButtonDecorationsConfig
    default_config = ButtonDecorationsConfig().dict()

    commands = [
        CommandDef(
            name="decorations",
            description="View and select button decorations",
            admin_only=True,
            aliases=["deco", "buttons"],
        ),
        CommandDef(
            name="setdecoration",
            description="Set button decoration for the group",
            admin_only=True,
            aliases=["setdeco"],
        ),
        CommandDef(
            name="customdecoration",
            description="Create custom button decoration",
            admin_only=True,
            aliases=["customdeco"],
        ),
    ]

    async def cmd_decorations(self, ctx: NexusContext, args: List[str]):
        """Show decoration selection menu."""
        if not self._is_enabled(ctx):
            return
        
        config = self.get_config(ctx.group_id)
        
        # Build category selection keyboard
        builder = InlineKeyboardBuilder()
        
        row = []
        for cat_key, category in DECORATION_CATEGORIES.items():
            row.append({
                "text": f"{category['icon']} {category['name']}",
                "callback_data": f"deco_cat:{cat_key}"
            })
            if len(row) == 2:
                builder.row(*[builder.button(**item) for item in row])
                row = []
        
        if row:
            builder.row(*[builder.button(**item) for item in row])
        
        # Add clear decoration option
        builder.row(
            builder.button(text="🗑️ Clear Decorations", callback_data="deco_clear"),
            builder.button(text="❌ Close", callback_data="deco_close")
        )
        
        # Show current decoration
        current = config.get("default_decoration", "minimal:none")
        cat_key, deco_key = current.split(":")
        current_name = "None"
        if cat_key in DECORATION_CATEGORIES and deco_key in DECORATION_CATEGORIES[cat_key]["decorations"]:
            current_name = DECORATION_CATEGORIES[cat_key]["decorations"][deco_key]["name"]
        
        await ctx.send(
            f"🎨 <b>Button Decorations</b>\n\n"
            f"Current: {current_name}\n"
            f"Select a category to choose decorations:",
            reply_markup=builder.as_markup()
        )

    async def cmd_setdecoration(self, ctx: NexusContext, args: List[str]):
        """Set decoration directly via command."""
        if not self._is_enabled(ctx):
            return
        
        if not args:
            await ctx.send(
                "❌ Usage: `/setdecoration <category>:<decoration>`\n"
                "Example: `/setdecoration nature:flowers`\n\n"
                "Use `/decorations` to see available options."
            )
            return
        
        decoration = args[0]
        if ":" not in decoration:
            await ctx.send("❌ Invalid format. Use `category:decoration`")
            return
        
        cat_key, deco_key = decoration.split(":")
        
        if cat_key not in DECORATION_CATEGORIES:
            await ctx.send(f"❌ Unknown category: {cat_key}")
            return
        
        if deco_key not in DECORATION_CATEGORIES[cat_key]["decorations"]:
            await ctx.send(f"❌ Unknown decoration: {deco_key} in category {cat_key}")
            return
        
        # Update config
        config = self.get_config(ctx.group_id)
        config["default_decoration"] = decoration
        config["enabled"] = True
        self.set_config(ctx.group_id, config)
        
        deco_name = DECORATION_CATEGORIES[cat_key]["decorations"][deco_key]["name"]
        await ctx.send(f"✅ Button decoration set to: {deco_name}")

    async def cmd_customdecoration(self, ctx: NexusContext, args: List[str]):
        """Create a custom decoration."""
        if not self._is_enabled(ctx):
            return
        
        if len(args) < 3:
            await ctx.send(
                "❌ Usage: `/customdecoration <name> <prefix> <suffix>`\n"
                "Example: `/customdecoration mycool ⚡ ⚡`\n\n"
                "Leave prefix/suffix empty for none."
            )
            return
        
        name = args[0]
        prefix = args[1]
        suffix = args[2]
        
        config = self.get_config(ctx.group_id)
        
        if "custom_decorations" not in config:
            config["custom_decorations"] = {}
        
        config["custom_decorations"][name] = {
            "name": name,
            "prefix": prefix,
            "suffix": suffix
        }
        
        self.set_config(ctx.group_id, config)
        
        await ctx.send(f"✅ Custom decoration '{name}' created with prefix '{prefix}' and suffix '{suffix}'")

    async def on_callback_query(self, callback: CallbackQuery, ctx: NexusContext):
        """Handle decoration callback queries."""
        if not callback.data or not callback.data.startswith("deco_"):
            return
        
        parts = callback.data.split(":")
        action = parts[0]
        
        if action == "deco_cat":
            cat_key = parts[1]
            await self._show_decorations_in_category(callback, ctx, cat_key)
            await callback.answer()
        elif action == "deco_select":
            cat_key = parts[1]
            deco_key = parts[2]
            await self._select_decoration(callback, ctx, cat_key, deco_key)
            await callback.answer()
        elif action == "deco_clear":
            await self._clear_decoration(callback, ctx)
            await callback.answer()
        elif action == "deco_close":
            await callback.message.delete()
            await callback.answer()

    async def _show_decorations_in_category(self, callback: CallbackQuery, ctx: NexusContext, cat_key: str):
        """Show decorations in a specific category."""
        if cat_key not in DECORATION_CATEGORIES:
            await callback.answer("Category not found")
            return
        
        category = DECORATION_CATEGORIES[cat_key]
        builder = InlineKeyboardBuilder()
        
        row = []
        for deco_key, deco in category["decorations"].items():
            # Preview button with decoration applied
            preview = self._apply_decoration("Button", deco["prefix"], deco["suffix"])
            row.append({
                "text": preview,
                "callback_data": f"deco_select:{cat_key}:{deco_key}"
            })
            if len(row) == 2:
                builder.row(*[builder.button(**item) for item in row])
                row = []
        
        if row:
            builder.row(*[builder.button(**item) for item in row])
        
        # Back button
        builder.row(builder.button(text="◀️ Back to Categories", callback_data="deco_cat:back"))
        
        await callback.message.edit_text(
            f"🎨 {category['icon']} <b>{category['name']}</b>\n\n"
            f"Select a decoration:",
            reply_markup=builder.as_markup()
        )

    async def _select_decoration(self, callback: CallbackQuery, ctx: NexusContext, cat_key: str, deco_key: str):
        """Apply selected decoration."""
        config = self.get_config(ctx.group_id)
        
        decoration = f"{cat_key}:{deco_key}"
        config["default_decoration"] = decoration
        config["enabled"] = True
        self.set_config(ctx.group_id, config)
        
        deco_name = DECORATION_CATEGORIES[cat_key]["decorations"][deco_key]["name"]
        
        builder = InlineKeyboardBuilder()
        builder.row(builder.button(text="✅ Done", callback_data="deco_close"))
        
        await callback.message.edit_text(
            f"✅ Button decoration set to: <b>{deco_name}</b>\n\n"
            f"Your inline keyboard buttons will now use this decoration!",
            reply_markup=builder.as_markup()
        )

    async def _clear_decoration(self, callback: CallbackQuery, ctx: NexusContext):
        """Clear all decorations."""
        config = self.get_config(ctx.group_id)
        config["default_decoration"] = "minimal:none"
        config["enabled"] = False
        self.set_config(ctx.group_id, config)
        
        builder = InlineKeyboardBuilder()
        builder.row(builder.button(text="✅ Done", callback_data="deco_close"))
        
        await callback.message.edit_text(
            "🗑️ Button decorations cleared.\n\n"
            "Buttons will appear without decorations.",
            reply_markup=builder.as_markup()
        )

    def _is_enabled(self, ctx: NexusContext) -> bool:
        """Check if decorations are enabled for the group."""
        config = self.get_config(ctx.group_id)
        return config.get("enabled", False)

    def apply_decoration(self, text: str, group_id: int) -> str:
        """
        Apply decoration to button text.
        
        Args:
            text: Original button text
            group_id: Group ID
            
        Returns:
            Decorated button text
        """
        config = self.get_config(group_id)
        
        if not config.get("enabled", False):
            return text
        
        decoration = config.get("default_decoration", "minimal:none")
        position = config.get("position", "both")
        
        # Handle custom decorations
        if decoration.startswith("custom:"):
            custom_name = decoration.split(":", 1)[1]
            custom_decorations = config.get("custom_decorations", {})
            if custom_name in custom_decorations:
                custom = custom_decorations[custom_name]
                return self._apply_decoration(text, custom["prefix"], custom["suffix"], position)
        
        # Handle predefined decorations
        if ":" in decoration:
            cat_key, deco_key = decoration.split(":")
            if cat_key in DECORATION_CATEGORIES and deco_key in DECORATION_CATEGORIES[cat_key]["decorations"]:
                deco = DECORATION_CATEGORIES[cat_key]["decorations"][deco_key]
                return self._apply_decoration(text, deco["prefix"], deco["suffix"], position)
        
        return text

    def _apply_decoration(self, text: str, prefix: str, suffix: str, position: str = "both") -> str:
        """Apply decoration with specified position."""
        if position == "prefix":
            return f"{prefix} {text}"
        elif position == "suffix":
            return f"{text} {suffix}"
        else:  # both
            return f"{prefix} {text} {suffix}"


# Global instance for accessing decoration functionality
_decoration_module: Optional[ButtonDecorationsModule] = None


def get_decoration_module() -> Optional[ButtonDecorationsModule]:
    """Get the decoration module instance."""
    return _decoration_module


def set_decoration_module(module: ButtonDecorationsModule):
    """Set the decoration module instance."""
    global _decoration_module
    _decoration_module = module


def apply_button_decoration(text: str, group_id: int) -> str:
    """
    Convenience function to apply button decoration.
    
    Usage:
        from bot.modules.button_decorations.module import apply_button_decoration
        
        original_text = "Click Me"
        decorated_text = apply_button_decoration(original_text, group_id)
        # Results in: "🌸 Click Me 🌺" if nature:flowers is set
    """
    module = get_decoration_module()
    if module:
        return module.apply_decoration(text, group_id)
    return text
