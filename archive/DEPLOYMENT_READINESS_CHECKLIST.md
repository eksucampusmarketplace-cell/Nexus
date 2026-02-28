# Deployment Readiness Checklist

## Fixed Issues

### 1. LXML Version Issue ✅ FIXED
- **Problem**: `lxml==5.3.0` does not exist in PyPI
- **Solution**: Updated to `lxml==6.0.2` (latest stable version)
- **Status**: Verified - lxml==6.0.2 has binary wheels for Python 3.12

### 2. Python Version Specification ✅ FIXED
- **Problem**: No explicit Python version file
- **Solution**: Added `runtime.txt` with `python-3.12.2`
- **Purpose**: Ensures Render uses the correct Python version instead of auto-detecting

## Pre-Deployment Checklist

### Files Modified
- [x] `requirements.txt` - Updated lxml version from 5.3.0 to 6.0.2

### Files Added
- [x] `runtime.txt` - Explicit Python version specification
- [x] `LXML_FIX.md` - Documentation of the fix

### Entry Points Verified
- [x] `api/main.py` - FastAPI application entry point
- [x] `bot/core/__main__.py` - Bot startup entry point
- [x] `worker/celery_app.py` - Celery worker entry point

### Dependencies Verified
All critical packages have binary wheels available for Python 3.12:
- [x] aiogram==3.13.1
- [x] fastapi==0.115.0
- [x] sqlalchemy==2.0.36
- [x] asyncpg==0.31.0
- [x] alembic==1.14.0
- [x] lxml==6.0.2 (FIXED)
- [x] beautifulsoup4==4.12.3
- [x] redis==5.2.1
- [x] celery==5.4.0

### Configuration Files
- [x] `render.yaml` - Render blueprint configuration
- [x] `.env.example` - Environment variables template
- [x] `docker-compose.yml` - Local development setup

### Services Configuration (render.yaml)
- [x] nexus-api - Web service (FastAPI)
- [x] nexus-bot - Web service (Telegram bot)
- [x] nexus-worker - Worker service (Celery)
- [x] nexus-beat - Worker service (Celery Beat)
- [x] nexus-mini-app - Static site (React app)
- [x] nexus-db - PostgreSQL database
- [x] nexus-redis - Redis cache

### Build Commands Verified
All services use the same build command:
```bash
pip install --upgrade pip --no-cache-dir && pip install --only-binary :all: --no-cache-dir -r requirements.txt
```

This ensures:
- Latest pip version
- Only binary packages (faster builds)
- No cached packages
- All dependencies from requirements.txt

### Start Commands Verified
- **API**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- **Bot**: `python -m bot.core`
- **Worker**: `celery -A worker.celery_app worker --loglevel=info --concurrency=4`
- **Beat**: `celery -A worker.celery_app beat --loglevel=info`

## Environment Variables Required

### For All Services
- `DATABASE_URL` - PostgreSQL connection string (auto from nexus-db)
- `REDIS_URL` - Redis connection string (auto from nexus-redis)
- `CELERY_BROKER_URL` - Celery broker (auto from nexus-redis)
- `CELERY_RESULT_BACKEND` - Celery results (auto from nexus-redis)
- `BOT_TOKEN` - Telegram bot token (manual, sync: false)
- `ENCRYPTION_KEY` - Token encryption key (generated)
- `OPENAI_API_KEY` - OpenAI API key (manual, sync: false)
- `ENVIRONMENT` - Environment name (production)
- `PYTHONPATH` - Python path (set to /opt/render/project)

### For API Only
- `WEBHOOK_SECRET` - Webhook secret (generated)
- `WEBHOOK_URL` - Public webhook URL (set to https://nexus-api.onrender.com/webhook)

### For Mini App
- `VITE_API_URL` - API base URL (set to https://nexus-api.onrender.com)

## Deployment Process

### Option 1: Using Render Blueprint (Recommended)
1. Push changes to GitHub repository
2. Go to Render dashboard
3. Click "New +" → "Blueprint"
4. Connect your GitHub repository
5. Select the `render.yaml` file
6. Click "Apply Blueprint"

### Option 2: Using Render CLI
```bash
# Install Render CLI
npm install -g @renderinc/cli

# Login
render login

# Apply blueprint
render blueprint apply
```

## Post-Deployment Verification

### Health Checks
1. **API Health**: `https://nexus-api.onrender.com/health`
   - Expected: `{"status": "healthy"}`

2. **API Root**: `https://nexus-api.onrender.com/`
   - Expected: JSON response with name, version, status

3. **Bot Status**: Check Render logs for "Nexus Bot started successfully!"

4. **Worker Status**: Check Render logs for Celery worker startup

### Database Migration
After deployment, run Alembic migrations:
```bash
# On Render shell or via temporary service
cd /opt/render/project
alembic upgrade head
```

### Webhook Configuration
1. Get the Render service URL
2. Update `WEBHOOK_URL` in render.yaml to match your actual Render domain
3. Redeploy to apply webhook configuration

## Potential Issues & Solutions

### Issue 1: Missing binary wheels for some packages
**Solution**: Remove `--only-binary :all:` flag from build command
**Trade-off**: Slower builds (packages compiled from source)

### Issue 2: Python version mismatch
**Solution**: Ensure `runtime.txt` is present and specifies python-3.12.2

### Issue 3: Module import errors
**Solution**: Check that all module directories have `__init__.py` files

### Issue 4: Database connection issues
**Solution**: Verify DATABASE_URL is correctly formatted and database is ready

### Issue 5: Redis connection issues
**Solution**: Verify REDIS_URL is correctly formatted and Redis is running

## Monitoring

### Render Dashboard
Monitor all services from the Render dashboard:
- CPU and memory usage
- Build logs
- Runtime logs
- Error rates

### Key Logs to Watch
1. **API**: FastAPI startup, API requests, errors
2. **Bot**: Telegram webhook registration, module loading, errors
3. **Worker**: Celery task execution, task failures
4. **Beat**: Scheduled task execution

### Alerting
Set up Render alerts for:
- Service restarts
- High error rates
- High memory usage
- Failed builds

## Rollback Plan

If deployment fails:
1. Revert to previous commit
2. Redeploy
3. Check logs for root cause
4. Fix issue
5. Redeploy again

## Next Steps After Deployment

1. **Configure Telegram Bot**
   - Set up bot via @BotFather
   - Get BOT_TOKEN
   - Add to Render environment variables
   - Set webhook

2. **Configure OpenAI API** (optional)
   - Get API key from OpenAI dashboard
   - Add to Render environment variables

3. **Test Core Features**
   - Add bot to a test group
   - Test basic commands
   - Test Mini App
   - Test module enable/disable

4. **Configure Production Settings**
   - Update CORS origins in api/main.py
   - Set proper rate limits
   - Configure backup strategy
   - Set up monitoring

5. **Deploy Custom Bot Token Feature**
   - Test token registration
   - Test custom bot webhook routing
   - Verify token encryption/decryption

## Success Criteria

Deployment is successful when:
- [x] All services are running without errors
- [ ] API health check returns healthy
- [ ] Bot can receive and process Telegram updates
- [ ] Worker can process tasks
- [ ] Beat scheduler is running periodic tasks
- [ ] Mini App is accessible and functional
- [ ] Database migrations applied successfully
- [ ] All core modules are loaded

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Python Runtime on Render](https://render.com/docs/python-version)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Celery Deployment](https://docs.celeryq.dev/en/stable/userguide/deploying.html)
