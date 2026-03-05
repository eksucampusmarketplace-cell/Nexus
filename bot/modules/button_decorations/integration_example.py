"""
Example: Integrating Button Decorations into existing modules.

This file shows how to integrate the button decorations system
into existing Nexus modules.
"""

from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.core.context import NexusContext
from bot.modules.button_decorations.decorated_builder import (
    DecoratedInlineKeyboardBuilder,
    DecoratedKeyboardLayout,
    create_button_set,
)
from bot.modules.button_decorations.module import apply_button_decoration


# Example 1: Simple decorator approach
# =====================================

async def example_simple_menu(ctx: NexusContext):
    """
    Example: Simple menu with decorated buttons.
    
    This is the easiest way to add decorations - just wrap your button text.
    """
    builder = InlineKeyboardBuilder()
    
    # Original button: "View Stats"
    # With decoration (nature:flowers): "🌸 View Stats 🌺"
    builder.row(
        builder.button(
            text=apply_button_decoration("View Stats", ctx.group_id),
            callback_data="stats"
        ),
        builder.button(
            text=apply_button_decoration("Settings", ctx.group_id),
            callback_data="settings"
        )
    )
    
    builder.row(
        builder.button(
            text=apply_button_decoration("Help", ctx.group_id),
            callback_data="help"
        )
    )
    
    await ctx.send(
        "📊 <b>Menu</b>\n\nChoose an option:",
        reply_markup=builder.as_markup()
    )


# Example 2: Using DecoratedInlineKeyboardBuilder
# ===============================================

async def example_builder_menu(ctx: NexusContext):
    """
    Example: Using DecoratedInlineKeyboardBuilder for automatic decoration.
    
    This builder automatically applies decorations to all buttons.
    """
    builder = DecoratedInlineKeyboardBuilder(group_id=ctx.group_id)
    
    builder.button(text="Dashboard", callback_data="dashboard")
    builder.button(text="Analytics", callback_data="analytics")
    builder.button(text="Members", callback_data="members")
    
    builder.row()  # New row
    
    builder.button(text="Settings", callback_data="settings")
    builder.button(text="Logout", callback_data="logout")
    
    await ctx.send(
        "🏠 <b>Dashboard</b>",
        reply_markup=builder.as_markup()
    )


# Example 3: Using DecoratedKeyboardLayout
# =========================================

async def example_layout_menu(ctx: NexusContext):
    """
    Example: Using DecoratedKeyboardLayout for structured menus.
    
    Provides section headers and organized button layouts.
    """
    layout = DecoratedKeyboardLayout(group_id=ctx.group_id)
    
    # Section 1
    layout.add_section("User Actions")
    layout.add_button("Profile", callback="profile", icon="👤")
    layout.add_button("Stats", callback="stats", icon="📊")
    
    # Section 2
    layout.add_section("Admin Tools")
    layout.add_button("Moderate", callback="moderate", icon="🛡️")
    layout.add_button("Manage", callback="manage", icon="⚙️")
    
    # Section 3
    layout.add_section("Navigation")
    layout.add_button("Back", callback="back", icon="◀️")
    layout.add_button("Close", callback="close", icon="❌")
    
    await ctx.send(
        "🎛️ <b>Control Panel</b>",
        reply_markup=layout.build()
    )


# Example 4: Using predefined button sets
# =======================================

async def example_button_sets(ctx: NexusContext):
    """
    Example: Using predefined button sets.
    
    Quick way to add common button groups with decorations.
    """
    
    # Confirmation dialog
    confirmation_markup = create_button_set(ctx.group_id, "confirmation")
    
    await ctx.send(
        "⚠️ <b>Are you sure?</b>\n\n"
        "This action cannot be undone.",
        reply_markup=confirmation_markup
    )


# Example 5: Mixed decorated and non-decorated buttons
# ======================================================

async def example_mixed_buttons(ctx: NexusContext):
    """
    Example: Mix of decorated and non-decorated buttons.
    
    Use skip_decoration=True for buttons you don't want decorated.
    """
    builder = DecoratedInlineKeyboardBuilder(group_id=ctx.group_id)
    
    # These will be decorated
    builder.button(text="Yes, proceed", callback_data="confirm")
    builder.button(text="No, cancel", callback_data="cancel")
    
    builder.row()
    
    # This won't be decorated (skip_decoration=True)
    builder.button(
        text="ℹ️ Learn More",
        url="https://example.com/help",
        skip_decoration=True
    )
    
    await ctx.send(
        "Confirm your action:",
        reply_markup=builder.as_markup()
    )


