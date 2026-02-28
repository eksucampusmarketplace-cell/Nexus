# Nexus Bot - Comprehensive Testing Guide

## Overview
This guide provides step-by-step instructions for testing all implemented features of the Nexus bot on Telegram.

---

## 🚀 Quick Start

### 1. Start the Bot
```
/start
```

**Expected Output**: Welcome message with quick start options and feature overview

### 2. View All Commands
```
/commands
```

**Expected Output**: Categorized list of all available commands

### 3. View Help for Specific Command
```
/help warn
```

**Expected Output**: Detailed help for the warn command including usage, examples, and permissions

---

## 🛡️ Moderation Testing

### Test Warn System
1. **Test basic warn** (as admin):
   ```
   /warn @username Spamming
   ```
   **Expected**: User warned, history displayed

2. **Test silent warn**:
   ```
   /warn! @username Violating rules
   ```
   **Expected**: User warned without announcement

3. **Test warn by reply**:
   - Reply to a user's message
   - Send `/warn Inappropriate content`
   **Expected**: Warning issued to replied user

4. **View warnings**:
   ```
   /warns @username
   ```
   **Expected**: List of all warnings for user

5. **Reset warnings**:
   ```
   /resetwarns @username
   ```
   **Expected**: All warnings cleared

### Test Mute System
1. **Test temporary mute**:
   ```
   /mute @username 1h Spamming
   ```
   **Expected**: User muted for 1 hour

2. **Test permanent mute**:
   ```
   /mute @username Repeated violations
   ```
   **Expected**: User muted permanently

3. **Test unmute**:
   ```
   /unmute @username
   ```
   **Expected**: User unmuted

4. **Test mute by duration format**:
   ```
   /mute 30m
   /mute 2h
   /mute 1d
   /mute 1w
   ```
   **Expected**: All duration formats work

### Test Ban System
1. **Test ban**:
   ```
   /ban @username Spamming
   ```
   **Expected**: User banned permanently

2. **Test temporary ban**:
   ```
   /tban @username 7d
   ```
   **Expected**: User banned for 7 days

3. **Test unban**:
   ```
   /unban @username
   ```
   **Expected**: User unbanned

### Test Kick System
1. **Test kick**:
   ```
   /kick @username
   ```
   **Expected**: User kicked from group

2. **Test kickme**:
   ```
   /kickme
   ```
   **Expected**: You are kicked from group

### Test Pin/Unpin
1. **Test pin**:
   - Reply to a message
   - Send `/pin`
   **Expected**: Message pinned

2. **Test silent pin**:
   - Reply to a message
   - Send `/pin silent`
   **Expected**: Message pinned without notification

3. **Test unpin**:
   - Reply to a pinned message
   - Send `/unpin`
   **Expected**: Message unpinned

4. **Test unpinall**:
   ```
   /unpinall
   ```
   **Expected**: All pinned messages unpinned

### Test Purge/Delete
1. **Test purge**:
   - Reply to the last message you want to delete
   - Send `/purge`
   **Expected**: Messages from replied message to command deleted

2. **Test del**:
   - Reply to a message
   - Send `/del`
   **Expected**: Replied message and command deleted

### Test History
1. **View user history**:
   ```
   /history @username
   ```
   **Expected**: Complete moderation history with warnings, mutes, bans, kicks

### Test Trust/Approve
1. **Trust user**:
   ```
   /trust @username
   ```
   **Expected**: User trusted

2. **Untrust user**:
   ```
   /untrust @username
   ```
   **Expected**: User untrusted

3. **Approve user**:
   ```
   /approve @username
   ```
   **Expected**: User approved

4. **View approved users**:
   ```
   /approvals
   ```
   **Expected**: List of approved users

### Test Report System
1. **Report a message**:
   - Reply to a message
   - Send `/report This is spam`
   **Expected**: Report submitted to admins

2. **View reports** (as admin):
   ```
   /reports
   ```
   **Expected**: List of pending reports

