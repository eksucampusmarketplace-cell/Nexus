"""Button Decorations Module - Customize inline keyboard button styles with emoji decorations."""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


# Animated/GIF decoration frames (cycling through for animation effect)
ANIMATED_DECORATIONS = {
    "pulse": {
        "name": "Pulse",
        "frames": ["💫", "✨", "💫", "⭐"],
        "frame_duration": 0.5,
        "type": "animation"
    },
    "sparkle": {
        "name": "Sparkle",
        "frames": ["✨", "💖", "✨", "💫"],
        "frame_duration": 0.4,
        "type": "animation"
    },
    "rainbow": {
        "name": "Rainbow",
        "frames": ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤"],
        "frame_duration": 0.3,
        "type": "animation"
    },
    "fire": {
        "name": "Fire",
        "frames": ["🔥", "🔥", "💥", "🔥", "🔥"],
        "frame_duration": 0.4,
        "type": "animation"
    },
    "wave": {
        "name": "Wave",
        "frames": "🌊",  # Static but mentioned for animation
        "type": "static"
    },
    "aurora": {
        "name": "Aurora",
        "frames": ["🌌", "✨", "🌟", "✨"],
        "frame_duration": 0.6,
        "type": "animation"
    },
    "galaxy": {
        "name": "Galaxy",
        "frames": ["🌌", "🔮", "✨", "🌟"],
        "frame_duration": 0.5,
        "type": "animation"
    },
    "hearts": {
        "name": "Hearts",
        "frames": ["💗", "💖", "💓", "💕"],
        "frame_duration": 0.4,
        "type": "animation"
    },
    "stars": {
        "name": "Stars",
        "frames": ["⭐", "🌟", "✨", "💫"],
        "frame_duration": 0.5,
        "type": "animation"
    },
    "bounce": {
        "name": "Bounce",
        "frames": ["🔵", "🟢", "🔴", "🟡"],
        "frame_duration": 0.3,
        "type": "animation"
    },
}

# Color-coded button styles by action type
BUTTON_COLORS = {
    "danger": {
        "name": "Danger",
        "icon": "🔴",
        "decorations": {
            "warning": {"prefix": "⛔", "suffix": "⛔"},
            "stop": {"prefix": "🛑", "suffix": "🛑"},
            "ban": {"prefix": "🚫", "suffix": "🚫"},
            "block": {"prefix": "🚷", "suffix": "🚷"},
        }
    },
    "success": {
        "name": "Success",
        "icon": "🟢",
        "decorations": {
            "approve": {"prefix": "✅", "suffix": "✅"},
            "accept": {"prefix": "✔️", "suffix": "✔️"},
            "check": {"prefix": "☑️", "suffix": "☑️"},
        }
    },
    "warning": {
        "name": "Warning",
        "icon": "⚠️",
        "decorations": {
            "warn": {"prefix": "⚠️", "suffix": "⚠️"},
            "caution": {"prefix": "⚡", "suffix": "⚡"},
            "alert": {"prefix": "🚨", "suffix": "🚨"},
        }
    },
    "info": {
        "name": "Info",
        "icon": "🔵",
        "decorations": {
            "info": {"prefix": "ℹ️", "suffix": "ℹ️"},
            "help": {"prefix": "❓", "suffix": "❓"},
            "question": {"prefix": "❔", "suffix": "❔"},
        }
    },
    "primary": {
        "name": "Primary",
        "icon": "🟣",
        "decorations": {
            "star": {"prefix": "⭐", "suffix": "⭐"},
            "crown": {"prefix": "👑", "suffix": "👑"},
            "gem": {"prefix": "💎", "suffix": "💎"},
        }
    },
    "neutral": {
        "name": "Neutral",
        "icon": "⚪",
        "decorations": {
            "normal": {"prefix": "◻️", "suffix": "◻️"},
            "default": {"prefix": "⬜", "suffix": "⬜"},
            "blank": {"prefix": "▫️", "suffix": "▫️"},
        }
    },
}

