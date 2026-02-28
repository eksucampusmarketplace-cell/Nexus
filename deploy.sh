#!/bin/bash

# Nexus Deployment Script
# Usage: ./deploy.sh [production|development]

set -e

ENV=${1:-development}
echo "Deploying Nexus in $ENV mode..."

# Check prerequisites
command -v docker-compose >/dev/null 2>&1 || { echo "docker-compose is required"; exit 1; }

if [ ! -f .env ]; then
    echo "Error: .env file not found. Copy .env.example to .env and configure it."
    exit 1
fi

# Pull latest changes if in production
if [ "$ENV" = "production" ]; then
    git pull origin main
fi

# Build and start services
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Run migrations
echo "Running database migrations..."
sleep 5  # Wait for postgres to be ready
docker-compose exec -T api alembic upgrade head

# Health check
echo "Checking health..."
sleep 2
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Deployment successful!"
    echo "API: http://localhost:8000"
    echo "Mini App: http://localhost:3000"
else
    echo "⚠️ Health check failed. Check logs with: docker-compose logs"
    exit 1
fi
