"""
Button Decorations Module - Interactive Demo

This demonstrates all features of the button decorations system.
Run this in a group with the bot to see decorations in action!
"""

from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.core.context import NexusContext
from bot.modules.button_decorations.decorated_builder import (
    DecoratedInlineKeyboardBuilder,
    DecoratedKeyboardLayout,
    create_button_set,
)
from bot.modules.button_decorations.module import apply_button_decoration, DECORATION_CATEGORIES


async def cmd_buttontest(ctx: NexusContext, args: list):
    """Main demo command - showcases all decoration features."""
    
    # Create main demo menu
    builder = InlineKeyboardBuilder()
    
    builder.row(
        builder.button(
            text=apply_button_decoration("🎨 Browse Decorations", ctx.group_id),
            callback_data="demo_browse"
        )
    )
    
    builder.row(
        builder.button(
            text=apply_button_decoration("🔮 Quick Demo", ctx.group_id),
            callback_data="demo_quick"
        )
    )
    
    builder.row(
        builder.button(
            text=apply_button_decoration("🧪 Test Custom", ctx.group_id),
            callback_data="demo_custom"
        )
    )
    
    builder.row(
        builder.button(
            text=apply_button_decoration("📊 All Categories", ctx.group_id),
            callback_data="demo_categories"
        )
    )
    
    builder.row(
        builder.button(
            text=apply_button_decoration("🎯 Preset Buttons", ctx.group_id),
            callback_data="demo_presets"
        )
    )
    
    await ctx.send(
        "🎨 <b>Button Decorations Demo</b>\n\n"
        "Explore all the beautiful decoration options available for your bot!\n\n"
        "Use /setdecoration to change styles",
        reply_markup=builder.as_markup()
    )


async def demo_browse(ctx: NexusContext):
    """Show browse decorations menu."""
    
    builder = InlineKeyboardBuilder()
    
    # Add category buttons
    for cat_key, category in DECORATION_CATEGORIES.items():
        builder.row(
            builder.button(
                text=apply_button_decoration(
                    f"{category['icon']} {category['name']}",
                    ctx.group_id
                ),
                callback_data=f"demo_cat:{cat_key}"
            )
        )
    
    builder.row(
        builder.button(
            text=apply_button_decoration("◀️ Back to Demo", ctx.group_id),
            callback_data="demo_main"
        )
    )
    
    await ctx.send(
        "🌸 <b>Browse Decorations</b>\n\n"
        "Select a category to see available decorations:",
        reply_markup=builder.as_markup()
    )


async def demo_show_category(ctx: NexusContext, cat_key: str):
    """Show decorations in a category with live preview."""
    
    if cat_key not in DECORATION_CATEGORIES:
        await ctx.send("Category not found!")
        return
    
    category = DECORATION_CATEGORIES[cat_key]
    
    builder = InlineKeyboardBuilder()
    
    # Show each decoration with preview
    for deco_key, deco in category["decorations"].items():
        preview = apply_button_decoration("Example Button", ctx.group_id)
        
        # Temporarily set this decoration for preview
        from bot.modules.button_decorations.module import get_decoration_module
        deco_module = get_decoration_module()
        
        if deco_module:
            config = deco_module.get_config(ctx.group_id)
            original = config.get("default_decoration", "minimal:none")
            
            # Preview with this decoration
            config["default_decoration"] = f"{cat_key}:{deco_key}"
            config["enabled"] = True
            deco_module.set_config(ctx.group_id, config)
            
            preview = apply_button_decoration("Example Button", ctx.group_id)
            
            # Restore original
            config["default_decoration"] = original
            deco_module.set_config(ctx.group_id, config)
        
        builder.row(
            builder.button(
                text=preview,
                callback_data=f"demo_select:{cat_key}:{deco_key}"
            )
        )
    
    builder.row(
        builder.button(
            text=apply_button_decoration("◀️ Back to Categories", ctx.group_id),
            callback_data="demo_browse"
        )
    )
    
    await ctx.send(
        f"{category['icon']} <b>{category['name']}</b>\n\n"
        f"Tap any decoration to try it out!",
        reply_markup=builder.as_markup()
    )


