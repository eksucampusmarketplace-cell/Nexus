# Button Decorations - Quick Start Guide

Get started with beautiful button decorations in 5 minutes!

## 🚀 Installation (Already Done!)

The Button Decorations module is already installed in Nexus. Just enable it!

## 📱 Step 1: Enable Decorations

In any group where Nexus is active, run:

```
/decorations
```

or

```
/deco
```

This opens an interactive menu to browse and select decorations.

## 🎨 Step 2: Choose Your Decoration

You'll see categories like:
- 🌿 Nature (flowers, trees, plants)
- 🦁 Animals (lions, cats, dogs, birds)
- ✨ Objects (stars, hearts, gems, crowns)
- 🔷 Symbols (arrows, checkmarks)
- 🍔 Food (fruits, candy)
- ⚪ Minimal (no decoration)

Tap a category, then choose a decoration!

## ✅ Step 3: That's It!

All inline keyboard buttons in your bot will now use the selected decoration!

## 🎯 Quick Examples

### Example 1: Set Decoration Directly

```
/setdecoration nature:flowers
```

Your buttons now look like:
```
🌸 Click Me 🌺
🌸 View Stats 🌺
🌸 Settings 🌺
```

### Example 2: Try Different Styles

```
/setdecoration animals:lions
```

Your buttons now look like:
```
🦁 Click Me 🐾
🦁 View Stats 🐾
🦁 Settings 🐾
```

```
/setdecoration objects:stars
```

Your buttons now look like:
```
⭐ Click Me 🌟
⭐ View Stats 🌟
⭐ Settings 🌟
```

### Example 3: Create Custom Decoration

```
/customdecoration mycool ⚡ ⚡
```

Then set it:
```
/setdecoration custom:mycool
```

Your buttons now look like:
```
⚡ Click Me ⚡
⚡ View Stats ⚡
⚡ Settings ⚡
```

## 🎨 Available Decorations

### 🌿 Nature
- `nature:flowers` - 🌸 text 🌺
- `nature:trees` - 🌳 text 🌴
- `nature:plants` - 🌵 text 🌱
- `nature:leaves` - 🍃 text 🍂
- `nature:seasonal` - 🌸 text 🍁

### 🦁 Animals
- `animals:lions` - 🦁 text 🐾
- `animals:cats` - 🐱 text 😺
- `animals:dogs` - 🐕 text 🐶
- `animals:birds` - 🦅 text 🐦
- `animals:ocean` - 🐬 text 🦈
- `animals:wild` - 🦊 text 🐻

### ✨ Objects
- `objects:stars` - ⭐ text 🌟
- `objects:hearts` - ❤️ text 💕
- `objects:gems` - 💎 text 💠
- `objects:crowns` - 👑 text 🏆
- `objects:sparkles` - ✨ text 💫
- `objects:fire` - 🔥 text 💥

### 🔷 Symbols
- `symbols:arrows` - ➡️ text ⬅️
- `symbols:checkmarks` - ✅ text ☑️
- `symbols:bullets` - • text •
- `symbols:diamonds` - 🔷 text 🔶
- `symbols:squares` - ⬛ text ⬜

### 🍔 Food
- `food:fruits` - 🍎 text 🍊
- `food:drinks` - 🥤 text 🍹
- `food:candy` - 🍬 text 🍭
- `food:fastfood` - 🍔 text 🍟

### ⚪ Minimal
- `minimal:none` - text (no decoration)
- `minimal:simple` - ▫️ text ▫️
- `minimal:dots` - • text •
- `minimal:clean` - text (minimal spacing)

## 💡 Pro Tips

### 1. Match Your Theme
Choose decorations that fit your group's vibe:
- 🌸 Welcome/greeting groups: `nature:flowers` or `objects:hearts`
- 👑 Admin/moderation groups: `objects:crowns` or `symbols:checkmarks`
- 🎮 Gaming groups: `objects:stars` or `animals:cats`
- 💰 Economy/trading groups: `objects:gems`
- 🌍 Community groups: `objects:hearts`

### 2. Try Before Committing
Test different decorations to see what looks best:
```
/setdecoration nature:flowers
/setdecoration objects:stars
/setdecoration minimal:none
```

### 3. Clear When Needed
Remove all decorations:
```
/setdecoration minimal:none
```

Or disable the module entirely in settings.

### 4. Custom Combinations
Create your own unique style:
```
/customdecoration fancy 💫 ✨
/customdecoration tech 🤖 ⚙️
/customdecoration magic 🔮 🪄
```

## 🔧 For Developers

### Integration in Your Modules

```python
from bot.modules.button_decorations.module import apply_button_decoration

async def my_command(ctx: NexusContext):
    builder = InlineKeyboardBuilder()
    
    # Just wrap your button text!
    builder.button(
        text=apply_button_decoration("Click Me", ctx.group_id),
        callback_data="clicked"
    )
    
    await ctx.send("Choose:", reply_markup=builder.as_markup())
```

That's it! The decoration is automatically applied if enabled.

### Use the Decorated Builder

```python
from bot.modules.button_decorations.decorated_builder import DecoratedInlineKeyboardBuilder

async def my_command(ctx: NexusContext):
    builder = DecoratedInlineKeyboardBuilder(group_id=ctx.group_id)
    
    # All buttons are automatically decorated!
    builder.button(text="Click Me", callback_data="clicked")
    
    await ctx.send("Choose:", reply_markup=builder.as_markup())
```

## 📊 Before & After Examples

### Before (No Decoration)
```
View Stats   Settings   Help
```

### After (nature:flowers)
```
🌸 View Stats 🌺   🌸 Settings 🌺   🌸 Help 🌺
```

### After (objects:stars)
```
⭐ View Stats 🌟   ⭐ Settings 🌟   ⭐ Help 🌟
```

### After (animals:lions)
```
🦁 View Stats 🐾   🦁 Settings 🐾   🦁 Help 🐾
```

## ❓ Common Questions

**Q: Does this affect regular messages?**
A: No! Only inline keyboard buttons (the ones you can click in messages) are decorated.

**Q: Can different groups have different decorations?**
A: Yes! Each group can have its own decoration setting.

**Q: Can I disable it for specific buttons?**
A: Yes! Use `skip_decoration=True` when using the DecoratedInlineKeyboardBuilder.

**Q: Will my users still understand what the buttons do?**
A: Absolutely! The decorations just add visual flair. The button text remains clear and readable.

**Q: Can I use this in my custom bot flows?**
A: Yes! Just import and use the `apply_button_decoration` function.

## 🎉 Enjoy Your Beautiful Buttons!

You're all set! Your bot's buttons will now look amazing with your chosen decorations.

For more advanced usage and examples, see:
- `integration_example.py` - Code examples for developers
- `README.md` - Full documentation
- `decorated_builder.py` - Builder utilities

Need help? Check the Nexus documentation or ask in the community!
