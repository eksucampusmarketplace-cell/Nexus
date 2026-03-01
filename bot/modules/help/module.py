"""Help module - Comprehensive help system for all Nexus modules."""

import os
from typing import Dict, List, Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.markdown import hbold, hcode, hitalic

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


def get_mini_app_keyboard():
    """Get inline keyboard with Mini App button."""
    mini_app_url = os.getenv("MINI_APP_URL", "")
    if mini_app_url:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚀 Open Mini App",
                        web_app=WebAppInfo(url=mini_app_url)
                    )
                ],
                [
                    InlineKeyboardButton(text="📚 Help", callback_data="help"),
                    InlineKeyboardButton(text="⚡ Commands", callback_data="commands")
                ]
            ]
        )
    return None


COMMAND_DETAILS: Dict[str, Dict] = {
    # Moderation
    "warn": {
        "usage": "/warn [@user|reply] [reason]",
        "examples": ["/warn @username Spamming", "/warn Breaking rules"],
        "category": "Moderation",
    },
    "warns": {
        "usage": "/warns [@user|reply]",
        "examples": ["/warns @username", "/warns (reply to user)"],
        "category": "Moderation",
    },
    "resetwarns": {
        "usage": "/resetwarns [@user|reply]",
        "examples": ["/resetwarns @username"],
        "category": "Moderation",
    },
    "warnlimit": {
        "usage": "/warnlimit <number>",
        "examples": ["/warnlimit 3", "/warnlimit 5"],
        "category": "Moderation",
    },
    "warntime": {
        "usage": "/warntime <duration>",
        "examples": ["/warntime 7d", "/warntime 30d"],
        "category": "Moderation",
    },
    "warnmode": {
        "usage": "/warnmode <mute|kick|ban>",
        "examples": ["/warnmode mute", "/warnmode ban"],
        "category": "Moderation",
    },
    "mute": {
        "usage": "/mute [@user|reply] [duration] [reason]",
        "examples": ["/mute @username 1h Spamming", "/mute 30m"],
        "category": "Moderation",
    },
    "unmute": {
        "usage": "/unmute [@user|reply]",
        "examples": ["/unmute @username"],
        "category": "Moderation",
    },
    "ban": {
        "usage": "/ban [@user|reply] [duration] [reason]",
        "examples": ["/ban @username Scammer", "/ban 7d Breaking rules", "/tban @user 1d"],
        "category": "Moderation",
    },
    "unban": {
        "usage": "/unban [@user|reply]",
        "examples": ["/unban @username"],
        "category": "Moderation",
    },
    "kick": {
        "usage": "/kick [@user|reply] [reason]",
        "examples": ["/kick @username Violating rules"],
        "category": "Moderation",
    },
    "kickme": {
        "usage": "/kickme",
        "examples": ["/kickme"],
        "category": "Moderation",
    },
    "promote": {
        "usage": "/promote [@user|reply] [admin|mod]",
        "examples": ["/promote @username admin", "/promote @username mod"],
        "category": "Moderation",
    },
    "demote": {
        "usage": "/demote [@user|reply]",
        "examples": ["/demote @username"],
        "category": "Moderation",
    },
    "title": {
        "usage": "/title <custom title> (reply to admin)",
        "examples": ["/title Head Moderator"],
        "category": "Moderation",
    },
    "pin": {
        "usage": "/pin [silent] (reply to message)",
        "examples": ["/pin", "/pin silent"],
        "category": "Moderation",
    },
    "unpin": {
        "usage": "/unpin (reply to message)",
        "examples": ["/unpin"],
        "category": "Moderation",
    },
    "unpinall": {
        "usage": "/unpinall",
        "examples": ["/unpinall"],
        "category": "Moderation",
    },
    "purge": {
        "usage": "/purge (reply to oldest message to delete)",
        "examples": ["/purge"],
        "category": "Moderation",
    },
    "del": {
        "usage": "/del (reply to message)",
        "examples": ["/del"],
        "category": "Moderation",
    },
    "history": {
        "usage": "/history [@user|reply]",
        "examples": ["/history @username"],
        "category": "Moderation",
    },
    "trust": {
        "usage": "/trust [@user|reply]",
        "examples": ["/trust @username"],
        "category": "Moderation",
    },
    "untrust": {
        "usage": "/untrust [@user|reply]",
        "examples": ["/untrust @username"],
        "category": "Moderation",
    },
    "approve": {
        "usage": "/approve [@user|reply]",
        "examples": ["/approve @username"],
        "category": "Moderation",
    },
    "unapprove": {
        "usage": "/unapprove [@user|reply]",
        "examples": ["/unapprove @username"],
        "category": "Moderation",
    },
    "approvals": {
        "usage": "/approvals",
        "examples": ["/approvals"],
        "category": "Moderation",
    },
    "report": {
        "usage": "/report [reason] (reply to message)",
        "examples": ["/report Spamming", "/report Offensive content"],
        "category": "Moderation",
    },
    "reports": {
        "usage": "/reports",
        "examples": ["/reports"],
        "category": "Moderation",
    },
    "review": {
        "usage": "/review <report_id> [warn|mute|ban|kick|dismiss]",
        "examples": ["/review 5 ban", "/review 3 dismiss"],
        "category": "Moderation",
    },
    "slowmode": {
        "usage": "/slowmode [seconds|off]",
        "examples": ["/slowmode 10", "/slowmode off"],
        "category": "Moderation",
    },
    "restrict": {
        "usage": "/restrict [@user|reply] <all|none|text|media|links|invite>",
        "examples": ["/restrict @username none", "/restrict @user text"],
        "category": "Moderation",
    },
    # Welcome
    "setwelcome": {
        "usage": "/setwelcome <message>",
        "examples": ["/setwelcome Welcome {first} to {chatname}!"],
        "category": "Welcome",
    },
    "welcome": {
        "usage": "/welcome",
        "examples": ["/welcome"],
        "category": "Welcome",
    },
    "resetwelcome": {
        "usage": "/resetwelcome",
        "examples": ["/resetwelcome"],
        "category": "Welcome",
    },
    "setgoodbye": {
        "usage": "/setgoodbye <message>",
        "examples": ["/setgoodbye Goodbye {first}!"],
        "category": "Welcome",
    },
    "goodbye": {
        "usage": "/goodbye",
        "examples": ["/goodbye"],
        "category": "Welcome",
    },
    "resetgoodbye": {
        "usage": "/resetgoodbye",
        "examples": ["/resetgoodbye"],
        "category": "Welcome",
    },
    "cleanwelcome": {
        "usage": "/cleanwelcome [on|off]",
        "examples": ["/cleanwelcome on", "/cleanwelcome off"],
        "category": "Welcome",
    },
    "welcomemute": {
        "usage": "/welcomemute [on|off]",
        "examples": ["/welcomemute on"],
        "category": "Welcome",
    },
    "welcomehelp": {
        "usage": "/welcomehelp",
        "examples": ["/welcomehelp"],
        "category": "Welcome",
    },
    # Anti-Spam
    "antiflood": {
        "usage": "/antiflood [limit] [window_seconds] [action]",
        "examples": ["/antiflood 5 5 mute", "/antiflood"],
        "category": "Anti-Spam",
    },
    "antiraid": {
        "usage": "/antiraid [threshold] [window] [action]",
        "examples": ["/antiraid 10 60 lock"],
        "category": "Anti-Spam",
    },
    "setcasban": {
        "usage": "/setcasban [on|off]",
        "examples": ["/setcasban on"],
        "category": "Anti-Spam",
    },
    # Locks
    "locktypes": {
        "usage": "/locktypes",
        "examples": ["/locktypes"],
        "category": "Locks",
    },
    "lock": {
        "usage": "/lock <type> [mode] [duration]",
        "examples": ["/lock links delete", "/lock sticker warn", "/lock url mute 1h"],
        "category": "Locks",
    },
    "unlock": {
        "usage": "/unlock <type>",
        "examples": ["/unlock links", "/unlock sticker"],
        "category": "Locks",
    },
    "locks": {
        "usage": "/locks",
        "examples": ["/locks"],
        "category": "Locks",
    },
    "lockall": {
        "usage": "/lockall",
        "examples": ["/lockall"],
        "category": "Locks",
    },
    "unlockall": {
        "usage": "/unlockall",
        "examples": ["/unlockall"],
        "category": "Locks",
    },
    # Notes
    "save": {
        "usage": "/save <notename> <content>",
        "examples": ["/save rules Please follow the rules!", "/save welcome Hi {first}"],
        "category": "Notes",
    },
    "note": {
        "usage": "/note <notename>  or  #notename",
        "examples": ["/note rules", "#welcome"],
        "category": "Notes",
    },
    "notes": {
        "usage": "/notes",
        "examples": ["/notes"],
        "category": "Notes",
    },
    "clear": {
        "usage": "/clear <notename>",
        "examples": ["/clear rules"],
        "category": "Notes",
    },
    "clearall": {
        "usage": "/clearall",
        "examples": ["/clearall"],
        "category": "Notes",
    },
    # Filters
    "filter": {
        "usage": "/filter <keyword> <response>",
        "examples": ["/filter hello Hi there!", "/filter spam You are banned for spamming"],
        "category": "Filters",
    },
    "filters": {
        "usage": "/filters",
        "examples": ["/filters"],
        "category": "Filters",
    },
    "stop": {
        "usage": "/stop <keyword>",
        "examples": ["/stop hello"],
        "category": "Filters",
    },
    "stopall": {
        "usage": "/stopall",
        "examples": ["/stopall"],
        "category": "Filters",
    },
    "filtermode": {
        "usage": "/filtermode <reply|delete|warn|mute|ban>",
        "examples": ["/filtermode delete", "/filtermode warn"],
        "category": "Filters",
    },
    "filterregex": {
        "usage": "/filterregex [on|off]",
        "examples": ["/filterregex on"],
        "category": "Filters",
    },
    "filtercase": {
        "usage": "/filtercase [on|off]",
        "examples": ["/filtercase off"],
        "category": "Filters",
    },
    # Rules
    "setrules": {
        "usage": "/setrules <rules text>",
        "examples": ["/setrules 1. Be kind\n2. No spam"],
        "category": "Rules",
    },
    "rules": {
        "usage": "/rules",
        "examples": ["/rules"],
        "category": "Rules",
    },
    "resetrules": {
        "usage": "/resetrules",
        "examples": ["/resetrules"],
        "category": "Rules",
    },
    # Economy
    "balance": {
        "usage": "/balance [@user]",
        "examples": ["/balance", "/balance @username"],
        "category": "Economy",
    },
    "daily": {
        "usage": "/daily",
        "examples": ["/daily"],
        "category": "Economy",
    },
    "give": {
        "usage": "/give @user <amount>",
        "examples": ["/give @username 100", "/pay @user 50"],
        "category": "Economy",
    },
    "leaderboard": {
        "usage": "/leaderboard",
        "examples": ["/leaderboard", "/lb"],
        "category": "Economy",
    },
    "transactions": {
        "usage": "/transactions",
        "examples": ["/transactions", "/tx"],
        "category": "Economy",
    },
    "shop": {
        "usage": "/shop",
        "examples": ["/shop"],
        "category": "Economy",
    },
    "buy": {
        "usage": "/buy <item_id>",
        "examples": ["/buy 1"],
        "category": "Economy",
    },
    "inventory": {
        "usage": "/inventory",
        "examples": ["/inventory", "/inv"],
        "category": "Economy",
    },
    "coinflip": {
        "usage": "/coinflip [heads|tails] <amount>",
        "examples": ["/coinflip heads 50", "/coinflip tails 100"],
        "category": "Economy",
    },
    "gamble": {
        "usage": "/gamble <amount>",
        "examples": ["/gamble 100"],
        "category": "Economy",
    },
    "rob": {
        "usage": "/rob @user",
        "examples": ["/rob @username"],
        "category": "Economy",
    },
    "beg": {
        "usage": "/beg",
        "examples": ["/beg"],
        "category": "Economy",
    },
    "work": {
        "usage": "/work",
        "examples": ["/work"],
        "category": "Economy",
    },
    "crime": {
        "usage": "/crime",
        "examples": ["/crime"],
        "category": "Economy",
    },
    "deposit": {
        "usage": "/deposit <amount|all>",
        "examples": ["/deposit 500", "/deposit all"],
        "category": "Economy",
    },
    "withdraw": {
        "usage": "/withdraw <amount|all>",
        "examples": ["/withdraw 200", "/withdraw all"],
        "category": "Economy",
    },
    "bank": {
        "usage": "/bank",
        "examples": ["/bank"],
        "category": "Economy",
    },
    "loan": {
        "usage": "/loan <amount>",
        "examples": ["/loan 1000"],
        "category": "Economy",
    },
    "repay": {
        "usage": "/repay <amount|all>",
        "examples": ["/repay all"],
        "category": "Economy",
    },
    # Reputation
    "rep": {
        "usage": "/rep [@user|reply]",
        "examples": ["/rep @username", "+rep (reply to user)"],
        "category": "Reputation",
    },
    "reputation": {
        "usage": "/reputation [@user]",
        "examples": ["/reputation", "/reputation @username"],
        "category": "Reputation",
    },
    "repleaderboard": {
        "usage": "/repleaderboard",
        "examples": ["/repleaderboard", "/replb"],
        "category": "Reputation",
    },
    # Scheduler
    "schedule": {
        "usage": "/schedule <time> <message>",
        "examples": ["/schedule 2h Reminder: meeting!", "/schedule 30m Check this out"],
        "category": "Scheduler",
    },
    "recurring": {
        "usage": "/recurring <cron> <message>",
        "examples": ["/recurring 0 9 * * * Good morning!", "/recur daily Good morning!"],
        "category": "Scheduler",
    },
    "listscheduled": {
        "usage": "/listscheduled",
        "examples": ["/listscheduled", "/schedlist"],
        "category": "Scheduler",
    },
    "cancelschedule": {
        "usage": "/cancelschedule <id>",
        "examples": ["/cancelschedule 1"],
        "category": "Scheduler",
    },
    "clearschedule": {
        "usage": "/clearschedule",
        "examples": ["/clearschedule"],
        "category": "Scheduler",
    },
    # Identity
    "me": {
        "usage": "/me",
        "examples": ["/me", "/profile", "/myprofile"],
        "category": "Identity",
    },
    "profile": {
        "usage": "/profile [@user]",
        "examples": ["/profile", "/profile @username"],
        "category": "Identity",
    },
    "rank": {
        "usage": "/rank [@user]",
        "examples": ["/rank", "/rank @username"],
        "category": "Identity",
    },
    "level": {
        "usage": "/level",
        "examples": ["/level"],
        "category": "Identity",
    },
    "xp": {
        "usage": "/xp",
        "examples": ["/xp"],
        "category": "Identity",
    },
    "streak": {
        "usage": "/streak",
        "examples": ["/streak"],
        "category": "Identity",
    },
    "badges": {
        "usage": "/badges",
        "examples": ["/badges", "/achievements"],
        "category": "Identity",
    },
    "achievements": {
        "usage": "/achievements",
        "examples": ["/achievements"],
        "category": "Identity",
    },
    "awardxp": {
        "usage": "/awardxp @user <amount>",
        "examples": ["/awardxp @username 100"],
        "category": "Identity",
    },
    "awardachievement": {
        "usage": "/awardachievement @user <achievement>",
        "examples": ["/awardachievement @username first_post"],
        "category": "Identity",
    },
    "setlevel": {
        "usage": "/setlevel @user <level>",
        "examples": ["/setlevel @username 10"],
        "category": "Identity",
    },
    # Community
    "match": {
        "usage": "/match",
        "examples": ["/match"],
        "category": "Community",
    },
    "interestgroups": {
        "usage": "/interestgroups",
        "examples": ["/interestgroups", "/interests"],
        "category": "Community",
    },
    "joingroup": {
        "usage": "/joingroup <group_name>",
        "examples": ["/joingroup gaming"],
        "category": "Community",
    },
    "leavegroup": {
        "usage": "/leavegroup <group_name>",
        "examples": ["/leavegroup gaming"],
        "category": "Community",
    },
    "creategroup": {
        "usage": "/creategroup <group_name>",
        "examples": ["/creategroup gaming"],
        "category": "Community",
    },
    "events": {
        "usage": "/events",
        "examples": ["/events"],
        "category": "Community",
    },
    "createevent": {
        "usage": "/createevent <name> <date> <description>",
        "examples": ["/createevent GameNight 2024-12-25 Let's play games!"],
        "category": "Community",
    },
    "rsvp": {
        "usage": "/rsvp <event_id>",
        "examples": ["/rsvp 1"],
        "category": "Community",
    },
    "myevents": {
        "usage": "/myevents",
        "examples": ["/myevents"],
        "category": "Community",
    },
    "topevents": {
        "usage": "/topevents",
        "examples": ["/topevents"],
        "category": "Community",
    },
    "celebrate": {
        "usage": "/celebrate @user",
        "examples": ["/celebrate @username"],
        "category": "Community",
    },
    "birthday": {
        "usage": "/birthday [MM-DD]",
        "examples": ["/birthday 12-25", "/birthday"],
        "category": "Community",
    },
    "birthdays": {
        "usage": "/birthdays",
        "examples": ["/birthdays"],
        "category": "Community",
    },
    "bio": {
        "usage": "/bio <text>",
        "examples": ["/bio I love coding!"],
        "category": "Community",
    },
    "membercount": {
        "usage": "/membercount",
        "examples": ["/membercount", "/members"],
        "category": "Community",
    },
    # Integrations
    "addrss": {
        "usage": "/addrss <url>",
        "examples": ["/addrss https://example.com/feed.rss"],
        "category": "Integrations",
    },
    "removerss": {
        "usage": "/removerss <url>",
        "examples": ["/removerss https://example.com/feed.rss"],
        "category": "Integrations",
    },
    "listrss": {
        "usage": "/listrss",
        "examples": ["/listrss"],
        "category": "Integrations",
    },
    "addyoutube": {
        "usage": "/addyoutube <channel_id>",
        "examples": ["/addyoutube UCxxxxxxxx"],
        "category": "Integrations",
    },
    "removeyoutube": {
        "usage": "/removeyoutube <channel_id>",
        "examples": ["/removeyoutube UCxxxxxxxx"],
        "category": "Integrations",
    },
    "listyoutube": {
        "usage": "/listyoutube",
        "examples": ["/listyoutube"],
        "category": "Integrations",
    },
    "addgithub": {
        "usage": "/addgithub <owner/repo>",
        "examples": ["/addgithub torvalds/linux"],
        "category": "Integrations",
    },
    "removegithub": {
        "usage": "/removegithub <owner/repo>",
        "examples": ["/removegithub torvalds/linux"],
        "category": "Integrations",
    },
    "listgithub": {
        "usage": "/listgithub",
        "examples": ["/listgithub"],
        "category": "Integrations",
    },
    "addwebhook": {
        "usage": "/addwebhook <url>",
        "examples": ["/addwebhook https://example.com/webhook"],
        "category": "Integrations",
    },
    "removewebhook": {
        "usage": "/removewebhook <url>",
        "examples": ["/removewebhook https://example.com/webhook"],
        "category": "Integrations",
    },
    "listwebhooks": {
        "usage": "/listwebhooks",
        "examples": ["/listwebhooks"],
        "category": "Integrations",
    },
    "addtwitter": {
        "usage": "/addtwitter @username",
        "examples": ["/addtwitter @elonmusk"],
        "category": "Integrations",
    },
    "removetwitter": {
        "usage": "/removetwitter @username",
        "examples": ["/removetwitter @elonmusk"],
        "category": "Integrations",
    },
    # Games
    "trivia": {
        "usage": "/trivia [category]",
        "examples": ["/trivia", "/trivia science"],
        "category": "Games",
    },
    "wordle": {
        "usage": "/wordle",
        "examples": ["/wordle"],
        "category": "Games",
    },
    "hangman": {
        "usage": "/hangman",
        "examples": ["/hangman"],
        "category": "Games",
    },
    "mathrace": {
        "usage": "/mathrace",
        "examples": ["/mathrace"],
        "category": "Games",
    },
    "typerace": {
        "usage": "/typerace",
        "examples": ["/typerace"],
        "category": "Games",
    },
    "8ball": {
        "usage": "/8ball <question>",
        "examples": ["/8ball Will I be rich?"],
        "category": "Games",
    },
    "roll": {
        "usage": "/roll [sides]",
        "examples": ["/roll", "/roll 20"],
        "category": "Games",
    },
    "flip": {
        "usage": "/flip",
        "examples": ["/flip"],
        "category": "Games",
    },
    "rps": {
        "usage": "/rps <rock|paper|scissors>",
        "examples": ["/rps rock", "/rps scissors"],
        "category": "Games",
    },
    "dice": {
        "usage": "/dice [bet]",
        "examples": ["/dice", "/dice 50"],
        "category": "Games",
    },
    "spin": {
        "usage": "/spin [bet]",
        "examples": ["/spin", "/spin 100"],
        "category": "Games",
    },
    "lottery": {
        "usage": "/lottery [tickets]",
        "examples": ["/lottery 5"],
        "category": "Games",
    },
    "blackjack": {
        "usage": "/blackjack <bet>",
        "examples": ["/blackjack 50"],
        "category": "Games",
    },
    "roulette": {
        "usage": "/roulette <bet> [number|color]",
        "examples": ["/roulette 50 red", "/roulette 100 7"],
        "category": "Games",
    },
    "slots": {
        "usage": "/slots <bet>",
        "examples": ["/slots 25"],
        "category": "Games",
    },
    "guessnumber": {
        "usage": "/guessnumber",
        "examples": ["/guessnumber"],
        "category": "Games",
    },
    "unscramble": {
        "usage": "/unscramble",
        "examples": ["/unscramble"],
        "category": "Games",
    },
    "quiz": {
        "usage": "/quiz",
        "examples": ["/quiz"],
        "category": "Games",
    },
    "tictactoe": {
        "usage": "/tictactoe @user",
        "examples": ["/tictactoe @username"],
        "category": "Games",
    },
    # Analytics
    "stats": {
        "usage": "/stats",
        "examples": ["/stats"],
        "category": "Analytics",
    },
    "activity": {
        "usage": "/activity [@user]",
        "examples": ["/activity", "/activity @username"],
        "category": "Analytics",
    },
    "top": {
        "usage": "/top",
        "examples": ["/top"],
        "category": "Analytics",
    },
    "chart": {
        "usage": "/chart [type]",
        "examples": ["/chart messages", "/chart members"],
        "category": "Analytics",
    },
    "sentiment": {
        "usage": "/sentiment",
        "examples": ["/sentiment"],
        "category": "Analytics",
    },
    "growth": {
        "usage": "/growth",
        "examples": ["/growth"],
        "category": "Analytics",
    },
    "heatmap": {
        "usage": "/heatmap",
        "examples": ["/heatmap"],
        "category": "Analytics",
    },
    "reportcard": {
        "usage": "/reportcard",
        "examples": ["/reportcard"],
        "category": "Analytics",
    },
    # AI Assistant
    "ai": {
        "usage": "/ai <question>",
        "examples": ["/ai Explain quantum computing", "/ai Write a welcome message"],
        "category": "AI Assistant",
    },
    "summarize": {
        "usage": "/summarize [count]",
        "examples": ["/summarize", "/summarize 50"],
        "category": "AI Assistant",
    },
    "translate": {
        "usage": "/translate <lang> <text>  or  reply to message",
        "examples": ["/translate en Hello", "/translate es (reply to message)"],
        "category": "AI Assistant",
    },
    "factcheck": {
        "usage": "/factcheck <claim>",
        "examples": ["/factcheck The Earth is flat"],
        "category": "AI Assistant",
    },
    "detectscam": {
        "usage": "/detectscam (reply to message)",
        "examples": ["/detectscam"],
        "category": "AI Assistant",
    },
    "draft": {
        "usage": "/draft <topic>",
        "examples": ["/draft Welcome announcement"],
        "category": "AI Assistant",
    },
    "suggestpromote": {
        "usage": "/suggestpromote @user",
        "examples": ["/suggestpromote @username"],
        "category": "AI Assistant",
    },
    "weeklyreport": {
        "usage": "/weeklyreport",
        "examples": ["/weeklyreport"],
        "category": "AI Assistant",
    },
    "whatidid": {
        "usage": "/whatidid",
        "examples": ["/whatidid"],
        "category": "AI Assistant",
    },
    # Info
    "info": {
        "usage": "/info [@user|reply]",
        "examples": ["/info @username", "/info (reply to user)"],
        "category": "Info",
    },
    "chatinfo": {
        "usage": "/chatinfo",
        "examples": ["/chatinfo"],
        "category": "Info",
    },
    "id": {
        "usage": "/id [@user|reply]",
        "examples": ["/id", "/id @username"],
        "category": "Info",
    },
    "adminlist": {
        "usage": "/adminlist",
        "examples": ["/adminlist"],
        "category": "Info",
    },
    # Polls
    "poll": {
        "usage": "/poll <question>\\n<option1>\\n<option2>...",
        "examples": ["/poll Favorite color?\\nRed\\nBlue\\nGreen"],
        "category": "Polls",
    },
    "closepoll": {
        "usage": "/closepoll <poll_id>",
        "examples": ["/closepoll 1"],
        "category": "Polls",
    },
    "vote": {
        "usage": "/vote <poll_id> <option>",
        "examples": ["/vote 1 A"],
        "category": "Polls",
    },
    "pollresults": {
        "usage": "/pollresults <poll_id>",
        "examples": ["/pollresults 1"],
        "category": "Polls",
    },
    "pollsettings": {
        "usage": "/pollsettings",
        "examples": ["/pollsettings"],
        "category": "Polls",
    },
    # Cleaning
    "cleanservice": {
        "usage": "/cleanservice [on|off]",
        "examples": ["/cleanservice on"],
        "category": "Cleaning",
    },
    "cleancommands": {
        "usage": "/cleancommands [on|off]",
        "examples": ["/cleancommands on"],
        "category": "Cleaning",
    },
    "clean": {
        "usage": "/clean",
        "examples": ["/clean"],
        "category": "Cleaning",
    },
    # Formatting
    "markdownhelp": {
        "usage": "/markdownhelp",
        "examples": ["/markdownhelp"],
        "category": "Formatting",
    },
    "formattinghelp": {
        "usage": "/formattinghelp",
        "examples": ["/formattinghelp"],
        "category": "Formatting",
    },
    "bold": {
        "usage": "/bold <text>",
        "examples": ["/bold Hello World"],
        "category": "Formatting",
    },
    "italic": {
        "usage": "/italic <text>",
        "examples": ["/italic Hello World"],
        "category": "Formatting",
    },
    "underline": {
        "usage": "/underline <text>",
        "examples": ["/underline Hello World"],
        "category": "Formatting",
    },
    "strike": {
        "usage": "/strike <text>",
        "examples": ["/strike Hello World"],
        "category": "Formatting",
    },
    "spoiler": {
        "usage": "/spoiler <text>",
        "examples": ["/spoiler Secret message"],
        "category": "Formatting",
    },
    "code": {
        "usage": "/code <text>",
        "examples": ["/code print('hello')"],
        "category": "Formatting",
    },
    "pre": {
        "usage": "/pre <text>",
        "examples": ["/pre code block here"],
        "category": "Formatting",
    },
    "link": {
        "usage": "/link <text> <url>",
        "examples": ["/link Click here https://example.com"],
        "category": "Formatting",
    },
    "button": {
        "usage": "/button <text> <url>",
        "examples": ["/button Visit Site https://example.com"],
        "category": "Formatting",
    },
    # Echo
    "echo": {
        "usage": "/echo <text>",
        "examples": ["/echo Hello everyone!"],
        "category": "Echo",
    },
    "say": {
        "usage": "/say <text>",
        "examples": ["/say Announcement text"],
        "category": "Echo",
    },
    # Captcha
    "captcha": {
        "usage": "/captcha <text|button|math|off>",
        "examples": ["/captcha button", "/captcha math", "/captcha off"],
        "category": "Captcha",
    },
    "captchatimeout": {
        "usage": "/captchatimeout <seconds>",
        "examples": ["/captchatimeout 120"],
        "category": "Captcha",
    },
    "captchaaction": {
        "usage": "/captchaaction <kick|ban|mute>",
        "examples": ["/captchaaction kick"],
        "category": "Captcha",
    },
    # Blocklist
    "blocklist": {
        "usage": "/blocklist",
        "examples": ["/blocklist"],
        "category": "Blocklist",
    },
    "addblacklist": {
        "usage": "/addblacklist <word>",
        "examples": ["/addblacklist spam", "/addblacklist badword"],
        "category": "Blocklist",
    },
    "rmblacklist": {
        "usage": "/rmblacklist <word>",
        "examples": ["/rmblacklist spam"],
        "category": "Blocklist",
    },
    "blacklistmode": {
        "usage": "/blacklistmode <delete|warn|mute|kick|ban>",
        "examples": ["/blacklistmode delete", "/blacklistmode warn"],
        "category": "Blocklist",
    },
    # Core
    "start": {
        "usage": "/start",
        "examples": ["/start"],
        "category": "Core",
    },
    "help": {
        "usage": "/help [command|category]",
        "examples": ["/help", "/help ban", "/help Moderation"],
        "category": "Core",
    },
    "about": {
        "usage": "/about",
        "examples": ["/about"],
        "category": "Core",
    },
    "ping": {
        "usage": "/ping",
        "examples": ["/ping"],
        "category": "Core",
    },
    "version": {
        "usage": "/version",
        "examples": ["/version"],
        "category": "Core",
    },
}

