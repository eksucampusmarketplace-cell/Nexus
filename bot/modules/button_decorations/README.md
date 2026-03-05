# Button Decorations Module

A beautiful customization system for inline keyboard button decorations in Nexus bot.

## Features

- 🎨 **6 Decoration Categories**: Nature, Animals, Objects, Symbols, Food, Minimal
- 🌸 **20+ Predefined Decorations**: Flowers, Lions, Stars, Hearts, and more
- ✨ **Custom Decorations**: Create your own prefix/suffix combinations
- 🔧 **Easy Integration**: Simple function call to decorate any button
- ⚙️ **Flexible Configuration**: Enable/disable, choose position (prefix/suffix/both)

## Installation

The module is included in Nexus. Enable it for your group:

```
/decorations
```

## Commands

### `/decorations` or `/deco`
Opens an interactive menu to browse and select button decorations.

### `/setdecoration <category>:<decoration>`
Sets a decoration directly via command.

**Examples:**
```
/setdecoration nature:flowers
/setdecoration animals:lions
/setdecoration objects:stars
/setdecoration minimal:none
```

### `/customdecoration <name> <prefix> <suffix>`
Creates a custom decoration.

**Examples:**
```
/customdecoration mycool ⚡ ⚡
/customdecoration simple • 
/customdecoration fancy 💫 ✨
```

## Decoration Categories

### 🌿 Nature
- `flowers`: 🌸 text 🌺
- `trees`: 🌳 text 🌴
- `plants`: 🌵 text 🌱
- `leaves`: 🍃 text 🍂
- `seasonal`: 🌸 text 🍁

### 🦁 Animals
- `lions`: 🦁 text 🐾
- `cats`: 🐱 text 😺
- `dogs`: 🐕 text 🐶
- `birds`: 🦅 text 🐦
- `ocean`: 🐬 text 🦈
- `wild`: 🦊 text 🐻

### ✨ Objects
- `stars`: ⭐ text 🌟
- `hearts`: ❤️ text 💕
- `gems`: 💎 text 💠
- `crowns`: 👑 text 🏆
- `sparkles`: ✨ text 💫
- `fire`: 🔥 text 💥

### 🔷 Symbols
- `arrows`: ➡️ text ⬅️
- `checkmarks`: ✅ text ☑️
- `bullets`: • text •
- `diamonds`: 🔷 text 🔶
- `squares`: ⬛ text ⬜

### 🍔 Food
- `fruits`: 🍎 text 🍊
- `drinks`: 🥤 text 🍹
- `candy`: 🍬 text 🍭
- `fastfood`: 🍔 text 🍟

### ⚪ Minimal
- `none`: text (no decoration)
- `simple`: ▫️ text ▫️
- `dots`: • text •
- `clean`:  text  (spacing only)

## Integration Guide

### Basic Usage

Import and use the decoration function:

```python
from bot.modules.button_decorations.module import apply_button_decoration

# In any module that creates inline keyboards
async def my_command(ctx: NexusContext):
    builder = InlineKeyboardBuilder()
    
    # Apply decoration to button text
    decorated_text = apply_button_decoration("Click Here", ctx.group_id)
    
    builder.button(text=decorated_text, callback_data="clicked")
    
    await ctx.send("Choose an option:", reply_markup=builder.as_markup())
```

### Integration with KeyboardBuilder

```python
from bot.modules.button_decorations.module import apply_button_decoration
from bot.core.keyboard_state import InteractiveKeyboardBuilder

# Extend InteractiveKeyboardBuilder to auto-apply decorations
class DecoratedKeyboardBuilder(InteractiveKeyboardBuilder):
    def add_button(self, text: str, **kwargs):
        decorated_text = apply_button_decoration(text, self.group_id)
        return super().add_button(decorated_text, **kwargs)
```

### Integration with Existing Modules

Update any module that creates inline keyboards:

```python
# Before (without decorations)
builder.button(text="Option 1", callback_data="opt1")

# After (with decorations)
from bot.modules.button_decorations.module import apply_button_decoration
builder.button(
    text=apply_button_decoration("Option 1", ctx.group_id),
    callback_data="opt1"
)
```

## Configuration

The decorations system stores per-group configuration:

```python
{
    "enabled": True,  # Whether decorations are active
    "default_decoration": "nature:flowers",  # Selected decoration
    "position": "both",  # "prefix", "suffix", or "both"
    "custom_decorations": {
        "mycool": {
            "name": "mycool",
            "prefix": "⚡",
            "suffix": "⚡"
        }
    }
}
```

## Examples

### Example 1: Moderation Module with Decorations

```python
async def show_moderation_menu(ctx: NexusContext):
    builder = InlineKeyboardBuilder()
    
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
    
    await ctx.send("Moderation Actions:", reply_markup=builder.as_markup())
```

**Result (with nature:flowers):**
```
⚠️ Warn   🔇 Mute
🚫 Ban    👢 Kick

Becomes:

🌸 ⚠️ Warn 🌺   🌸 🔇 Mute 🌺
🌸 🚫 Ban 🌺   🌸 👢 Kick 🌺
```

### Example 2: Games Module with Decorations

```python
async def show_game_menu(ctx: NexusContext):
    builder = InlineKeyboardBuilder()
    
    games = ["Tic Tac Toe", "Rock Paper Scissors", "Trivia", "Slots"]
    
    for game in games:
        builder.row(
            builder.button(
                text=apply_button_decoration(f"🎮 {game}", ctx.group_id),
                callback_data=f"game:{game.lower().replace(' ', '_')}"
            )
        )
    
    await ctx.send("🎲 Choose a game:", reply_markup=builder.as_markup())
```

**Result (with objects:stars):**
```
⭐ 🎮 Tic Tac Toe 🌟
⭐ 🎮 Rock Paper Scissors 🌟
⭐ 🎮 Trivia 🌟
⭐ 🎮 Slots 🌟
```

## Advanced Features

### Per-Message-Type Decorations

You can set different decorations for different message types:

```python
config = module.get_config(group_id)
config["message_type_decorations"] = {
    "moderation": "objects:crowns",
    "games": "objects:stars",
    "welcome": "nature:flowers"
}
module.set_config(group_id, config)
```

### Custom Decoration Positions

```python
config = module.get_config(group_id)
config["position"] = "prefix"  # Only prefix, no suffix
# Options: "prefix", "suffix", "both"
module.set_config(group_id, config)
```

### Conditional Application

```python
config = module.get_config(group_id)
config["apply_to_admin_only"] = True  # Only decorate admin command buttons
config["apply_to_commands_only"] = False  # Or only command-related buttons
module.set_config(group_id, config)
```

## Tips

1. **Keep it simple**: Too many decorations can look cluttered
2. **Match your theme**: Choose decorations that fit your group's vibe
3. **Test first**: Try different decorations before settling on one
4. **Consider accessibility**: Some users might prefer minimal decorations

## Future Enhancements

- Animated button decorations (using GIFs)
- Color-coded buttons based on action type
- User-specific decoration preferences
- Seasonal decorations that auto-change
- Decoration packs and marketplace

## Support

For issues or suggestions, please contact the Nexus development team.
