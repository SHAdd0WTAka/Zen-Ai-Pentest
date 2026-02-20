# Production Hardening Guide

This guide covers security hardening steps for deploying Zen AI Pentest in production environments.

## Quick Reference

| Check | Priority | Status |
|-------|----------|--------|
| Environment Variables | Critical | Required |
| Database Security | Critical | Required |
| TLS/SSL | Critical | Required |
| Network Security | High | Required |
| Rate Limiting | High | Configured |
| CSRF Protection | High | Configured |
| Audit Logging | High | Required |
| Secrets Rotation | Medium | Recommended |
| Security Headers | Medium | Recommended |

---

## 1. Environment Variables

### Required Secrets

Create a `.env` file with strong, unique values:

```bash
# JWT Configuration
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Admin Credentials
ADMIN_PASSWORD=$(openssl rand -base64 24)

# Database (PostgreSQL recommended for production)
DATABASE_URL=postgresql://user:password@localhost/zen_pentest
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# CSRF Protection
CSRF_SECRET_KEY=$(openssl rand -hex 32)

# KI Integration
KI_API_KEY=your_ki_api_key

# Rate Limiting (Redis recommended for multi-instance)
REDIS_URL=redis://localhost:6379/0
```

### Generate Secure Keys

```bash
# JWT Secret (256-bit)
openssl rand -hex 32

# CSRF Secret
openssl rand -hex 32

# Admin Password
openssl rand -base64 24

# Database Password
openssl rand -base64 32
```

---

## 2. Database Security

### PostgreSQL Hardening

```sql
-- Create dedicated user
CREATE USER zen_pentest WITH PASSWORD 'strong_password';

-- Create database
CREATE DATABASE zen_pentest OWNER zen_pentest;

-- Revoke public access
REVOKE ALL ON DATABASE zen_pentest FROM PUBLIC;

-- Enable SSL
ALTER SYSTEM SET ssl = on;
```

### pg_hba.conf

```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
hostssl zen_pentest     zen_pentest     10.0.0.0/8              scram-sha-256
hostssl zen_pentest     zen_pentest     172.16.0.0/12           scram-sha-256
hostssl zen_pentest     zen_pentest     192.168.0.0/16          scram-sha-256
local   all             all                                     peer
```

### Connection Pooling

Database connection pooling is configured with these defaults:

```python
POOL_CONFIG = {
    "pool_size": 10,           # Standard connections
    "max_overflow": 20,        # Additional connections under load
    "pool_timeout": 30,        # Seconds to wait for connection
    "pool_recycle": 3600,      # Recycle connections after 1 hour
    "pool_pre_ping": True      # Verify connections before use
}
```

---

## 3. TLS/SSL Configuration

### Nginx Reverse Proxy

```nginx
server {
    listen 443 ssl http2;
    server_name pentest.example.com;

    ssl_certificate /etc/ssl/certs/pentest.crt;
    ssl_certificate_key /etc/ssl/private/pentest.key;

    # Strong SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Certificate Management

```bash
# Let's Encrypt
sudo certbot --nginx -d pentest.example.com

# Auto-renewal
echo "0 3 * * * root certbot renew --quiet" | sudo tee -a /etc/crontab
```

---

## 4. Network Security

### Firewall Rules (iptables)

```bash
#!/bin/bash
iptables -F

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH (restrict to specific IP if possible)
iptables -A INPUT -p tcp --dport 22 -s YOUR_IP/32 -j ACCEPT

# Allow HTTPS
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow HTTP (redirect to HTTPS)
iptables -A INPUT -p tcp --dport 80 -j ACCEPT

# Rate limit incoming connections
iptables -A INPUT -p tcp --dport 443 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
```

### Fail2Ban

```ini
# /etc/fail2ban/jail.local
[zen-pentest]
enabled = true
port = http,https
filter = zen-pentest
logpath = /var/log/zen-pentest/api.log
maxretry = 5
bantime = 3600
```

---

## 5. Rate Limiting

Rate limiting is implemented at multiple levels:

### Application Level

```python
# General API: 60 requests/minute
@rate_limit(requests=60, window=60)

# Authentication: 5 attempts/minute
@rate_limit(requests=5, window=60, scope="auth")
```

### Redis Backend (Multi-instance)

```bash
# Install Redis for distributed rate limiting
sudo apt install redis-server