# Alias map for looking up commands by alias
ALIAS_MAP: Dict[str, str] = {
    "w": "warn",
    "m": "mute",
    "tm": "mute",
    "tmute": "mute",
    "um": "unmute",
    "b": "ban",
    "tb": "ban",
    "tban": "ban",
    "ub": "unban",
    "k": "kick",
    "bal": "balance",
    "wallet": "balance",
    "transfer": "give",
    "pay": "give",
    "lb": "leaderboard",
    "rich": "leaderboard",
    "tx": "transactions",
    "inv": "inventory",
    "+rep": "rep",
    "-rep": "rep",
    "repcheck": "reputation",
    "replb": "repleaderboard",
    "sched": "schedule",
    "delay": "schedule",
    "recur": "recurring",
    "cron": "recurring",
    "schedlist": "listscheduled",
    "ls": "listscheduled",
    "cancelsched": "cancelschedule",
    "cs": "cancelschedule",
    "profile": "me",
    "myprofile": "me",
    "p": "profile",
    "achievements": "badges",
    "findfriend": "match",
    "matchme": "match",
    "interests": "interestgroups",
    "groups": "interestgroups",
    "communities": "interestgroups",
    "joininterest": "joingroup",
    "joinig": "joingroup",
    "leaveinterest": "leavegroup",
    "leaveig": "leavegroup",
    "createig": "creategroup",
    "makegroup": "creategroup",
    "addevent": "createevent",
    "event": "createevent",
    "members": "membercount",
    "count": "membercount",
    "get": "note",
    "#": "note",
}