# Seasonal decorations that auto-change
SEASONAL_DECORATIONS = {
    "spring": {
        "name": "Spring",
        "icon": "🌸",
        "months": [3, 4, 5],
        "decorations": {
            "blossom": {"prefix": "🌸", "suffix": "🌺"},
            "tulip": {"prefix": "🌷", "suffix": "🌷"},
            "flower": {"prefix": "🌼", "suffix": "🌸"},
            "rain": {"prefix": "🌧️", "suffix": "🌦️"},
        }
    },
    "summer": {
        "name": "Summer",
        "icon": "☀️",
        "months": [6, 7, 8],
        "decorations": {
            "sun": {"prefix": "☀️", "suffix": "🌞"},
            "beach": {"prefix": "🏖️", "suffix": "🏝️"},
            "ocean": {"prefix": "🌊", "suffix": "🏄"},
            "palm": {"prefix": "🌴", "suffix": "🌺"},
        }
    },
    "autumn": {
        "name": "Autumn",
        "icon": "🍁",
        "months": [9, 10, 11],
        "decorations": {
            "leaf": {"prefix": "🍁", "suffix": "🍂"},
            "pumpkin": {"prefix": "🎃", "suffix": "🎃"},
            "harvest": {"prefix": "🌾", "suffix": "🍂"},
            "fall": {"prefix": "🧡", "suffix": "🍁"},
        }
    },
    "winter": {
        "name": "Winter",
        "icon": "❄️",
        "months": [12, 1, 2],
        "decorations": {
            "snow": {"prefix": "❄️", "suffix": "☃️"},
            "snowflake": {"prefix": "❄️", "suffix": "❄️"},
            "gift": {"prefix": "🎁", "suffix": "🎄"},
            "holiday": {"prefix": "🎄", "suffix": "🎅"},
        }
    },
    "halloween": {
        "name": "Halloween",
        "icon": "🎃",
        "months": [10],  # October only
        "decorations": {
            "spooky": {"prefix": "👻", "suffix": "👻"},
            "pumpkin": {"prefix": "🎃", "suffix": "🎃"},
            "bat": {"prefix": "🦇", "suffix": "🦇"},
            "web": {"prefix": "🕸️", "suffix": "🕸️"},
        }
    },
    "christmas": {
        "name": "Christmas",
        "icon": "🎄",
        "months": [12],  # December only
        "decorations": {
            "tree": {"prefix": "🎄", "suffix": "🎁"},
            "santa": {"prefix": "🎅", "suffix": "🎅"},
            "gift": {"prefix": "🎁", "suffix": "🎁"},
            "bells": {"prefix": "🔔", "suffix": "🔔"},
        }
    },
    "newyear": {
        "name": "New Year",
        "icon": "🎉",
        "months": [1],  # January only
        "decorations": {
            "party": {"prefix": "🎉", "suffix": "🎊"},
            "ball": {"prefix": "🪩", "suffix": "🎆"},
            "countdown": {"prefix": "⏰", "suffix": "🎆"},
            "celebration": {"prefix": "🥳", "suffix": "🎉"},
        }
    },
    "valentine": {
        "name": "Valentine",
        "icon": "💕",
        "months": [2],  # February only
        "decorations": {
            "heart": {"prefix": "❤️", "suffix": "💕"},
            "rose": {"prefix": "🌹", "suffix": "💐"},
            "cupid": {"prefix": "💘", "suffix": "💝"},
            "love": {"prefix": "💖", "suffix": "💗"},
        }
    },
}

# Premium decoration packs (require premium status)
PREMIUM_PACKS = {
    "gold": {
        "name": "Gold Pack",
        "icon": "👑",
        "description": "Luxurious gold-themed decorations",
        "premium_required": True,
        "decorations": {
            "gold_star": {"prefix": "🌟", "suffix": "🌟"},
            "gold_crown": {"prefix": "👑", "suffix": "👑"},
            "gold_gem": {"prefix": "💎", "suffix": "💎"},
            "gold_trophy": {"prefix": "🏆", "suffix": "🏆"},
            "medal": {"prefix": "🥇", "suffix": "🥇"},
        }
    },
    "neon": {
        "name": "Neon Pack",
        "icon": "💜",
        "description": "Neon glow effect decorations",
        "premium_required": True,
        "decorations": {
            "neon_pink": {"prefix": "💜", "suffix": "💜"},
            "neon_blue": {"prefix": "💙", "suffix": "💙"},
            "neon_green": {"prefix": "💚", "suffix": "💚"},
            "neon_purple": {"prefix": "💛", "suffix": "💛"},
        }
    },
    "cosmic": {
        "name": "Cosmic Pack",
        "icon": "🌌",
        "description": "Out of this world decorations",
        "premium_required": True,
        "decorations": {
            "galaxy": {"prefix": "🌌", "suffix": "🌌"},
            "rocket": {"prefix": "🚀", "suffix": "🚀"},
            "planet": {"prefix": "🪐", "suffix": "🪐"},
            "ufo": {"prefix": "🛸", "suffix": "🛸"},
            "star": {"prefix": "⭐", "suffix": "⭐"},
        }
    },
    "mythical": {
        "name": "Mythical Pack",
        "icon": "🐲",
        "description": "Dragons and mythical creatures",
        "premium_required": True,
        "decorations": {
            "dragon": {"prefix": "🐉", "suffix": "🐉"},
            "phoenix": {"prefix": "🔥", "suffix": "🦅"},
            "unicorn": {"prefix": "🦄", "suffix": "🦄"},
            "fairy": {"prefix": "🧚", "suffix": "🧚"},
            "wizard": {"prefix": "🧙", "suffix": "🧙"},
        }
    },
}


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
    
    # Animated decoration settings
    use_animations: bool = False
    animation_speed: float = 0.5  # seconds per frame
    
    # Color-coded buttons (by action type)
    use_color_coding: bool = False
    color_by_action: Dict[str, str] = {}  # action -> color mapping
    
    # Seasonal auto-changing decorations
    auto_seasonal: bool = False
    seasonal_override: Optional[str] = None  # force specific season
    
    # Premium packs enabled
    premium_packs_enabled: Dict[str, bool] = {}  # pack_name -> enabled
    
    # User-specific preferences (per-user override)
    user_preferences: Dict[int, Dict[str, Any]] = {}  # user_id -> preferences
    
    # Marketplace/shared decorations
    marketplace_listings: Dict[str, Dict[str, Any]] = {}  # listing_id -> listing
    
    # Animation effect type
    animation_effect: str = "none"  # "none", "pulse", "sparkle", "rainbow", "fire", etc.