# Configure Redis
sudo sed -i 's/^# requirepass.*/requirepass your_redis_password/' /etc/redis/redis.conf
sudo systemctl restart redis
```

---

## 6. CSRF Protection

CSRF protection uses the Double-Submit Cookie pattern:

### Configuration

```python
# CSRF token settings
CSRF_TOKEN_TTL = 86400  # 24 hours
CSRF_COOKIE_SECURE = True  # HTTPS only
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
```

### Client Implementation

```javascript
// Get CSRF token from meta tag or cookie
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

// Include in requests
fetch('/api/protected', {
    method: 'POST',
    headers: {
        'X-CSRF-Token': csrfToken
    },
    credentials: 'include'
});
```

---

## 7. Audit Logging

### Log Configuration

```python
LOGGING_CONFIG = {
    "version": 1,
    "handlers": {
        "audit_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/zen-pentest/audit.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "formatter": "audit"
        }
    },
    "loggers": {
        "zen_audit": {
            "handlers": ["audit_file"],
            "level": "INFO"
        }
    }
}
```

### Audit Events

| Event | Level | Data Logged |
|-------|-------|-------------|
| login | INFO | user_id, ip, success/failure |
| scan_start | INFO | scan_id, user_id, target |
| scan_complete | INFO | scan_id, findings_count |
| export | INFO | report_id, user_id, format |
| config_change | WARN | user_id, setting, old->new |

---

## 8. Secrets Rotation

### Rotation Schedule

| Secret | Rotation Frequency |
|--------|-------------------|
| JWT Secret | Every 90 days |
| Database Password | Every 180 days |
| API Keys | Every 90 days |
| Admin Password | Every 90 days |

### Rotation Script

```bash
#!/bin/bash
# secrets-rotation.sh

# Generate new secrets
NEW_JWT_SECRET=$(openssl rand -hex 32)
NEW_CSRF_SECRET=$(openssl rand -hex 32)

# Update environment
# (Use your secret management system: Vault, AWS Secrets Manager, etc.)
echo "JWT_SECRET_KEY=$NEW_JWT_SECRET" > .env.new

# Graceful restart (zero-downtime with multiple instances)
systemctl reload zen-pentest
```

---

## 9. Security Headers

### FastAPI Middleware

```python
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

---

## 10. Docker Security

### Dockerfile Hardening

```dockerfile
# Non-root user
RUN adduser --disabled-password --gecos '' zenuser
USER zenuser

# Read-only filesystem
VOLUME ["/tmp", "/var/log"]

# Drop capabilities
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE
```

### docker-compose.security.yml

```yaml
version: '3.8'
services:
  app:
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
```

---

## 11. Backup and Recovery

### Database Backup

```bash
#!/bin/bash
# backup.sh - Run daily via cron

BACKUP_DIR="/backup/zen-pentest"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
pg_dump -h localhost -U zen_pentest zen_pentest | \
    gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Retention: Keep 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
```

### Encryption

```bash
# Encrypt backups
gpg --symmetric --cipher-algo AES256 \
    --output "db_$DATE.sql.gz.gpg" \
    "db_$DATE.sql.gz"
```

---

## 12. Monitoring and Alerting

### Key Metrics

| Metric | Threshold | Action |
|--------|-----------|--------|
| Failed Logins | > 10/min | Alert admin |
| API Errors | > 5% rate | Investigate |
| Response Time | > 2s avg | Scale up |
| Disk Usage | > 80% | Cleanup/expand |
| Memory Usage | > 90% | Alert/scale |

### Prometheus/Grafana

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

---

## 13. Incident Response

### Security Incident Checklist

1. **Immediate Response**
   - [ ] Isolate affected systems
   - [ ] Preserve logs and evidence
   - [ ] Notify security team

2. **Investigation**
   - [ ] Review audit logs
   - [ ] Analyze access patterns
   - [ ] Identify attack vector

3. **Containment**
   - [ ] Rotate all secrets
   - [ ] Revoke compromised sessions
   - [ ] Block malicious IPs

4. **Recovery**
   - [ ] Restore from clean backup
   - [ ] Apply security patches
   - [ ] Verify system integrity

5. **Post-Incident**
   - [ ] Document lessons learned
   - [ ] Update security controls
   - [ ] Share threat intelligence

---

## 14. Compliance

### GDPR Considerations

- [ ] Data minimization (only store necessary data)
- [ ] Right to erasure (delete user data on request)
- [ ] Data portability (export user data)
- [ ] Breach notification (72-hour window)

### Penetration Test Data

- [ ] Encrypt all scan results at rest
- [ ] Anonymize target data in logs
- [ ] Set data retention limits (e.g., 90 days)
- [ ] Secure deletion procedures

---

## Resources

- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

**Last Updated**: 2026-02-04
**Version**: 1.0
**Classification**: Internal Use