CATEGORIES: Dict[str, List[str]] = {
    "Core": ["start", "help", "about", "ping", "version"],
    "Moderation": [
        "warn", "warns", "resetwarns", "warnlimit", "warntime", "warnmode",
        "mute", "unmute", "ban", "unban", "kick", "kickme",
        "promote", "demote", "title", "pin", "unpin", "unpinall", "purge", "del",
        "history", "trust", "untrust", "approve", "unapprove", "approvals",
        "report", "reports", "review", "slowmode", "restrict",
    ],
    "Welcome": [
        "setwelcome", "welcome", "resetwelcome", "setgoodbye", "goodbye",
        "resetgoodbye", "cleanwelcome", "welcomemute", "welcomehelp",
    ],
    "Anti-Spam": ["antiflood", "antiraid", "setcasban"],
    "Locks": ["locktypes", "lock", "unlock", "locks", "lockall", "unlockall"],
    "Notes": ["save", "note", "notes", "clear", "clearall"],
    "Filters": ["filter", "filters", "stop", "stopall", "filtermode", "filterregex", "filtercase"],
    "Rules": ["setrules", "rules", "resetrules"],
    "Economy": [
        "balance", "daily", "give", "leaderboard", "transactions", "shop", "buy",
        "inventory", "coinflip", "gamble", "rob", "beg", "work", "crime",
        "deposit", "withdraw", "bank", "loan", "repay",
    ],
    "Reputation": ["rep", "reputation", "repleaderboard"],
    "Scheduler": ["schedule", "recurring", "listscheduled", "cancelschedule", "clearschedule"],
    "Identity": [
        "me", "profile", "rank", "level", "xp", "streak", "badges", "achievements",
        "awardxp", "awardachievement", "setlevel",
    ],
    "Community": [
        "match", "interestgroups", "joingroup", "leavegroup", "creategroup",
        "events", "createevent", "rsvp", "myevents", "topevents",
        "celebrate", "birthday", "birthdays", "bio", "membercount",
    ],
    "Integrations": [
        "addrss", "removerss", "listrss", "addyoutube", "removeyoutube", "listyoutube",
        "addgithub", "removegithub", "listgithub", "addwebhook", "removewebhook",
        "listwebhooks", "addtwitter", "removetwitter",
    ],
    "Games": [
        "trivia", "wordle", "hangman", "mathrace", "typerace", "8ball", "roll",
        "flip", "rps", "dice", "spin", "lottery", "blackjack", "roulette",
        "slots", "guessnumber", "unscramble", "quiz", "tictactoe",
    ],
    "Analytics": ["stats", "activity", "top", "chart", "sentiment", "growth", "heatmap", "reportcard"],
    "AI Assistant": [
        "ai", "summarize", "translate", "factcheck", "detectscam",
        "draft", "suggestpromote", "weeklyreport", "whatidid",
    ],
    "Info": ["info", "chatinfo", "id", "adminlist"],
    "Polls": ["poll", "closepoll", "vote", "pollresults", "pollsettings"],
    "Cleaning": ["cleanservice", "cleancommands", "clean"],
    "Formatting": [
        "markdownhelp", "formattinghelp", "bold", "italic", "underline",
        "strike", "spoiler", "code", "pre", "link", "button",
    ],
    "Echo": ["echo", "say"],
    "Captcha": ["captcha", "captchatimeout", "captchaaction"],
    "Blocklist": ["blocklist", "addblacklist", "rmblacklist", "blacklistmode"],
}