# Example 6: Integrating into an existing module
# ==============================================

async def show_moderation_menu_with_decorations(ctx: NexusContext):
    """
    Example: Enhancing an existing moderation menu with decorations.
    
    Before:
        builder = InlineKeyboardBuilder()
        builder.button(text="Warn", callback_data="warn")
        
    After:
        from bot.modules.button_decorations.module import apply_button_decoration
        builder.button(
            text=apply_button_decoration("Warn", ctx.group_id),
            callback_data="warn"
        )
    """
    builder = InlineKeyboardBuilder()
    
    # Row 1: Moderation actions
    builder.row(
        builder.button(
            text=apply_button_decoration("⚠️ Warn", ctx.group_id),
            callback_data="mod_warn"
        ),
        builder.button(
            text=apply_button_decoration("🔇 Mute", ctx.group_id),
            callback_data="mod_mute"
        )
    )
    
    # Row 2: Severe actions
    builder.row(
        builder.button(
            text=apply_button_decoration("🚫 Ban", ctx.group_id),
            callback_data="mod_ban"
        ),
        builder.button(
            text=apply_button_decoration("👢 Kick", ctx.group_id),
            callback_data="mod_kick"
        )
    )
    
    # Row 3: Un-actions
    builder.row(
        builder.button(
            text=apply_button_decoration("✅ Unban", ctx.group_id),
            callback_data="mod_unban"
        ),
        builder.button(
            text=apply_button_decoration("🔊 Unmute", ctx.group_id),
            callback_data="mod_unmute"
        )
    )
    
    await ctx.send(
        "🛡️ <b>Moderation Actions</b>\n\n"
        "Select an action:",
        reply_markup=builder.as_markup()
    )


# Example 7: Games menu with decorations
# ======================================

async def show_games_menu_with_decorations(ctx: NexusContext):
    """
    Example: Games menu with fun decorations.
    
    Games benefit greatly from colorful decorations!
    """
    builder = InlineKeyboardBuilder()
    
    games = [
        ("🎮 Tic Tac Toe", "game_ttt"),
        ("🎲 Roll Dice", "game_dice"),
        ("🃏 Cards", "game_cards"),
        ("🎯 Guess Number", "game_guess"),
        ("🎰 Slots", "game_slots"),
        ("🧩 Trivia", "game_trivia"),
    ]
    
    for game_name, game_callback in games:
        builder.button(
            text=apply_button_decoration(game_name, ctx.group_id),
            callback_data=game_callback
        )
    
    await ctx.send(
        "🎲 <b>Games</b>\n\n"
        "Choose a game to play:",
        reply_markup=builder.as_markup()
    )


# Example 8: Economy/Shop menu with decorations
# ==============================================

async def show_shop_menu_with_decorations(ctx: NexusContext):
    """
    Example: Shop menu with gem/jewel decorations.
    
    Economy menus look great with objects:gems decoration.
    """
    layout = DecoratedKeyboardLayout(group_id=ctx.group_id)
    
    layout.add_section("💰 Items")
    layout.add_button("Lucky Charm", callback="buy_charm", icon="🍀")
    layout.add_button("VIP Badge", callback="buy_vip", icon="⭐")
    layout.add_button("Power Up", callback="buy_power", icon="⚡")
    
    layout.add_section("🏆 Upgrades")
    layout.add_button("Level Boost", callback="buy_level", icon="📈")
    layout.add_button("XP Multiplier", callback="buy_xp", icon="✨")
    
    layout.add_section("🔙 Navigation")
    layout.add_button("Back", callback="back", icon="◀️")
    
    await ctx.send(
        "🛒 <b>Shop</b>\n\n"
        "Spend your coins on items and upgrades!",
        reply_markup=layout.build()
    )


# Example 9: Conditional decoration based on user role
# ====================================================

