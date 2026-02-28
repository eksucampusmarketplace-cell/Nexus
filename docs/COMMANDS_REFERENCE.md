# Nexus Bot - Complete Command Reference

## Table of Contents
1. [Moderation Commands](#moderation)
2. [Welcome & Greetings](#welcome)
3. [Captcha](#captcha)
4. [Locks](#locks)
5. [Antispam](#antispam)
6. [Blocklist](#blocklist)
7. [Notes](#notes)
8. [Filters](#filters)
9. [Rules](#rules)
10. [Info](#info)
11. [Economy](#economy)
12. [Reputation](#reputation)
13. [Games](#games)
14. [Polls](#polls)
15. [Scheduler](#scheduler)
16. [AI Assistant](#ai-assistant)
17. [Analytics](#analytics)
18. [Federations](#federations)
19. [Connections](#connections)
20. [Approvals](#approvals)
21. [Cleaning](#cleaning)
22. [Pins](#pins)
23. [Languages](#languages)
24. [Formatting](#formatting)
25. [Echo](#echo)
26. [Disabled Commands](#disabled)
27. [Admin Logging](#admin-logging)
28. [Portability](#portability)
29. [Identity](#identity)
30. [Community](#community)
31. [Silent Actions](#silent-actions)
32. [Integrations](#integrations)
33. [Privacy](#privacy)

---

## MODERATION

### `/warn` or `/w` [reason]
**Description**: Warn a user. Works by reply or mention.
**Usage**: Reply to a message or mention a user
**Examples**:
- `/warn` (replying to a message)
- `/warn Spamming in the chat`
- `/w Inappropriate language`
**Permissions**: Admin/Moderator
**Alias**: `/w`

### `/warns` [@user]
**Description**: View a user's warning history.
**Usage**: Check your own warnings or another user's
**Examples**:
- `/warns` (your warnings)
- `/warns @username`
**Permissions**: Admin/Moderator

### `/resetwarns` [@user]
**Description**: Reset all warnings for a user.
**Usage**: Reply or mention user
**Examples**:
- `/resetwarns`
- `/resetwarns @username`
**Permissions**: Admin

### `/warnlimit` <number>
**Description**: Set the warning threshold. When reached, auto-action triggers.
**Default**: 3
**Examples**:
- `/warnlimit 5`
- `/warnlimit 2`
**Permissions**: Admin

### `/warntime` <duration>
**Description**: Set warning expiration time.
**Examples**:
- `/warntime 7d` (warnings expire after 7 days)
- `/warntime never`
**Permissions**: Admin

### `/warnmode` <action>
**Description**: Set auto-action after warning threshold.
**Options**: mute, kick, ban
**Default**: mute
**Examples**:
- `/warnmode mute`
- `/warnmode kick`
- `/warnmode ban`
**Permissions**: Admin

### `/mute` or `/m` or `/tm` [duration] [reason]
**Description**: Mute a user. Works by reply or mention.
**Duration formats**: 1s, 1m, 1h, 1d, 1w
**Examples**:
- `/mute` (permanent)
- `/mute 1h Spamming`
- `/m 24h Repeated violations`
- `/tm 1d` (temporary mute)
**Permissions**: Admin/Moderator
**Aliases**: `/m`, `/tm`

### `/unmute` or `/um` [@user]
**Description**: Unmute a user.
**Examples**:
- `/unmute`
- `/um @username`
**Permissions**: Admin
**Alias**: `/um`

### `/ban` or `/b` or `/tb` [duration] [reason]
**Description**: Ban a user. Works by reply or mention.
**Duration formats**: 1s, 1m, 1h, 1d, 1w (or permanent without duration)
**Examples**:
- `/ban` (permanent ban)
- `/ban 7d Spamming`
- `/b 30d Repeated violations`
- `/tb 1d` (temporary ban)
**Permissions**: Admin
**Aliases**: `/b`, `/tb`

### `/unban` or `/ub` [@user]
**Description**: Unban a user.
**Examples**:
- `/unban`
- `/ub @username`
**Permissions**: Admin
**Alias**: `/ub`

### `/kick` or `/k` [@user] [reason]
**Description**: Kick a user from the group. Works by reply or mention.
**Examples**:
- `/kick`
- `/kick @username Spamming`
- `/k Inappropriate behavior`
**Permissions**: Admin
**Alias**: `/k`

### `/kickme` [reason]
**Description**: Kick yourself from the group.
**Examples**:
- `/kickme`
- `/kickme Leaving group`
**Permissions**: All users

### `/promote` [@user] [role]
**Description**: Promote a user to admin or moderator.
**Roles**: admin, mod
**Examples**:
- `/promote` (promote to admin)
- `/promote @username admin`
- `/promote @username mod`
**Permissions**: Owner only

### `/demote` [@user]
**Description**: Demote a user from admin/moderator.
**Examples**:
- `/demote`
- `/demote @username`
**Permissions**: Owner only

### `/title` [title]
**Description**: Set custom admin title for a user. Reply to user.
**Examples**:
- `/title Moderator`
- `/title Head Admin`
- `/title` (clear title)
**Permissions**: Admin

### `/pin` [silent]
**Description**: Pin a message. Reply to the message.
**Examples**:
- `/pin`
- `/pin silent` (pin without notification)
**Permissions**: Admin

### `/unpin`
**Description**: Unpin a message. Reply to the message.
**Examples**:
- `/unpin`
**Permissions**: Admin

### `/unpinall`
**Description**: Unpin all messages in the group.
**Examples**:
- `/unpinall`
**Permissions**: Admin

### `/purge`
**Description**: Delete messages in a range. Reply to the last message to delete.
**Examples**:
- `/purge` (delete from replied message to command)
**Permissions**: Admin

### `/del`
**Description**: Delete a message. Reply to message or use on command message.
**Examples**:
- `/del` (delete replied message)
- `/del` (delete command message)
**Permissions**: Admin

### `/history` [@user]
**Description**: View a user's complete moderation history.
**Shows**: Warnings, mutes, bans, kicks, messages, trust score, XP, level, role
**Examples**:
- `/history`
- `/history @username`
**Permissions**: Moderator+

### `/trust` [@user]
**Description**: Trust a user (bypass some restrictions).
**Examples**:
- `/trust`
- `/trust @username`
**Permissions**: Admin

### `/untrust` [@user]
**Description**: Untrust a user.
**Examples**:
- `/untrust`
- `/untrust @username`
**Permissions**: Admin

### `/approve` [@user]
**Description**: Approve a user (bypass all restrictions).
**Examples**:
- `/approve`
- `/approve @username`
**Permissions**: Admin

### `/unapprove` [@user]
**Description**: Unapprove a user.
**Examples**:
- `/unapprove`
- `/unapprove @username`
**Permissions**: Admin

### `/approvals`
**Description**: List all approved users.
**Examples**:
- `/approvals`
**Permissions**: Moderator+

### `/report` [reason]
**Description**: Report a message to admins. Reply to the message.
**Examples**:
- `/report`
- `/report This is spam`
- `/report Inappropriate content`
**Permissions**: All users

### `/reports`
**Description**: View pending reports.
**Examples**:
- `/reports`
**Permissions**: Moderator+

### `/review` <report_id> <action>
**Description**: Review and resolve a report.
**Actions**: warn, mute, ban, kick, dismiss
**Examples**:
- `/review 123 warn`
- `/review 123 dismiss`
**Permissions**: Moderator+

### `/slowmode` <seconds> | off
**Description**: Enable or disable slow mode.
**Examples**:
- `/slowmode 30` (30 seconds between messages)
- `/slowmode off`
**Permissions**: Admin

### `/restrict` [@user] <permissions>
**Description**: Restrict user permissions.
**Permissions**: all, none, text, media, polls, links, invite
**Examples**:
- `/restrict @user text` (text only)
- `/restrict @user media` (text + media)
- `/restrict @user none` (no permissions)
**Permissions**: Admin

---

## WELCOME

### `/setwelcome` <content>
**Description**: Set welcome message.
**Variables**: {first}, {last}, {fullname}, {username}, {mention}, {id}, {count}, {chatname}, {rules}
**Examples**:
- `/setwelcome Welcome {first}!`
- `/setwelcome Hello {mention}! You are member #{count} of {chatname}`
- `/setwelcome Welcome! Please read the rules: {rules}`
**Permissions**: Admin

### `/welcome`
**Description**: View current welcome message.
**Examples**:
- `/welcome`
**Permissions**: All users

### `/resetwelcome`
**Description**: Reset welcome message to default.
**Examples**:
- `/resetwelcome`
**Permissions**: Admin

### `/setgoodbye` <content>
**Description**: Set goodbye message for users leaving.
**Variables**: Same as welcome
**Examples**:
- `/setgoodbye Goodbye {first}!`
**Permissions**: Admin

### `/goodbye`
**Description**: View current goodbye message.
**Examples**:
- `/goodbye`
**Permissions**: All users

### `/resetgoodbye`
**Description**: Reset goodbye message to default.
**Examples**:
- `/resetgoodbye`
**Permissions**: Admin

### `/cleanwelcome` [on|off]
**Description**: Auto-delete previous welcome messages.
**Examples**:
- `/cleanwelcome on`
- `/cleanwelcome off`
**Permissions**: Admin

### `/welcomemute` [on|off]
**Description**: Mute new members until they complete captcha.
**Examples**:
- `/welcomemute on`
- `/welcomemute off`
**Permissions**: Admin

### `/welcomehelp`
**Description**: Show welcome message help and variables.
**Examples**:
- `/welcomehelp`
**Permissions**: All users

---

## CAPTCHA

### `/captcha` <type>
**Description**: Set CAPTCHA type.
**Types**: button, math, quiz, image, emoji
**Examples**:
- `/captcha button`
- `/captcha math`
- `/captcha quiz`
- `/captcha image`
- `/captcha emoji`
**Permissions**: Admin

### `/captchatimeout` <seconds>
**Description**: Set CAPTCHA timeout.
**Default**: 90 seconds
**Examples**:
- `/captchatimeout 60`
- `/captchatimeout 120`
**Permissions**: Admin

### `/captchaaction` <action>
**Description**: Set action when CAPTCHA fails.
**Actions**: kick, ban, restrict
**Examples**:
- `/captchaaction kick`
- `/captchaaction ban`
- `/captchaaction restrict`
**Permissions**: Admin

### `/captchamute` [on|off]
**Description**: Mute users until they complete CAPTCHA.
**Examples**:
- `/captchamute on`
- `/captchamute off`
**Permissions**: Admin

### `/captchatext` <text>
**Description**: Set custom CAPTCHA message.
**Examples**:
- `/captchatext Please click the button to verify you're human`
**Permissions**: Admin

### `/captchareset`
**Description**: Reset CAPTCHA settings to default.
**Examples**:
- `/captchareset`
**Permissions**: Admin

---

## LOCKS

### `/lock` <type>
**Description**: Lock a content type.
**Types**: audio, bot, button, command, contact, document, email, forward, forward_channel, game, gif, inline, invoice, location, phone, photo, poll, rtl, spoiler, sticker, url, video, video_note, voice, mention, caption, no_caption, emoji_only, unofficial_client, arabic, farsi
**Examples**:
- `/lock url`
- `/lock sticker`
- `/lock links`
- `/lock images`
**Permissions**: Admin

### `/unlock` <type>
**Description**: Unlock a content type.
**Examples**:
- `/unlock url`
- `/unlock sticker`
**Permissions**: Admin

### `/locktype` <type> <mode> [duration]
**Description**: Set lock mode and duration.
**Modes**: delete, warn, kick, ban, tban TIME, tmute TIME
**Examples**:
- `/locktype url warn`
- `/locktype sticker mute 1h`
- `/locktype gif delete`
- `/locktype links ban 1d`
**Permissions**: Admin

### `/locks`
**Description**: List all active locks.
**Examples**:
- `/locks`
**Permissions**: All users

### `/locktypes`
**Description**: List all available lock types.
**Examples**:
- `/locktypes`
**Permissions**: All users

### `/lockchannel` <channel_id>
**Description**: Lock forwards from a specific channel.
**Examples**:
- `/lockchannel @channelname`
- `/lockchannel -1001234567890`
**Permissions**: Admin

---

## ANTISPAM

### `/antiflood` [limit] [window]
**Description**: Configure anti-flood settings.
**Default**: 5 messages in 5 seconds
**Examples**:
- `/antiflood 10 10` (10 messages in 10 seconds)
- `/antiflood off`
**Permissions**: Admin

### `/antifloodmedia` [limit]
**Description**: Configure media flood detection.
**Examples**:
- `/antifloodmedia 5` (5 media messages per window)
- `/antifloodmedia off`
**Permissions**: Admin

### `/antiraidthreshold` <number>
**Description**: Set raid detection threshold.
**Default**: 10 joins in 60 seconds
**Examples**:
- `/antiraidthreshold 20`
- `/antiraidthreshold 5`
**Permissions**: Admin

### `/antiraidaction` <action>
**Description**: Set action on raid detection.
**Actions**: lock, restrict, ban
**Examples**:
- `/antiraidaction lock`
- `/antiraidaction ban`
**Permissions**: Admin

### `/antifloodaction` <action>
**Description**: Set action on flood detection.
**Actions**: mute, kick, ban
**Examples**:
- `/antifloodaction mute`
- `/antifloodaction ban`
**Permissions**: Admin

---

## BLOCKLIST

### `/blocklist` <list_number>
**Description**: View blocked words list.
**Lists**: 1 or 2
**Examples**:
- `/blocklist 1`
- `/blocklist 2`
**Permissions**: Moderator+

### `/addblacklist` <word> <list_number> [regex]
**Description**: Add word to blocklist.
**Examples**:
- `/addblacklist spam 1`
- `/addblacklist .*\.com 2 regex`
**Permissions**: Moderator+

### `/rmblacklist` <word>
**Description**: Remove word from blocklist.
**Examples**:
- `/rmblacklist spam`
**Permissions**: Moderator+

### `/blacklistmode` <list_number> <action> [duration]
**Description**: Set blocklist action mode.
**Actions**: delete, warn, mute, kick, ban, tban, tmute
**Examples**:
- `/blacklistmode 1 delete`
- `/blacklistmode 2 mute 1h`
**Permissions**: Admin

### `/blacklistlist`
**Description**: List all blocked words.
**Examples**:
- `/blacklistlist`
**Permissions**: Moderator+

### `/blacklistclear` <list_number>
**Description**: Clear a blocklist.
**Examples**:
- `/blacklistclear 1`
**Permissions**: Admin

---

## NOTES

### `/save` <notename> <content>
**Description**: Save a note. Reply to media for media notes.
**Examples**:
- `/save rules Our group rules...`
- `/save meme` (reply to image)
**Permissions**: Admin/Moderator

### `#notename` or `/get` <notename>
**Description**: Retrieve a note.
**Examples**:
- `#rules`
- `/get rules`
**Permissions**: All users

### `/notes`
**Description**: List all notes.
**Examples**:
- `/notes`
**Permissions**: All users

### `/clear` <notename>
**Description**: Delete a note.
**Examples**:
- `/clear rules`
**Permissions**: Admin/Moderator

### `/clearall`
**Description:** Delete all notes.
**Examples**:
- `/clearall`
**Permissions**: Admin

---

## FILTERS

### `/filter` <trigger>
**Description**: Create or view a filter. Reply with response.
**Examples**:
- `/filter hello` (reply with "Hi there!")
- `/filter hello` (view existing filter)
**Permissions**: Admin/Moderator

### `/stop` <trigger>
**Description**: Remove a filter.
**Examples**:
- `/stop hello`
**Permissions**: Admin/Moderator

### `/stopall`
**Description**: Remove all filters.
**Examples**:
- `/stopall`
**Permissions**: Admin

### `/filters`
**Description**: List all filters.
**Examples**:
- `/filters`
**Permissions**: Moderator+

### `/filtermode` <trigger> <type>
**Description**: Set filter match type.
**Types**: exact, contains, regex, startswith, endswith, fuzzy
**Examples**:
- `/filtermode hello contains`
**Permissions**: Admin/Moderator

---

## RULES

### `/setrules` <content>
**Description**: Set group rules.
**Formatting**: Supports markdown and HTML
**Examples**:
- `/setrules 1. Be respectful\n2. No spam\n3. Follow Telegram TOS`
**Permissions**: Admin

### `/rules`
**Description**: View group rules.
**Examples**:
- `/rules`
**Permissions**: All users

### `/resetrules`
**Description**: Reset rules to default.
**Examples**:
- `/resetrules`
**Permissions**: Admin

### `/clearrules`
**Description**: Clear all rules.
**Examples**:
- `/clearrules`
**Permissions**: Admin

---

## INFO

### `/info` [@user]
**Description**: View user information.
**Shows**: ID, username, name, status, common groups, XP, level, badges
**Examples**:
- `/info`
- `/info @username`
**Permissions**: All users

### `/chatinfo`
**Description**: View group information.
**Shows**: ID, title, username, member count, admins, settings
**Examples**:
- `/chatinfo`
**Permissions**: All users

### `/id` [@user]
**Description**: Get user or chat ID.
**Examples**:
- `/id`
- `/id @username`
**Permissions**: All users

### `/adminlist`
**Description**: List all admins in the group.
**Examples**:
- `/adminlist`
**Permissions**: All users

---

## ECONOMY

### `/balance` [@user]
**Description**: Check wallet balance.
**Examples**:
- `/balance`
- `/balance @username`
**Permissions**: All users

### `/daily`
**Description**: Claim daily bonus.
**Cooldown**: 24 hours
**Examples**:
- `/daily`
**Permissions**: All users

### `/give` @user <amount>
**Description**: Send coins to another user.
**Examples**:
- `/give @username 100`
**Permissions**: All users

### `/leaderboard` [type]
**Description**: View economy leaderboard.
**Types**: coins, xp (default: coins)
**Examples**:
- `/leaderboard`
- `/leaderboard xp`
**Permissions**: All users

### `/transactions`
**Description**: View your recent transactions.
**Examples**:
- `/transactions`
**Permissions**: All users

### `/gamble` <amount>
**Description**: Gamble coins.
**Win chance**: 50%
**Examples**:
- `/gamble 50`
**Permissions**: All users

### `/slots` <amount>
**Description**: Play slot machine.
**Examples**:
- `/slots 10`
**Permissions**: All users

### `/roulette` <amount>
**Description**: Play roulette.
**Examples**:
- `/roulette 20`
**Permissions**: All users

### `/coinflip` <amount> [heads|tails]
**Description**: Flip a coin.
**Examples**:
- `/coinflip 10 heads`
- `/coinflip 10`
**Permissions**: All users

### `/dice` <amount>
**Description**: Roll dice.
**Examples**:
- `/dice 5`
**Permissions**: All users

### `/wheel` <amount>
**Description**: Spin the wheel.
**Examples**:
- `/wheel 15`
**Permissions**: All users

### `/shop`
**Description**: View shop items.
**Examples**:
- `/shop`
**Permissions**: All users

### `/buy` <item>
**Description**: Buy an item from shop.
**Examples**:
- `/buy premium`
**Permissions**: All users

### `/sell` <item>
**Description:** Sell an item.
**Examples**:
- `/sell premium`
**Permissions**: All users

### `/inventory`
**Description**: View your inventory.
**Examples**:
- `/inventory`
**Permissions**: All users

---

## REPUTATION

### `/rep` [@user] [+1|-1]
**Description**: Give or remove reputation.
**Cooldown**: 5 minutes between reps
**Examples**:
- `/rep @username +1`
- `/rep -1`
- `/rep` (rep user you're replying to)
**Permissions**: All users

### `/reputation` [@user]
**Description**: View user's reputation.
**Examples**:
- `/reputation`
- `/reputation @username`
**Permissions**: All users

### `/repleaderboard`
**Description**: View reputation leaderboard.
**Examples**:
- `/repleaderboard`
**Permissions**: All users

---

## GAMES

### `/trivia` [category] [difficulty]
**Description**: Start a trivia game.
**Categories**: general, science, history, geography, entertainment, sports
**Difficulty**: easy, medium, hard
**Examples**:
- `/trivia`
- `/trivia science hard`
**Permissions**: All users

### `/quiz`
**Description**: Start a quiz.
**Examples**:
- `/quiz`
**Permissions**: All users

### `/wordle`
**Description**: Play Wordle.
**Examples**:
- `/wordle`
**Permissions**: All users

### `/hangman`
**Description**: Play Hangman.
**Examples**:
- `/hangman`
**Permissions**: All users

### `/chess` [@opponent]
**Description**: Start a chess game.
**Examples**:
- `/chess`
- `/chess @username`
**Permissions**: All users

### `/tictactoe` [@opponent]
**Description**: Play Tic Tac Toe.
**Examples**:
- `/tictactoe`
- `/tictactoe @username`
**Permissions**: All users

### `/rps` [@opponent] [choice]
**Description**: Play Rock Paper Scissors.
**Choices**: rock, paper, scissors
**Examples**:
- `/rps`
- `/rps @username`
- `/rps rock`
**Permissions**: All users

### `/dice`
**Description**: Roll dice (1-6).
**Examples**:
- `/dice`
**Permissions**: All users

### `/coinflip`
**Description**: Flip a coin.
**Examples**:
- `/coinflip`
**Permissions**: All users

### `/wheel`
**Description**: Spin the wheel.
**Examples**:
- `/wheel`
**Permissions**: All users

### `/memory`
**Description**: Play memory card game.
**Examples**:
- `/memory`
**Permissions**: All users

### `/guessnumber`
**Description**: Guess the number game.
**Examples**:
- `/guessnumber`
**Permissions**: All users

### `/unscramble`
**Description**: Unscramble the word.
**Examples**:
- `/unscramble`
**Permissions**: All users

### `/typerace`
**Description**: Start a typing race.
**Examples**:
- `/typerace`
**Permissions**: All users

### `/mathrace`
**Description**: Math race game.
**Examples**:
- `/mathrace`
**Permissions**: All users

### `/wyr`
**Description**: Would You Rather.
**Examples**:
- `/wyr`
**Permissions**: All users

### `/truth`
**Description**: Truth question.
**Examples**:
- `/truth`
**Permissions**: All users

### `/dare`
**Description**: Dare challenge.
**Examples**:
- `/dare`
**Permissions**: All users

### `/8ball`
**Description**: Magic 8-Ball.
**Examples**:
- `/8ball Will I win?`
**Permissions**: All users

---

## POLLS

### `/poll` <question>
**Description**: Create a poll.
**Examples**:
- `/poll What should we have for dinner?`
**Permissions**: Moderator+

### `/strawpoll` <question>
**Description**: Create a straw poll.
**Examples**:
- `/strawpoll Which movie should we watch?`
**Permissions**: All users

### `/vote`
**Description**: Vote on active poll.
**Examples**:
- `/vote 1`
**Permissions**: All users

### `/closepoll`
**Description**: Close current poll.
**Examples**:
- `/closepoll`
**Permissions**: Poll creator or Admin

---

## SCHEDULER

### `/schedule` <time> <message>
**Description**: Schedule a message.
**Time formats**: HH:MM, "tomorrow 9am", "Monday at 10am"
**Examples**:
- `/schedule 18:00 Meeting at 8pm`
- `/schedule tomorrow 9am Good morning everyone`
**Permissions**: Admin/Moderator

### `/recurring` <cron> <message>
**Description:** Schedule a recurring message.
**Cron format**: minute hour day month weekday
**Examples**:
- `/recurring "0 9 * * 1" Weekly announcement every Monday 9am`
- `/recurring "0 */6 * * *" Every 6 hours`
**Permissions**: Admin

### `/unschedule` <id>
**Description**: Cancel a scheduled message.
**Examples**:
- `/unschedule 1`
**Permissions**: Admin/Moderator

### `/listschedules`
**Description**: List all scheduled messages.
**Examples**:
- `/listschedules`
**Permissions**: Admin/Moderator

### `/cleanschedules`
**Description**: Clear all scheduled messages.
**Examples**:
- `/cleanschedules`
**Permissions**: Admin

---

## AI ASSISTANT

### `/ai` <prompt>
**Description**: Ask AI anything.
**Examples**:
- `/ai What should we do for the group event?`
- `/ai Summarize the last 50 messages`
**Permissions**: All users

### `/summarize` <N>
**Description**: Summarize last N messages.
**Examples**:
- `/summarize 50`
- `/summarize 100`
**Permissions**: All users

### `/translate` <text>
**Description**: Translate text. Reply to message or provide text.
**Examples**:
- `/translate`
- `/translate Hello`
**Permissions**: All users

### `/factcheck` <claim>
**Description**: Fact-check a claim. Reply to message.
**Examples**:
- `/factcheck`
- `/factcheck The earth is flat`
**Permissions**: All users

### `/scam` <text>
**Description**: Check for scam. Reply to suspicious message.
**Examples**:
- `/scam`
- `/scam Click here to win`
**Permissions**: All users

### `/draft` <topic>
**Description**: AI draft an announcement.
**Examples**:
- `/draft announcement about our weekly event`
**Permissions**: Admin/Moderator

### `/recommendation`
**Description**: Get AI recommendations.
**Examples**:
- `/recommendation Who should I promote?`
**Permissions**: Admin/Moderator

---

## ANALYTICS

### `/stats`
**Description**: View group statistics.
**Examples**:
- `/stats`
**Permissions**: Admin

### `/activity` [days]
**Description**: View activity over time.
**Examples**:
- `/activity`
- `/activity 7`
**Permissions**: Admin

### `/members`
**Description**: View member statistics.
**Examples**:
- `/members`
**Permissions**: Admin

### `/growth`
**Description**: View group growth.
**Examples**:
- `/growth`
**Permissions**: Admin

### `/heatmap`
**Description**: View activity heatmap.
**Examples**:
- `/heatmap`
**Permissions**: Admin

---

## FEDERATIONS

### `/newfed` <name>
**Description**: Create a new federation.
**Examples**:
- `/newfed MyFed`
**Permissions**: All users

### `/joinfed` <fed_id>
**Description**: Join a federation.
**Examples**:
- `/joinfed 12345678-1234-5678-1234-567812345678`
**Permissions**: Admin

### `/leavefed`
**Description**: Leave current federation.
**Examples**:
- `/leavefed`
**Permissions**: Admin

### `/fedinfo`
**Description**: View federation info.
**Examples**:
- `/fedinfo`
**Permissions**: All users

### `/fban` @user <reason>
**Description**: Federation ban.
**Examples**:
- `/fban @username Spamming across feds`
**Permissions**: Fed Admin

### `/unfban` @user
**Description**: Remove federation ban.
**Examples**:
- `/unfban @username`
**Permissions**: Fed Admin

### `/fedadmins`
**Description**: List federation admins.
**Examples**:
- `/fedadmins`
**Permissions**: Fed Admin

### `/addfedadmin` @user
**Description**: Add federation admin.
**Examples**:
- `/addfedadmin @username`
**Permissions**: Fed Owner

### `/rmfedadmin` @user
**Description**: Remove federation admin.
**Examples**:
- `/rmfedadmin @username`
**Permissions**: Fed Owner

### `/fedbans`
**Description**: List federation bans.
**Examples**:
- `/fedbans`
**Permissions**: Fed Admin

### `/myfeds`
**Description**: List your federations.
**Examples**:
- `/myfeds`
**Permissions**: All users

### `/fedchats`
**Description**: List groups in federation.
**Examples**:
- `/fedchats`
**Permissions**: Fed Admin

### `/exportfedbans`
**Description**: Export federation ban list.
**Examples**:
- `/exportfedbans`
**Permissions**: Fed Admin

### `/importfedbans`
**Description**: Import federation ban list.
**Examples**:
- `/importfedbans` (reply to file)
**Permissions**: Fed Admin

---

## CONNECTIONS

### `/connect` <group_id>
**Description**: Connect to a group from DM.
**Examples**:
- `/connect -1001234567890`
**Permissions**: Admin (in connected group)

### `/disconnect` <group_id>
**Description**: Disconnect from a group.
**Examples**:
- `/disconnect -1001234567890`
**Permissions**: All users

### `/connected`
**Description**: List your connected groups.
**Examples**:
- `/connected`
**Permissions**: All users

### `/connections`
**Description**: Manage your connections.
**Examples**:
- `/connections`
**Permissions**: All users

---

## APPROVALS

### `/approve` @user
**Description**: Approve a user.
**Examples**:
- `/approve @username`
**Permissions**: Admin

### `/unapprove` @user
**Description:** Unapprove a user.
**Examples**:
- `/unapprove @username`
**Permissions**: Admin

### `/approvals`
**Description**: List approved users.
**Examples**:
- `/approvals`
**Permissions**: Moderator+

### `/approved`
**Description**: Check if a user is approved.
**Examples**:
- `/approved`
**Permissions**: All users

---

## CLEANING

### `/cleanservice` [on|off]
**Description**: Auto-delete join/leave service messages.
**Examples**:
- `/cleanservice on`
- `/cleanservice off`
**Permissions**: Admin

### `/cleancommands` [on|off]
**Description**: Auto-delete command messages.
**Examples**:
- `/cleancommands on`
- `/cleancommands off`
**Permissions**: Admin

### `/clean` <count>
**Description**: Delete last N bot messages.
**Examples**:
- `/clean 10`
**Permissions**: Admin

---

## PINS

### `/permapin`
**Description**: Pin and announce message permanently.
**Examples**:
- `/permapin`
**Permissions**: Admin

### `/antipin` [on|off]
**Description**: Prevent non-admins from pinning.
**Examples**:
- `/antipin on`
- `/antipin off`
**Permissions**: Admin

### `/pinned`
**Description**: List pinned messages.
**Examples**:
- `/pinned`
**Permissions**: All users

---

## LANGUAGES

### `/setlang` <language>
**Description**: Set bot language for this group.
**Languages**: en, es, fr, de, ru, ar, zh, ja, ko, etc.
**Examples**:
- `/setlang en`
- `/setlang es`
**Permissions**: Admin

### `/lang`
**Description**: View current language.
**Examples**:
- `/lang`
**Permissions**: All users

### `/languages`
**Description**: List available languages.
**Examples**:
- `/languages`
**Permissions**: All users

---

## FORMATTING

### `/markdownhelp`
**Description**: Show markdown formatting help.
**Examples**:
- `/markdownhelp`
**Permissions**: All users

### `/formattinghelp`
**Description**: Show formatting help.
**Examples**:
- `/formattinghelp`
**Permissions**: All users

### `/bold` <text>
**Description**: Format text as bold.
**Examples**:
- `/bold Hello World`
**Permissions**: All users

### `/italic` <text>
**Description**: Format text as italic.
**Examples**:
- `/italic Hello World`
**Permissions**: All users

### `/underline` <text>
**Description**: Format text as underlined.
**Examples**:
- `/underline Hello World`
**Permissions**: All users

### `/strikethrough` <text>
**Description**: Format text as strikethrough.
**Examples**:
- `/strikethrough Hello World`
**Permissions**: All users

### `/code` <text>
**Description**: Format text as code.
**Examples**:
- `/code print("Hello")`
**Permissions**: All users

### `/pre` <text>
**Description**: Format text as preformatted code block.
**Examples**:
- `/pre print("Hello")`
**Permissions**: All users

---

## ECHO

### `/echo` <text>
**Description**: Bot repeats the text with formatting.
**Examples**:
- `/echo Hello <b>World</b>!`
**Permissions**: Admin/Moderator

### `/say` <text>
**Description:** Bot says the text.
**Examples**:
- `/say Hello everyone!`
**Permissions**: Admin/Moderator

---

## DISABLED

### `/disable` <command>
**Description**: Disable a command.
**Examples**:
- `/disable balance`
- `/disable daily`
**Permissions**: Admin

### `/enable` <command>
**Description**: Enable a disabled command.
**Examples**:
- `/enable balance`
**Permissions**: Admin

### `/disabled`
**Description**: List disabled commands.
**Examples**:
- `/disabled`
**Permissions**: Moderator+

### `/enableall`
**Description**: Enable all commands.
**Examples**:
- `/enableall`
**Permissions**: Admin

---

## ADMIN_LOGGING

### `/logchannel`
**Description**: Set log channel.
**Examples**:
- `/logchannel @logchannel`
**Permissions**: Admin

### `/setlog` <channel>
**Description**: Set log channel for specific actions.
**Examples**:
- `/setlog @logchannel`
**Permissions**: Admin

### `/unsetlog`
**Description**: Unset log channel.
**Examples**:
- `/unsetlog`
**Permissions**: Admin

### `/logtypes`
**Description**: Configure log types.
**Examples**:
- `/logtypes warn,ban,mute`
**Permissions**: Admin

---

## PORTABILITY

### `/export` [modules...]
**Description**: Export group settings.
**Modules**: admin, antiflood, blocklists, disabled, federations, filters, greetings, locks, notes, pins, raids, reports, rules, warnings
**Examples**:
- `/export`
- `/export notes filters rules`
**Permissions**: Admin

### `/import` <file>
**Description**: Import settings from file.
**Examples**:
- `/import` (reply to file)
**Permissions**: Admin

### `/exportall`
**Description**: Export all group settings.
**Examples**:
- `/exportall`
**Permissions**: Admin

### `/importall` <file>
**Description**: Import all settings from file.
**Examples**:
- `/importall` (reply to file)
**Permissions**: Admin

---

## IDENTITY

### `/me`
**Description**: View your profile.
**Shows**: Name, level, XP, trust score, badges, role
**Examples**:
- `/me`
**Permissions**: All users

### `/profile` [@user]
**Description**: View user profile.
**Examples**:
- `/profile`
- `/profile @username`
**Permissions**: All users

### `/level` [@user]
**Description**: View user level.
**Examples**:
- `/level`
- `/level @username`
**Permissions**: All users

### `/xp` [@user]
**Description**: View user XP.
**Examples**:
- `/xp`
- `/xp @username`
**Permissions**: All users

### `/badges` [@user]
**Description**: View user badges.
**Examples**:
- `/badges`
- `/badges @username`
**Permissions**: All users

### `/setbio` <text>
**Description**: Set your bio.
**Examples**:
- `/setbio I love coding!`
**Permissions**: All users

### `/setbirthday` <date>
**Description**: Set your birthday.
**Format**: YYYY-MM-DD
**Examples**:
- `/setbirthday 1990-01-15`
**Permissions**: All users

### `/settheme` <theme>
**Description:** Set your profile theme (Mini App).
**Examples**:
- `/settheme dark`
**Permissions**: All users

---

## COMMUNITY

### `/event`
**Description**: Create/view events.
**Examples**:
- `/event`
**Permissions**: All users

### `/events`
**Description**: List upcoming events.
**Examples**:
- `/events`
**Permissions**: All users

### `/rsvp` <event_id> <status>
**Description**: RSVP to an event.
**Status**: yes, no, maybe
**Examples**:
- `/rsvp 1 yes`
**Permissions**: All users

### `/milestone` <title>
**Description**: Create a milestone.
**Examples**:
- `/milestone We reached 1000 members!`
**Permissions**: Admin

### `/digest`
**Description**: View weekly digest.
**Examples**:
- `/digest`
**Permissions**: All users

### `/spotlight`
**Description**: View member spotlight.
**Examples**:
- `/spotlight`
**Permissions**: All users

### `/birthday` [@user]
**Description**: View birthdays.
**Examples**:
- `/birthday`
- `/birthday @username`
**Permissions**: All users

### `/birthdays`
**Description**: List upcoming birthdays.
**Examples**:
- `/birthdays`
**Permissions**: All users

---

## SILENT_ACTIONS

### `/silence` [on|off]
**Description**: Enable/disable silent mode for all actions.
**Examples**:
- `/silence on`
- `/silence off`
**Permissions**: Admin

### `/quietmode` [on|off]
**Description:** Enable/disable quiet mode.
**Examples**:
- `/quietmode on`
- `/quietmode off`
**Permissions**: Admin

---

## INTEGRATIONS

### `/reddit` <subreddit>
**Description**: Enable Reddit auto-posting.
**Examples**:
- `/reddit r/technology`
**Permissions**: Admin

### `/twitter` <handle>
**Description**: Enable Twitter integration.
**Examples**:
- `/twitter @username`
**Permissions**: Admin

### `/youtube` <channel_id>
**Description**: Enable YouTube integration.
**Examples**:
- `/youtube UC...`
**Permissions**: Admin

### `/weather` <city>
**Description**: Get weather.
**Examples**:
- `/weather London`
**Permissions**: All users

### `/convert` <amount> <from> <to>
**Description**: Currency converter.
**Examples**:
- `/convert 100 USD EUR`
**Permissions**: All users

### `/price` <crypto>
**Description**: Get crypto price.
**Examples**:
- `/price BTC`
**Permissions**: All users

### `/wiki` <query>
**Description**: Wikipedia search.
**Examples**:
- `/wiki Albert Einstein`
**Permissions**: All users

---

## PRIVACY

### `/privacy`
**Description**: View privacy policy.
**Examples**:
- `/privacy`
**Permissions**: All users

### `/forgetme`
**Description**: Delete your data from this group.
**Examples**:
- `/forgetme`
**Permissions**: All users

### `/deletemydata`
**Description**: Delete all your data across all groups.
**Examples**:
- `/deletemydata`
**Permissions**: All users

### `/exportmydata`
**Description**: Export all your data.
**Examples**:
- `/exportmydata`
**Permissions**: All users

---

## COMMAND STATISTICS

### Total Commands: 300+
### Total Modules: 33
### Commands per Module: 5-25 average

---

## COMMAND CATEGORIES

### Admin Only: ~150 commands
### Moderator+: ~100 commands
### All Users: ~50 commands

---

## COMMAND ALIASES

### Common Aliases:
- `/w` = `/warn`
- `/m` = `/mute`
- `/um` = `/unmute`
- `/b` = `/ban`
- `/ub` = `/unban`
- `/k` = `/kick`
- `/tm` = `/tmute`
- `/tb` = `/tban`
- `/rep` = `/reputation`

---

## SILENT MODE

All moderation commands support silent mode by adding `!` at the end:
- `/ban!` (silent ban)
- `/mute!` (silent mute)
- `/warn!` (silent warn)

---

This is a complete reference for all 300+ commands available in Nexus bot.