ADMIN_COMMANDS = {
    "warn", "warns", "resetwarns", "warnlimit", "warntime", "warnmode",
    "mute", "unmute", "ban", "unban", "kick",
    "promote", "demote", "title", "pin", "unpin", "unpinall", "purge", "del",
    "history", "trust", "untrust", "approve", "unapprove", "approvals",
    "reports", "review", "slowmode", "restrict",
    "setwelcome", "resetwelcome", "setgoodbye", "resetgoodbye", "cleanwelcome", "welcomemute",
    "antiflood", "antiraid", "setcasban",
    "lock", "unlock", "lockall", "unlockall", "lockchannel", "unlockchannel",
    "clear", "clearall",
    "filter", "filters", "stop", "stopall", "filtermode", "filterregex", "filtercase",
    "setrules", "resetrules",
    "listscheduled", "cancelschedule", "clearschedule",
    "awardxp", "awardachievement", "setlevel",
    "addrss", "removerss", "listrss",
    "addyoutube", "removeyoutube", "listyoutube",
    "addgithub", "removegithub", "listgithub",
    "addwebhook", "removewebhook", "listwebhooks",
    "addtwitter", "removetwitter",
    "closepoll", "pollsettings",
    "cleanservice", "cleancommands", "clean",
    "captcha", "captchatimeout", "captchaaction",
    "blocklist", "addblacklist", "rmblacklist", "blacklistmode",
    "draft", "suggestpromote", "weeklyreport",
}

