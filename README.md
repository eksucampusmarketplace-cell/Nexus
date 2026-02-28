# Nexus - The Ultimate Telegram Bot Platform

Nexus is the most complete, modern, AI-native Telegram bot platform ever built. It combines every feature from MissRose, GroupHelp, Group-Bot, Combot, Shieldy, Guardian, Baymax, Group Butler, and every other notable Telegram bot into one unified, intelligent, fully configurable system.

## 🚀 Features Overview

### 📦 Modules: 27 Production-Ready
- **Core:** Moderation, Welcome, Anti-Spam, Locks, Notes, Filters, Rules
- **Gamification:** Economy, Reputation, Identity, Scheduler, Games
- **AI:** AI Assistant (GPT-4), Analytics, Sentiment Analysis
- **Community:** Community (events, interest groups, matching), Integrations
- **Utility:** Info, Polls, Cleaning, Formatting, Echo, Help
- **Advanced:** Captcha, Blocklist, Channels, Scraping, Bot Builder

### 🎮 Commands: 230+ Fully Documented
- **Moderation:** warn, mute, ban, kick, promote, demote, history, trust, approve, report, slowmode, etc.
- **Economy:** balance, daily, give, transfer, shop, buy, inventory, coinflip, gamble, rob, work, crime, bank, loan, repay
- **Reputation:** rep, +rep, -rep, reputation, repleaderboard
- **Identity:** me, profile, rank, level, xp, streak, badges, achievements
- **Community:** match, interestgroups, joingroup, creategroup, events, createevent, rsvp, myevents, celebrate, birthday, birthdays, bio, membercount
- **Integrations:** addrss, addyoutube, addgithub, addwebhook, addtwitter
- **Scheduler:** schedule, recurring, listscheduled, cancelschedule, clearschedule
- **Notes:** save, note, notes, clear, clearall
- **Filters:** filter, filters, stop, stopall, filtermode, filterregex, filtercase
- **Locks:** lock, unlock, locktypes, locks, lockall, unlockall
- **Games:** trivia, wordle, hangman, mathrace, typerace, 8ball, roll, flip, rps, dice, spin, lottery, blackjack, roulette, slots, guessnumber, unscramble, quiz, tictactoe
- **Analytics:** stats, activity, top, chart, sentiment, growth, heatmap, reportcard
- **AI Assistant:** ai, summarize, translate, factcheck, detectscam, draft, suggestpromote, weeklyreport, whatidid
- **Info:** info, chatinfo, id, adminlist
- **Polls:** poll, quiz, closepoll, vote, pollresults, pollsettings
- **Formatting:** bold, italic, underline, strike, spoiler, code, pre, link, button
- **Echo:** echo, say
- **Help:** help, start, about, ping, version, donate, support, feedback, privacy, deleteaccount
- **Cleaning:** cleanservice, cleancommands, clean
- **Captcha:** captcha, captchatimeout, captchaaction
- **Blocklist:** blocklist, addblacklist, rmblacklist, blacklistmode
- **Welcome:** setwelcome, welcome, resetwelcome, setgoodbye, goodbye, resetgoodbye, cleanwelcome, welcomemute, welcomehelp
- **Anti-Spam:** antiflood, antiraid, setcasban
- **Rules:** setrules, rules, resetrules

### 🎨 Multi-Token Architecture
- **Shared Bot Mode:** One central bot (@NexusBot) that any group can add
- **Custom Bot Tokens:** Group owners can use their own bot tokens (white-label mode)
- **Token Encryption:** All custom tokens encrypted at rest (Fernet)
- **Seamless Routing:** Automatic routing based on incoming webhook token
- **Unified Management:** Single admin panel for all tokens

### 🤖 AI-Native Design
- **GPT-4 Integration:** Advanced AI assistant powered by OpenAI GPT-4
- **Smart Moderation:** AI-powered content analysis, toxicity detection, spam detection
- **Content Generation:** AI-powered announcements, summaries, translations
- **Sentiment Analysis:** Track group sentiment trends over time
- **Automated Insights:** AI-powered recommendations for engagement and growth