### Test Promote/Demote
1. **Promote to admin** (as owner):
   ```
   /promote @username admin
   ```
   **Expected**: User promoted to admin

2. **Promote to mod**:
   ```
   /promote @username mod
   ```
   **Expected**: User promoted to moderator

3. **Demote**:
   ```
   /demote @username
   ```
   **Expected**: User demoted to member

4. **Set custom title**:
   - Reply to admin
   - Send `/title Head Mod`
   **Expected**: Custom title set

### Test Slow Mode
1. **Enable slow mode**:
   ```
   /slowmode 30
   ```
   **Expected**: 30 second delay between messages

2. **Disable slow mode**:
   ```
   /slowmode off
   ```
   **Expected**: Slow mode disabled

### Test Restrictions
1. **Restrict to text only**:
   ```
   /restrict @username text
   ```
   **Expected**: User can only send text

2. **Restrict all**:
   ```
   /restrict @username none
   ```
   **Expected**: User cannot send anything

3. **Restrict links**:
   ```
   /restrict @username links
   ```
   **Expected**: User cannot send links

---

## 🚫 Antispam Testing

### Test Anti-Flood
1. **Set flood limit**:
   ```
   /antiflood 10 10
   ```
   **Expected**: 10 messages per 10 seconds allowed

2. **Set flood action**:
   ```
   /antifloodaction mute
   ```
   **Expected**: Flooding users are muted

3. **Test flood detection**:
   - Send 10+ messages quickly
   **Expected**: Anti-flood triggered

### Test Media Flood
1. **Set media flood limit**:
   ```
   /antifloodmedia 5
   ```
   **Expected**: 5 media messages allowed

2. **Test media flood**:
   - Send 5+ images/videos quickly
   **Expected**: Media flood triggered

### Test Anti-Raid
1. **Set raid threshold**:
   ```
   /antiraidthreshold 20
   ```
   **Expected**: 20 joins in 60 seconds triggers raid protection

2. **Set raid action**:
   ```
   /antiraidaction lock
   ```
   **Expected**: Group locks on raid

3. **Test raid detection** (requires multiple accounts):
   - Have 20+ users join within 60 seconds
   **Expected**: Raid protection triggered

---

## 🔒 Locks Testing

### Test Basic Locks
1. **Lock URLs**:
   ```
   /lock url
   ```
   **Expected**: URLs are deleted/blocked

2. **Test sending URL**:
   - Try sending `https://example.com`
   **Expected**: Message deleted or action taken

3. **Unlock URLs**:
   ```
   /unlock url
   ```
   **Expected**: URLs allowed again

### Test All Lock Types
Test each lock type:
```
/lock audio
/lock sticker
/lock gif
/lock photo
/lock video
/lock voice
/lock document
/lock contact
/lock poll
/lock forward
```

### Test Lock with Mode
1. **Warn on URL**:
   ```
   /lock url warn
   ```
   **Expected**: URLs trigger warnings

2. **Mute on sticker**:
   ```
   /lock sticker mute 1h
   ```
   **Expected**: Sticker usage triggers 1h mute

3. **Ban on GIF**:
   ```
   /lock gif ban
   ```
   **Expected**: GIF usage triggers ban

### View Locks
1. **List all locks**:
   ```
   /locks
   ```
   **Expected**: List of all active locks

2. **View lock types**:
   ```
   /locktypes
   ```
   **Expected**: List of all available lock types

---

## 👋 Welcome Testing

### Test Welcome Message
1. **Set welcome**:
   ```
   /setwelcome Welcome {first}! You are member #{count}.
   ```
   **Expected**: Welcome message set

2. **Test variables**:
   ```
   /setwelcome Hello {mention}! Welcome to {chatname}.
   ```
   **Expected**: Variables work correctly

3. **View welcome**:
   ```
   /welcome
   ```
   **Expected**: Current welcome message displayed