CATEGORY_ICONS = {
    "Core": "⚙️",
    "Moderation": "🛡️",
    "Welcome": "👋",
    "Anti-Spam": "🚫",
    "Locks": "🔒",
    "Notes": "📝",
    "Filters": "🔍",
    "Rules": "📋",
    "Economy": "💰",
    "Reputation": "⭐",
    "Scheduler": "📅",
    "Identity": "🏆",
    "Community": "👥",
    "Integrations": "🔌",
    "Games": "🎮",
    "Analytics": "📊",
    "AI Assistant": "🤖",
    "Info": "ℹ️",
    "Polls": "📊",
    "Cleaning": "🧹",
    "Formatting": "✨",
    "Echo": "🔊",
    "Captcha": "🔐",
    "Blocklist": "🚫",
}


def _resolve_command(name: str) -> Optional[str]:
    """Resolve a command name or alias to its canonical name."""
    name = name.lower().lstrip("/")
    if name in COMMAND_DETAILS:
        return name
    if name in ALIAS_MAP:
        canonical = ALIAS_MAP[name]
        if canonical in COMMAND_DETAILS:
            return canonical
    return None


def _find_category(command: str) -> Optional[str]:
    """Find the category for a command."""
    details = COMMAND_DETAILS.get(command, {})
    if details.get("category"):
        return details["category"]
    for cat, cmds in CATEGORIES.items():
        if command in cmds:
            return cat
    return None


