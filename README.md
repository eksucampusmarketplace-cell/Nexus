# Nexus — The Ultimate Telegram Bot Platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-teal)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18%2B-61DAFB?logo=react)](https://react.dev/)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-blueviolet)](https://docs.aiogram.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Nexus is a comprehensive, AI-native Telegram bot platform consolidating features from major Telegram bots into a unified system with **41+ pluggable modules**, **280+ commands**, and **72,000+ lines** of production code.

---

## 📊 Codebase Statistics

| Component | Files | Lines of Code |
|-----------|-------|---------------|
| **Bot Engine** (aiogram) | 100+ | 34,559 |
| **REST API** (FastAPI) | 20+ | 8,405 |
| **Shared Layer** (Models/Schemas) | 10+ | 8,375 |
| **Mini App** (React/TypeScript) | 50+ | 17,750 |
| **Worker** (Celery) | 3+ | 581 |
| **Migrations** (Alembic) | 5+ | 1,642 |
| **Total** | **230+** | **~72,000** |

---

## 🚀 Key Features

### Dual Bot Mode System
- **Shared Bot Mode**: One central NexusBot added to any group
- **White-Label Mode**: Bring your own BotFather token for custom branding

### Triple Command Interface
- `!command` — Activate/execute features
- `!!command` — Deactivate/remove features  
- `/command` — Standard Telegram slash commands
- Configurable prefix per group

### Mini App Dashboard
Full-featured Telegram WebApp for visual management:
- **Module Toggles** — Enable/disable without commands
- **Quick Actions** — Instant moderation via UI
- **Group Manager** — Multi-group management
- **Analytics Dashboard** — Statistics and trends
- **Automation Center** — Visual workflow builder

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NEXUS PLATFORM                                │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  Telegram    │  │   Mini App   │  │       Web Clients        │  │
│  │    Bot       │  │  (React/TS)  │  │      (WebSocket)         │  │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘  │
│         │                 │                       │                │
│  ┌──────▼─────────────────▼───────────────────────▼─────────────┐  │
│  │                    FASTAPI GATEWAY                             │  │
│  │         REST API │ WebSocket │ Webhooks │ Auth                │  │
│  └──────┬────────────────────────────────────────────────────────┘  │
│         │                                                           │
│  ┌──────▼────────────────────────────────────────────────────────┐  │
│  │                    CORE SERVICES                               │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │  │
│  │  │   Context    │  │   Module     │  │  Token Manager   │    │  │
│  │  │   System     │  │   Registry   │  │  (Multi-bot)     │    │  │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘    │  │
│  └──────┬────────────────────────────────────────────────────────┘  │
│         │                                                           │
│  ┌──────▼────────────────────────────────────────────────────────┐  │
│  │              41+ PLUGGABLE MODULES                             │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │  │
│  │  │Moderation│ │Community │ │  Economy │ │   Games  │  ...    │  │
│  │  │  Locks   │ │ Welcome  │ │Reputation│ │ Analytics│         │  │
│  │  │ Antispam │ │Identity  │ │Scheduler │ │  AI Asst │         │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │  │
│  └────────────────────────────────────────────────────────────────┘  │
│         │                                                           │
│  ┌──────▼────────────────────────────────────────────────────────┐  │
│  │              DATA & INFRASTRUCTURE                             │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │  │
│  │  │PostgreSQL│ │  Redis   │ │  Celery  │ │  Alembic │         │  │
│  │  │SQLAlchemy│ │  Cache   │ │ Workers  │ │Migrations│         │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │  │
│  └────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Project Structure