4. **Test with new member**:
   - Have a new user join the group
   **Expected**: Welcome message sent

### Test Welcome Media
1. **Set media welcome**:
   - Reply to a photo/video
   - Send `/setwelcome Welcome {first}!`
   **Expected**: Media welcome set

### Test Goodbye
1. **Set goodbye**:
   ```
   /setgoodbye Goodbye {first}!
   ```
   **Expected**: Goodbye message set

2. **Test with leaving member**:
   - Have a user leave the group
   **Expected**: Goodbye message sent

### Test Clean Welcome
1. **Enable clean welcome**:
   ```
   /cleanwelcome on
   ```
   **Expected**: Previous welcome messages auto-deleted

### Test Welcome Mute
1. **Enable welcome mute**:
   ```
   /welcomemute on
   ```
   **Expected**: New members muted until captcha

---

## 🔐 Captcha Testing

### Test CAPTCHA Types
1. **Set button CAPTCHA**:
   ```
   /captcha button
   ```
   **Expected**: New members see button CAPTCHA

2. **Set math CAPTCHA**:
   ```
   /captcha math
   ```
   **Expected**: New members solve math problem

3. **Set quiz CAPTCHA**:
   ```
   /captcha quiz
   ```
   **Expected**: New members answer quiz question

4. **Set image CAPTCHA**:
   ```
   /captcha image
   ```
   **Expected**: New users identify images

5. **Set emoji CAPTCHA**:
   ```
   /captcha emoji
   ```
   **Expected**: New users select emojis

### Test CAPTCHA Configuration
1. **Set timeout**:
   ```
   /captchatimeout 120
   ```
   **Expected**: 120 seconds to solve CAPTCHA

2. **Set action on fail**:
   ```
   /captchaaction ban
   ```
   **Expected**: Failed CAPTCHA triggers ban

3. **Set mute on join**:
   ```
   /captchamute on
   ```
   **Expected**: New members muted until CAPTCHA

4. **Set custom message**:
   ```
   /captchatext Click to verify you're human!
   ```
   **Expected**: Custom CAPTCHA message displayed

### Test CAPTCHA Flow
1. **New user joins**:
   - Have a new user join
   **Expected**: CAPTCHA displayed, user muted

2. **User solves CAPTCHA**:
   - User completes CAPTCHA
   **Expected**: User unmuted, welcome sent

3. **User fails CAPTCHA**:
   - User doesn't solve within timeout
   **Expected**: Action taken (kick/ban/restrict)

---

## 📝 Notes Testing

### Test Save Notes
1. **Save text note**:
   ```
   /save rules Our group rules: 1. Be respectful
   ```
   **Expected**: Note saved as "rules"

2. **Save media note**:
   - Reply to an image/video/GIF
   - Send `/save meme`
   **Expected**: Media note saved

### Test Retrieve Notes
1. **Retrieve by hashtag**:
   ```
   #rules
   ```
   **Expected**: Rules note displayed

2. **Retrieve by command**:
   ```
   /get meme
   ```
   **Expected**: Meme note displayed

### Test List Notes
1. **View all notes**:
   ```
   /notes
   ```
   **Expected**: List of all saved notes

### Test Delete Notes
1. **Delete specific note**:
   ```
   /clear rules
   ```
   **Expected**: Rules note deleted

2. **Delete all notes**:
   ```
   /clearall
   ```
   **Expected**: All notes deleted

---

## 🔍 Filters Testing

### Test Create Filters
1. **Create text filter**:
   - Reply with "Hi there!"
   - Send `/filter hello`
   **Expected**: Filter created, "hello" triggers "Hi there!"

2. **Create media filter**:
   - Reply to a sticker
   - Send `/filter react`
   **Expected**: Sticker filter created

### Test Filter Match Types
1. **Set exact match**:
   ```
   /filtermode hello exact
   ```
   **Expected**: Only "hello" exact match triggers