class HelpModule(NexusModule):
    """Comprehensive help system for all modules."""

    name = "help"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Complete help system for all Nexus modules"
    category = ModuleCategory.UTILITY

    commands = [
        CommandDef(name="start", description="Start bot and see welcome", admin_only=False),
        CommandDef(name="help", description="Show this help message", admin_only=False,
                   args="[command|category]"),
        CommandDef(name="about", description="About Nexus bot", admin_only=False),
        CommandDef(name="ping", description="Check bot latency", admin_only=False),
        CommandDef(name="version", description="Show bot version", admin_only=False),
    ]

    async def on_load(self, app):
        self.register_command("start", self.cmd_start)
        self.register_command("help", self.cmd_help)
        self.register_command("about", self.cmd_about)
        self.register_command("ping", self.cmd_ping)
        self.register_command("version", self.cmd_version)

    async def cmd_start(self, ctx: NexusContext):
        text = (
            f"👋 {hbold('Welcome to Nexus Bot!')} 🚀\n\n"
            f"{hbold('The Ultimate Telegram Bot Platform')} 🎉\n\n"
            f"📚 {hcode('/help')} - View all commands\n"
            f"📱 {hcode('/settings')} - Open settings panel\n"
            f"ℹ️ Use commands or open the Mini App for full control!\n\n"
            f"💡 {hitalic('Type /help <command> for detailed information')}"
        )
        keyboard = get_mini_app_keyboard()
        await ctx.reply(text, reply_markup=keyboard)

    async def cmd_help(self, ctx: NexusContext):
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if args:
            query = args[0].lower().lstrip("/")
            # Check if it's a category name (case-insensitive)
            matched_category = next(
                (cat for cat in CATEGORIES if cat.lower() == query), None
            )
            if matched_category:
                await self._show_category_help(ctx, matched_category)
            else:
                await self._show_command_help(ctx, query)
        else:
            await self._show_general_help(ctx)

    async def _show_command_help(self, ctx: NexusContext, command_name: str):
        canonical = _resolve_command(command_name)
        if not canonical:
            await ctx.reply(
                f"❌ Command {hcode(command_name)} not found.\n\n"
                f"Use {hcode('/help')} to see all categories, or "
                f"{hcode('/help <category>')} to list commands."
            )
            return

        details = COMMAND_DETAILS.get(canonical, {})
        category = _find_category(canonical)
        usage = details.get("usage", f"/{canonical}")
        examples = details.get("examples", [])
        is_admin = canonical in ADMIN_COMMANDS

        # Detect aliases pointing to this command
        aliases = [alias for alias, target in ALIAS_MAP.items() if target == canonical]

        text = f"📚 {hbold(f'/{canonical}')}\n"
        text += f"📂 {hbold('Category:')} {category or 'General'}\n\n"

        # Description from COMMAND_DETAILS or fallback
        desc = details.get("description", "")
        if not desc:
            # Look up from the module registry
            for cmds in CATEGORIES.values():
                if canonical in cmds:
                    break
        text += f"📝 {hbold('Description:')}\n"

        # Find description from command registry
        cmd_desc = self._get_command_description(canonical)
        text += f"{cmd_desc}\n\n"

        text += f"🔧 {hbold('Usage:')}\n{hcode(usage)}\n\n"

        if examples:
            text += f"📌 {hbold('Examples:')}\n"
            for ex in examples:
                text += f"• {hcode(ex)}\n"
            text += "\n"

        if aliases:
            text += f"🔀 {hbold('Aliases:')}\n"
            for alias in sorted(aliases):
                text += f"• {hcode('/' + alias)}\n"
            text += "\n"

        if is_admin:
            text += f"🔒 {hbold('Permissions:')} Admin Only\n"
        else:
            text += f"✅ {hbold('Permissions:')} Everyone\n"

        await ctx.reply(text)

    def _get_command_description(self, command: str) -> str:
        descriptions = {
            "warn": "Issue a warning to a user. After reaching the warn limit, automatic action is taken.",
            "warns": "View the active warnings for a user.",
            "resetwarns": "Clear all warnings for a user.",
            "warnlimit": "Set how many warnings trigger automatic action (default: 3).",
            "warntime": "Set warning expiration duration. Warnings older than this are ignored.",
            "warnmode": "Set the action taken when a user reaches the warn limit.",
            "mute": "Restrict a user from sending messages. Optionally set a duration.",
            "unmute": "Remove mute restrictions from a user.",
            "ban": "Permanently or temporarily ban a user from the group.",
            "unban": "Remove a ban, allowing the user back into the group.",
            "kick": "Remove a user from the group (they can rejoin).",
            "kickme": "Kick yourself from the group.",
            "promote": "Grant admin or moderator permissions to a user.",
            "demote": "Remove admin permissions from a user.",
            "title": "Set a custom title for an admin (reply to them).",
            "pin": "Pin a message in the group (reply to the message).",
            "unpin": "Unpin a pinned message.",
            "unpinall": "Unpin all pinned messages in the group.",
            "purge": "Delete all messages from the replied message up to this command.",
            "del": "Delete a specific message (reply to it).",
            "history": "View a user's full moderation history.",
            "trust": "Mark a user as trusted, bypassing some restrictions.",
            "untrust": "Remove trusted status from a user.",
            "approve": "Approve a user to bypass all group restrictions.",
            "unapprove": "Remove approval from a user.",
            "approvals": "List all approved users in the group.",
            "report": "Report a message to group admins for review.",
            "reports": "View pending reports submitted by members.",
            "review": "Review and take action on a reported message.",
            "slowmode": "Enable slow mode to limit how often users can send messages.",
            "restrict": "Set specific permissions for a user.",
            "setwelcome": "Set the welcome message shown to new members.",
            "welcome": "Preview the current welcome message.",
            "resetwelcome": "Reset the welcome message to the default.",
            "setgoodbye": "Set the goodbye message shown when members leave.",
            "goodbye": "Preview the current goodbye message.",
            "resetgoodbye": "Reset the goodbye message to the default.",
            "cleanwelcome": "Automatically delete the previous welcome message when a new one is sent.",
            "welcomemute": "Mute new members until they complete the CAPTCHA.",
            "welcomehelp": "Show available variables for welcome/goodbye messages.",
            "antiflood": "Configure anti-flood protection settings.",
            "antiraid": "Configure anti-raid protection settings.",
            "setcasban": "Enable or disable CAS (Combot Anti-Spam) ban checking.",
            "locktypes": "List all available content lock types.",
            "lock": "Prevent a specific content type from being sent.",
            "unlock": "Allow a previously locked content type.",
            "locks": "View all currently active content locks.",
            "lockall": "Lock all content types at once.",
            "unlockall": "Unlock all content types at once.",
            "save": "Save a note with a keyword for easy retrieval.",
            "note": "Retrieve a saved note by its keyword.",
            "notes": "List all saved notes in this group.",
            "clear": "Delete a specific saved note.",
            "clearall": "Delete all saved notes in this group.",
            "filter": "Create an auto-response that triggers on a keyword.",
            "filters": "List all active filters in the group.",
            "stop": "Delete a specific filter.",
            "stopall": "Delete all filters in the group.",
            "filtermode": "Set the default action taken when a filter is triggered.",
            "filterregex": "Enable or disable regex matching in filters.",
            "filtercase": "Enable or disable case-sensitive matching in filters.",
            "setrules": "Set the group rules.",
            "rules": "View the group rules.",
            "resetrules": "Clear the group rules.",
            "balance": "Check your coin balance or another user's balance.",
            "daily": "Claim your daily coin bonus.",
            "give": "Transfer coins to another user.",
            "leaderboard": "View the richest users in the group.",
            "transactions": "View your recent transaction history.",
            "shop": "Browse items available in the group shop.",
            "buy": "Purchase an item from the shop.",
            "inventory": "View items you own.",
            "coinflip": "Bet coins on a coin flip.",
            "gamble": "Bet coins on a 50/50 gamble.",
            "rob": "Attempt to steal coins from another user.",
            "beg": "Beg for a small amount of coins.",
            "work": "Work to earn coins (has a cooldown).",
            "crime": "Commit a crime for a chance at big rewards (has a cooldown).",
            "deposit": "Deposit coins into your bank for safekeeping.",
            "withdraw": "Withdraw coins from your bank.",
            "bank": "View your bank balance.",
            "loan": "Take out a loan (must be repaid with interest).",
            "repay": "Repay your outstanding loan.",
            "rep": "Give a reputation point to another user.",
            "reputation": "View a user's reputation score.",
            "repleaderboard": "View the users with the highest reputation.",
            "schedule": "Schedule a message to be sent at a future time.",
            "recurring": "Create a recurring scheduled message.",
            "listscheduled": "List all scheduled messages.",
            "cancelschedule": "Cancel a scheduled message.",
            "clearschedule": "Cancel all scheduled messages.",
            "me": "View your profile, XP, level, and badges.",
            "profile": "View another user's profile.",
            "rank": "View your rank and level in the group.",
            "level": "View your current level and XP.",
            "xp": "View your XP progress toward the next level.",
            "streak": "View your activity streak.",
            "badges": "View your earned badges and achievements.",
            "achievements": "View all available achievements.",
            "awardxp": "Award XP to a user (admin only).",
            "awardachievement": "Award an achievement to a user (admin only).",
            "setlevel": "Set a user's level (admin only).",
            "match": "Get matched with a compatible group member.",
            "interestgroups": "View all interest groups in this group.",
            "joingroup": "Join an interest group.",
            "leavegroup": "Leave an interest group.",
            "creategroup": "Create a new interest group.",
            "events": "View upcoming events in the group.",
            "createevent": "Create a new event.",
            "rsvp": "RSVP to an event.",
            "myevents": "View events you've RSVPed to.",
            "topevents": "View the most popular events.",
            "celebrate": "Send a celebration message for a member's milestone.",
            "birthday": "Set or view your birthday.",
            "birthdays": "View upcoming birthdays in the group.",
            "bio": "Set your personal bio displayed in your profile.",
            "membercount": "Show the current member count milestone.",
            "addrss": "Add an RSS feed to monitor for new posts.",
            "removerss": "Remove an RSS feed.",
            "listrss": "List all monitored RSS feeds.",
            "addyoutube": "Add a YouTube channel to monitor for new videos.",
            "removeyoutube": "Remove a YouTube channel.",
            "listyoutube": "List all monitored YouTube channels.",
            "addgithub": "Add a GitHub repository to monitor for commits/releases.",
            "removegithub": "Remove a GitHub repository.",
            "listgithub": "List all monitored GitHub repositories.",
            "addwebhook": "Add a webhook integration.",
            "removewebhook": "Remove a webhook integration.",
            "listwebhooks": "List all webhook integrations.",
            "addtwitter": "Add a Twitter/X account to monitor for new tweets.",
            "removetwitter": "Remove a Twitter/X account.",
            "trivia": "Start a trivia quiz game.",
            "wordle": "Play a game of Wordle.",
            "hangman": "Start a game of Hangman.",
            "mathrace": "Start a math race competition.",
            "typerace": "Start a typing speed race.",
            "8ball": "Ask the magic 8-ball a yes/no question.",
            "roll": "Roll a dice.",
            "flip": "Flip a coin.",
            "rps": "Play rock-paper-scissors against the bot.",
            "dice": "Roll a dice and optionally bet coins.",
            "spin": "Spin the wheel of fortune and optionally bet coins.",
            "lottery": "Enter the lottery for a chance to win big.",
            "blackjack": "Play a game of Blackjack.",
            "roulette": "Play roulette and bet on numbers or colors.",
            "slots": "Pull the slot machine lever.",
            "guessnumber": "Play a number guessing game.",
            "unscramble": "Unscramble a word puzzle.",
            "quiz": "Start a quiz game.",
            "tictactoe": "Play Tic-Tac-Toe against another user.",
            "stats": "View general group statistics.",
            "activity": "View message activity statistics.",
            "top": "View the top active users.",
            "chart": "Generate a chart of group statistics.",
            "sentiment": "Analyze the sentiment of recent messages.",
            "growth": "View member growth over time.",
            "heatmap": "View an activity heatmap by hour/day.",
            "reportcard": "Generate a full group analytics report card.",
            "ai": "Ask the AI assistant a question or request.",
            "summarize": "Summarize recent group messages using AI.",
            "translate": "Translate text to another language using AI.",
            "factcheck": "Check a claim for factual accuracy using AI.",
            "detectscam": "Analyze a message for potential scam content.",
            "draft": "Draft an announcement using AI.",
            "suggestpromote": "Get an AI suggestion on promoting a user.",
            "weeklyreport": "Generate a weekly group activity report.",
            "whatidid": "Summarize what you missed while away.",
            "info": "View detailed information about a user.",
            "chatinfo": "View information about this group.",
            "id": "Get the Telegram ID of a user or this chat.",
            "adminlist": "List all admins in the group.",
            "poll": "Create a poll for group members to vote on.",
            "closepoll": "Close a poll and show the final results.",
            "vote": "Cast a vote on an active poll.",
            "pollresults": "View the current results of a poll.",
            "pollsettings": "Configure poll settings for the group.",
            "cleanservice": "Automatically delete join/leave service messages.",
            "cleancommands": "Automatically delete command messages after processing.",
            "clean": "Delete recent bot messages.",
            "markdownhelp": "Show Markdown formatting syntax help.",
            "formattinghelp": "Show all formatting options including buttons.",
            "bold": "Send bold text.",
            "italic": "Send italic text.",
            "underline": "Send underlined text.",
            "strike": "Send strikethrough text.",
            "spoiler": "Send a spoiler-hidden message.",
            "code": "Send inline code.",
            "pre": "Send a preformatted code block.",
            "link": "Send a clickable hyperlink.",
            "button": "Send a message with an inline button.",
            "echo": "Repeat a message as the bot.",
            "say": "Make the bot say something.",
            "captcha": "Set the type of CAPTCHA for new members.",
            "captchatimeout": "Set how long new members have to complete the CAPTCHA.",
            "captchaaction": "Set what happens if a member fails the CAPTCHA.",
            "blocklist": "View all blocked words in this group.",
            "addblacklist": "Add a word to the blocked words list.",
            "rmblacklist": "Remove a word from the blocked words list.",
            "blacklistmode": "Set the action taken when a blocked word is detected.",
            "start": "Start the bot and see the welcome message.",
            "help": "Show the help menu. Use /help <command> for specific info.",
            "about": "Learn about Nexus Bot and its features.",
            "ping": "Check the bot's response time.",
            "version": "View the bot version and statistics.",
        }
        return descriptions.get(command, "No description available.")

    async def _show_category_help(self, ctx: NexusContext, category: str):
        commands = CATEGORIES.get(category, [])
        icon = CATEGORY_ICONS.get(category, "📦")

        text = f"{icon} {hbold(category + ' Commands')}\n\n"
        for cmd in commands:
            is_admin = cmd in ADMIN_COMMANDS
            lock = "🔒 " if is_admin else ""
            details = COMMAND_DETAILS.get(cmd, {})
            usage = details.get("usage", f"/{cmd}")
            text += f"{lock}{hcode('/' + cmd)} - {self._get_command_description(cmd)}\n"

        text += f"\n💡 Use {hcode('/help <command>')} for detailed info on any command."
        await ctx.reply(text)

    async def _show_general_help(self, ctx: NexusContext):
        text = f"📚 {hbold('Nexus Bot — Command Help')} 🎉\n\n"
        text += f"Use {hcode('/help <command>')} for details on a specific command.\n"
        text += f"Use {hcode('/help <category>')} to list commands in a category.\n\n"
        text += f"{hbold('Categories:')}\n\n"

        for i, (cat, cmds) in enumerate(CATEGORIES.items(), 1):
            icon = CATEGORY_ICONS.get(cat, "📦")
            text += f"{i}. {icon} {hbold(cat)} — {len(cmds)} commands\n"

        text += f"\n💡 {hitalic('Add me to a group to enable all features.')}"
        keyboard = get_mini_app_keyboard()
        await ctx.reply(text, reply_markup=keyboard)

    async def cmd_about(self, ctx: NexusContext):
        text = (
            f"🤖 {hbold('Nexus Bot')} v1.0.0\n\n"
            f"{hbold('The Ultimate Telegram Bot Platform')} 🚀\n\n"
            f"🎉 {hbold('Features:')}\n"
            f"• 27 production-ready modules\n"
            f"• 230+ commands\n"
            f"• Complete economy & reputation systems\n"
            f"• 20+ integrated games\n"
            f"• AI-powered assistant\n"
            f"• Beautiful Mini App dashboard\n"
            f"• Multi-token (white-label) support\n\n"
            f"🌟 {hbold('Built with:')}\n"
            f"• Python 3.12 + aiogram 3.x\n"
            f"• FastAPI + PostgreSQL + Redis\n"
            f"• React 18 + TypeScript\n"
            f"• Docker & Render deployment ready\n\n"
            f"💡 {hbold('Get Started:')}\n"
            f"• Add the bot to your group\n"
            f"• Type {hcode('/help')} to see all commands\n"
            f"• Type {hcode('/settings')} to open the Mini App\n\n"
            f"📖 {hbold('Open Source')} — AGPL-3.0 License"
        )
        await ctx.reply(text)

    async def cmd_ping(self, ctx: NexusContext):
        import time
        start = time.time()
        bot_info = await ctx.bot.get_me()
        latency = int((time.time() - start) * 1000)

        text = (
            f"🏓 {hbold('Pong!')} ⚡\n\n"
            f"🤖 Bot: {hcode(bot_info.username or bot_info.first_name)}\n"
            f"📊 Latency: {hbold(f'{latency}ms')}\n"
            f"⚙️ Status: {hcode('✅ Online')}"
        )
        await ctx.reply(text)

    async def cmd_version(self, ctx: NexusContext):
        text = (
            f"🤖 {hbold('Nexus Bot')} v1.0.0\n\n"
            f"📊 {hbold('Statistics:')}\n"
            f"• Modules: {hcode('27')}\n"
            f"• Commands: {hcode('230+')}\n"
            f"• Games: {hcode('20+')}\n"
            f"• Lock Types: {hcode('40+')}\n"
            f"• Achievements: {hcode('20+')}\n\n"
            f"🚀 {hbold('Deployment:')}\n"
            f"• Docker & Docker Compose ready\n"
            f"• Render (render.yaml) configured\n"
            f"• Any VPS with Docker support\n\n"
            f"🎉 {hbold('Ready for Production!')}"
        )
        await ctx.reply(text)
