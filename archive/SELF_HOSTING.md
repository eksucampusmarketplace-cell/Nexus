# Self-Hosting Nexus

This guide will help you set up your own Nexus instance.

## Requirements

- Docker & Docker Compose
- 2GB RAM minimum
- Domain name (for webhooks)

## Quick Start with Docker Compose

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/nexus.git
cd nexus
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Generate encryption key**
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Add this to ENCRYPTION_KEY in .env
```

4. **Start services**
```bash
docker-compose up -d
```

5. **Run migrations**
```bash
docker-compose exec api alembic upgrade head
```

## Configuration

### Bot Token
Get a bot token from [@BotFather](https://t.me/BotFather):
1. Create a new bot
2. Copy the token to `BOT_TOKEN` in `.env`
3. Set the webhook URL in your domain

### Webhooks
For webhooks to work, your server must be publicly accessible. Set `WEBHOOK_URL` to your public URL:
```
WEBHOOK_URL=https://your-domain.com
```

### Database
The default Docker Compose setup includes PostgreSQL. For production, use a managed database service.

### Redis
Redis is used for caching, sessions, and Celery queue. The Docker Compose includes Redis by default.

### OpenAI (Optional)
For AI features, add your OpenAI API key:
```
OPENAI_API_KEY=sk-...
```

## Updating

1. Pull latest changes:
```bash
git pull origin main
```

2. Rebuild and restart:
```bash
docker-compose down
docker-compose up -d --build
```

3. Run migrations:
```bash
docker-compose exec api alembic upgrade head
```

## Backup

### Database
```bash
docker-compose exec postgres pg_dump -U nexus nexus > backup.sql
```

### Restore
```bash
docker-compose exec -T postgres psql -U nexus nexus < backup.sql
```

## Monitoring

### Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f bot
docker-compose logs -f worker
```

### Health Check
```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Webhook not working
- Check `WEBHOOK_URL` is correct and publicly accessible
- Ensure HTTPS is used (required by Telegram)
- Check firewall rules

### Database connection issues
- Check `DATABASE_URL` format
- Ensure database container is running: `docker-compose ps`

### Module not loading
- Check module dependencies are satisfied
- Check for conflicts between modules
- Review logs for errors

## Advanced Configuration

### Custom Domain
1. Point your domain to your server
2. Set up SSL/TLS (Let's Encrypt recommended)
3. Update `WEBHOOK_URL` with HTTPS URL

### Scaling Workers
Edit `docker-compose.yml` to increase Celery worker count:
```yaml
worker:
  command: celery -A worker.celery_app worker --loglevel=info --concurrency=8
```

### External Services
For production, consider using:
- Managed PostgreSQL (AWS RDS, Google Cloud SQL)
- Managed Redis (AWS ElastiCache, Redis Cloud)
- S3-compatible storage for exports

## Support

For support, join our Telegram community: [@NexusSupport](https://t.me/nexussupport)
