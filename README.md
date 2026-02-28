# Nexus - The Ultimate Telegram Bot Platform

Nexus is the most complete, modern, AI-native Telegram bot platform ever built. It combines every feature from MissRose, GroupHelp, Group-Bot, Combot, Shieldy, Guardian, Baymax, Group Butler, and every other notable Telegram bot into one unified, intelligent, fully configurable system.

## Features

### Core Features
- **Shared Bot Mode**: One central bot (@NexusBot) that any group can add
- **Custom Bot Tokens (White Label)**: Group owners can use their own bot tokens
- **Full Mini App**: Beautiful React-based Telegram Web App for configuration
- **AI Integration**: GPT-4 powered assistant, content moderation, and insights
- **Complete Moderation**: Warn, mute, ban, kick with advanced features
- **Anti-Spam**: Anti-flood, CAS integration, raid protection

### Modules (30+)
1. **Moderation** - Core moderation tools
2. **Welcome** - Welcome/goodbye messages
3. **Captcha** - Anti-bot verification
4. **Locks** - Content type locking
5. **Anti-Spam** - Flood and spam protection
6. **Blocklist** - Banned words
7. **Notes** - Saved notes system
8. **Filters** - Keyword auto-responses
9. **Rules** - Group rules management
10. **Economy** - Virtual currency system
11. **Reputation** - Member reputation
12. **Games** - Game suite
13. **Polls** - Advanced polls
14. **Scheduler** - Message scheduling
15. **AI Assistant** - GPT-4 powered assistant
16. **Analytics** - Group insights
17. **Federations** - Cross-group ban sync
18. **And more...**

## Tech Stack

- **Backend**: Python 3.12 + aiogram 3.x + FastAPI
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0 async
- **Cache**: Redis 7
- **Queue**: Celery 5 + Redis
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **AI**: OpenAI GPT-4o
- **Deployment**: Docker + Render

## Quick Start

### Local Development

1. Clone the repository
2. Create `.env` file from `.env.example`
3. Start services with Docker Compose:

```bash
docker-compose up -d
```

### Deploy to Render

1. Fork this repository
2. Create a new Web Service on Render
3. Select "Deploy from GitHub"
4. Choose your forked repository
5. Use the `render.yaml` blueprint for automatic configuration

Or use the Render CLI:

```bash
render blueprint apply
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Telegram Bot Token from @BotFather | Yes |
| `DATABASE_URL` | PostgreSQL connection URL | Yes |
| `REDIS_URL` | Redis connection URL | Yes |
| `OPENAI_API_KEY` | OpenAI API key | No |
| `ENCRYPTION_KEY` | Fernet key for token encryption | Yes |
| `WEBHOOK_URL` | Public webhook URL | Yes |

## Architecture

```
Webhook → Token Router → Auth Middleware → Group Config → 
  Rate Limiter → Module Router → Response
```

### Multi-Token Architecture
Nexus supports running multiple bot tokens on the same infrastructure:
- **Shared Bot**: Default mode, one bot for all groups
- **Custom Tokens**: Groups can use their own bot tokens for white-label experience

## API Documentation

The REST API is available at `/api/v1/` with the following endpoints:

### Authentication
- `POST /api/v1/auth/token` - Authenticate via Telegram initData

### Groups
- `GET /api/v1/groups` - List user's groups
- `GET /api/v1/groups/{id}` - Get group details
- `GET /api/v1/groups/{id}/stats` - Get group statistics

### Members
- `GET /api/v1/groups/{id}/members` - List members
- `POST /api/v1/groups/{id}/members/{uid}/warn` - Warn member
- `POST /api/v1/groups/{id}/members/{uid}/mute` - Mute member
- `POST /api/v1/groups/{id}/members/{uid}/ban` - Ban member

### Modules
- `GET /api/v1/modules/registry` - List available modules
- `POST /api/v1/groups/{id}/modules/{name}/enable` - Enable module
- `POST /api/v1/groups/{id}/modules/{name}/disable` - Disable module

## Mini App

The Mini App is a React-based Telegram Web App that provides:
- Admin Dashboard with full group management
- Member Profile with XP, levels, and badges
- Module configuration UI
- Analytics and insights
- Economy and reputation management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

AGPL-3.0 - See LICENSE file for details

## Credits

Built by the Nexus Team. Inspired by MissRose, GroupHelp, Combot, and all the great Telegram bots that came before.
