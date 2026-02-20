# Docker Setup Guide - Zen AI Pentest

## Overview

This guide provides comprehensive instructions for deploying Zen AI Pentest using Docker and Docker Compose. The setup supports multiple environments from development to production.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Deployment Scenarios](#deployment-scenarios)
- [Production Deployment](#production-deployment)
- [Monitoring & Logging](#monitoring--logging)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)

## Prerequisites

### Required Software

```bash
# Docker Engine 24.0+
docker --version

# Docker Compose v2.20+
docker compose version

# Git
git --version
```

### System Requirements

| Environment | CPU | RAM | Storage | Network |
|-------------|-----|-----|---------|---------|
| Development | 2 cores | 4 GB | 20 GB | Any |
| Testing | 2 cores | 4 GB | 20 GB | Any |
| Production | 4+ cores | 8+ GB | 50+ GB | Restricted |

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
cd zen-ai-pentest
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Start Services

```bash
# Basic setup (app + database + cache)
docker-compose up -d

# With monitoring (ELK stack)
docker-compose --profile monitoring up -d

# With VPN support
docker-compose --profile vpn up -d

# Full production setup
docker-compose --profile monitoring --profile proxy up -d
```

### 4. Verify Installation

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f zen-ai-pentest

# Test health endpoint
curl http://localhost:8080/health
```

## Architecture

### Service Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker Host                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    zen-network (bridge)                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │   Traefik    │  │  Zen AI      │  │   Nuclei     │  │   │
│  │  │   (Proxy)    │  │  Pentest     │  │  (Scanner)   │  │   │
│  │  │   :80, :443  │  │  :8080       │  │              │  │   │
│  │  └──────────────┘  └──────┬───────┘  └──────────────┘  │   │
│  │                           │                            │   │
│  │  ┌──────────────┐  ┌──────┴──────┐  ┌──────────────┐  │   │
│  │  │   Worker     │  │   Worker    │  │   Worker     │  │   │
│  │  │   Node 1     │  │   Node 2    │  │   Node 3     │  │   │
│  │  └──────────────┘  └─────────────┘  └──────────────┘  │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────┼──────────────────────────────┐   │
│  │              zen-backend (internal)                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │  PostgreSQL  │  │    Redis     │  │Elasticsearch │  │   │
│  │  │   :5432      │  │   :6379      │  │   :9200      │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  │                                                          │   │
│  │  ┌──────────────┐  ┌──────────────┐                     │   │
│  │  │   Logstash   │  │    Kibana    │                     │   │
│  │  │              │  │   :5601      │                     │   │
│  │  └──────────────┘  └──────────────┘                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Network Design

**zen-network (Public-facing):**
- Main application access
- External API endpoints
- Scanner containers

**zen-backend (Internal-only):**
- Database connections
- Cache access
- Message queue
- No external access

## Configuration

### Environment Variables

Create `.env` file:

```bash
# =============================================================================
# Core Configuration
# =============================================================================
ZEN_AI_ENV=production
ZEN_AI_LOG_LEVEL=INFO

# =============================================================================
# Database Configuration
# =============================================================================
DB_PASSWORD=your-secure-password-here
DB_PORT=5432

# =============================================================================
# Redis Configuration
# =============================================================================
REDIS_PASSWORD=your-redis-password-here
REDIS_PORT=6379

# =============================================================================
# API Keys (Optional)
# =============================================================================
OPENROUTER_API_KEY=sk-or-v1-...
PROTONVPN_USERNAME=your-vpn-username
PROTONVPN_PASSWORD=your-vpn-password
WIREGUARD_PRIVATE_KEY=...

# =============================================================================
# Ports
# =============================================================================
ZEN_API_PORT=8080
ZEN_WEB_PORT=3000
KIBANA_PORT=5601
TRAEFIK_DASHBOARD_PORT=8080

# =============================================================================
# Scaling
# =============================================================================
WORKER_REPLICAS=2
WORKER_SCALE=2

# =============================================================================
# SSL/TLS (Production)
# =============================================================================
ACME_EMAIL=admin@yourdomain.com
```

### Secrets Management

For production, use Docker secrets:

```bash
# Create secrets directory
mkdir -p secrets

# Generate secure passwords
openssl rand -base64 32 > secrets/db_password.txt
openssl rand -base64 32 > secrets/redis_password.txt

# Set permissions
chmod 600 secrets/*
```

## Deployment Scenarios

### Scenario 1: Development Environment

```bash
# Start with development profile
docker-compose up -d

# View logs
docker-compose logs -f

# Execute commands in container
docker-compose exec zen-ai-pentest bash

# Run tests
docker-compose exec zen-ai-pentest pytest

# Stop everything
docker-compose down
```

### Scenario 2: Testing with Monitoring

```bash
# Start with ELK stack
docker-compose --profile monitoring up -d

# Access Kibana
open http://localhost:5601

# View application logs in Kibana
# Navigate to: Stack Management → Index Patterns → Create index pattern
# Pattern: zen-logs-*
```

### Scenario 3: VPN-Protected Scanning

```bash
# Start with VPN sidecar
docker-compose --profile vpn up -d

# Verify VPN connection
docker-compose exec protonvpn protonvpn-cli status

# Check IP
docker-compose exec zen-ai-pentest curl ip.me

# All traffic from zen-ai-pentest now goes through VPN
```

### Scenario 4: Production with Load Balancer

```bash
# Start with Traefik reverse proxy
docker-compose --profile proxy up -d

# Scale workers horizontally
docker-compose up -d --scale worker=5

# Access Traefik dashboard
open http://localhost:8080/dashboard/

# Application is now available on standard ports
# HTTP: 80, HTTPS: 443
```

## Production Deployment

### Security Hardening

1. **Use Non-Root Users**
   ```dockerfile
   RUN useradd -u 1000 -m pentest
   USER pentest
   ```

2. **Read-Only Root Filesystem**
   ```yaml
   services:
     zen-ai-pentest:
       read_only: true
       tmpfs:
         - /tmp
         - /var/tmp
   ```

3. **Resource Limits**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 2G
       reservations:
         cpus: '0.5'
         memory: 512M
   ```

4. **Security Options**
   ```yaml
   security_opt:
     - no-new-privileges:true
   cap_drop:
     - ALL
   cap_add:
     - NET_BIND_SERVICE
   ```

### Backup Strategy

```bash
#!/bin/bash
# backup.sh

# Backup database
docker-compose exec postgres pg_dump -U zenuser zenpentest > backup_$(date +%Y%m%d).sql

# Backup evidence
docker run --rm -v zen-ai-pentest_zen-evidence:/data -v $(pwd):/backup alpine tar czf /backup/evidence_$(date +%Y%m%d).tar.gz /data

# Backup Redis
docker-compose exec redis redis-cli BGSAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb backup_redis_$(date +%Y%m%d).rdb
```

### Update Procedure

```bash
# 1. Pull latest images
docker-compose pull

# 2. Backup data
./backup.sh

# 3. Stop services gracefully
docker-compose down

# 4. Start with new images
docker-compose up -d

# 5. Verify health
docker-compose ps
```

## Monitoring & Logging

### Health Checks

All services include health checks:

```bash
# View health status
docker-compose ps

# Inspect health check
docker inspect --format='{{.State.Health.Status}}' zen-ai-pentest

# View health check logs
docker inspect --format='{{json .State.Health}}' zen-ai-pentest | jq
```

### Centralized Logging (ELK)

When using `--profile monitoring`:

1. **Access Kibana**: http://localhost:5601
2. **Create Index Pattern**: `zen-logs-*`
3. **Explore Logs**: Discover → Select index pattern

### Metrics with Prometheus

Add to `docker-compose.monitoring.yml`:

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana-data:/var/lib/grafana
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs zen-ai-pentest

# Check for port conflicts
sudo lsof -i :8080

# Verify environment variables
docker-compose config
```

### Database Connection Issues

```bash
# Test database connection
docker-compose exec zen-ai-pentest python -c "
import psycopg2
conn = psycopg2.connect(
    host='postgres',
    database='zenpentest',
    user='zenuser',
    password='your-password'
)
print('Connected!')
conn.close()
"

# Check database logs
docker-compose logs postgres

# Reset database (WARNING: Destroys data!)
docker-compose down -v
docker-compose up -d postgres
```

### VPN Connection Failed

```bash
# Check VPN logs
docker-compose logs protonvpn

# Verify credentials
docker-compose exec protonvpn protonvpn-cli login

# Test without VPN first
docker-compose up -d zen-ai-pentest
```

### Performance Issues

```bash
# Check resource usage
docker stats

# View top processes in container
docker-compose exec zen-ai-pentest top

# Scale workers if needed
docker-compose up -d --scale worker=5
```

## Security Best Practices

### 1. Image Security

```bash
# Scan image for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image zen-ai-pentest:latest

# Use distroless images where possible
FROM gcr.io/distroless/python3-debian12
```

### 2. Network Security

```yaml
# Isolate sensitive services
networks:
  backend:
    internal: true  # No external access

  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 3. Secret Management

```bash
# Use Docker secrets (Swarm mode)
docker secret create db_password secrets/db_password.txt

# Or use external secret manager
# - HashiCorp Vault
# - AWS Secrets Manager
# - Azure Key Vault
```

### 4. Runtime Security

```bash
# Enable Docker Content Trust
export DOCKER_CONTENT_TRUST=1

# Use seccomp profiles
docker run --security-opt seccomp=default.json zen-ai-pentest

# Enable user namespaces
dockerd --userns-remap=default
```

## Useful Commands

```bash
# Start specific service
docker-compose up -d zen-ai-pentest

# Scale service
docker-compose up -d --scale worker=3

# Execute command in running container
docker-compose exec zen-ai-pentest python -m pytest

# View resource usage
docker-compose stats

# Clean up unused resources
docker system prune -a --volumes

# Export container filesystem
docker export $(docker-compose ps -q zen-ai-pentest) > zen-ai.tar

# Import data
docker-compose exec -T postgres psql -U zenuser zenpentest < backup.sql
```

## Migration Guide

### From Local Installation to Docker

1. **Backup local data**
   ```bash
   cp -r data data-backup
   cp -r evidence evidence-backup
   ```

2. **Start Docker environment**
   ```bash
   docker-compose up -d
   ```

3. **Restore data**
   ```bash
   docker cp data-backup/. $(docker-compose ps -q zen-ai-pentest):/app/data/
   docker cp evidence-backup/. $(docker-compose ps -q zen-ai-pentest):/app/evidence/
   ```

4. **Update configuration**
   ```bash
   # Edit config inside container
   docker-compose exec zen-ai-pentest nano config/zen-ai.yaml
   ```

## Support

For issues and questions:
- GitHub Issues: https://github.com/SHAdd0WTAka/zen-ai-pentest/issues
- Documentation: https://github.com/SHAdd0WTAka/zen-ai-pentest/docs

---

*Last updated: 2026-01-30*
*Authors: SHAdd0WTAka, Kimi AI*