async def demo_quick(ctx: NexusContext):
    """Quick demo - show various button styles."""
    
    layout = DecoratedKeyboardLayout(group_id=ctx.group_id)
    
    layout.add_section("Primary Actions")
    layout.add_button("Confirm", callback="confirm", icon="✅")
    layout.add_button("Cancel", callback="cancel", icon="❌")
    
    layout.add_section("Secondary Actions")
    layout.add_button("View Details", callback="details", icon="📄")
    layout.add_button("Settings", callback="settings", icon="⚙️")
    layout.add_button("Help", callback="help", icon="❓")
    
    layout.add_section("Navigation")
    layout.add_button("Back", callback="back", icon="◀️")
    layout.add_button("Next", callback="next", icon="▶️")
    layout.add_button("Close", callback="close", icon="❌")
    
    await ctx.send(
        "🔮 <b>Quick Demo</b>\n\n"
        "Here are various button types with decorations applied:",
        reply_markup=layout.build()
    )


async def demo_custom(ctx: NexusContext):
    """Test custom decorations."""
    
    builder = InlineKeyboardBuilder()
    
    # Create some test custom decorations
    from bot.modules.button_decorations.module import get_decoration_module
    deco_module = get_decoration_module()
    
    if deco_module:
        config = deco_module.get_config(ctx.group_id)
        
        # Set up some fun custom decorations
        test_decorations = {
            "rainbow": {"name": "Rainbow", "prefix": "🌈", "suffix": "🦄"},
            "magic": {"name": "Magic", "prefix": "🔮", "suffix": "✨"},
            "robot": {"name": "Robot", "prefix": "🤖", "suffix": "⚙️"},
            "party": {"name": "Party", "prefix": "🎉", "suffix": "🎊"},
        }
        
        config["custom_decorations"] = test_decorations
        deco_module.set_config(ctx.group_id, config)
    
    # Show custom decoration options
    for custom_name, custom_deco in test_decorations.items():
        preview = apply_button_decoration("Test Button", ctx.group_id)
        
        # Temporarily apply custom decoration
        if deco_module:
            config = deco_module.get_config(ctx.group_id)
            original = config.get("default_decoration", "minimal:none")
            config["default_decoration"] = f"custom:{custom_name}"
            config["enabled"] = True
            deco_module.set_config(ctx.group_id, config)
            
            preview = apply_button_decoration("Test Button", ctx.group_id)
            
            # Restore
            config["default_decoration"] = original
            deco_module.set_config(ctx.group_id, config)
        
        builder.row(
            builder.button(
                text=preview,
                callback_data=f"demo_custom_select:{custom_name}"
            )
        )
    
    builder.row(
        builder.button(
            text=apply_button_decoration("◀️ Back to Demo", ctx.group_id),
            callback_data="demo_main"
        )
    )
    
    await ctx.send(
        "🧪 <b>Custom Decorations</b>\n\n"
        "Try these fun custom decorations:",
        reply_markup=builder.as_markup()
    )


async def demo_categories(ctx: NexusContext):
    """Show all decoration categories with examples."""
    
    builder = InlineKeyboardBuilder()
    
    # Showcase different categories with context
    examples = [
        ("Nature", "nature:flowers", "🌻"),
        ("Animals", "animals:lions", "🦁"),
        ("Objects", "objects:stars", "⭐"),
        ("Symbols", "symbols:diamonds", "💎"),
        ("Food", "food:fruits", "🍎"),
    ]
    
    for name, deco, icon in examples:
        from bot.modules.button_decorations.module import get_decoration_module
        deco_module = get_decoration_module()
        
        if deco_module:
            config = deco_module.get_config(ctx.group_id)
            original = config.get("default_decoration", "minimal:none")
            
            # Apply decoration for preview
            config["default_decoration"] = deco
            config["enabled"] = True
            deco_module.set_config(ctx.group_id, config)
            
            preview = apply_button_decoration(f"{icon} {name}", ctx.group_id)
            
            # Restore
            config["default_decoration"] = original
            deco_module.set_config(ctx.group_id, config)
        
        builder.row(
            builder.button(
                text=preview,
                callback_data=f"demo_select:{deco}"
            )
        )
    
    builder.row(
        builder.button(
            text=apply_button_decoration("◀️ Back to Demo", ctx.group_id),
            callback_data="demo_main"
        )
    )
    
    await ctx.send(
        "📊 <b>All Decoration Categories</b>\n\n"
        "Each category has its own style and personality!",
        reply_markup=builder.as_markup()
    )


