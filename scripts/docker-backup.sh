#!/bin/bash
# =============================================================================
# Zen AI Pentest - Docker Backup Script
# =============================================================================
# Creates backups of all persistent data
# Usage: ./scripts/docker-backup.sh [backup_dir]
# =============================================================================

set -e

BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"
COMPOSE_CMD="docker-compose"

# Check if docker compose v2 is available
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
fi

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Creating backup at: $BACKUP_PATH${NC}"
mkdir -p "$BACKUP_PATH"

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
$COMPOSE_CMD exec -T postgres pg_dump -U zenuser zenpentest > "$BACKUP_PATH/database.sql" || echo "Warning: Database backup failed"

# Backup Redis
echo "Backing up Redis..."
$COMPOSE_CMD exec redis redis-cli BGSAVE
docker cp $($COMPOSE_CMD ps -q redis):/data/dump.rdb "$BACKUP_PATH/redis.rdb" || echo "Warning: Redis backup failed"

# Backup volumes
echo "Backing up volumes..."
docker run --rm \
    -v zen-ai-pentest_zen-evidence:/evidence \
    -v zen-ai-pentest_zen-reports:/reports \
    -v zen-ai-pentest_zen-sessions:/sessions \
    -v $(pwd)/$BACKUP_PATH:/backup \
    alpine sh -c "
        tar czf /backup/evidence.tar.gz /evidence
        tar czf /backup/reports.tar.gz /reports
        tar czf /backup/sessions.tar.gz /sessions
    " || echo "Warning: Volume backup failed"

# Create metadata
cat > "$BACKUP_PATH/metadata.txt" << EOF
Backup created: $(date)
Zen AI Pentest Version: $(git describe --tags --always 2>/dev/null || echo "unknown")
Docker Compose Version: $($COMPOSE_CMD version)
Volumes:
  - evidence
  - reports
  - sessions
EOF

# Create archive
echo "Creating final archive..."
tar czf "$BACKUP_DIR/zen-ai-backup-$TIMESTAMP.tar.gz" -C "$BACKUP_DIR" "backup_$TIMESTAMP"
rm -rf "$BACKUP_PATH"

echo -e "${GREEN}Backup completed: $BACKUP_DIR/zen-ai-backup-$TIMESTAMP.tar.gz${NC}"