async def show_role_based_menu(ctx: NexusContext):
    """
    Example: Different decorations for different user roles.
    
    Admins get crown decoration, members get simple decoration.
    """
    from bot.modules.button_decorations.module import get_decoration_module
    
    decoration_module = get_decoration_module()
    if not decoration_module:
        # Fallback if module not loaded
        return await example_simple_menu(ctx)
    
    # Check user role and apply different decoration
    member = await ctx.get_member()
    is_admin = member and member.role in ["admin", "owner", "moderator"]
    
    if is_admin:
        # Temporarily override decoration for this keyboard
        config = decoration_module.get_config(ctx.group_id)
        original_decoration = config.get("default_decoration", "minimal:none")
        config["default_decoration"] = "objects:crowns"
        decoration_module.set_config(ctx.group_id, config)
        
        # Build menu
        builder = InlineKeyboardBuilder()
        builder.button(text="Admin Panel", callback_data="admin")
        builder.button(text="Manage Users", callback_data="users")
        
        await ctx.send("Admin Menu", reply_markup=builder.as_markup())
        
        # Restore original decoration
        config["default_decoration"] = original_decoration
        decoration_module.set_config(ctx.group_id, config)
    else:
        # Regular member menu
        builder = InlineKeyboardBuilder()
        builder.button(text="My Profile", callback_data="profile")
        builder.button(text="Help", callback_data="help")
        
        await ctx.send("Member Menu", reply_markup=builder.as_markup())


# Example 10: Dynamic decorations based on content
# ================================================

async def show_context_aware_menu(ctx: NexusContext, context_type: str):
    """
    Example: Different decorations based on menu context.
    
    Nature-themed menus get nature decorations, games get fun decorations, etc.
    """
    from bot.modules.button_decorations.module import get_decoration_module
    
    decoration_module = get_decoration_module()
    if not decoration_module:
        return await example_simple_menu(ctx)
    
    # Map context types to decorations
    context_decorations = {
        "welcome": "nature:flowers",
        "moderation": "objects:crowns",
        "games": "objects:stars",
        "economy": "objects:gems",
        "community": "hearts:default",
    }
    
    # Apply context-aware decoration
    config = decoration_module.get_config(ctx.group_id)
    original_decoration = config.get("default_decoration", "minimal:none")
    
    target_decoration = context_decorations.get(context_type, original_decoration)
    config["default_decoration"] = target_decoration
    decoration_module.set_config(ctx.group_id, config)
    
    # Build menu
    builder = InlineKeyboardBuilder()
    builder.button(text="Option 1", callback_data="opt1")
    builder.button(text="Option 2", callback_data="opt2")
    
    await ctx.send(f"Menu ({context_type})", reply_markup=builder.as_markup())
    
    # Restore original decoration
    config["default_decoration"] = original_decoration
    decoration_module.set_config(ctx.group_id, config)


# Migration guide: Adding decorations to existing code
# ======================================================

async def migrate_existing_keyboard(old_function, ctx: NexusContext):
    """
    Migration template for existing keyboard functions.
    
    Before:
        async def my_menu(ctx: NexusContext):
            builder = InlineKeyboardBuilder()
            builder.button(text="Button 1", callback_data="btn1")
            await ctx.send("Menu", reply_markup=builder.as_markup())
    
    After:
        async def my_menu(ctx: NexusContext):
            from bot.modules.button_decorations.module import apply_button_decoration
            
            builder = InlineKeyboardBuilder()
            builder.button(
                text=apply_button_decoration("Button 1", ctx.group_id),
                callback_data="btn1"
            )
            await ctx.send("Menu", reply_markup=builder.as_markup())
    """
    # Import the decoration function
    from bot.modules.button_decorations.module import apply_button_decoration
    
    # Call the old function
    await old_function(ctx)


# Tips for best results
# =======================

"""
1. Keep button text short - decorations add visual weight
2. Choose decorations that match your group's theme
3. Test different decorations to find what works
4. Consider using minimal decorations for important/menacing actions
5. Use consistent decorations throughout your bot
6. Document which decoration is used where for consistency
7. Remember that some users may prefer minimal decorations

Decoration recommendations by context:
- Welcome messages: nature:flowers or objects:hearts
- Moderation: objects:crowns or symbols:checkmarks
- Games: objects:stars or animals:cats
- Economy: objects:gems or objects:sparkles
- Information: symbols:diamonds or minimal:simple
- Navigation: symbols:arrows or minimal:dots
"""
