#!/bin/bash
set -e

echo "🚀 Starting Zen-AI Pentest API..."
echo "⏳ Waiting for services..."

# Check if database is ready (optional, for postgres)
if [ "$DATABASE_URL" ]; then
    echo "📊 Database configured"
fi

# Check if redis is ready (optional)
if [ "$REDIS_URL" ]; then
    echo "💾 Redis configured"
fi

echo "✅ Starting API server..."
exec "$@"