class ButtonDecorationsModule(NexusModule):
    """Customize inline keyboard button styles with emoji decorations."""

    name = "button_decorations"
    version = "1.1.0"
    author = "Nexus Team"
    description = "Add beautiful emoji decorations to inline keyboard buttons with animations, colors, and premium packs"
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
        CommandDef(
            name="animations",
            description="View and select button animations",
            admin_only=True,
            aliases=["anims", "anim"],
        ),
        CommandDef(
            name="colorbuttons",
            description="Configure color-coded buttons",
            admin_only=True,
            aliases=["colors", "btncolor"],
        ),
        CommandDef(
            name="seasonal",
            description="Configure seasonal auto-changing decorations",
            admin_only=True,
            aliases=["season"],
        ),
        CommandDef(
            name="premiumpacks",
            description="Browse premium decoration packs",
            admin_only=False,
            aliases=["premium", "packs"],
        ),
        CommandDef(
            name="marketplace",
            description="Browse decoration marketplace",
            admin_only=False,
            aliases=["shop", "store"],
        ),
        CommandDef(
            name="mydecoration",
            description="Set your personal decoration preference",
            admin_only=False,
            aliases=["mydeco", "userdeco"],
        ),
    ]

    async def cmd_decorations(self, ctx: NexusContext, args: List[str]):
        """Show decoration selection menu with all new features."""
        config = self.get_config(ctx.group_id)
        
        # Build category selection keyboard with tabs for different decoration types
        builder = InlineKeyboardBuilder()
        
        # Main categories
        builder.row(
            builder.button(text="📦 Standard", callback_data="deco_tab:standard"),
            builder.button(text="🎬 Animations", callback_data="deco_tab:animations"),
            builder.button(text="🎨 Colors", callback_data="deco_tab:colors"),
        )
        builder.row(
            builder.button(text="❄️ Seasonal", callback_data="deco_tab:seasonal"),
            builder.button(text="👑 Premium", callback_data="deco_tab:premium"),
            builder.button(text="🏪 Marketplace", callback_data="deco_tab:marketplace"),
        )
        
        # Current decoration display
        current = config.get("default_decoration", "minimal:none")
        current_name = self._get_decoration_name(current)
        
        # Animation status
        anim_status = ""
        if config.get("use_animations", False):
            anim = config.get("animation_effect", "none")
            if anim != "none":
                anim_status = f"\n✨ Animation: {anim}"
        
        # Color coding status
        color_status = ""
        if config.get("use_color_coding", False):
            color_status = "\n🎨 Color-coded buttons: ON"
        
        # Seasonal status
        seasonal_status = ""
        if config.get("auto_seasonal", False):
            season = self._get_current_season()
            seasonal_status = f"\n❄️ Seasonal: {season}"
        
        await ctx.send(
            f"🎨 <b>Button Decorations</b>\n\n"
            f"Current: {current_name}{anim_status}{color_status}{season_status}\n\n"
            f"Select a category to choose decorations:",
            reply_markup=builder.as_markup()
        )

    async def cmd_animations(self, ctx: NexusContext, args: List[str]):
        """Show animation selection menu."""
        if not self._is_enabled(ctx):
            return
        
        config = self.get_config(ctx.group_id)
        builder = InlineKeyboardBuilder()
        
        row = []
        for anim_key, anim in ANIMATED_DECORATIONS.items():
            is_active = config.get("animation_effect") == anim_key
            status = " ✅" if is_active else ""
            row.append({
                "text": f"{anim['name']}{status}",
                "callback_data": f"anim_select:{anim_key}"
            })
            if len(row) == 2:
                builder.row(*[builder.button(**item) for item in row])
                row = []
        
        if row:
            builder.row(*[builder.button(**item) for item in row])
        
        # Toggle animations
        current_effect = config.get("animation_effect", "none")
        if current_effect != "none":
            builder.row(
                builder.button(text="🚫 Disable Animations", callback_data="anim_disable"),
            )
        
        builder.row(builder.button(text="❌ Close", callback_data="deco_close"))
        
        await ctx.send(
            f"🎬 <b>Button Animations</b>\n\n"
            f"Current: {current_effect}\n"
            f"Select an animation effect:",
            reply_markup=builder.as_markup()
        )

    async def cmd_colorbuttons(self, ctx: NexusContext, args: List[str]):
        """Configure color-coded buttons."""
        if not self._is_enabled(ctx):
            return
        
        config = self.get_config(ctx.group_id)
        builder = InlineKeyboardBuilder()
        
        # Toggle color coding
        use_colors = config.get("use_color_coding", False)
        toggle_text = "🔴 Disable Color Coding" if use_colors else "🟢 Enable Color Coding"
        builder.row(builder.button(text=toggle_text, callback_data="color_toggle"))
        
        if use_colors:
            # Show color categories
            for color_key, color in BUTTON_COLORS.items():
                builder.row(
                    builder.button(text=f"{color['icon']} {color['name']}", callback_data=f"color_cat:{color_key}")
                )
        
        builder.row(builder.button(text="❌ Close", callback_data="deco_close"))
        
        await ctx.send(
            f"🎨 <b>Color-Coded Buttons</b>\n\n"
            f"Buttons will be color-coded based on their action type:\n"
            f"• 🔴 Danger - ban, kick, block\n"
            f"• 🟢 Success - approve, accept\n"
            f"• ⚠️ Warning - warn, alert\n"
            f"• ℹ️ Info - help, question\n"
            f"• 🟣 Primary - star, crown\n"
            f"• ⚪ Neutral - default",
            reply_markup=builder.as_markup()
        )

    async def cmd_seasonal(self, ctx: NexusContext, args: List[str]):
        """Configure seasonal auto-changing decorations."""
        if not self._is_enabled(ctx):
            return
        
        config = self.get_config(ctx.group_id)
        builder = InlineKeyboardBuilder()
        
        # Toggle seasonal
        auto_seasonal = config.get("auto_seasonal", False)
        toggle_text = "🚫 Disable Seasonal" if auto_seasonal else "✅ Enable Seasonal"
        builder.row(builder.button(text=toggle_text, callback_data="seasonal_toggle"))
        
        if auto_seasonal:
            # Show override options
            builder.row(builder.button(text="🌸 Spring", callback_data="season_spring"))
            builder.row(builder.button(text="☀️ Summer", callback_data="season_summer"))
            builder.row(builder.button(text="🍁 Autumn", callback_data="season_autumn"))
            builder.row(builder.button(text="❄️ Winter", callback_data="season_winter"))
            builder.row(builder.button(text="🔄 Auto (Based on date)", callback_data="season_auto"))
        
        # Show current season
        current_season = self._get_current_season()
        
        builder.row(builder.button(text="❌ Close", callback_data="deco_close"))
        
        await ctx.send(
            f"❄️ <b>Seasonal Decorations</b>\n\n"
            f"Automatically change decorations based on the time of year!\n"
            f"Current season: {current_season}\n\n"
            f"Special events:\n"
            f"• 🎃 Halloween (October)\n"
            f"• 🎄 Christmas (December)\n"
            f"• 🎉 New Year (January)\n"
            f"• 💕 Valentine (February)",
            reply_markup=builder.as_markup()
        )

    async def cmd_premiumpacks(self, ctx: NexusContext, args: List[str]):
        """Browse premium decoration packs."""
        if not self._is_enabled(ctx):
            return
        
        config = self.get_config(ctx.group_id)
        
        # Check if group is premium (simplified check)
        is_premium = config.get("is_premium", False)
        
        builder = InlineKeyboardBuilder()
        
        for pack_key, pack in PREMIUM_PACKS.items():
            is_enabled = config.get("premium_packs_enabled", {}).get(pack_key, False)
            status = " ✅" if is_enabled else ""
            
            # Show lock if not premium
            if not is_premium and pack.get("premium_required"):
                builder.row(
                    builder.button(text=f"{pack['icon']} {pack['name']} 🔒", callback_data=f"premium_locked:{pack_key}")
                )
            else:
                builder.row(
                    builder.button(text=f"{pack['icon']} {pack['name']}{status}", callback_data=f"premium_select:{pack_key}")
                )
        
        builder.row(builder.button(text="❌ Close", callback_data="deco_close"))
        
        premium_msg = "" if is_premium else "\n🔒 Premium groups can unlock these packs!"
        
        await ctx.send(
            f"👑 <b>Premium Decoration Packs</b>\n\n"
            f"Exclusive decoration packs for premium groups.{premium_msg}",
            reply_markup=builder.as_markup()
        )

    async def cmd_marketplace(self, ctx: NexusContext, args: List[str]):
        """Browse decoration marketplace."""
        if not self._is_enabled(ctx):
            return
        
        config = self.get_config(ctx.group_id)
        builder = InlineKeyboardBuilder()
        
        # Show marketplace listings
        marketplace = config.get("marketplace_listings", {})
        
        if not marketplace:
            builder.row(
                builder.button(text="➕ Create Listing", callback_data="marketplace_create")
            )
        else:
            for listing_id, listing in marketplace.items():
                builder.row(
                    builder.button(text=f"🛒 {listing.get('name', 'Unnamed')}", callback_data=f"marketplace_view:{listing_id}")
                )
            builder.row(
                builder.button(text="➕ New Listing", callback_data="marketplace_create"),
                builder.button(text="🔄 Refresh", callback_data="marketplace_refresh"),
            )
        
        builder.row(builder.button(text="❌ Close", callback_data="deco_close"))
        
        await ctx.send(
            f"🏪 <b>Decoration Marketplace</b>\n\n"
            f"Share and discover custom decorations from other groups!\n\n"
            f"Create listings to share your custom decorations with the community.",
            reply_markup=builder.as_markup()
        )

    async def cmd_mydecoration(self, ctx: NexusContext, args: List[str]):
        """Set personal decoration preference."""
        config = self.get_config(ctx.group_id)
        user_id = ctx.user_id
        
        user_prefs = config.get("user_preferences", {})
        user_pref = user_prefs.get(user_id, {})
        
        # Check if user has a preference set
        current_user_deco = user_pref.get("decoration", "default")
        
        builder = InlineKeyboardBuilder()
        
        # Quick options
        builder.row(
            builder.button(text="🔰 Use Group Default", callback_data="userdeco_default"),
        )
        
        row = []
        for cat_key, category in DECORATION_CATEGORIES.items():
            row.append({
                "text": f"{category['icon']}",
                "callback_data": f"userdeco_cat:{cat_key}"
            })
            if len(row) == 3:
                builder.row(*[builder.button(**item) for item in row])
                row = []
        
        if row:
            builder.row(*[builder.button(**item) for item in row])
        
        builder.row(builder.button(text="❌ Close", callback_data="deco_close"))
        
        await ctx.send(
            f"👤 <b>My Decoration Preference</b>\n\n"
            f"Current: {current_user_deco}\n\n"
            f"Set your personal decoration preference. "
            f"This will override the group default for your messages.",
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
        if not callback.data:
            return
        
        # Handle new callback patterns
        if callback.data.startswith("deco_tab:"):
            tab = callback.data.split(":", 1)[1]
            await self._handle_tab(callback, ctx, tab)
            await callback.answer()
        elif callback.data.startswith("anim_select:"):
            anim_key = callback.data.split(":", 1)[1]
            await self._select_animation(callback, ctx, anim_key)
            await callback.answer()
        elif callback.data == "anim_disable":
            await self._disable_animation(callback, ctx)
            await callback.answer()
        elif callback.data == "color_toggle":
            await self._toggle_color_coding(callback, ctx)
            await callback.answer()
        elif callback.data.startswith("color_cat:"):
            color_key = callback.data.split(":", 1)[1]
            await self._show_color_decorations(callback, ctx, color_key)
            await callback.answer()
        elif callback.data == "seasonal_toggle":
            await self._toggle_seasonal(callback, ctx)
            await callback.answer()
        elif callback.data.startswith("season_"):
            season = callback.data.replace("season_", "")
            await self._set_season(callback, ctx, season)
            await callback.answer()
        elif callback.data.startswith("premium_select:"):
            pack_key = callback.data.split(":", 1)[1]
            await self._select_premium_pack(callback, ctx, pack_key)
            await callback.answer()
        elif callback.data.startswith("premium_locked:"):
            pack_key = callback.data.split(":", 1)[1]
            await callback.answer("Premium required for this pack!")
        elif callback.data.startswith("userdeco_"):
            await self._handle_user_decoration(callback, ctx)
            await callback.answer()
        elif callback.data.startswith("marketplace_"):
            await self._handle_marketplace(callback, ctx)
            await callback.answer()
        
        # Legacy handlers
        elif callback.data.startswith("deco_"):
            await self._handle_legacy_callback(callback, ctx)

    async def _handle_tab(self, callback: CallbackQuery, ctx: NexusContext, tab: str):
        """Handle tab navigation."""
        if tab == "standard":
            await self._show_standard_decorations(callback, ctx)
        elif tab == "animations":
            await callback.message.edit_text(
                "Use /animations command to select button animations",
                reply_markup=None
            )
        elif tab == "colors":
            await self.cmd_colorbuttons(ctx, [])
        elif tab == "seasonal":
            await self.cmd_seasonal(ctx, [])
        elif tab == "premium":
            await self.cmd_premiumpacks(ctx, [])
        elif tab == "marketplace":
            await self.cmd_marketplace(ctx, [])

    async def _show_standard_decorations(self, callback: CallbackQuery, ctx: NexusContext):
        """Show standard decoration categories."""
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
        
        builder.row(
            builder.button(text="🗑️ Clear Decorations", callback_data="deco_clear"),
            builder.button(text="❌ Close", callback_data="deco_close")
        )
        
        await callback.message.edit_text(
            "📦 <b>Standard Decorations</b>\n\n"
            "Select a category to choose decorations:",
            reply_markup=builder.as_markup()
        )

    async def _select_animation(self, callback: CallbackQuery, ctx: NexusContext, anim_key: str):
        """Select animation effect."""
        if anim_key not in ANIMATED_DECORATIONS:
            await callback.answer("Animation not found")
            return
        
        config = self.get_config(ctx.group_id)
        config["animation_effect"] = anim_key
        config["use_animations"] = True
        self.set_config(ctx.group_id, config)
        
        anim = ANIMATED_DECORATIONS[anim_key]
        
        builder = InlineKeyboardBuilder()
        builder.row(builder.button(text="✅ Done", callback_data="deco_close"))
        
        await callback.message.edit_text(
            f"✅ Animation set to: <b>{anim['name']}</b>\n\n"
            f"Your buttons will now animate with this effect!",
            reply_markup=builder.as_markup()
        )

    async def _disable_animation(self, callback: CallbackQuery, ctx: NexusContext):
        """Disable animations."""
        config = self.get_config(ctx.group_id)
        config["animation_effect"] = "none"
        config["use_animations"] = False
        self.set_config(ctx.group_id, config)
        
        builder = InlineKeyboardBuilder()
        builder.row(builder.button(text="✅ Done", callback_data="deco_close"))
        
        await callback.message.edit_text(
            "🚫 Animations disabled.\n\n"
            "Buttons will no longer animate.",
            reply_markup=builder.as_markup()
        )

    async def _toggle_color_coding(self, callback: CallbackQuery, ctx: NexusContext):
        """Toggle color-coded buttons."""
        config = self.get_config(ctx.group_id)
        config["use_color_coding"] = not config.get("use_color_coding", False)
        self.set_config(ctx.group_id, config)
        
        status = "enabled" if config["use_color_coding"] else "disabled"
        
        builder = InlineKeyboardBuilder()
        builder.row(builder.button(text="✅ Done", callback_data="deco_close"))
        
        await callback.message.edit_text(
            f"🎨 Color-coding {status}.\n\n"
            f"Buttons will be colored based on their action type.",
            reply_markup=builder.as_markup()
        )

    async def _show_color_decorations(self, callback: CallbackQuery, ctx: NexusContext, color_key: str):
        """Show decorations for a color category."""
        if color_key not in BUTTON_COLORS:
            await callback.answer("Color not found")
            return
        
        color = BUTTON_COLORS[color_key]
        builder = InlineKeyboardBuilder()
        
        for deco_key, deco in color["decorations"].items():
            preview = self._apply_decoration("Button", deco["prefix"], deco["suffix"])
            builder.row(
                builder.button(text=preview, callback_data=f"color_apply:{color_key}:{deco_key}")
            )
        
        builder.row(builder.button(text="◀️ Back", callback_data="color_back"))
        
        await callback.message.edit_text(
            f"{color['icon']} <b>{color['name']} Buttons</b>\n\n"
            f"Select a decoration:",
            reply_markup=builder.as_markup()
        )

    async def _toggle_seasonal(self, callback: CallbackQuery, ctx: NexusContext):
        """Toggle seasonal auto-changing decorations."""
        config = self.get_config(ctx.group_id)
        config["auto_seasonal"] = not config.get("auto_seasonal", False)
        self.set_config(ctx.group_id, config)
        
        status = "enabled" if config["auto_seasonal"] else "disabled"
        
        builder = InlineKeyboardBuilder()
        builder.row(builder.button(text="✅ Done", callback_data="deco_close"))
        
        await callback.message.edit_text(
            f"❄️ Seasonal decorations {status}.\n\n"
            f"Decorations will automatically change based on the time of year.",
            reply_markup=builder.as_markup()
        )

    async def _set_season(self, callback: CallbackQuery, ctx: NexusContext, season: str):
        """Set specific season or auto."""
        config = self.get_config(ctx.group_id)
        
        if season == "auto":
            config["seasonal_override"] = None
            config["auto_seasonal"] = True
            season_name = "Auto (Based on date)"
        else:
            config["seasonal_override"] = season
            config["auto_seasonal"] = True
            season_name = SEASONAL_DECORATIONS.get(season, {}).get("name", season)
        
        self.set_config(ctx.group_id, config)
        
        builder = InlineKeyboardBuilder()
        builder.row(builder.button(text="✅ Done", callback_data="deco_close"))
        
        await callback.message.edit_text(
            f"✅ Season set to: <b>{season_name}</b>",
            reply_markup=builder.as_markup()
        )

    async def _select_premium_pack(self, callback: CallbackQuery, ctx: NexusContext, pack_key: str):
        """Select a premium pack."""
        if pack_key not in PREMIUM_PACKS:
            await callback.answer("Pack not found")
            return
        
        config = self.get_config(ctx.group_id)
        
        if "premium_packs_enabled" not in config:
            config["premium_packs_enabled"] = {}
        
        # Toggle pack
        current = config["premium_packs_enabled"].get(pack_key, False)
        config["premium_packs_enabled"][pack_key] = not current
        
        self.set_config(ctx.group_id, config)
        
        pack = PREMIUM_PACKS[pack_key]
        status = "enabled" if config["premium_packs_enabled"][pack_key] else "disabled"
        
        builder = InlineKeyboardBuilder()
        builder.row(builder.button(text="✅ Done", callback_data="deco_close"))
        
        await callback.message.edit_text(
            f"👑 {pack['name']} pack {status}.\n\n"
            f"You can now use these exclusive decorations!",
            reply_markup=builder.as_markup()
        )

    async def _handle_user_decoration(self, callback: CallbackQuery, ctx: NexusContext):
        """Handle user decoration preferences."""
        data = callback.data
        config = self.get_config(ctx.group_id)
        user_id = ctx.user_id
        
        if "user_preferences" not in config:
            config["user_preferences"] = {}
        
        if data == "userdeco_default":
            # Reset to group default
            if user_id in config["user_preferences"]:
                del config["user_preferences"][user_id]
            self.set_config(ctx.group_id, config)
            
            await callback.message.edit_text(
                "🔰 Your decoration preference has been reset to group default.",
                reply_markup=None
            )
        elif data.startswith("userdeco_cat:"):
            cat_key = data.split(":", 1)[1]
            await self._show_user_category_decorations(callback, ctx, cat_key)

    async def _show_user_category_decorations(self, callback: CallbackQuery, ctx: NexusContext, cat_key: str):
        """Show decorations for user preference selection."""
        if cat_key not in DECORATION_CATEGORIES:
            await callback.answer("Category not found")
            return
        
        category = DECORATION_CATEGORIES[cat_key]
        builder = InlineKeyboardBuilder()
        
        for deco_key, deco in category["decorations"].items():
            preview = self._apply_decoration("Button", deco["prefix"], deco["suffix"])
            builder.row(
                builder.button(text=preview, callback_data=f"userdeco_apply:{cat_key}:{deco_key}")
            )
        
        builder.row(builder.button(text="◀️ Back", callback_data="userdeco_back"))
        
        await callback.message.edit_text(
            f"👤 <b>Your Decoration</b> - {category['name']}\n\n"
            f"Select your personal preference:",
            reply_markup=builder.as_markup()
        )

    async def _handle_marketplace(self, callback: CallbackQuery, ctx: NexusContext):
        """Handle marketplace actions."""
        data = callback.data
        
        if data == "marketplace_create":
            await callback.message.edit_text(
                "🏪 <b>Create Marketplace Listing</b>\n\n"
                "Use `/customdecoration <name> <prefix> <suffix>` to create a custom decoration, "
                "then share it with the marketplace.",
                reply_markup=None
            )
        elif data.startswith("marketplace_view:"):
            listing_id = data.split(":", 1)[1]
            config = self.get_config(ctx.group_id)
            listing = config.get("marketplace_listings", {}).get(listing_id)
            
            if listing:
                builder = InlineKeyboardBuilder()
                builder.row(
                    builder.button(text="📥 Import", callback_data=f"marketplace_import:{listing_id}"),
                    builder.button(text="🗑️ Delete", callback_data=f"marketplace_delete:{listing_id}"),
                )
                builder.row(builder.button(text="◀️ Back", callback_data="marketplace_back"))
                
                await callback.message.edit_text(
                    f"🛒 <b>{listing.get('name', 'Listing')}</b>\n\n"
                    f"Prefix: {listing.get('prefix', '')}\n"
                    f"Suffix: {listing.get('suffix', '')}\n\n"
                    f"By: {listing.get('author', 'Unknown')}",
                    reply_markup=builder.as_markup()
                )

    async def _handle_legacy_callback(self, callback: CallbackQuery, ctx: NexusContext):
        """Handle legacy callback patterns."""
        parts = callback.data.split(":")
        action = parts[0]
        
        if action == "deco_cat":
            cat_key = parts[1]
            if cat_key == "back":
                await self.cmd_decorations(ctx, [])
            else:
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
        elif action == "color_back":
            await self.cmd_colorbuttons(ctx, [])
            await callback.answer()
        elif action == "userdeco_back":
            await self.cmd_mydecoration(ctx, [])
            await callback.answer()
        elif action == "userdeco_apply":
            cat_key = parts[1]
            deco_key = parts[2]
            await self._apply_user_decoration(callback, ctx, cat_key, deco_key)
            await callback.answer()
        elif data.startswith("color_apply:"):
            apply_parts = data.split(":")
            color_key = apply_parts[1]
            deco_key = apply_parts[2]
            await self._apply_color_decoration(callback, ctx, color_key, deco_key)
            await callback.answer()
        elif action == "marketplace_back":
            await self.cmd_marketplace(ctx, [])
            await callback.answer()

    async def _apply_user_decoration(self, callback: CallbackQuery, ctx: NexusContext, cat_key: str, deco_key: str):
        """Apply user-specific decoration preference."""
        config = self.get_config(ctx.group_id)
        user_id = ctx.user_id
        
        if "user_preferences" not in config:
            config["user_preferences"] = {}
        
        config["user_preferences"][user_id] = {
            "decoration": f"{cat_key}:{deco_key}"
        }
        
        self.set_config(ctx.group_id, config)
        
        deco_name = DECORATION_CATEGORIES[cat_key]["decorations"][deco_key]["name"]
        
        builder = InlineKeyboardBuilder()
        builder.row(builder.button(text="✅ Done", callback_data="deco_close"))
        
        await callback.message.edit_text(
            f"✅ Your decoration preference set to: <b>{deco_name}</b>",
            reply_markup=builder.as_markup()
        )

    async def _apply_color_decoration(self, callback: CallbackQuery, ctx: NexusContext, color_key: str, deco_key: str):
        """Apply color-coded decoration."""
        config = self.get_config(ctx.group_id)
        
        if "color_by_action" not in config:
            config["color_by_action"] = {}
        
        # Apply to common actions
        default_actions = {
            "danger": ["ban", "kick", "block", "warn"],
            "success": ["approve", "accept", "unban", "unmute"],
            "warning": ["warn", "alert"],
            "info": ["help", "info"],
            "primary": ["star", "crown"],
            "neutral": ["default"]
        }
        
        if color_key in default_actions:
            deco = BUTTON_COLORS[color_key]["decorations"].get(deco_key, {})
            for action in default_actions[color_key]:
                config["color_by_action"][action] = f"{color_key}:{deco_key}"
        
        config["use_color_coding"] = True
        self.set_config(ctx.group_id, config)
        
        color = BUTTON_COLORS[color_key]
        builder = InlineKeyboardBuilder()
        builder.row(builder.button(text="✅ Done", callback_data="deco_close"))
        
        await callback.message.edit_text(
            f"✅ Color-coded buttons set to: <b>{color['name']}</b>\n\n"
            f"Buttons matching action types will use this color.",
            reply_markup=builder.as_markup()
        )

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

    def _get_decoration_name(self, decoration: str) -> str:
        """Get human-readable decoration name."""
        if decoration == "minimal:none" or not decoration:
            return "None"
        
        if ":" in decoration:
            cat_key, deco_key = decoration.split(":")
            
            # Check standard categories
            if cat_key in DECORATION_CATEGORIES and deco_key in DECORATION_CATEGORIES[cat_key]["decorations"]:
                return DECORATION_CATEGORIES[cat_key]["decorations"][deco_key]["name"]
            
            # Check seasonal
            if cat_key in SEASONAL_DECORATIONS and deco_key in SEASONAL_DECORATIONS[cat_key]["decorations"]:
                return SEASONAL_DECORATIONS[cat_key]["decorations"][deco_key]["name"]
            
            # Check premium
            if cat_key in PREMIUM_PACKS and deco_key in PREMIUM_PACKS[cat_key]["decorations"]:
                return PREMIUM_PACKS[cat_key]["decorations"][deco_key]["name"]
            
            # Check colors
            if cat_key in BUTTON_COLORS and deco_key in BUTTON_COLORS[cat_key]["decorations"]:
                return BUTTON_COLORS[cat_key]["decorations"][deco_key]["name"]
        
        return decoration

    def _get_current_season(self) -> str:
        """Get current season based on date."""
        now = datetime.now()
        month = now.month
        
        # Check special events first
        if month == 10:  # October
            return "🎃 Halloween"
        elif month == 12:  # December
            return "🎄 Christmas"
        elif month == 1:  # January
            return "🎉 New Year"
        elif month == 2:  # February
            return "💕 Valentine"
        
        # Regular seasons
        if month in [3, 4, 5]:
            return "🌸 Spring"
        elif month in [6, 7, 8]:
            return "☀️ Summer"
        elif month in [9, 10, 11]:
            return "🍁 Autumn"
        else:
            return "❄️ Winter"

    def _get_seasonal_decoration(self, group_id: int) -> Optional[Dict[str, str]]:
        """Get the seasonal decoration for the current time."""
        config = self.get_config(group_id)
        
        # Check for seasonal override
        override = config.get("seasonal_override")
        if override and override in SEASONAL_DECORATIONS:
            season = SEASONAL_DECORATIONS[override]
            # Get first decoration in the season
            deco_key = list(season["decorations"].keys())[0]
            return season["decorations"][deco_key]
        
        # Auto-detect season
        now = datetime.now()
        month = now.month
        
        # Check special events
        special_events = {
            10: "halloween",
            12: "christmas",
            1: "newyear",
            2: "valentine"
        }
        
        if month in special_events:
            season_key = special_events[month]
            if season_key in SEASONAL_DECORATIONS:
                season = SEASONAL_DECORATIONS[season_key]
                deco_key = list(season["decorations"].keys())[0]
                return season["decorations"][deco_key]
        
        # Regular seasons
        if month in [3, 4, 5]:
            season_key = "spring"
        elif month in [6, 7, 8]:
            season_key = "summer"
        elif month in [9, 10, 11]:
            season_key = "autumn"
        else:
            season_key = "winter"
        
        if season_key in SEASONAL_DECORATIONS:
            season = SEASONAL_DECORATIONS[season_key]
            deco_key = list(season["decorations"].keys())[0]
            return season["decorations"][deco_key]
        
        return None

    def apply_decoration(self, text: str, group_id: int, user_id: Optional[int] = None) -> str:
        """
        Apply decoration to button text.
        
        Args:
            text: Original button text
            group_id: Group ID
            user_id: Optional user ID for user-specific preferences
            
        Returns:
            Decorated button text
        """
        config = self.get_config(group_id)
        
        if not config.get("enabled", False):
            return text
        
        # Check for user-specific preference first
        if user_id and config.get("user_preferences"):
            user_pref = config["user_preferences"].get(user_id, {})
            if user_pref.get("decoration") and user_pref["decoration"] != "default":
                user_decoration = user_pref["decoration"]
                if ":" in user_decoration:
                    cat_key, deco_key = user_decoration.split(":")
                    if cat_key in DECORATION_CATEGORIES and deco_key in DECORATION_CATEGORIES[cat_key]["decorations"]:
                        deco = DECORATION_CATEGORIES[cat_key]["decorations"][deco_key]
                        return self._apply_decoration(text, deco["prefix"], deco["suffix"], config.get("position", "both"))
        
        # Check for seasonal auto-change
        if config.get("auto_seasonal", False):
            seasonal_deco = self._get_seasonal_decoration(group_id)
            if seasonal_deco:
                return self._apply_decoration(text, seasonal_deco["prefix"], seasonal_deco["suffix"], config.get("position", "both"))
        
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
            
            # Check standard categories
            if cat_key in DECORATION_CATEGORIES and deco_key in DECORATION_CATEGORIES[cat_key]["decorations"]:
                deco = DECORATION_CATEGORIES[cat_key]["decorations"][deco_key]
                return self._apply_decoration(text, deco["prefix"], deco["suffix"], position)
            
            # Check premium packs
            premium_enabled = config.get("premium_packs_enabled", {})
            if cat_key in PREMIUM_PACKS and premium_enabled.get(cat_key, False):
                if deco_key in PREMIUM_PACKS[cat_key]["decorations"]:
                    deco = PREMIUM_PACKS[cat_key]["decorations"][deco_key]
                    return self._apply_decoration(text, deco["prefix"], deco["suffix"], position)
        
        return text

    def apply_animation(self, text: str, group_id: int) -> str:
        """
        Apply animation frame to text.
        
        Args:
            text: Original button text
            group_id: Group ID
            
        Returns:
            Text with animation frame applied
        """
        config = self.get_config(group_id)
        
        if not config.get("use_animations", False):
            return text
        
        animation_effect = config.get("animation_effect", "none")
        if animation_effect == "none" or animation_effect not in ANIMATED_DECORATIONS:
            return text
        
        anim = ANIMATED_DECORATIONS[animation_effect]
        frames = anim.get("frames", [])
        
        if not frames or isinstance(frames, str):
            return text
        
        # Use current time to determine frame
        import time
        frame_index = int(time.time() / anim.get("frame_duration", 0.5)) % len(frames)
        frame = frames[frame_index]
        
        # Apply frame as decoration
        return self._apply_decoration(text, frame, frame, "both")

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