2. **Set contains match**:
   ```
   /filtermode help contains
   ```
   **Expected**: Any message containing "help" triggers

3. **Set regex match**:
   ```
   /filtermode email regex
   ```
   **Expected**: Regex pattern matches email

4. **Set startswith**:
   ```
   /filtermode !admin startswith
   ```
   **Expected**: Messages starting with "!admin" trigger

5. **Set endswith**:
   ```
   /filtermode ? endswith
   ```
   **Expected**: Messages ending with "?" trigger

### Test Filter Actions
1. **Set warn action**:
   - Create filter with response that includes `|warn`
   **Expected**: Filter triggers warning

2. **Set mute action**:
   - Create filter with response that includes `|mute 1h`
   **Expected**: Filter triggers 1h mute

3. **Set ban action**:
   - Create filter with response that includes `|ban`
   **Expected**: Filter triggers ban

4. **Set delete action**:
   - Create filter with response that includes `|delete`
   **Expected**: Message deleted

### Test Delete Trigger
1. **Create filter that deletes trigger**:
   - Set filter with admin-only option
   **Expected**: Trigger message deleted

### Test View Filters
1. **List all filters**:
   ```
   /filters
   ```
   **Expected**: List of all active filters

### Test Remove Filters
1. **Remove specific filter**:
   ```
   /stop hello
   ```
   **Expected**: "hello" filter removed

2. **Remove all filters**:
   ```
   /stopall
   ```
   **Expected**: All filters removed

---

## 📜 Rules Testing

### Test Set Rules
1. **Set basic rules**:
   ```
   /setrules 1. Be respectful
   ```
   **Expected**: Rules set

2. **Set formatted rules**:
   ```
   /setrules *1. Be respectful*
   ```
   **Expected**: Formatted rules set

3. **Set multi-line rules**:
   ```
   /setrules 1. Be respectful\n2. No spam\n3. Follow TOS
   ```
   **Expected**: Multi-line rules set

### Test View Rules
1. **View rules**:
   ```
   /rules
   ```
   **Expected**: Current rules displayed

### Test Reset Rules
1. **Reset to default**:
   ```
   /resetrules
   ```
   **Expected**: Rules reset to default

2. **Clear rules**:
   ```
   /clearrules
   ```
   **Expected**: All rules cleared

---

## ℹ️ Info Testing

### Test User Info
1. **View own info**:
   ```
   /info
   ```
   **Expected**: Your user info displayed

2. **View other user**:
   ```
   /info @username
   ```
   **Expected**: User info displayed

### Test Group Info
1. **View group info**:
   ```
   /chatinfo
   ```
   **Expected**: Group information displayed

### Test Get ID
1. **Get user ID**:
   ```
   /id
   ```
   **Expected**: Your user ID displayed

2. **Get other user ID**:
   ```
   /id @username
   ```
   **Expected**: User's ID displayed

### Test Admin List
1. **List admins**:
   ```
   /adminlist
   ```
   **Expected**: List of group admins displayed

---

## 🚫 Blocklist Testing

### Test Blocklist Management
1. **View blocklist 1**:
   ```
   /blocklist 1
   ```
   **Expected**: Words in blocklist 1 displayed

2. **Add word**:
   ```
   /addblacklist spam 1
   ```
   **Expected**: "spam" added to blocklist 1

3. **Add regex word**:
   ```
   /addblacklist .*\.com 2 regex
   ```
   **Expected**: Regex pattern added to blocklist 2

4. **Remove word**:
   ```
   /rmblacklist spam
   ```
   **Expected**: "spam" removed from blocklists

5. **Set blocklist mode**:
   ```
   /blacklistmode 1 delete
   ```
   **Expected**: Blocklist 1 action set to delete

6. **Clear blocklist**:
   ```
   /blacklistclear 1
   ```
   **Expected**: Blocklist 1 cleared

---

## 🧹 Cleaning Testing

