# Nexus Bot - Complete Commands Reference

## 📖 Table of Contents
- [Moderation Commands](#moderation-commands)
- [Welcome & Greetings Commands](#welcome--greetings-commands)
- [Anti-Spam Commands](#anti-spam-commands)
- [Locks Commands](#locks-commands)
- [Notes & Filters Commands](#notes--filters-commands)
- [Economy & Reputation Commands](#economy--reputation-commands)
- [Games Commands](#games-commands)
- [Analytics Commands](#analytics-commands)
- [AI Assistant Commands](#ai-assistant-commands)
- [Rules & Info Commands](#rules--info-commands)
- [Polls Commands](#polls-commands)
- [Admin & Management Commands](#admin--management-commands)
- [Cleaning Commands](#cleaning-commands)
- [Formatting Commands](#formatting-commands)
- [Help & Utility Commands](#help--utility-commands)

---

## 🛡️ Moderation Commands

### `/warn [user] [reason]`
Warn a user. Reply to a message or mention @username. Add `!` at the end for silent mode.
- **Aliases:** `/w`
- **Permissions:** Admin
- **Examples:**
  - `/warn @username spamming` - Warn with reason
  - `/warn!` - Warn silently (no announcement)
  - `/warn` - Reply to message to warn sender

### `/warns [user]`
View user's active warnings. If no user specified, shows your own warnings.
- **Permissions:** Admin (for others)
- **Example:** `/warns @username`

### `/resetwarns [user]`
Reset all warnings for a user.
- **Permissions:** Admin
- **Example:** `/resetwarns @username`

### `/warnlimit <number>`
Set warning threshold (default: 3 warns = auto-action).
- **Permissions:** Admin
- **Example:** `/warnlimit 5`

### `/warntime <duration>`
Set warning expiration time. Warnings expire after this period.
- **Permissions:** Admin
- **Duration formats:** `1m`, `1h`, `1d`, `1w`
- **Example:** `/warntime 7d`

### `/warnmode <action>`
Set automatic action when warning threshold is reached.
- **Permissions:** Admin
- **Actions:** `mute`, `kick`, `ban`
- **Example:** `/warnmode ban`

### `/mute [user] [duration] [reason]`
Mute a user. Reply to message or mention @username.
- **Aliases:** `/m`, `/tmute`, `/tm`
- **Permissions:** Moderator
- **Duration formats:** `1m`, `1h`, `1d`, `1w` (default: permanent)
- **Examples:**
  - `/mute @username 1h spamming`
  - `/mute 2d` - Reply to message
  - `/tm 1w` - Using alias

### `/unmute [user]`
Unmute a user.
- **Aliases:** `/um`
- **Permissions:** Admin
- **Example:** `/unmute @username`

### `/ban [user] [duration] [reason]`
Ban a user from the group. Reply to message or mention @username.
- **Aliases:** `/b`, `/tban`, `/tb`
- **Permissions:** Admin
- **Duration formats:** `1m`, `1h`, `1d`, `1w` (default: permanent)
- **Examples:**
  - `/ban @username spam`
  - `/ban! 7d` - Ban silently for 7 days
  - `/tban 30d` - Using alias

### `/unban [user]`
Unban a user from the group.
- **Aliases:** `/ub`
- **Permissions:** Admin
- **Example:** `/unban @username`

### `/kick [user] [reason]`
Kick a user from the group (they can rejoin).
- **Aliases:** `/k`, `/kickme`
- **Permissions:** Admin
- **Example:** `/kick @username spamming`

### `/kickme [reason]`
Kick yourself from the group.
- **Permissions:** Everyone
- **Example:** `/kickme leaving group`

### `/promote [user] [role]`
Promote a user to admin or moderator.
- **Permissions:** Owner
- **Roles:** `admin`, `mod`
- **Example:** `/promote @username admin`

### `/demote [user]`
Demote a user from admin/moderator role.
- **Permissions:** Owner
- **Example:** `/demote @username`

### `/title [user] [title]`
Set custom admin title for a user. Reply to user to set their title.
- **Permissions:** Admin
- **Example:** `/title Community Manager`

### `/pin`
Pin a message. Reply to message to pin it. Add `silent` to notify silently.
- **Permissions:** Admin
- **Example:** `/pin silent`

### `/unpin`
Unpin a message. Reply to message to unpin it.
- **Permissions:** Admin
- **Example:** `/unpin`

### `/unpinall`
Unpin all messages in the group.
- **Permissions:** Admin
- **Example:** `/unpinall`

### `/purge`
Delete all messages between replied message and command.
- **Permissions:** Admin
- **Example:** Reply to last message → `/purge`

### `/del`
Delete a message. Reply to message or delete command message itself.
- **Permissions:** Admin
- **Example:** `/del`

### `/history [user]`
View user's complete moderation history including warnings, mutes, bans, kicks, and stats.
- **Permissions:** Moderator
- **Example:** `/history @username`

### `/trust [user]`
Trust a user (bypass some automatic restrictions).
- **Permissions:** Admin
- **Example:** `/trust @username`

### `/untrust [user]`
Remove trusted status from a user.
- **Permissions:** Admin
- **Example:** `/untrust @username`

### `/approve [user]`
Approve a user (bypass ALL restrictions).
- **Permissions:** Admin
- **Example:** `/approve @username`

### `/unapprove [user]`
Remove approved status from a user.
- **Permissions:** Admin
- **Example:** `/unapprove @username`

### `/approvals`
List all approved users in the group.
- **Permissions:** Moderator
- **Example:** `/approvals`

### `/report [reason]`
Report a message to admins. Reply to message to report it.
- **Permissions:** Everyone
- **Example:** Reply to message → `/report spam`

### `/reports`
View all pending reports.
- **Permissions:** Moderator
- **Example:** `/reports`

### `/review <report_id> <action>`
Review and resolve a report.
- **Permissions:** Moderator
- **Actions:** `warn`, `mute`, `ban`, `kick`, `dismiss`
- **Example:** `/review 123 warn`

### `/slowmode [seconds|off]`
Enable slow mode (limit message frequency) or disable it.
- **Permissions:** Admin
- **Example:** `/slowmode 30` or `/slowmode off`

### `/restrict [user] <permission>`
Restrict user permissions.
- **Permissions:** Admin
- **Permissions:** `all`, `none`, `text`, `media`, `polls`, `links`, `invite`
- **Example:** `/restrict @username media`

---

## 👋 Welcome & Greetings Commands

### `/setwelcome [message]`
Set welcome message for new members. Use variables like `{first}`, `{last}`, `{username}`, `{chatname}`, `{rules}`.
- **Permissions:** Admin
- **Variables:** `{first}`, `{last}`, `{fullname}`, `{username}`, `{mention}`, `{id}`, `{count}`, `{chatname}`, `{rules}`
- **Format:** Markdown or HTML
- **Example:** `/setwelcome Welcome {first}! Read {rules}`

### `/welcome`
View current welcome message.
- **Permissions:** Everyone
- **Example:** `/welcome`

### `/resetwelcome`
Reset welcome message to default.
- **Permissions:** Admin
- **Example:** `/resetwelcome`

### `/setgoodbye [message]`
Set goodbye message for leaving members.
- **Permissions:** Admin
- **Variables:** Same as welcome
- **Example:** `/setgoodbye Goodbye {first}! We'll miss you.`

### `/goodbye`
View current goodbye message.
- **Permissions:** Everyone
- **Example:** `/goodbye`

### `/resetgoodbye`
Reset goodbye message to default.
- **Permissions:** Admin
- **Example:** `/resetgoodbye`

### `/cleanwelcome`
Toggle automatic deletion of welcome messages after a time.
- **Permissions:** Admin
- **Example:** `/cleanwelcome on`

### `/welcomemute <seconds>`
Mute new members until they complete CAPTCHA.
- **Permissions:** Admin
- **Example:** `/welcomemute 60`

### `/welcomehelp`
Show help for welcome system with variable reference.
- **Permissions:** Everyone
- **Example:** `/welcomehelp`

---

## 🛡️ Anti-Spam Commands

### `/antiflood <limit> <window>`
Set anti-flood protection limits.
- **Permissions:** Admin
- **Limit:** Max messages allowed
- **Window:** Time window in seconds
- **Example:** `/antiflood 5 5` - 5 messages per 5 seconds

### `/antiflood off`
Disable anti-flood protection.
- **Permissions:** Admin
- **Example:** `/antiflood off`

### `/antiraid <threshold> <window>`
Set anti-raid protection (mass join detection).
- **Permissions:** Admin
- **Threshold:** Number of joins to trigger
- **Window:** Time window in seconds
- **Example:** `/antiraid 10 60` - 10 joins in 60 seconds

### `/antiraid off`
Disable anti-raid protection.
- **Permissions:** Admin
- **Example:** `/antiraid off`

### `/setcasban <on|off>`
Enable/disable CAS (Combot Anti-Spam) integration.
- **Permissions:** Admin
- **Example:** `/setcasban on`

### `/blocklist`
List all blocked words and phrases.
- **Permissions:** Admin
- **Example:** `/blocklist`

### `/addblacklist <word> [list]`
Add a word to the blocklist.
- **Permissions:** Admin
- **List:** `1` or `2` (default: 1)
- **Example:** `/addblacklist spam 1`

### `/rmblacklist <word> [list]`
Remove a word from the blocklist.
- **Permissions:** Admin
- **Example:** `/rmblacklist spam 1`

### `/blacklistmode <action> [list]`
Set action for blocklist violations.
- **Permissions:** Admin
- **Actions:** `delete`, `warn`, `mute`, `kick`, `ban`, `tban`, `tmute`
- **Example:** `/blacklistmode delete 1`

---

## 🔒 Locks Commands

### `/locktypes`
List all available lock types.
- **Permissions:** Admin
- **Example:** `/locktypes`

### `/lock <type>`
Lock a content type. Messages of this type will be deleted.
- **Permissions:** Admin
- **Types:** `audio`, `bot`, `button`, `command`, `contact`, `document`, `email`, `forward`, `forward_channel`, `game`, `gif`, `inline`, `invoice`, `location`, `phone`, `photo`, `poll`, `rtl`, `spoiler`, `sticker`, `url`, `video`, `video_note`, `voice`, `mention`, `caption`, `no_caption`, `emoji_only`, `arabic`, `farsi`, `unofficial_client`
- **Example:** `/lock url`

### `/unlock <type>`
Unlock a content type.
- **Permissions:** Admin
- **Example:** `/unlock url`

### `/lock <type> <mode> [duration]`
Set lock mode with optional duration.
- **Permissions:** Admin
- **Modes:** `delete`, `warn`, `kick`, `ban`, `tban`, `tmute`
- **Example:** `/lock url ban 1d`

### `/locks`
View all current locks in the group.
- **Permissions:** Everyone
- **Example:** `/locks`

### `/lockall`
Lock all content types (except text).
- **Permissions:** Admin
- **Example:** `/lockall`

### `/unlockall`
Unlock all content types.
- **Permissions:** Admin
- **Example:** `/unlockall`

### `/lockchannel <channel_username>`
Lock all forwards from a specific channel.
- **Permissions:** Admin
- **Example:** `/lockchannel @spam_channel`

### `/unlockchannel <channel_username>`
Unlock forwards from a specific channel.
- **Permissions:** Admin
- **Example:** `/unlockchannel @spam_channel`

---

## 📝 Notes & Filters Commands

### Notes Commands

### `/save <notename> [content]`
Save a note. Reply to media to save as note, or provide text content.
- **Permissions:** Everyone (admin-only for some notes)
- **Example:** `/save rules No spam allowed!`

### `/note <notename>`
Retrieve a saved note.
- **Aliases:** `/get`, `#notename`
- **Permissions:** Depends on note privacy
- **Example:** `/note rules` or `#rules`

### `/notes`
List all saved notes.
- **Permissions:** Everyone
- **Example:** `/notes`

### `/clear <notename>`
Delete a specific note.
- **Permissions:** Admin (for all), owner (for own notes)
- **Example:** `/clear rules`

### `/clearall`
Delete all notes in the group.
- **Permissions:** Admin
- **Example:** `/clearall`

### Filters Commands

### `/filter <trigger> [response]`
Create a filter that responds to a keyword/phrase.
- **Permissions:** Admin
- **Example:** `/filter hello Hi there! Welcome to the group.`

### `/filters`
List all active filters.
- **Permissions:** Admin
- **Example:** `/filters`

### `/stop <trigger>`
Delete a specific filter.
- **Permissions:** Admin
- **Example:** `/stop hello`

### `/stopall`
Delete all filters.
- **Permissions:** Admin
- **Example:** `/stopall`

### `/filtermode <mode>`
Set default action for filters.
- **Permissions:** Admin
- **Actions:** `none`, `warn`, `mute`, `kick`, `ban`, `delete`
- **Example:** `/filtermode delete`

### `/filterregex <on|off>`
Enable/disable regex matching in filters.
- **Permissions:** Admin
- **Example:** `/filterregex on`

### `/filtercase <on|off>`
Enable/disable case sensitivity in filters.
- **Permissions:** Admin
- **Example:** `/filtercase off`

---

## 💰 Economy & Reputation Commands

### Economy Commands

### `/balance [@user]`
Check wallet balance. If no user specified, shows your own balance.
- **Permissions:** Everyone
- **Example:** `/balance` or `/balance @username`

### `/daily`
Claim daily bonus coins.
- **Permissions:** Everyone
- **Example:** `/daily`

### `/give <@user> <amount> [reason]`
Send coins to another user.
- **Permissions:** Everyone
- **Example:** `/give @username 100 thanks for help`

### `/transfer <@user> <amount>`
Same as `/give`.
- **Permissions:** Everyone
- **Example:** `/transfer @username 50`

### `/leaderboard`
View the group's economy leaderboard.
- **Permissions:** Everyone
- **Example:** `/leaderboard`

### `/transactions [@user]`
View recent transactions. If no user specified, shows your own.
- **Permissions:** Everyone
- **Example:** `/transactions`

### `/shop`
View the group shop with available items.
- **Permissions:** Everyone
- **Example:** `/shop`

### `/buy <item>`
Purchase an item from the shop.
- **Permissions:** Everyone
- **Example:** `/buy VIP badge`

### `/sell <item>`
Sell an item from your inventory.
- **Permissions:** Everyone
- **Example:** `/sell VIP badge`

### `/inventory`
View your inventory.
- **Permissions:** Everyone
- **Example:** `/inventory`

### `/coinflip <amount> [heads|tails]`
Flip a coin and bet coins.
- **Permissions:** Everyone
- **Example:** `/coinflip 100 heads`

### `/gamble <amount>`
Gamble coins with 50/50 chance to double or lose.
- **Permissions:** Everyone
- **Example:** `/gamble 50`

### `/rob <@user>`
Attempt to rob another user (low success rate).
- **Permissions:** Everyone
- **Example:** `/rob @username`

### `/beg`
Beg for coins (small chance to get some).
- **Permissions:** Everyone
- **Example:** `/beg`

### `/work`
Work to earn coins.
- **Permissions:** Everyone
- **Cooldown:** 1 hour
- **Example:** `/work`

### `/crime`
Commit a crime for chance of big reward or punishment.
- **Permissions:** Everyone
- **Cooldown:** 30 minutes
- **Example:** `/crime`

### `/deposit <amount>`
Deposit coins to bank (saves from robbery).
- **Permissions:** Everyone
- **Example:** `/deposit 1000`

### `/withdraw <amount>`
Withdraw coins from bank.
- **Permissions:** Everyone
- **Example:** `/withdraw 500`

### `/bank [@user]`
View bank balance.
- **Permissions:** Everyone
- **Example:** `/bank`

### `/loan <amount>`
Take a loan from the bank.
- **Permissions:** Everyone
- **Example:** `/loan 1000`

### `/repay <amount>`
Repay your loan.
- **Permissions:** Everyone
- **Example:** `/repay 500`

### Reputation Commands

### `/rep [@user]`
Give reputation to a user. Reply to message or mention @username.
- **Permissions:** Everyone
- **Example:** `/rep @username` or Reply to message → `/rep`

### `/+rep [@user]`
Same as `/rep`.
- **Permissions:** Everyone
- **Example:** `/+rep @username`

### `/-rep [@user]`
Give negative reputation.
- **Permissions:** Everyone
- **Example:** `/-rep @username`

### `/reputation [@user]`
View user's reputation score and history.
- **Permissions:** Everyone
- **Example:** `/reputation @username`

### `/repleaderboard`
View reputation leaderboard.
- **Aliases:** `/replb`
- **Permissions:** Everyone
- **Example:** `/repleaderboard`

---

## 🎮 Games Commands

### `/trivia [category] [difficulty]`
Start a trivia quiz.
- **Permissions:** Everyone
- **Categories:** `general`, `science`, `history`, `geography`, `entertainment`, `sports`
- **Difficulty:** `easy`, `medium`, `hard`
- **Example:** `/trivia science hard`

### `/wordle`
Start a Wordle game.
- **Permissions:** Everyone
- **Example:** `/wordle`

### `/hangman [word]`
Start a Hangman game. Admin can provide word, otherwise random.
- **Permissions:** Everyone
- **Example:** `/hangman`

### `/mathrace`
Start a math race (first to answer wins).
- **Permissions:** Everyone
- **Example:** `/mathrace`

### `/typerace <sentence>`
Start a typing race with a sentence.
- **Permissions:** Everyone
- **Example:** `/typerace The quick brown fox`

### `/8ball <question>`
Ask the magic 8-ball a yes/no question.
- **Permissions:** Everyone
- **Example:** `/8ball Will I win today?`

### `/roll [dice]`
Roll dice.
- **Permissions:** Everyone
- **Examples:**
  - `/roll` - Roll 6-sided die
  - `/roll 2d10` - Roll 2 10-sided dice
  - `/roll 1d20` - Roll 20-sided die

### `/flip`
Flip a coin.
- **Permissions:** Everyone
- **Example:** `/flip`

### `/rps [choice]`
Play rock-paper-scissors against bot.
- **Permissions:** Everyone
- **Choices:** `rock`, `paper`, `scissors`, `r`, `p`, `s`
- **Example:** `/rps rock`

### `/dice <bet> <guess>`
Roll dice and bet on outcome.
- **Permissions:** Everyone
- **Example:** `/dice 100 6` - Bet 100 coins on rolling 6

### `/spin <bet>`
Spin the wheel of fortune.
- **Permissions:** Everyone
- **Example:** `/spin 50`

### `/lottery <amount>`
Buy lottery tickets.
- **Permissions:** Everyone
- **Example:** `/lottery 10`

### `/blackjack <bet>`
Play blackjack.
- **Permissions:** Everyone
- **Example:** `/blackjack 50`

### `/roulette <bet> <number|color>`
Play roulette.
- **Permissions:** Everyone
- **Example:** `/roulette 10 red`

### `/slots <bet>`
Play slot machine.
- **Permissions:** Everyone
- **Example:** `/slots 10`

### `/guessnumber <min> <max>`
Start a number guessing game.
- **Permissions:** Everyone
- **Example:** `/guessnumber 1 100`

### `/unscramble`
Start a word unscramble game.
- **Permissions:** Everyone
- **Example:** `/unscramble`

### `/quiz`
Start a quiz with multiple questions.
- **Permissions:** Everyone
- **Example:** `/quiz`

### `/tictactoe [@user]`
Challenge someone to Tic-Tac-Toe.
- **Permissions:** Everyone
- **Example:** `/tictactoe @username`

---

## 📊 Analytics Commands

### `/stats`
View general group statistics.
- **Permissions:** Everyone
- **Example:** `/stats`

### `/activity`
View group activity statistics.
- **Permissions:** Everyone
- **Example:** `/activity`

### `/top [type] [period]`
View top users by various metrics.
- **Permissions:** Everyone
- **Types:** `messages`, `coins`, `xp`, `rep`
- **Periods:** `day`, `week`, `month`, `all`
- **Example:** `/top messages week`

### `/chart [type] [period]`
Generate a chart of group activity.
- **Permissions:** Everyone
- **Example:** `/chart messages month`

### `/sentiment`
View group sentiment analysis.
- **Permissions:** Everyone
- **Example:** `/sentiment`

### `/growth`
View member growth over time.
- **Permissions:** Everyone
- **Example:** `/growth`

### `/heatmap`
View activity heatmap (hour vs day of week).
- **Permissions:** Everyone
- **Example:** `/heatmap`

### `/reportcard`
Generate a group report card.
- **Permissions:** Everyone
- **Example:** `/reportcard`

---

## 🤖 AI Assistant Commands

### `/ai [prompt]`
Ask the AI assistant a question.
- **Permissions:** Everyone
- **Example:** `/ai summarize the last 100 messages`

### `/summarize [count]`
Summarize recent messages.
- **Permissions:** Everyone
- **Example:** `/summarize 50`

### `/translate [text]`
Translate text to group language.
- **Permissions:** Everyone
- **Example:** `/translate Hello world`

### `/factcheck [claim]`
Fact-check a claim.
- **Permissions:** Everyone
- **Example:** `/factcheck The earth is flat`

### `/detectscam`
Reply to a suspicious message to detect if it's a scam.
- **Permissions:** Everyone
- **Example:** Reply to message → `/detectscam`

### `/draft [topic]`
Draft an announcement about a topic.
- **Permissions:** Admin
- **Example:** `/draft New group rules about spam`

### `/suggestpromote`
Suggest who to promote based on activity.
- **Permissions:** Admin
- **Example:** `/suggestpromote`

### `/weeklyreport`
Generate weekly group report.
- **Permissions:** Admin
- **Example:** `/weeklyreport`

### `/whatidid`
Get a summary of what you missed.
- **Permissions:** Everyone
- **Example:** `/whatidid`

---

## 📋 Rules & Info Commands

### Rules Commands

### `/setrules [rules]`
Set group rules.
- **Permissions:** Admin
- **Format:** Markdown or HTML
- **Example:** `/setrules 1. No spam\n2. Be respectful`

### `/rules`
View group rules.
- **Permissions:** Everyone
- **Example:** `/rules`

### `/resetrules`
Reset group rules to default.
- **Permissions:** Admin
- **Example:** `/resetrules`

### Info Commands

### `/info [@user]`
View user information.
- **Permissions:** Everyone
- **Example:** `/info @username`

### `/chatinfo`
View group information.
- **Permissions:** Everyone
- **Example:** `/chatinfo`

### `/id [@user]`
Get user or group ID.
- **Permissions:** Everyone
- **Example:** `/id` or `/id @username`

### `/adminlist`
List all group admins.
- **Permissions:** Everyone
- **Example:** `/adminlist`

---

## 📊 Polls Commands

### `/poll <question> [options...]`
Create a poll with multiple options.
- **Permissions:** Everyone
- **Example:** `/poll What's your favorite color? Red Blue Green`

### `/quiz <question> [options...] <correct>`
Create a quiz poll with a correct answer.
- **Permissions:** Everyone
- **Example:** `/quiz What is 2+2? 3 4 5 4`

### `/closepoll`
Close the most recent poll.
- **Permissions:** Admin
- **Example:** `/closepoll`

### `/vote <option>`
Vote on a poll (alternative to clicking).
- **Permissions:** Everyone
- **Example:** `/vote 1`

### `/pollresults`
View detailed poll results.
- **Permissions:** Everyone
- **Example:** `/pollresults`

### `/pollsettings <setting> <value>`
Configure poll settings.
- **Permissions:** Admin
- **Settings:** `anonymous`, `multiple`, `close_time`
- **Example:** `/pollsettings close_time 1h`

---

## ⚙️ Admin & Management Commands

### `/settings`
Open the settings Mini App.
- **Permissions:** Everyone
- **Example:** `/settings`

### `/config`
Configure module settings via Mini App.
- **Permissions:** Admin
- **Example:** `/config`

### `/enable <module>`
Enable a module.
- **Permissions:** Admin
- **Example:** `/enable welcome`

### `/disable <module>`
Disable a module.
- **Permissions:** Admin
- **Example:** `/disable welcome`

### `/disabled`
List disabled commands and modules.
- **Permissions:** Everyone
- **Example:** `/disabled`

### `/disablecommand <command>`
Disable a specific command.
- **Permissions:** Admin
- **Example:** `/disablecommand /kick`

### `/enablecommand <command>`
Re-enable a disabled command.
- **Permissions:** Admin
- **Example:** `/enablecommand /kick`

### `/export [modules...]`
Export group settings.
- **Permissions:** Admin
- **Example:** `/export welcome rules notes`

### `/import [modules...]`
Import group settings (reply to file).
- **Permissions:** Admin
- **Example:** `/import welcome rules`

### `/backup`
Create a full backup of group settings.
- **Permissions:** Admin
- **Example:** `/backup`

### `/restore`
Restore from backup.
- **Permissions:** Admin
- **Example:** `/restore`

### `/customtoken [token]`
Set custom bot token for white-label mode.
- **Permissions:** Owner
- **Example:** `/customtoken 123456:ABC-DEF...`

### `/removetoken`
Remove custom bot token and revert to shared bot.
- **Permissions:** Owner
- **Example:** `/removetoken`

### `/newfed <name> [description]`
Create a new federation.
- **Permissions:** Everyone
- **Example:** `/newfed MyFed Network of trusted groups`

### `/joinfed <fed_id>`
Join a federation.
- **Permissions:** Admin
- **Example:** `/joinfed abc123-def456`

### `/leavefed`
Leave current federation.
- **Permissions:** Admin
- **Example:** `/leavefed`

### `/fedinfo`
View federation information.
- **Permissions:** Admin
- **Example:** `/fedinfo`

### `/fban <@user> [reason]`
Federation ban (bans from all groups in federation).
- **Permissions:** Federation Admin
- **Example:** `/fban @username spammer`

### `/unfban <@user>`
Remove federation ban.
- **Permissions:** Federation Admin
- **Example:** `/unfban @username`

### `/fedadmins`
List federation admins.
- **Permissions:** Federation Admin
- **Example:** `/fedadmins`

### `/addfedadmin <@user>`
Add federation admin.
- **Permissions:** Federation Owner
- **Example:** `/addfedadmin @username`

### `/rmfedadmin <@user>`
Remove federation admin.
- **Permissions:** Federation Owner
- **Example:** `/rmfedadmin @username`

### `/fedbans`
List all federation bans.
- **Permissions:** Federation Admin
- **Example:** `/fedbans`

### `/myfeds`
List federations you manage.
- **Permissions:** Everyone
- **Example:** `/myfeds`

### `/fedchats`
List groups in federation.
- **Permissions:** Federation Admin
- **Example:** `/fedchats`

### `/connect <group_id>`
Connect to a group from DM (multi-group management).
- **Permissions:** Everyone
- **Example:** `/connect -1001234567890`

### `/disconnect [group_id]`
Disconnect from a group.
- **Permissions:** Everyone
- **Example:** `/disconnect -1001234567890`

### `/connected`
List all connected groups.
- **Permissions:** Everyone
- **Example:** `/connected`

---

## 🧹 Cleaning Commands

### `/cleanservice <on|off>`
Auto-delete join/leave service messages.
- **Permissions:** Admin
- **Example:** `/cleanservice on`

### `/cleancommands <on|off>`
Auto-delete command messages after execution.
- **Permissions:** Admin
- **Example:** `/cleancommands on`

### `/clean <count>`
Delete last N bot messages.
- **Permissions:** Admin
- **Example:** `/clean 10`

---

## ✨ Formatting Commands

### `/markdownhelp`
Show Markdown formatting help.
- **Permissions:** Everyone
- **Example:** `/markdownhelp`

### `/formattinghelp`
Show formatting help including buttons.
- **Permissions:** Everyone
- **Example:** `/formattinghelp`

### `/bold <text>`
Format text as bold.
- **Permissions:** Everyone
- **Example:** `/bold Hello world`

### `/italic <text>`
Format text as italic.
- **Permissions:** Everyone
- **Example:** `/italic Hello world`

### `/underline <text>`
Format text as underline (HTML only).
- **Permissions:** Everyone
- **Example:** `/underline Hello world`

### `/strike <text>`
Format text as strikethrough.
- **Permissions:** Everyone
- **Example:** `/strike Hello world`

### `/spoiler <text>`
Format text as spoiler.
- **Permissions:** Everyone
- **Example:** `/spoiler Secret message`

### `/code <text>`
Format text as code block.
- **Permissions:** Everyone
- **Example:** `/code print("Hello")`

### `/pre <text>`
Format text as preformatted block.
- **Permissions:** Everyone
- **Example:** `/pre multiline code`

### `/link <url> <text>`
Create a link with custom text.
- **Permissions:** Everyone
- **Example:** `/link https://google.com Google`

### `/button <text> <url>`
Create a button (for use in notes/filters).
- **Permissions:** Everyone
- **Example:** `/button Open https://example.com`

---

## ❓ Help & Utility Commands

### `/help`
Show general help message.
- **Permissions:** Everyone
- **Example:** `/help`

### `/help <module>`
Show help for a specific module.
- **Permissions:** Everyone
- **Example:** `/help moderation`

### `/start`
Start the bot (shows welcome message).
- **Permissions:** Everyone
- **Example:** `/start`

### `/about`
Show information about Nexus bot.
- **Permissions:** Everyone
- **Example:** `/about`

### `/ping`
Check bot latency.
- **Permissions:** Everyone
- **Example:** `/ping`

### `/version`
Show bot version.
- **Permissions:** Everyone
- **Example:** `/version`

### `/donate`
Show donation information.
- **Permissions:** Everyone
- **Example:** `/donate`

### `/support`
Get support contact information.
- **Permissions:** Everyone
- **Example:** `/support`

### `/feedback <message>`
Send feedback to bot developers.
- **Permissions:** Everyone
- **Example:** `/feedback Great bot!`

### `/privacy`
View privacy policy.
- **Permissions:** Everyone
- **Example:** `/privacy`

### `/deleteaccount`
Request deletion of your data.
- **Permissions:** Everyone
- **Example:** `/deleteaccount`

### `/me`
View your profile.
- **Permissions:** Everyone
- **Example:** `/me`

### `/profile [@user]`
View user profile.
- **Permissions:** Everyone
- **Example:** `/profile @username`

### `/badges`
View available badges.
- **Permissions:** Everyone
- **Example:** `/badges`

### `/achievements`
View your achievements.
- **Permissions:** Everyone
- **Example:** `/achievements`

### `/rank [@user]`
View user rank and level.
- **Permissions:** Everyone
- **Example:** `/rank @username`

### `/streak`
View your current streak.
- **Permissions:** Everyone
- **Example:** `/streak`

### `/level`
View your level and XP.
- **Permissions:** Everyone
- **Example:** `/level`

---

## 🎯 Tips & Best Practices

### Using Commands Efficiently

1. **Reply-First Moderation:** Most moderation commands work best when you reply to the message you want to act on. The bot will automatically detect the target user.

2. **Silent Mode:** Add `!` at the end of commands like `/warn!`, `/ban!`, `/mute!` to perform actions silently without announcements.

3. **Duration Parsing:** Use shorthand for durations: `30s` (30 seconds), `5m` (5 minutes), `2h` (2 hours), `1d` (1 day), `1w` (1 week).

4. **Mentions:** You can mention users by `@username`, reply to their message, or use their ID.

5. **Keyboard Shortcuts:** Many commands have aliases for faster typing (e.g., `/w` for `/warn`, `/m` for `/mute`).

### Mini App Usage

The Mini App provides a visual interface for:
- Module configuration
- Member management
- Analytics and reports
- Economy and reputation
- Custom bot token management
- Import/export settings

Access the Mini App via:
- Bot menu button (if enabled)
- `/settings` command
- Inline buttons in bot messages

---

## 🔧 Advanced Features

### Variables in Welcome/Notes

- `{first}` - User's first name
- `{last}` - User's last name
- `{fullname}` - Full name
- `{username}` - Username
- `{mention}` - User mention
- `{id}` - User ID
- `{count}` - Member count
- `{chatname}` - Group name
- `{rules}` - Group rules
- `{date}` - Current date
- `{time}` - Current time

### Formatting in Notes/Filters

**Markdown:**
- `*bold*` or `__bold__`
- `_italic_` or `*italic*`
- `[link](url)`
- `` `code` ``
- `~~strikethrough~~`

**HTML:**
- `<b>bold</b>`
- `<i>italic</i>`
- `<a href="url">link</a>`
- `<code>code</code>`
- `<pre>code block</pre>`
- `<u>underline</u>`
- `<s>strikethrough</s>`

### Buttons in Notes/Filters

- `[Text](buttonurl:URL)` - URL button
- `[Text](buttonurl:URL:same)` - URL button (same row)
- `[Text](callback:DATA)` - Callback button

---

## 📞 Support

For help, questions, or feedback:
- Use `/support` to get contact information
- Join our support group (link in `/start` message)
- Report bugs using `/feedback`

---

**Nexus Bot v1.0.0** - The Ultimate Telegram Bot Platform
