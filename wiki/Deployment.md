# Deployment Guide

Complete guide for deploying Zen-AI-Pentest in production.

## Deployment Options

| Option | Best For | Complexity | Cost |
|--------|----------|------------|------|
| **Docker Compose** | Single Server | Low | Low |
| **Kubernetes** | Scale/Enterprise | High | Medium |
| **Cloudflare Pages** | Frontend Only | Low | Free |
| **AWS/Azure/GCP** | Enterprise | Medium | High |

## Docker Compose (Recommended)

### Quick Start

```bash
# Clone repository
git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
cd zen-ai-pentest

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Start services
docker-compose up -d
```

### Production docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/zen_pentest
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - KIMI_API_KEY=${KIMI_API_KEY}
    volumes:
      - ./data:/app/data
    depends_on:
      - db
      - redis
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=zen_pentest
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  worker:
    build: .
    command: celery -A core.tasks worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/zen_pentest
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    restart: unless-stopped

  frontend:
    image: zen-ai-pentest-frontend:latest
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://api:8000
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Environment Variables

```env
# Database
DB_PASSWORD=your-secure-password

# Security
SECRET_KEY=$(openssl rand -hex 32)

# AI Providers
KIMI_API_KEY=your-kimi-api-key
OPENAI_API_KEY=your-openai-key  # Optional

# Domain
DOMAIN=your-domain.com
EMAIL=admin@your-domain.com  # For SSL
```

## Kubernetes

### Namespace

```bash
kubectl create namespace zen-pentest
```

### Secrets

```bash
kubectl create secret generic app-secrets \
  --from-literal=DATABASE_URL="postgresql://..." \
  --from-literal=SECRET_KEY="..." \
  --from-literal=KIMI_API_KEY="..." \
  -n zen-pentest
```

### Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zen-api
  namespace: zen-pentest
spec:
  replicas: 3
  selector:
    matchLabels:
      app: zen-api
  template:
    metadata:
      labels:
        app: zen-api
    spec:
      containers:
      - name: api
        image: zen-ai-pentest:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: app-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service & Ingress

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: zen-api-service
  namespace: zen-pentest
spec:
  selector:
    app: zen-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: zen-ingress
  namespace: zen-pentest
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: zen-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: zen-api-service
            port:
              number: 80
```

### Deploy

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

## Cloudflare Pages (Frontend)

### Build Settings

```bash
# Build command
npm run build

# Build output directory
dist

# Environment variables
VITE_API_URL=https://api.your-domain.com
```

### Deployment

```bash
# Install Wrangler
npm install -g wrangler

# Login
wrangler login

# Deploy
wrangler pages deploy dist
```

## AWS Deployment

### ECS with Fargate

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name zen-pentest

# Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster zen-pentest \
  --service-name zen-api \
  --task-definition zen-api:1 \
  --desired-count 2 \
  --launch-type FARGATE
```

### RDS Database

```bash
aws rds create-db-instance \
  --db-instance-identifier zen-pentest-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password your-password \
  --allocated-storage 20
```

## SSL/TLS

### Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt-get install certbot

# Obtain certificate
sudo certbot certonly --standalone -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Traefik (Docker Compose)

```yaml
# docker-compose.yml
traefik:
  image: traefik:v2.10
  command:
    - "--api.insecure=true"
    - "--providers.docker=true"
    - "--entrypoints.websecure.address=:443"
    - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
    - "--certificatesresolvers.letsencrypt.acme.email=admin@your-domain.com"
    - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
  ports:
    - "443:443"
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
    - ./letsencrypt:/letsencrypt
```

## Monitoring

### Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
  volumes:
    - grafana_data:/var/lib/grafana
```

### Health Checks

```python
# api/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "healthy"}

@router.get("/ready")
def readiness_check():
    # Check database connection
    # Check Redis connection
    return {"ready": True}
```

## Backup & Restore

### Database Backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
docker exec zen-pentest_db_1 pg_dump -U postgres zen_pentest > \
  $BACKUP_DIR/zen_pentest_$DATE.sql

# Compress
gzip $BACKUP_DIR/zen_pentest_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

### Automated Backups (Cron)

```bash
# Edit crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh
```

## Security Hardening

### 1. Firewall

```bash
# UFW
sudo ufw default deny incoming
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 2. Fail2Ban

```bash
sudo apt-get install fail2ban

# /etc/fail2ban/jail.local
[sshd]
enabled = true
maxretry = 3
bantime = 3600
```

### 3. Docker Security

```bash
# Run as non-root user
useradd -m zen-user
usermod -aG docker zen-user

# Enable Docker Content Trust
export DOCKER_CONTENT_TRUST=1
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs api

# Check environment
docker-compose exec api env

# Test database connection
docker-compose exec api python3 -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://...')
engine.connect()
print('Connected!')
"
```

### High Memory Usage

```bash
# Check container stats
docker stats

# Set memory limits
docker run -m 2g --memory-swap 2g zen-ai-pentest
```

## Updates

### Rolling Update (Zero Downtime)

```bash
# Build new image
docker-compose build api

# Rolling update
docker-compose up -d --no-deps --scale api=2 api
docker-compose up -d --no-deps --scale api=1 api
```

### Database Migrations

```bash
# Backup first
./backup.sh

# Run migrations
docker-compose exec api alembic upgrade head
```