### Test Clean Service Messages
1. **Enable service cleaning**:
   ```
   /cleanservice on
   ```
   **Expected**: Service messages auto-deleted

2. **Disable service cleaning**:
   ```
   /cleanservice off
   ```
   **Expected**: Service messages not deleted

### Test Clean Commands
1. **Enable command cleaning**:
   ```
   /cleancommands on
   ```
   **Expected**: Command messages auto-deleted

### Test Clean Bot Messages
1. **Clean last N messages**:
   ```
   /clean 10
   ```
   **Expected**: Last 10 bot messages deleted

2. **Clean all bot messages**:
   ```
   /cleanbot
   ```
   **Expected**: All bot messages deleted

---

## 📝 Formatting Testing

### Test Text Formatting
1. **Bold text**:
   ```
   /bold Hello World
   ```
   **Expected**: *Hello World*

2. **Italic text**:
   ```
   /italic Hello World
   ```
   **Expected**: _Hello World_

3. **Underline text**:
   ```
   /underline Hello World
   ```
   **Expected**: __Hello World__

4. **Strikethrough**:
   ```
   /strikethrough Hello World
   ```
   **Expected**: ~Hello World~

5. **Code**:
   ```
   /code print("Hello")
   ```
   **Expected**: `print("Hello")`

6. **Preformatted**:
   ```
   /pre def hello():
       print("World")
   ```
   **Expected**: Code block displayed

7. **Spoiler**:
   ```
   /spoiler Surprise!
   ```
   **Expected**: Spoiler text (tap to reveal)

### Test Links and Mentions
1. **Create link**:
   ```
   /link https://example.com Click Here
   ```
   **Expected**: Click Here (hyperlink)

2. **Create mention**:
   ```
   /mention 123456789 Click to mention
   ```
   **Expected**: Click to mention (mention)

### Test Emoji Search
1. **Search emoji**:
   ```
   /emoji heart
   ```
   **Expected**: Heart emojis displayed

2. **Search other emojis**:
   ```
   /emoji smile
   /emoji star
   /emoji fire
   ```
   **Expected**: Relevant emojis displayed

### View Formatting Help
1. **Markdown help**:
   ```
   /markdownhelp
   ```
   **Expected**: Detailed markdown guide displayed

2. **Formatting help**:
   ```
   /formattinghelp
   ```
   **Expected**: Quick formatting help displayed

---

## 📢 Echo Testing

### Test Echo
1. **Echo message**:
   ```
   /echo Hello <b>World</b>!
   ```
   **Expected**: Bot repeats message with formatting

### Test Say
1. **Bot says message**:
   ```
   /say Hello everyone!
   ```
   **Expected**: Bot sends message

### Test Broadcast
1. **Broadcast to all**:
   ```
   /broadcast Important announcement!
   ```
   **Expected**: Message sent to all members

### Test Announce
1. **Make announcement**:
   ```
   /announce Meeting at 8pm!
   ```
   **Expected**: Announcement sent and pinned

### Test Ping
1. **Check latency**:
   ```
   /ping
   ```
   **Expected**: Pong with latency

### Test Uptime
1. **View uptime**:
   ```
   /uptime
   ```
   **Expected**: Bot uptime displayed

### Test Version
1. **View version**:
   ```
   /version
   ```
   **Expected**: Bot version and info displayed

---

## 📖 Help System Testing

### Test Main Help
1. **View help menu**:
   ```
   /help
   ```
   **Expected**: Main help menu with categories displayed

### Test Command Help
1. **View specific command help**:
   ```
   /help warn
   ```
   **Expected**: Detailed help for warn command

2. **Test other commands**:
   ```
   /help mute
   /help ban
   /help info
   ```
   **Expected**: Detailed help for each command

### Test Commands List
1. **View all commands**:
   ```
   /commands
   ```
   **Expected**: All commands listed by category

2. **View category commands**:
   ```
   /commands moderation
   ```
   **Expected**: Moderation commands only

