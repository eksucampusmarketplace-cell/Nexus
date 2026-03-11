# 🛡️ Nexus Advanced Capabilities Report: Deep Dive

This report provides a comprehensive breakdown of the Nexus platform's attributes, deep settings, and command structure for both the Telegram Bot and the Mini App.

---

## 1. 📱 Mini App: Attributes & Description
The Nexus Mini App is a high-performance **React 18 + TypeScript** dashboard that runs natively inside Telegram.

### 📋 Core Attributes
- **Visual Toggle System**: Real-time enabling/disabling of 41+ modules via a graphical UI.
- **Responsive Layout**: Optimized for both mobile (Telegram WebApp) and desktop browsers.
- **Interactive Analytics**: SVG-based charts and heatmaps for group activity, sentiment, and growth.
- **State Persistence**: Uses **Zustand** for seamless state management across different views.
- **Direct API Integration**: Communicates with a **FastAPI** backend for instant updates to group settings.
- **Security**: Authenticated via Telegram's **InitData** (HMAC-SHA256) for secure admin access.

---

## 2. 📝 Setting New Text (Greetings & Rules)
Nexus allows complex text configuration for group management, supporting variables and Markdown.

### 🛠️ Where to Set It
- **Mini App**: `Dashboard` -> `Manage` -> `Rules & Greetings`.
- **Bot**: `/setwelcome <text>`, `/setgoodbye <text>`, `/setrules <text>`.

### 🔠 Supported Variables
You can use these placeholders in any welcome, goodbye, or rules text:
- `{first}`: User's first name.
- `{last}`: User's last name.
- `{fullname}`: User's full name.
- `{username}`: User's @username (or ID if none).
- `{mention}`: Clickable mention (HTML link).
- `{id}`: User's numeric Telegram ID.
- `{count}`: Current member count of the group.
- `{chatname}`: The title of the group.
- `{rules}`: A link/reference to the group rules.

### 🌟 Advanced Text Features
- **Media Support**: Reply to a photo/video/GIF with `/setwelcome` to attach it to the message.
- **Markdown**: Full support for bold, italic, links, and code blocks.
- **DM Delivery**: Option to send welcome messages as Private Messages instead of in-group.

---

## 3. ⌨️ Commands & Aliases
Nexus uses a sophisticated command parser with built-in shorthand for power users.

### 🔄 The Triple Prefix System
- `!command`: **Activate** or Enable a feature (e.g., `!welcome`).
- `!!command`: **Deactivate** or Disable a feature (e.g., `!!welcome`).
- `/command`: **Execute** a one-time action (e.g., `/ban`).

### 🚀 Common Shorthand Aliases
Nexus includes 280+ commands, many with short versions:
- `/w` = `/warn`
- `/m` = `/mute`
- `/tm` = `/tmute` (Timed Mute)
- `/b` = `/ban`
- `/tb` = `/tban` (Timed Ban)
- `/ub` = `/unban`
- `/um` = `/unmute`
- `/k` = `/kick`
- `/p` = `/purge` (Delete messages)
- `/bal` = `/balance`
- `+rep` / `-rep` = Give/take reputation points.

### 📚 Command Intelligence (Help System)
The `/help` command acts as a "Commands in One" hub:
- `/help`: Shows all 20+ command categories.
- `/help <category>`: Lists all commands in that group (e.g., `/help Moderation`).
- `/help <command>`: Shows detailed usage, examples, and aliases for a specific command.

---

## 4. ⚙️ Deep Settings: Mini App Configuration List
Below is a list of "Deep Settings" you can configure in the Mini App without ever typing a command.

### 🛡️ Moderation (Deep)
- **Warn Threshold**: Number of warnings before automatic action (default: 3).
- **Warn Action**: Penalty type reaching the threshold (`mute`, `kick`, `ban`).
- **Warn Duration**: Penalty length in seconds/minutes/hours.
- **Silent Mode**: Send moderation logs to a private channel instead of the main chat.
- **Require Reason**: Force admins to provide reasons for bans/mutes.

### 👋 Greetings (Deep)
- **Welcome Toggle**: Global on/off for welcome messages.
- **Delete Previous**: Automatically remove the old welcome message when a new user joins.
- **Send as DM**: Send the welcome message privately to the new user.
- **Mute on Join**: Mute new members until they interact or complete a captcha.
- **Auto-Delete Timer**: Seconds before the welcome message is automatically removed.

### 🔒 Anti-Spam & Security (Deep)
- **Flood Sensitivity**: Messages per second threshold (e.g., 5 msgs / 5 sec).
- **Lock System**: Granular toggles for `stickers`, `links`, `media`, `forwarded`, `rtl_languages`.
- **Trust Score System**: 0-100 behavioral score based on `activity`, `history`, and `engagement`.
- **AI Confidence**: Threshold (0-100) for AI auto-deletion of toxic content.

### 💰 Economy & Games (Deep)
- **Currency Name**: Custom name for your group's money (e.g., "Credits", "Coins").
- **Daily Reward**: Amount of currency users get for the `/daily` command.
- **Game Payouts**: Adjust win/loss ratios for 20+ integrated games.
- **XP Formula**: Control the speed of the leveling system.

---

## 5. 🏆 Performance Recommendation

| Interface | Best For... | Why it works perfectly |
| :--- | :--- | :--- |
| **Bot (Text)** | **Reactive Tasks** | `/ban` or `/mute` takes 1 second. No loading time. |
| **Mini App** | **Strategic Tasks** | Configuring 40+ modules visually prevents command errors. |
| **Hybrid** | **Total Control** | The Bot handles the *live* chat, the Mini App handles the *deep* settings. |

---