### 💰 Complete Economy System
- **Wallet & Bank:** Virtual currency with savings and 5% daily interest
- **Loans:** Borrow up to 10x your balance with repayment tracking
- **Games:** Coin flip, gamble, dice, roulette, slots, blackjack
- **Shop System:** Purchase items, VIP badges, special abilities
- **Transactions:** Complete transaction history and transfer system
- **Tax System:** Configurable tax on transfers

### 📊 Complete Gamification
- **XP System:** Earn XP for messages with weekend multiplier
- **Levels:** 0-100 levels with automatic level-up announcements
- **Achievements:** 20+ achievements with automatic unlocking
- **Badges:** Visual badge system with emoji icons
- **Streaks:** Activity streaks (7-day, 30-day, 90-day milestones)
- **Reputation:** +rep/-rep system with cooldowns and limits
- **Leaderboards:** Economy and reputation leaderboards

### 🎮 Gaming Suite (20+ Games)
- **Trivia:** Multiple categories and difficulty levels
- **Word Games:** Wordle, Hangman, Unscramble
- **Math Games:** Math Race
- **Casino:** Coin Flip, Dice, Roulette, Slots, Blackjack
- **Party Games:** 8-Ball, Rock-Paper-Scissors, Tic-Tac-Toe
- **Betting Games:** All games support economy integration

### 👥 Community Features
- **Member Matching:** Find like-minded members automatically
- **Interest Groups:** Create and join topic-based communities
- **Events:** Create events with RSVPs, times, locations
- **Celebrations:** Celebrate member milestones and achievements
- **Birthdays:** Track birthdays and send automatic wishes
- **Profile Bios:** Set custom bio (280 character limit)
- **Member Milestones:** Track and announce member count milestones

### 🔌 External Integrations
- **RSS Feeds:** Add RSS feeds with auto-posting
- **YouTube:** Monitor channels and post new videos
- **GitHub:** Watch repositories for push, star, release events
- **Webhooks:** Custom webhook integrations with secrets
- **Twitter/X:** Monitor accounts and post new tweets
- **Async HTTP:** aiohttp for all external requests

### 📈 Analytics & Insights
- **Stats:** General group statistics
- **Activity:** Message activity over time
- **Top Users:** Top users by various metrics
- **Charts:** Generate activity charts
- **Sentiment:** Sentiment analysis and trends
- **Growth:** Member growth tracking
- **Heatmap:** Activity heatmap (hour vs day)
- **Report Card:** Generate group report card

### 🎯 Moderation
- **Warn/Mute/Ban/Kick:** Complete moderation actions
- **User History:** Full moderation history with evidence
- **Trust/Approve:** Bypass restrictions for trusted users
- **Slow Mode:** Configurable slow mode
- **Restrictions:** Granular user permission controls
- **Anti-Flood:** Configurable anti-flood limits
- **Anti-Raid:** Mass join protection
- **CAS Integration:** Combot Anti-Spam ban sync
- **Blocklist:** Two independent blocklists with actions
- **Locks:** 40+ content type locks with modes

### 👋 Welcome System
- **Custom Messages:** Fully customizable welcome and goodbye
- **Variables:** {first}, {last}, {username}, {mention}, {id}, {count}, {chatname}, {rules}, {date}, {time}
- **Media Support:** Photo, video, GIF, document attachments
- **Buttons:** Inline keyboard support
- **Auto-Delete:** Delete previous welcome messages
- **DM Mode:** Send welcome as direct message
- **CAPTCHA Mute:** Mute new members until CAPTCHA completion

### 🔒 Security
- **Token Encryption:** All custom bot tokens encrypted at rest
- **SQL Injection Prevention:** SQLAlchemy parameterized queries
- **XSS Protection:** Input validation and output encoding
- **CORS Configuration:** Configurable CORS headers
- **API Rate Limiting:** Redis-based token bucket algorithm
- **Bearer Token Auth:** Secure API authentication
- **Group Data Isolation:** Complete data separation by group
- **Audit Logging:** Comprehensive audit trail for all actions