```
├── api/                    # FastAPI REST API
│   ├── main.py             # Application entry point
│   └── routers/            # 20+ endpoint modules
│       ├── auth.py         # JWT authentication
│       ├── groups.py       # Group management
│       ├── toggles.py      # Module toggles
│       ├── moderation.py   # Moderation actions
│       ├── economy.py      # Economy system
│       └── ...
│
├── bot/                    # Telegram Bot (aiogram 3.x)
│   ├── core/               # Core framework
│   │   ├── middleware.py   # Request processing pipeline
│   │   ├── context.py      # NexusContext object
│   │   ├── module_base.py  # Base class for modules
│   │   ├── module_registry.py
│   │   ├── prefix_parser.py
│   │   └── token_manager.py
│   └── modules/            # 41+ feature modules
│       ├── moderation/
│       ├── economy/
│       ├── games/
│       ├── ai_assistant/
│       └── ...
│
├── mini-app/               # React 18 + TypeScript
│   └── src/
│       ├── App.tsx         # Main application
│       ├── views/          # 25+ page components
│       ├── components/     # Reusable UI components
│       ├── stores/         # Zustand state management
│       └── api/            # API client layer
│
├── shared/                 # Shared components
│   ├── models.py           # SQLAlchemy ORM models
│   ├── models_intelligence.py
│   ├── schemas.py          # Pydantic schemas
│   ├── database.py         # Database configuration
│   └── redis_client.py     # Redis cache layer
│
├── worker/                 # Celery background workers
│   └── celery_app.py       # Task queue processing
│
└── alembic/                # Database migrations
    └── versions/           # Migration scripts
```

---

## 📦 Available Modules (41+)

### 🛡️ Moderation
| Module | Description | Commands |
|--------|-------------|----------|
| `moderation` | Warn, mute, ban, kick, history | `/warn`, `/mute`, `/ban`, `/kick` |
| `locks` | Content-type restrictions | `!lock`, `!lockall` |
| `antispam` | Anti-flood and spam protection | `!antispam` |
| `antiraid` | Mass join detection | `!antiraid` |
| `word_filter` | Banned words filtering | `!filter` |
| `ai_moderation` | AI-powered content moderation | Auto |

### 👥 Community
| Module | Description | Commands |
|--------|-------------|----------|
| `welcome` | Welcome/goodbye messages | `!welcome` |
| `rules` | Group rules management | `/rules` |
| `economy` | Virtual currency system | `/balance`, `/pay`, `/shop` |
| `reputation` | Community reputation | `+rep`, `-rep` |
| `identity` | XP, levels, badges | `/profile`, `/rank` |
| `community` | Community features | — |
| `member_booster` | Member engagement tools | — |

### 🎮 Games & Fun
| Module | Description |
|--------|-------------|
| `games` | 20+ games with rewards |
| `games_hub` | Game management interface |
| `challenges` | Group challenges |
| `gamification_hub` | Gamification dashboard |

### 🤖 AI & Intelligence
| Module | Description |
|--------|-------------|
| `ai_assistant` | GPT-4 powered assistant |
| `group_intelligence` | Smart group insights |
| `advanced_analytics` | Deep analytics |
| `nl_interface` | Natural language commands |

### 🛠️ Utility
| Module | Description | Commands |
|--------|-------------|----------|
| `notes` | Saved notes with keywords | `/save`, `/get` |
| `filters` | Auto-responses | `!filter` |
| `scheduler` | Scheduled messages | `/schedule` |
| `polls` | Advanced polls | `/poll` |
| `notes_filters` | Combined notes & filters | — |

### 🔒 Security & Management
| Module | Description |
|--------|-------------|
| `captcha` | Verification challenges |
| `trust_system` | Trust-based permissions |
| `blocklist` | User blocking |
| `graveyard` | Deleted message recovery |
| `security_center` | Security dashboard |

### 🔧 Advanced
| Module | Description |
|--------|-------------|
| `automation` | Workflow automation |
| `bot_builder` | Custom bot creation |
| `federations` | Cross-group moderation |
| `integrations` | Third-party integrations |
| `channels` | Channel management |
| `scraping` | Content aggregation |
| `formatting` | Message formatting tools |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Node.js 18+ (for Mini App development)

### Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/nexus.git
cd nexus