async def demo_presets(ctx: NexusContext):
    """Show preset button sets."""
    
    builder = InlineKeyboardBuilder()
    
    builder.row(
        builder.button(
            text=apply_button_decoration("🛡️ Moderation Set", ctx.group_id),
            callback_data="demo_preset:moderation"
        )
    )
    
    builder.row(
        builder.button(
            text=apply_button_decoration("✅ Confirmation Set", ctx.group_id),
            callback_data="demo_preset:confirmation"
        )
    )
    
    builder.row(
        builder.button(
            text=apply_button_decoration("🧭 Navigation Set", ctx.group_id),
            callback_data="demo_preset:navigation"
        )
    )
    
    builder.row(
        builder.button(
            text=apply_button_decoration("◀️ Back to Demo", ctx.group_id),
            callback_data="demo_main"
        )
    )
    
    await ctx.send(
        "🎯 <b>Preset Button Sets</b>\n\n"
        "Pre-built button collections for common use cases:",
        reply_markup=builder.as_markup()
    )


async def demo_show_preset(ctx: NexusContext, preset_name: str):
    """Show a specific preset button set."""
    
    markup = create_button_set(ctx.group_id, preset_name)
    
    descriptions = {
        "moderation": "Common moderation actions for managing users",
        "confirmation": "Yes/No dialogs for confirming actions",
        "navigation": "Navigation buttons for multi-step flows"
    }
    
    await ctx.send(
        f"🎯 <b>{preset_name.title()} Set</b>\n\n"
        f"{descriptions.get(preset_name, '')}",
        reply_markup=markup
    )


# Demo callback handler
async def handle_demo_callback(ctx: NexusContext, callback_data: str):
    """Handle all demo callback queries."""
    
    if callback_data == "demo_main":
        await cmd_buttontest(ctx, [])
    elif callback_data == "demo_browse":
        await demo_browse(ctx)
    elif callback_data == "demo_quick":
        await demo_quick(ctx)
    elif callback_data == "demo_custom":
        await demo_custom(ctx)
    elif callback_data == "demo_categories":
        await demo_categories(ctx)
    elif callback_data == "demo_presets":
        await demo_presets(ctx)
    elif callback_data.startswith("demo_cat:"):
        cat_key = callback_data.split(":")[1]
        await demo_show_category(ctx, cat_key)
    elif callback_data.startswith("demo_select:"):
        parts = callback_data.split(":")
        cat_key = parts[1]
        deco_key = parts[2]
        await select_demo_decoration(ctx, cat_key, deco_key)
    elif callback_data.startswith("demo_custom_select:"):
        custom_name = callback_data.split(":")[1]
        await select_custom_demo_decoration(ctx, custom_name)
    elif callback_data.startswith("demo_preset:"):
        preset_name = callback_data.split(":")[1]
        await demo_show_preset(ctx, preset_name)


async def select_demo_decoration(ctx: NexusContext, cat_key: str, deco_key: str):
    """Apply selected decoration and show confirmation."""
    
    from bot.modules.button_decorations.module import get_decoration_module
    deco_module = get_decoration_module()
    
    if not deco_module:
        await ctx.send("Decoration module not available")
        return
    
    decoration = f"{cat_key}:{deco_key}"
    config = deco_module.get_config(ctx.group_id)
    
    config["default_decoration"] = decoration
    config["enabled"] = True
    deco_module.set_config(ctx.group_id, config)
    
    if cat_key in DECORATION_CATEGORIES:
        deco_name = DECORATION_CATEGORIES[cat_key]["decorations"].get(deco_key, {}).get("name", deco_key)
        
        # Show before/after example
        builder = InlineKeyboardBuilder()
        
        before = "Button Text"
        after = apply_button_decoration("Button Text", ctx.group_id)
        
        builder.row(
            builder.button(
                text=apply_button_decoration("✅ Great!", ctx.group_id),
                callback_data="demo_browse"
            )
        )
        
        builder.row(
            builder.button(
                text=apply_button_decoration("🔄 Try Another", ctx.group_id),
                callback_data="demo_browse"
            )
        )
        
        builder.row(
            builder.button(
                text=apply_button_decoration("◀️ Back to Demo", ctx.group_id),
                callback_data="demo_main"
            )
        )
        
        await ctx.send(
            f"✅ <b>Decoration Applied!</b>\n\n"
            f"Style: {deco_name}\n\n"
            f"<b>Before:</b>\n{before}\n\n"
            f"<b>After:</b>\n{after}\n\n"
            f"All your bot's buttons now use this style!",
            reply_markup=builder.as_markup()
        )


