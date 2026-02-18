# Docker Deployment Guide 🐳

Deploy Zen-AI-Pentest using Docker for easy installation and consistent environments.

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git
cd Zen-Ai-Pentest

# 2. Set environment variables (optional)
cp .env.example .env
# Edit .env with your settings

# 3. Start all services
docker-compose up -d

# 4. Check status
docker-compose ps

# 5. View logs
docker-compose logs -f api
```

**Access the API:** http://localhost:8000

**API Documentation:** http://localhost:8000/docs

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network                           │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌─────────────────────┐   │
│  │  Redis   │◄──►│   API    │◄──►│   PostgreSQL        │   │
│  │  (Cache) │    │ (Server) │    │   (Database)        │   │
│  └──────────┘    └────┬─────┘    └─────────────────────┘   │
│                       │                                     │
│                  ┌────┴────┐                               │
│                  │  Agent  │  (Optional, scalable)         │
│                  └─────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

### Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| API | Custom | 8000 | Main FastAPI server |
| Database | PostgreSQL 15 | 5432 | Data persistence |
| Cache | Redis 7 | 6379 | Caching & message queue |
| Agent | Custom | - | Pentest task execution |

---

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Database
DB_PASSWORD=your-secure-password

# Security (CHANGE IN PRODUCTION!)
JWT_SECRET_KEY=your-super-secret-key-min-32-characters
ADMIN_PASSWORD=your-admin-password

# Agent (optional)
AGENT_ID=docker-agent-1
AGENT_API_KEY=your-api-key
AGENT_API_SECRET=your-api-secret
```

### Volumes

| Path | Purpose |
|------|---------|
| `./data` | Application data |
| `./logs` | Log files |
| `./reports` | Generated pentest reports |
| `./evidence` | Scan evidence/files |

---

## Usage

### Start Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d api

# Scale agents (run 3 agents)
docker-compose up -d --scale agent=3
```

### Stop Services

```bash
# Stop all
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api
```

### Execute Commands

```bash
# Run CLI in container
docker-compose exec api python zen-cli.py --help

# Run database migrations
docker-compose exec api python -m alembic upgrade head

# Shell into container
docker-compose exec api bash

# Run nmap from agent
docker-compose exec agent nmap -Pn scanme.nmap.org
```

---

## Demo in Docker

```bash
# Start services
docker-compose up -d

# Wait for services to be ready
sleep 10

# Run E2E demo
docker-compose exec api python demo_e2e.py

# View generated report
docker-compose exec api cat /app/reports/pentest_report_*.md
```

---

## Production Deployment

### 1. Use Strong Secrets

```bash
# Generate secure keys
openssl rand -hex 32  # JWT_SECRET_KEY
openssl rand -hex 16  # DB_PASSWORD
```

### 2. Use Reverse Proxy (nginx/traefik)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
```

### 3. Enable HTTPS

```bash
# Using Let's Encrypt with Traefik
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 4. Resource Limits

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

## Building Images

### Build All

```bash
docker-compose build
```

### Build Specific Image

```bash
# API server
docker build -t zen-pentest-api -f Dockerfile .

# Agent
docker build -t zen-pentest-agent -f Dockerfile.agent .
```

### Push to Registry

```bash
# Tag
docker tag zen-pentest-api your-registry/zen-pentest-api:latest

# Push
docker push your-registry/zen-pentest-api:latest
```

---

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs api

# Check for port conflicts
sudo lsof -i :8000

# Restart with fresh build
docker-compose down
docker-compose up --build -d
```

### Database connection issues

```bash
# Check database health
docker-compose exec db pg_isready -U zen_user

# Reset database (WARNING: loses data!)
docker-compose down -v
docker-compose up -d db
```

### Permission denied for tools

Agent container runs with `privileged: true` for security tools.
If issues persist:

```bash
# Run as root (not recommended for production)
docker-compose exec -u root agent bash
```

### Out of disk space

```bash
# Clean up
docker system prune -a
docker volume prune
```

---

## Security Considerations

### 1. Change Default Passwords

```bash
# NEVER use defaults in production
ADMIN_PASSWORD=$(openssl rand -hex 16)
JWT_SECRET_KEY=$(openssl rand -hex 32)
```

### 2. Network Isolation

```yaml
# docker-compose.yml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access

services:
  api:
    networks:
      - frontend
      - backend
  db:
    networks:
      - backend  # Only accessible by API
```

### 3. Read-Only Root Filesystem

```yaml
services:
  api:
    read_only: true
    tmpfs:
      - /tmp
      - /var/tmp
```

### 4. Drop Capabilities

```yaml
services:
  api:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

---

## Updating

```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose build

# Restart services
docker-compose up -d

# Database migrations (if needed)
docker-compose exec api python -m alembic upgrade head
```

---

## Development

### Mount Code for Live Reload

```yaml
# docker-compose.dev.yml
services:
  api:
    volumes:
      - .:/app
    command: uvicorn api.main:app --host 0.0.0.0 --reload
```

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

---

## Monitoring

### Health Checks

All services include health checks:

```bash
# Check all services
docker-compose ps

# Health status
docker inspect --format='{{.State.Health.Status}}' zen-pentest-api
```

### Metrics

```bash
# Container stats
docker stats

# Resource usage
docker-compose exec api python -c "import psutil; print(psutil.virtual_memory())"
```

---

## Uninstallation

```bash
# Stop and remove everything
docker-compose down -v --rmi all

# Remove images
docker rmi zen-pentest-api zen-pentest-agent

# Clean up
docker system prune -a
```

---

**Happy Containerized Testing! 🐳🎯**
