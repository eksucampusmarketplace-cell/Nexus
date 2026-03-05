"""Module metadata for Button Decorations module."""

module_info = {
    "name": "button_decorations",
    "version": "1.0.0",
    "author": "Nexus Team",
    "description": "Add beautiful emoji decorations to inline keyboard buttons - customize with nature, animals, objects, symbols, and more!",
    "category": "utility",
    "enabled_by_default": False,
    "configurable": True,
    "permissions": {
        "admin_only": ["setdecoration", "customdecoration"],
        "user_allowed": ["decorations"],
    },
    "dependencies": [],
    "features": [
        "6 decoration categories (Nature, Animals, Objects, Symbols, Food, Minimal)",
        "20+ predefined decoration styles",
        "Custom decoration creation",
        "Per-group configuration",
        "Easy integration with existing keyboards",
        "Predefined button sets",
        "Live preview in demo mode",
    ],
    "commands": [
        {
            "name": "decorations",
            "aliases": ["deco", "buttons"],
            "description": "Browse and select button decorations",
            "admin_only": True,
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
    },
}