# Configure environment
cp .env.example .env
# Edit .env with your:
# - TELEGRAM_BOT_TOKEN
# - DATABASE_URL
# - REDIS_URL
# - OPENAI_API_KEY (optional)

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head
```

### Manual Development Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Mini App dependencies
cd mini-app && npm install && cd ..

# 3. Run database migrations
alembic upgrade head

# 4. Start services (in separate terminals)
# API Server
uvicorn api.main:app --reload --port 8000

# Bot Service
python -m bot.core

# Celery Worker
celery -A worker.celery_app worker --loglevel=info --concurrency=4

# Mini App (dev mode)
cd mini-app && npm run dev
```

---

## 🔌 API Reference

### Authentication
```bash
POST /api/v1/auth/token
Authorization: Bearer {telegram_init_data}
```

### Groups
```bash
GET    /api/v1/groups/my-groups           # List managed groups
GET    /api/v1/groups/{id}                # Group details
PATCH  /api/v1/groups/{id}                # Update settings
DELETE /api/v1/groups/{id}                # Leave group
```

### Module Toggles
```bash
GET    /api/v1/groups/{id}/toggles        # Get all toggles
PATCH  /api/v1/groups/{id}/modules/{name} # Toggle module
PATCH  /api/v1/groups/{id}/modules/{name}/features/{key}  # Update feature
```

### Moderation
```bash
POST /api/v1/groups/{id}/moderation/warn  # Warn user
POST /api/v1/groups/{id}/moderation/mute  # Mute user
POST /api/v1/groups/{id}/moderation/ban   # Ban user
POST /api/v1/groups/{id}/moderation/kick  # Kick user
```

### Economy
```bash
GET  /api/v1/groups/{id}/economy/leaderboard
GET  /api/v1/groups/{id}/members/{user_id}/balance
POST /api/v1/groups/{id}/economy/transfer
```

---

## 🧩 Creating a Module

```python
from bot.core.module_base import NexusModule, CommandDef, ModuleCategory
from bot.core.context import NexusContext

class MyModule(NexusModule):
    name = "my_module"
    version = "1.0.0"
    description = "My custom module"
    category = ModuleCategory.UTILITY
    
    commands = [
        CommandDef(
            name="hello",
            description="Say hello",
            usage="/hello [name]"
        )
    ]
    
    async def on_load(self, app):
        self.register_command("hello", self.cmd_hello)
    
    async def cmd_hello(self, ctx: NexusContext):
        name = ctx.args or "World"
        await ctx.reply(f"Hello, {name}! 👋")
```

---

## 🧪 Development

### Running Tests
```bash
pytest tests/ -v --cov=bot --cov=api
```

### Code Quality
```bash
# Format Python code
black .
isort .

# Type checking
mypy bot api shared

# Lint Mini App
cd mini-app && npm run lint
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) | Advanced feature overview |
| [ADVANCED_FEATURES_GUIDE.md](ADVANCED_FEATURES_GUIDE.md) | Implementation guide |
| [GROUP_INTELLIGENCE_GUIDE.md](GROUP_INTELLIGENCE_GUIDE.md) | AI intelligence features |
| [MESSAGE_GRAVEYARD_IMPLEMENTATION.md](MESSAGE_GRAVEYARD_IMPLEMENTATION.md) | Deleted message recovery |
| [NEXUS_CAPABILITIES_REPORT.md](NEXUS_CAPABILITIES_REPORT.md) | Detailed Bot vs. Mini App comparison |
| [DEBUG_GUIDE.md](DEBUG_GUIDE.md) | Troubleshooting |

---

## 🚢 Deployment

### Docker
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Render.com
One-click deployment with included `render.yaml`.

### Environment Variables
```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql://user:pass@localhost/nexus
REDIS_URL=redis://localhost:6379

# Optional
OPENAI_API_KEY=sk-...        # For AI features
SENTRY_DSN=...               # Error tracking
WEBHOOK_URL=https://...      # For production bot mode
```

---

## 📜 License

MIT License — See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/nexus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/nexus/discussions)
- **Telegram**: [@NexusSupport](https://t.me/nexussupport)

---

<p align="center">
  Built with ❤️ by the Nexus Team
</p>
