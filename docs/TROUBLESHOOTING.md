# Troubleshooting Guide

Comprehensive troubleshooting guide for Zen AI Pentest covering common issues and solutions.

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Database Connection Issues](#database-connection-issues)
3. [API Startup Errors](#api-startup-errors)
4. [Authentication Issues](#authentication-issues)
5. [Tool Execution Problems](#tool-execution-problems)
6. [Docker Problems](#docker-problems)
7. [Performance Issues](#performance-issues)
8. [WebSocket Issues](#websocket-issues)
9. [Memory Issues](#memory-issues)
10. [Common Error Messages](#common-error-messages)

---

## Quick Diagnostics

### Health Check Script

```bash
#!/bin/bash
# health_check.sh - Quick system health check

echo "=== Zen AI Pentest Health Check ==="
echo

# Check API
echo "1. Checking API..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$API_STATUS" = "200" ]; then
    echo "   ✓ API is running (HTTP $API_STATUS)"
else
    echo "   ✗ API error (HTTP $API_STATUS)"
fi

# Check Database
echo "2. Checking Database..."
if command -v psql &> /dev/null; then
    if psql "$DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1; then
        echo "   ✓ Database connection OK"
    else
        echo "   ✗ Database connection failed"
    fi
else
    echo "   ⚠ psql not installed, skipping DB check"
fi

# Check Redis
echo "3. Checking Redis..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping | grep -q "PONG"; then
        echo "   ✓ Redis is running"
    else
        echo "   ✗ Redis not responding"
    fi
else
    echo "   ⚠ redis-cli not installed, skipping Redis check"
fi

# Check Docker
echo "4. Checking Docker..."
if docker info > /dev/null 2>&1; then
    echo "   ✓ Docker is running"
else
    echo "   ✗ Docker is not running"
fi

# Check Disk Space
echo "5. Checking Disk Space..."
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo "   ✓ Disk usage: ${DISK_USAGE}%"
else
    echo "   ✗ Disk usage critical: ${DISK_USAGE}%"
fi

# Check Memory
echo "6. Checking Memory..."
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ "$MEM_USAGE" -lt 80 ]; then
    echo "   ✓ Memory usage: ${MEM_USAGE}%"
else
    echo "   ✗ Memory usage high: ${MEM_USAGE}%"
fi

echo
echo "=== Health Check Complete ==="
```

---

## Database Connection Issues

### Error: `psycopg2.OperationalError: connection refused`

**Cause:** PostgreSQL is not running or not accessible.

**Solutions:**

```bash
# 1. Check if PostgreSQL is running
sudo systemctl status postgresql

# 2. Start PostgreSQL if stopped
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 3. Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# 4. Verify connection settings in .env
cat .env | grep DATABASE_URL

# 5. Test connection manually
psql postgresql://username:password@localhost:5432/zen_pentest -c "SELECT 1;"
```

### Error: `FATAL: database "zen_pentest" does not exist`

**Cause:** Database not created or wrong database name.

**Solutions:**

```bash
# 1. Create database
sudo -u postgres psql -c "CREATE DATABASE zen_pentest;"

# 2. Run migrations
alembic upgrade head

# 3. Initialize database
python scripts/init_db.py
```

### Error: `FATAL: password authentication failed`

**Cause:** Wrong credentials or authentication method.

**Solutions:**

```bash
# 1. Reset password
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'newpassword';"

# 2. Update pg_hba.conf for local development
sudo nano /etc/postgresql/15/main/pg_hba.conf
# Change: local all all peer -> local all all md5

# 3. Restart PostgreSQL
sudo systemctl restart postgresql

# 4. Update .env with correct credentials
```

### Docker Database Issues

```bash
# Check Docker database container
docker-compose ps
docker-compose logs db

# Restart database container
docker-compose restart db

# Reset Docker volumes (WARNING: data loss)
docker-compose down -v
docker-compose up -d
```

---

## API Startup Errors

### Error: `ModuleNotFoundError: No module named 'xxx'`

**Cause:** Missing Python dependencies.

**Solutions:**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install in development mode
pip install -e .

# 3. Verify installation
pip list | grep -i module_name

# 4. Reinstall if corrupted
pip uninstall package_name
pip install package_name
```

### Error: `Address already in use`

**Cause:** Port 8000 is already in use.

**Solutions:**

```bash
# 1. Find process using port 8000
sudo lsof -i :8000
# or
sudo netstat -tulpn | grep :8000

# 2. Kill process
sudo kill -9 <PID>

# 3. Use different port
python api/main.py --port 8080
# or
uvicorn api.main:app --host 0.0.0.0 --port 8080
```

### Error: `SECRET_KEY not set`

**Cause:** Missing environment variables.

**Solutions:**

```bash
# 1. Copy example environment file
cp .env.example .env

# 2. Generate secure keys
python -c "import secrets; print(f'SECRET_KEY={secrets.token_hex(32)}')" >> .env
python -c "import secrets; print(f'JWT_SECRET_KEY={secrets.token_hex(32)}')" >> .env

# 3. Edit .env with required values
nano .env

# 4. Source environment
export $(cat .env | xargs)
```

### Error: `ImportError: cannot import name 'xxx' from 'yyy'`

**Cause:** Circular imports or wrong import paths.

**Solutions:**

```bash
# 1. Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# 2. Run from project root
cd /path/to/zen-ai-pentest
python -m api.main

# 3. Fix circular imports by reordering imports
# Move imports inside functions if needed
```

---

## Authentication Issues

### Error: `401 Unauthorized`

**Cause:** Invalid or expired JWT token.

**Solutions:**

```bash
# 1. Login again to get new token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'

# 2. Check token expiry
# Decode JWT at https://jwt.io

# 3. Verify JWT_SECRET_KEY matches between services
# Check .env on all services
```

### Error: `403 Forbidden`

**Cause:** Insufficient permissions.

**Solutions:**

```bash
# 1. Check user role in database
psql $DATABASE_URL -c "SELECT username, role FROM users WHERE username='admin';"

# 2. Create admin user if missing
python scripts/create_admin.py --username admin --password secure_password

# 3. Update user role
psql $DATABASE_URL -c "UPDATE users SET role='admin' WHERE username='admin';"
```

### CORS Errors in Browser

**Cause:** CORS not properly configured.

**Solutions:**

```bash
# 1. Update CORS origins in .env
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,https://yourdomain.com

# 2. For development, allow all origins (NOT for production)
# In api/main.py:
# app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```

---

## Tool Execution Problems

### Error: `nmap: command not found`

**Cause:** Nmap not installed or not in PATH.

**Solutions:**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y nmap

# macOS
brew install nmap

# CentOS/RHEL
sudo yum install -y nmap

# Verify installation
which nmap
nmap --version
```

### Error: `Permission denied` when running tools

**Cause:** Insufficient permissions for tool execution.

**Solutions:**

```bash
# 1. Add user to appropriate groups
sudo usermod -aG sudo $USER

# 2. Fix permissions on scripts
chmod +x scripts/*.sh
cd /path/to/zen-ai-pentest && sudo chown -R $USER:$USER .

# 3. For Docker, run with --privileged
docker run --privileged -v /var/run/docker.sock:/var/run/docker.sock ...
```

### Error: `Timeout waiting for tool execution`

**Cause:** Tool taking too long or hanging.

**Solutions:**

```python
# In configuration, increase timeout
TOOL_TIMEOUT = 600  # 10 minutes

# Or in .env
TOOL_TIMEOUT=600
```

### Error: `sqlmap requires target URL`

**Cause:** Missing or invalid target parameter.

**Solutions:**

```bash
# Verify target format
curl -X POST http://localhost:8000/tools/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "sqlmap_scan",
    "target": "http://example.com/page.php?id=1",
    "parameters": {"level": 1, "risk": 1}
  }'
```

---

## Docker Problems

### Error: `Cannot connect to Docker daemon`

**Cause:** Docker service not running or permission issues.

**Solutions:**

```bash
# 1. Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# 2. Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# 3. Verify Docker is running
docker info
```

### Error: `port is already allocated`

**Cause:** Another container or service using the port.

**Solutions:**

```bash
# 1. Find conflicting container
docker ps | grep 8000

# 2. Stop conflicting container
docker stop <container_id>
docker rm <container_id>

# 3. Or use different ports in docker-compose.yml
# ports:
#   - "8080:8000"
```

### Error: `no space left on device`

**Cause:** Docker disk full.

**Solutions:**

```bash
# 1. Clean up unused data
docker system prune -a
docker volume prune

# 2. Remove specific images
docker rmi $(docker images -q)

# 3. Check disk usage
docker system df

# 4. Increase Docker disk size (Docker Desktop)
# Preferences -> Resources -> Disk image size
```

### Container Exits Immediately

```bash
# Check container logs
docker-compose logs <service_name>

# Run container interactively for debugging
docker-compose run --rm api bash

# Check exit code
docker-compose ps
docker inspect <container_id> --format='{{.State.ExitCode}}'
```

---

## Performance Issues

### High CPU Usage

```bash
# Identify CPU-intensive processes
top -p $(pgrep -d',' -f zen)

# Profile Python code
python -m cProfile -o profile.stats api/main.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"

# Check for infinite loops in logs
tail -f logs/zen_ai_pentest.log | grep -i "error\|timeout"
```

### High Memory Usage

```bash
# Check memory usage
ps aux --sort=-%mem | head -20

# Monitor memory in real-time
watch -n 1 'free -h'

# Check for memory leaks
python -m tracemalloc api/main.py

# Limit container memory
docker run -m 2g --memory-swap 2g zen-ai-pentest
```

### Database Performance

```bash
# Check slow queries
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# Analyze and vacuum
psql $DATABASE_URL -c "VACUUM ANALYZE;"

# Check table sizes
psql $DATABASE_URL -c "
SELECT schemaname, tablename, 
pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC 
LIMIT 10;
"

# Add indexes if missing
psql $DATABASE_URL -c "CREATE INDEX CONCURRENTLY idx_findings_severity ON findings(severity);"
```

---

## WebSocket Issues

### Error: `WebSocket connection failed`

**Cause:** WebSocket not properly configured or blocked.

**Solutions:**

```bash
# 1. Verify WebSocket endpoint is running
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Host: localhost:8000" \
  -H "Origin: http://localhost:8000" \
  http://localhost:8000/ws/scans/1

# 2. Check nginx configuration (if using)
# Add to nginx.conf:
# location /ws/ {
#     proxy_pass http://backend;
#     proxy_http_version 1.1;
#     proxy_set_header Upgrade $http_upgrade;
#     proxy_set_header Connection "upgrade";
# }

# 3. Check firewall rules
sudo ufw status
sudo ufw allow 8000/tcp
```

### WebSocket Disconnects Frequently

```bash
# Increase ping timeout
# In WebSocket configuration:
PING_INTERVAL = 20
PING_TIMEOUT = 60

# Check for proxy timeout settings
# nginx: proxy_read_timeout 86400;
```

---

## Memory Issues

### Redis Memory Exhaustion

```bash
# Check Redis memory usage
redis-cli INFO memory

# Set maxmemory policy
redis-cli CONFIG SET maxmemory 1gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Clear Redis cache
redis-cli FLUSHDB
```

### Python Memory Leaks

```python
# Add to your code for debugging
import tracemalloc

tracemalloc.start()
# ... your code ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)
```

---

## Common Error Messages

### `sqlalchemy.exc.IntegrityError`

**Cause:** Database constraint violation.

**Solution:**
```bash
# Check for duplicates
psql $DATABASE_URL -c "SELECT target, COUNT(*) FROM scans GROUP BY target HAVING COUNT(*) > 1;"

# Fix unique constraints
psql $DATABASE_URL -c "DELETE FROM scans WHERE ctid NOT IN (SELECT min(ctid) FROM scans GROUP BY target);"
```

### `pydantic.ValidationError`

**Cause:** Invalid data format in API request.

**Solution:**
```bash
# Check request format
curl -X POST http://localhost:8000/scans \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Scan",
    "target": "example.com",
    "scan_type": "web"
  }'
```

### `asyncio.TimeoutError`

**Cause:** Async operation timed out.

**Solution:**
```python
# Increase timeout in configuration
REQUEST_TIMEOUT = 60  # seconds

# Or use longer timeout for specific calls
import asyncio
result = await asyncio.wait_for(long_operation(), timeout=120)
```

### `ValueError: Invalid database URL`

**Cause:** DATABASE_URL format is incorrect.

**Solution:**
```bash
# Correct format
DATABASE_URL=postgresql://username:password@host:port/database

# For SQLite (development only)
DATABASE_URL=sqlite:///./zen_pentest.db

# Verify URL parsing
python -c "from urllib.parse import urlparse; print(urlparse('$DATABASE_URL'))"
```

---

## Getting Help

If issues persist:

1. **Check Logs:**
   ```bash
   tail -f logs/zen_ai_pentest.log
   docker-compose logs -f
   ```

2. **Run Diagnostics:**
   ```bash
   python scripts/health_check.py
   ```

3. **Enable Debug Mode:**
   ```bash
   export LOG_LEVEL=DEBUG
   python api/main.py
   ```

4. **Contact Support:**
   - GitHub Issues: https://github.com/SHAdd0WTAka/zen-ai-pentest/issues
   - Discord: https://discord.gg/BSmCqjhY
   - Email: support@zen-ai-pentest.dev

5. **Provide Information:**
   - Error message and stack trace
   - Environment details (OS, Python version, Docker version)
   - Steps to reproduce
   - Recent changes made

---

<p align="center">
  <b>Still having issues? Check <a href="../SUPPORT.md">SUPPORT.md</a></b><br>
  <sub>For additional help, join our Discord community</sub>
</p>