async def select_custom_demo_decoration(ctx: NexusContext, custom_name: str):
    """Apply selected custom decoration."""
    
    from bot.modules.button_decorations.module import get_decoration_module
    deco_module = get_decoration_module()
    
    if not deco_module:
        await ctx.send("Decoration module not available")
        return
    
    decoration = f"custom:{custom_name}"
    config = deco_module.get_config(ctx.group_id)
    
    config["default_decoration"] = decoration
    config["enabled"] = True
    deco_module.set_config(ctx.group_id, config)
    
    custom_decorations = config.get("custom_decorations", {})
    custom = custom_decorations.get(custom_name, {})
    
    after = apply_button_decoration("Button Text", ctx.group_id)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        builder.button(
            text=apply_button_decoration("✅ Awesome!", ctx.group_id),
            callback_data="demo_main"
        )
    )
    
    await ctx.send(
        f"✅ <b>Custom Decoration Applied!</b>\n\n"
        f"Name: {custom_name}\n"
        f"Prefix: {custom.get('prefix', '')}\n"
        f"Suffix: {custom.get('suffix', '')}\n\n"
        f"<b>Result:</b>\n{after}\n\n"
        f"Create more with: /customdecoration <name> <prefix> <suffix>",
        reply_markup=builder.as_markup()
    )


# Command registration
def register_demo_commands():
    """Register demo commands with the module."""
    
    return {
        "buttontest": {
            "description": "Interactive button decorations demo",
            "handler": cmd_buttontest,
            "admin_only": False
        }
    }


def get_demo_callback_handler():
    """Get the demo callback handler."""
    return handle_demo_callback


# Demo message templates
DEMO_MESSAGES = {
    "intro": """
🎨 <b>Welcome to Button Decorations!</b>

This system lets you add beautiful emoji decorations to all your bot's inline keyboard buttons.

<b>Quick Start:</b>
• /decorations - Browse and select decorations
• /setdecoration nature:flowers - Set decoration directly
• /customdecoration mycool ⚡ ⚡ - Create custom style

<b>Categories Available:</b>
🌿 Nature - Flowers, trees, plants
🦁 Animals - Lions, cats, dogs, birds
✨ Objects - Stars, hearts, gems, crowns
🔷 Symbols - Arrows, checkmarks, diamonds
🍔 Food - Fruits, candy, fast food
⚪ Minimal - Clean, simple options

Tap below to explore!
    """,
    
    "categories": """
📋 <b>All Decoration Categories</b>

<b>🌿 Nature</b>
Flowers, trees, plants, leaves, seasonal

<b>🦁 Animals</b>
Lions, cats, dogs, birds, ocean, wild

<b>✨ Objects</b>
Stars, hearts, gems, crowns, sparkles, fire

<b>🔷 Symbols</b>
Arrows, checkmarks, bullets, diamonds, squares

<b>🍔 Food</b>
Fruits, drinks, candy, fast food

<b>⚪ Minimal</b>
None, simple, dots, clean

Each category has multiple decoration styles to choose from!
    """,
    
    "tips": """
💡 <b>Pro Tips</b>

1. <b>Match Your Theme</b>
   • Welcome groups → Nature or Hearts
   • Admin groups → Crowns or Checkmarks
   • Gaming groups → Stars or Animals
   • Economy → Gems or Sparkles

2. <b>Keep It Simple</b>
   Don't over-decorate - minimal is often better!

3. <b>Test Before Committing</b>
   Try different styles before settling on one.

4. <b>Consider Your Users</b>
   Some may prefer minimal decorations.

5. <b>Be Consistent</b>
   Use the same decoration throughout your bot.
    """
}
