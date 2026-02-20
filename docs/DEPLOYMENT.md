# Deployment Guide

## Quick Start

### Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git
cd Zen-Ai-Pentest

# Start with Docker Compose
docker-compose up -d

# Access API at http://localhost:8000
# Access Docs at http://localhost:8000/docs
```

### Manual Installation

```bash
# 1. Clone repository
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git
cd Zen-Ai-Pentest

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Run database migrations (if using PostgreSQL)
alembic upgrade head

# 6. Start the application
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Configuration

### Environment Variables

Create `.env` file:

```env
# Application
APP_NAME=Zen-AI-Pentest
DEBUG=false
LOG_LEVEL=info

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/zenpentest
# or for SQLite
DATABASE_URL=sqlite:///./zenpentest.db

# Security
SECRET_KEY=your-secret-key-here
JWT_EXPIRATION=3600
ENCRYPTION_KEY=your-encryption-key

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
KIMI_API_KEY=...

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# Compliance
AUDIT_LOG_RETENTION_DAYS=365
ENABLE_SIEM_EXPORT=true
SIEM_URL=https://splunk.example.com
```

### Production Configuration

```python
# config/production.py
from pydantic import BaseSettings

class ProductionConfig(BaseSettings):
    DEBUG = False
    LOG_LEVEL = "warning"

    # Database
    DATABASE_URL = "postgresql://..."

    # Security
    SECRET_KEY = "change-me-in-production"
    JWT_EXPIRATION = 1800  # 30 minutes

    # Workers
    MAX_WORKERS = 10
    TASK_TIMEOUT = 7200  # 2 hours

    # Cache
    CACHE_TTL = 600
    CACHE_MAX_SIZE = 100000

    class Config:
        env_file = ".env"
```

## Docker Deployment

### Basic Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t zen-ai-pentest .
docker run -p 8000:8000 --env-file .env zen-ai-pentest
```

### Docker Compose (Full Stack)

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/zenpentest
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  worker:
    build: .
    command: celery -A tasks worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/zenpentest
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: zenpentest
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

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
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

## Kubernetes Deployment

### Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: zen-pentest
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: zen-config
  namespace: zen-pentest
data:
  DEBUG: "false"
  LOG_LEVEL: "info"
  DATABASE_URL: "postgresql://..."
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: zen-secrets
  namespace: zen-pentest
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key"
  JWT_SECRET: "your-jwt-secret"
  DB_PASSWORD: "database-password"
```

### Deployment

```yaml
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
        - configMapRef:
            name: zen-config
        - secretRef:
            name: zen-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /live
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

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: zen-api
  namespace: zen-pentest
spec:
  selector:
    app: zen-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: zen-ingress
  namespace: zen-pentest
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: "letsencrypt"
spec:
  tls:
  - hosts:
    - api.zenpentest.example.com
    secretName: zen-tls
  rules:
  - host: api.zenpentest.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: zen-api
            port:
              number: 80
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: zen-api-hpa
  namespace: zen-pentest
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: zen-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Monitoring

### Prometheus Metrics

The application exposes metrics at `/metrics`:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'zen-pentest'
    static_configs:
      - targets: ['zen-api:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Import dashboard `grafana/dashboard.json` for:
- Request rate and latency
- Task queue depth
- System resource usage
- Error rates

### Health Checks

```bash
# Liveness probe
curl http://localhost:8000/live

# Readiness probe
curl http://localhost:8000/ready

# Full health check
curl http://localhost:8000/health
```

## Security Hardening

### 1. SSL/TLS

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.zenpentest.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://zen-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Network Policies (Kubernetes)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: zen-network-policy
  namespace: zen-pentest
spec:
  podSelector:
    matchLabels:
      app: zen-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

### 3. Secrets Management

Use external secret management:

```bash
# HashiCorp Vault
vault kv put secret/zen-pentest \
  SECRET_KEY="..." \
  DB_PASSWORD="..."

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name zen-pentest/config \
  --secret-string file://secrets.json
```

## Backup & Recovery

### Database Backup

```bash
# PostgreSQL
pg_dump -h localhost -U postgres zenpentest > backup.sql

# Automated with cron
0 2 * * * pg_dump -h localhost -U postgres zenpentest | gzip > /backups/zenpentest-$(date +%Y%m%d).sql.gz
```

### Configuration Backup

```bash
# Backup environment
tar -czf config-backup.tar.gz .env docker-compose.yml nginx.conf

# Store in S3
aws s3 cp config-backup.tar.gz s3://zen-pentest-backups/
```

### Recovery

```bash
# Restore database
gunzip < backup.sql.gz | psql -h localhost -U postgres zenpentest

# Restart services
docker-compose up -d
```

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Verify connection string
psql $DATABASE_URL -c "SELECT 1"
```

**2. Worker Not Processing Tasks**
```bash
# Check worker logs
docker-compose logs worker

# Verify Redis connection
redis-cli -u $REDIS_URL ping
```

**3. High Memory Usage**
```bash
# Check memory usage
docker stats

# Adjust worker count
export MAX_WORKERS=5
```

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=debug

# Run with reload
python -m uvicorn api.main:app --reload --log-level debug
```

## Upgrading

### Zero-Downtime Deployment

```bash
# 1. Deploy new version alongside old
docker-compose -f docker-compose.yml -f docker-compose.new.yml up -d

# 2. Verify new version works
curl http://localhost:8000/health

# 3. Switch traffic (nginx reload)
docker-compose exec nginx nginx -s reload

# 4. Remove old version
docker-compose -f docker-compose.yml stop api
docker-compose -f docker-compose.yml rm api
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Rollback (if needed)
alembic downgrade -1
```

## Performance Tuning

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_events_type ON events(type);
```

### Connection Pool Tuning

```env
# .env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
```

### Cache Configuration

```env
CACHE_TTL=300
CACHE_MAX_SIZE=100000
REDIS_CACHE_ENABLED=true
```

## Support

For deployment support:
- Documentation: https://docs.zenpentest.example.com
- Issues: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/issues
- Discussions: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/discussions
