"""Module metadata for Button Decorations module."""

module_info = {
    "name": "button_decorations",
    "version": "1.1.0",
    "author": "Nexus Team",
    "description": "Add beautiful emoji decorations to inline keyboard buttons with animations, color-coding, seasonal themes, premium packs, and marketplace sharing!",
    "category": "utility",
    "enabled_by_default": False,
    "configurable": True,
    "permissions": {
        "admin_only": ["setdecoration", "customdecoration", "animations", "colorbuttons", "seasonal"],
        "user_allowed": ["decorations", "premiumpacks", "marketplace", "mydecoration"],
    },
    "dependencies": [],
    "features": [
        # Standard features
        "6 decoration categories (Nature, Animals, Objects, Symbols, Food, Minimal)",
        "20+ predefined decoration styles",
        "Custom decoration creation",
        "Per-group configuration",
        "Easy integration with existing keyboards",
        "Predefined button sets",
        "Live preview in demo mode",
        # New features
        "Animated button decorations (10+ animation effects)",
        "Color-coded buttons based on action type",
        "User-specific decoration preferences",
        "Seasonal auto-changing decorations (with special events)",
        "Decoration marketplace/sharing",
        "Premium decoration packs (Gold, Neon, Cosmic, Mythical)",
        "Button animation effects (pulse, sparkle, rainbow, fire, etc.)",
    ],
    "commands": [
        {
            "name": "decorations",
            "aliases": ["deco", "buttons"],
            "description": "Browse and select button decorations (main menu)",
            "admin_only": False,
        },
        {
            "name": "setdecoration",
            "aliases": ["setdeco"],
            "description": "Set decoration for the group",
            "admin_only": True,
        },
        {
            "name": "customdecoration",
            "aliases": ["customdeco"],
            "description": "Create custom button decoration",
            "admin_only": True,
        },
        {
            "name": "animations",
            "aliases": ["anims", "anim"],
            "description": "View and select button animations",
            "admin_only": True,
        },
        {
            "name": "colorbuttons",
            "aliases": ["colors", "btncolor"],
            "description": "Configure color-coded buttons by action type",
            "admin_only": True,
        },
        {
            "name": "seasonal",
            "aliases": ["season"],
            "description": "Configure seasonal auto-changing decorations",
            "admin_only": True,
        },
        {
            "name": "premiumpacks",
            "aliases": ["premium", "packs"],
            "description": "Browse premium decoration packs",
            "admin_only": False,
        },
        {
            "name": "marketplace",
            "aliases": ["shop", "store"],
            "description": "Browse decoration marketplace",
            "admin_only": False,
        },
        {
            "name": "mydecoration",
            "aliases": ["mydeco", "userdeco"],
            "description": "Set your personal decoration preference",
            "admin_only": False,
        },
    ],
    "settings": {
        "enabled": {
            "type": "boolean",
            "default": False,
            "description": "Enable button decorations for this group",
        },
        "default_decoration": {
            "type": "string",
            "default": "minimal:none",
            "description": "Default decoration style (format: category:decoration)",
        },
        "position": {
            "type": "select",
            "default": "both",
            "options": ["prefix", "suffix", "both"],
            "description": "Decoration position",
        },
        "apply_to_all": {
            "type": "boolean",
            "default": False,
            "description": "Apply to all buttons",
        },
        "use_animations": {
            "type": "boolean",
            "default": False,
            "description": "Enable animated button decorations",
        },
        "animation_effect": {
            "type": "select",
            "default": "none",
            "options": ["none", "pulse", "sparkle", "rainbow", "fire", "aurora", "galaxy", "hearts", "stars", "bounce"],
            "description": "Animation effect type",
        },
        "animation_speed": {
            "type": "number",
            "default": 0.5,
            "description": "Animation speed in seconds per frame",
        },
        "use_color_coding": {
            "type": "boolean",
            "default": False,
            "description": "Enable color-coded buttons based on action type",
        },
        "color_by_action": {
            "type": "json",
            "default": {},
            "description": "Action to color mapping",
        },
        "auto_seasonal": {
            "type": "boolean",
            "default": False,
            "description": "Automatically change decorations based on season",
        },
        "seasonal_override": {
            "type": "string",
            "default": None,
            "description": "Force specific season (spring/summer/autumn/winter)",
        },
        "premium_packs_enabled": {
            "type": "json",
            "default": {},
            "description": "Enabled premium packs",
        },
        "user_preferences": {
            "type": "json",
            "default": {},
            "description": "User-specific decoration preferences",
        },
        "marketplace_listings": {
            "type": "json",
            "default": {},
            "description": "Shared marketplace listings",
        },
    },
}