### Test Modules List
1. **View all modules**:
   ```
   /modules
   ```
   **Expected**: All modules listed with status

### Test Mod Help
1. **View moderation help**:
   ```
   /modhelp
   ```
   **Expected**: Moderation commands only

### Test Admin Help
1. **View admin commands**:
   ```
   /adminhelp
   ```
   **Expected**: Admin-only commands displayed

---

## ✅ Integration Testing

### Test Multi-Module Scenarios

1. **Welcome + Captcha Flow**:
   - User joins
   - Captcha displayed
   - User completes captcha
   - Welcome message sent
   - **Expected**: Smooth flow through welcome and captcha

2. **Locks + Anti-Flood**:
   - Enable URL lock
   - Enable anti-flood
   - User sends multiple URLs quickly
   - **Expected**: Both lock and anti-flood work

3. **Moderation + Reports**:
   - User gets warned
   - User's message reported
   - Admin reviews report
   - **Expected**: Full moderation workflow

4. **Notes + Filters**:
   - Create filter that triggers note
   - Send trigger message
   - **Expected**: Note displayed

### Test Permission Levels

1. **Admin Commands**:
   - Test all admin commands as admin
   - **Expected**: All commands work

2. **Moderator Commands**:
   - Test mod commands as moderator
   - **Expected**: Mod commands work, owner-only commands fail

3. **User Commands**:
   - Test user commands as regular user
   - **Expected**: User commands work, admin commands fail

### Test Edge Cases

1. **Empty arguments**:
   - Send `/warn` (no args)
   - **Expected**: Usage error message

2. **Invalid duration**:
   - Send `/mute abc`
   - **Expected**: Duration parse error

3. **Non-existent user**:
   - Send `/warn @nonexistent`
   - **Expected**: User not found error

4. **Already muted user**:
   - Mute user, try again
   - **Expected**: Already muted message

5. **Already banned user**:
   - Ban user, try again
   - **Expected**: Already banned message

---

## 🐛 Bug Reporting

If you find any bugs during testing:
1. Document the exact command sent
2. Note the expected vs actual behavior
3. Include error messages (if any)
4. Report via: `/report <description>`

---

## 📊 Testing Checklist

Use this checklist to track completed tests:

### Moderation
- [ ] Warn system
- [ ] Mute system
- [ ] Ban system
- [ ] Kick system
- [ ] Pin/Unpin
- [ ] Purge/Delete
- [ ] History
- [ ] Trust/Approve
- [ ] Reports
- [ ] Promote/Demote
- [ ] Slow mode
- [ ] Restrictions

### Antispam
- [ ] Anti-flood
- [ ] Media flood
- [ ] Anti-raid

### Locks
- [ ] All lock types
- [ ] Lock modes
- [ ] Lock channels

### Welcome & Captcha
- [ ] Welcome messages
- [ ] Goodbye messages
- [ ] All CAPTCHA types
- [ ] CAPTCHA configuration

### Notes & Filters
- [ ] Save notes
- [ ] Retrieve notes
- [ ] Create filters
- [ ] Filter types
- [ ] Filter actions

### Rules & Info
- [ ] Set rules
- [ ] User info
- [ ] Group info
- [ ] Admin list

### Blocklist
- [ ] Add words
- [ ] Remove words
- [ ] Blocklist modes

### Utilities
- [ ] Cleaning
- [ ] Formatting
- [ ] Echo
- [ ] Help system

---

## 🎯 Success Criteria

All features are working correctly if:
1. ✅ All commands execute without errors
2. ✅ Expected output matches actual output
3. ✅ Permission checks work correctly
4. ✅ Multi-module integration works smoothly
5. ✅ Edge cases are handled gracefully
6. ✅ User feedback is clear and helpful

---

**Last Updated**: 2025-02-28
**Test Coverage**: 100+ commands
**Estimated Test Time**: 2-4 hours for full coverage
