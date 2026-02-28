# Nexus - The Ultimate Telegram Bot Platform

Nexus is a comprehensive, AI-native Telegram bot platform that consolidates features from major Telegram bots into a unified system with 27+ modules and 230+ commands.

## Key Features

### Dual Mode System
- **Shared Bot Mode**: One central NexusBot can be added to any group
- **White-Label Mode**: Bring your own BotFather token for custom branding

### Dual Prefix Command System
- `!command` - Activate/execute a feature
- `!!command` - Deactivate/remove a feature
- `/command` - Standard Telegram slash commands
- Configurable prefix per group

### Mini App Dashboard
- **Toggle Controls**: Enable/disable modules without sending commands
- **Quick Actions**: Execute moderation instantly via UI
- **Groups Manager**: Manage multiple groups from one interface
- **Analytics Dashboard**: View group statistics and trends

## Architecture

```
├── bot/                    # Bot service (aiogram)
│   ├── core/               # Core middleware and context
│   │   ├── middleware.py   # Request processing pipeline
│   │   ├── context.py      # NexusContext object
│   │   ├── prefix_parser.py# Dual prefix parsing
│   │   ├── token_manager.py# Multi-token management
│   │   └── module_*.py     # Module system
│   └── modules/            # All bot modules
├── api/                    # FastAPI REST API
│   ├── main.py             # App entry point
│   └── routers/            # API endpoints
├── mini-app/               # React Mini App
│   └── src/
│       ├── views/          # Page components
│       ├── components/     # Reusable components
│       └── api/            # API client
├── shared/                 # Shared utilities
│   ├── models.py           # SQLAlchemy models
│   ├── schemas.py          # Pydantic schemas
│   └── database.py         # Database config
├── worker/                 # Celery tasks
└── alembic/                # Database migrations
```

## Quick Start

### Using Docker Compose

```bash
# Clone the repository
git clone https://github.com/your-repo/nexus.git
cd nexus

# Copy environment file
cp .env.example .env

# Edit .env with your values
nano .env

# Start all services
docker-compose up -d
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn api.main:app --reload

# Start the bot service
python -m bot.core

# Start the Celery worker
celery -A worker.celery_app worker --loglevel=info
```

## Available Modules

### Moderation
- **moderation**: Warn, mute, ban, kick, history
- **locks**: Lock content types (links, stickers, etc.)
- **antispam**: Anti-flood and spam protection
- **antiraid**: Mass join detection
- **word_filter**: Banned words filtering

### Community
- **welcome**: Welcome/goodbye messages
- **rules**: Group rules management
- **economy**: Virtual currency system
- **reputation**: Community reputation
- **games**: 20+ games with rewards
- **identity**: XP, levels, badges

### Utility
- **notes**: Saved notes with keywords
- **filters**: Auto-responses
- **scheduler**: Scheduled messages
- **polls**: Advanced polls

### AI
- **ai_assistant**: GPT-4 powered assistant
- **analytics**: Group insights

## Mini App Features

### Toggle Manager
Manage all modules without sending commands:
```typescript
// Toggle a module
await toggleApi.toggleModule(groupId, 'moderation', true)

// Update a feature
await toggleApi.updateFeature(groupId, 'moderation', 'warn_threshold', 3)
```

### Quick Actions Panel
Execute moderation actions instantly:
```typescript
// Warn a user
await moderationToggleApi.warnUser(groupId, userId, 'Spam')

// Mute a user
await moderationToggleApi.muteUser(groupId, userId, '1h', 'Inappropriate behavior')
```

### Groups Manager
Manage multiple groups from one interface:
```typescript
// Get all managed groups
const groups = await api.get('/groups/my-groups')

// Switch between groups
<GroupCard onSelect={(groupId) => setSelectedGroup(groupId)} />
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/token` - Get API token

### Groups
- `GET /api/v1/groups/my-groups` - List managed groups
- `GET /api/v1/groups/{id}` - Get group info
- `PATCH /api/v1/groups/{id}` - Update settings

### Modules
- `GET /api/v1/groups/{id}/toggles` - Get all module toggles
- `PATCH /api/v1/groups/{id}/modules/{name}` - Toggle module
- `PATCH /api/v1/groups/{id}/modules/{name}/features/{key}` - Update feature

### Moderation
- `POST /api/v1/groups/{id}/moderation/warn` - Warn user
- `POST /api/v1/groups/{id}/moderation/mute` - Mute user
- `POST /api/v1/groups/{id}/moderation/ban` - Ban user

### Locks
- `GET /api/v1/groups/{id}/locks` - Get all locks
- `PATCH /api/v1/groups/{id}/locks/{type}` - Toggle lock
- `POST /api/v1/groups/{id}/locks/{type}/timed` - Set timed lock

## Development

### Running Tests
```bash
pytest tests/ -v --cov=bot --cov=api
```

### Code Style
```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy bot api
```

### Creating Migrations
```bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

## Deployment

### Docker
```bash
docker-compose -f docker-compose.yml up -d
```

### Render.com
The project includes a `render.yaml` for one-click deployment.

## License

MIT License - See LICENSE file for details.

## Support

- Documentation: `/docs` directory
- Issues: GitHub Issues
- Community: Telegram Group