### 📱 Mini App
- **React 18 + TypeScript:** Modern React with TypeScript
- **Vite + Tailwind CSS:** Fast build and beautiful UI
- **Admin Dashboard:** Complete admin control panel
- **Member Profiles:** View member profiles with stats
- **Module Configuration:** Visual configuration for all modules
- **Analytics Charts:** Beautiful charts and graphs
- **Economy Management:** Visual economy and shop management
- **Settings Panel:** Group settings and customization
- **Responsive Design:** Mobile-first responsive design

### ⚡ Performance
- **Async Throughout:** aiogram 3, FastAPI, SQLAlchemy async
- **Connection Pooling:** Optimized database connection pool
- **Redis Caching:** Group-scoped caching with TTL
- **Rate Limiting:** Token bucket algorithm for all operations
- **Webhook Processing:** Returns 200 immediately, processes in background
- **Background Tasks:** Celery for all background operations
- **Horizontal Scaling:** Ready for horizontal scaling
- **Load Balancing:** Can be load balanced with multiple instances

### 📚 Documentation
- **60,000+ Words:** Comprehensive documentation covering all features
- **Commands Reference:** Complete reference for all 230+ commands with examples
- **Implementation Guide:** Technical implementation details and architecture
- **API Documentation:** Complete OpenAPI/Swagger documentation
- **Testing Guide:** Comprehensive testing and deployment guide
- **Telegram API Compatibility:** Analysis of 1,090 features (80% implementable)

## 🛠 Tech Stack

- **Backend:** Python 3.12 + aiogram 3.x + FastAPI
- **Database:** PostgreSQL 16 + SQLAlchemy 2.0 async
- **Cache:** Redis 7
- **Queue:** Celery 5 + Redis
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS
- **AI:** OpenAI GPT-4o
- **Deployment:** Docker + Docker Compose + Render

## 🚀 Quick Start

### Local Development

```bash
# Clone repository
git clone <repository>
cd nexus

# Configure environment
cp .env.example .env
nano .env  # Add your tokens

# Start services
docker-compose up -d
```

### Deploy to Render

```bash
# Fork and clone
git clone https://github.com/your-username/nexus.git
cd nexus

# Create a New Web Service on Render
# Connect your GitHub repository
# Configure build and deploy

# Or use Render CLI
render blueprint apply
```

## 📖 Module Documentation

Each module is fully documented in its respective `module.py` file with:
- Complete command list
- Detailed descriptions
- Usage examples
- Permission requirements
- Configuration options
- Event handlers

## 📞 Support & Community

- **GitHub Issues:** Report bugs and request features
- **GitHub Discussions:** Ask questions and discuss
- **Documentation:** Read comprehensive guides in `/docs/`
- **Telegram:** Join support group (link in `/start` message)

## 📜 License

This project is licensed under the AGPL-3.0 License - see [LICENSE](LICENSE) for details.

## 👥 Credits

Built by the Nexus Team. Inspired by and combining features from:
- MissRose
- GroupHelp
- Group-Bot
- Combot
- Shieldy
- Guardian
- Baymax
- Group Butler
- And all other great Telegram bots

## 🎉 What Makes Nexus Unique

1. **Most Complete:** 230+ commands across 27 modules
2. **AI-Native:** GPT-4 integration throughout all features
3. **Multi-Token:** Shared bot + custom bot tokens for white-label
4. **All Features:** Every feature from major bots combined
5. **Production-Ready:** Built for production with proper error handling
6. **Beautiful UI:** Modern Mini App with admin dashboard
7. **Well Documented:** 60,000+ words of comprehensive documentation
8. **Highly Scalable:** Async throughout, horizontal scaling ready
9. **Secure:** Token encryption, SQL injection prevention, XSS protection
10. **Maintainable:** Modular architecture, type-hyped, well-organized

**Nexus is truly the Ultimate Telegram Bot Platform!** 🚀
