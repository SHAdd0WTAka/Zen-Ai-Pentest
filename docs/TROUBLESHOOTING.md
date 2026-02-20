# Troubleshooting Guide

> **Comprehensive troubleshooting for Zen-AI-Pentest**

---

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Common Installation Issues](#common-installation-issues)
- [Common Runtime Errors](#common-runtime-errors)
- [Windows-Specific Issues](#windows-specific-issues)
- [Linux-Specific Issues](#linux-specific-issues)
- [macOS-Specific Issues](#macos-specific-issues)
- [Docker Issues](#docker-issues)
- [Database Issues](#database-issues)
- [Authentication Issues](#authentication-issues)
- [Tool Execution Problems](#tool-execution-problems)
- [WebSocket Issues](#websocket-issues)
- [Performance Issues](#performance-issues)
- [Memory Issues](#memory-issues)
- [Network Issues](#network-issues)
- [Getting Help](#getting-help)

---

## Quick Diagnostics

### Automated Health Check

```bash
# Run the built-in health check
python scripts/health_check.py

# Or manually check components
curl http://localhost:8000/health
docker-compose ps
```

### Manual Health Check Script

```bash
#!/bin/bash
# save as: health_check.sh

echo "=== Zen-AI-Pentest Health Check ==="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Check API
echo "1. Checking API..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
if [ "$API_STATUS" = "200" ]; then
    echo -e "   ${GREEN}✓${NC} API is running (HTTP $API_STATUS)"
else
    echo -e "   ${RED}✗${NC} API error (HTTP ${API_STATUS:-"connection refused"})"
fi

# 2. Check Database
echo "2. Checking Database..."
if command -v psql &> /dev/null; then
    if psql "$DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1; then
        echo -e "   ${GREEN}✓${NC} Database connection OK"
    else
        echo -e "   ${RED}✗${NC} Database connection failed"
    fi
else
    echo -e "   ${YELLOW}⚠${NC} psql not installed, skipping DB check"
fi

# 3. Check Redis
echo "3. Checking Redis..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping 2>/dev/null | grep -q "PONG"; then
        echo -e "   ${GREEN}✓${NC} Redis is running"
    else
        echo -e "   ${RED}✗${NC} Redis not responding"
    fi
else
    echo -e "   ${YELLOW}⚠${NC} redis-cli not installed, skipping Redis check"
fi

# 4. Check Docker
echo "4. Checking Docker..."
if docker info > /dev/null 2>&1; then
    echo -e "   ${GREEN}✓${NC} Docker is running"
    
    # Check containers
    RUNNING=$(docker-compose ps -q 2>/dev/null | wc -l)
    echo "   Found $RUNNING running containers"
else
    echo -e "   ${RED}✗${NC} Docker is not running"
fi

# 5. Check Disk Space
echo "5. Checking Disk Space..."
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "   ${GREEN}✓${NC} Disk usage: ${DISK_USAGE}%"
else
    echo -e "   ${RED}✗${NC} Disk usage critical: ${DISK_USAGE}%"
fi

# 6. Check Memory
echo "6. Checking Memory..."
if command -v free &> /dev/null; then
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$MEM_USAGE" -lt 80 ]; then
        echo -e "   ${GREEN}✓${NC} Memory usage: ${MEM_USAGE}%"
    else
        echo -e "   ${RED}✗${NC} Memory usage high: ${MEM_USAGE}%"
    fi
else
    echo -e "   ${YELLOW}⚠${NC} Cannot check memory (free not available)"
fi

# 7. Check Python
echo "7. Checking Python..."
PY_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "   Python version: $PY_VERSION"

# 8. Check pip packages
echo "8. Checking pip packages..."
MISSING=$(pip list 2>/dev/null | grep -E "fastapi|uvicorn|sqlalchemy" | wc -l)
if [ "$MISSING" -ge 3 ]; then
    echo -e "   ${GREEN}✓${NC} Core packages installed"
else
    echo -e "   ${RED}✗${NC} Some packages missing"
fi

echo ""
echo "=== Health Check Complete ==="
```

---

## Common Installation Issues

### Python Version Issues

**Problem**: `Python 3.11+ required` error

**Solution:**
```bash
# Check Python version
python --version

# Install Python 3.11+ (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip

# Use pyenv for version management
curl https://pyenv.run | bash
pyenv install 3.11.0
pyenv local 3.11.0
```

### Virtual Environment Issues

**Problem**: `ModuleNotFoundError` after installation

**Solution:**
```bash
# Remove old venv
rm -rf venv

# Create fresh venv
python3.11 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Permission Denied During pip Install

**Solution:**
```bash
# Use --user flag
pip install --user -r requirements.txt

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Common Runtime Errors

### ImportError: cannot import name 'xxx'

**Problem**: Circular import or missing module

**Solution:**
```bash
# 1. Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# 2. Run from project root
cd /path/to/zen-ai-pentest
python -m api.main

# 3. Install missing package
pip install missing-package

# 4. Fix circular imports
# Move imports inside functions if needed
```

### ModuleNotFoundError: No module named 'xxx'

**Solution:**
```bash
# 1. Ensure venv is activated
which python
# Should show: /path/to/zen-ai-pentest/venv/bin/python

# 2. Reinstall requirements
pip install -r requirements.txt

# 3. Install in editable mode
pip install -e .

# 4. Check package is installed
pip list | grep package_name
```

### Address Already in Use

**Problem**: Port 8000 is already in use

**Solution:**
```bash
# Linux/macOS: Find and kill process
sudo lsof -i :8000
sudo kill -9 <PID>

# Or use different port
uvicorn api.main:app --port 8080

# Windows: Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### SECRET_KEY not set

**Problem**: Missing environment variables

**Solution:**
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

---

## Windows-Specific Issues

### PowerShell Execution Policy

**Problem**: `cannot be loaded because running scripts is disabled`

**Solution:**
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Verify
Get-ExecutionPolicy
```

### Path Length Limit

**Problem**: `File path too long` error

**Solution:**
```powershell
# Enable long path support (Windows 10 1607+)
# Run as Administrator in PowerShell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
  -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Or use Python prefix
\\?\C:\very\long\path
```

### Docker Desktop WSL2 Issues

**Problem**: Docker Desktop not starting or slow

**Solution:**
```powershell
# 1. Enable WSL2
wsl --set-default-version 2

# 2. Convert existing distro
wsl --set-version Ubuntu 2

# 3. Set WSL2 as default in Docker Desktop
# Settings → General → Use WSL 2 based engine

# 4. Reset Docker Desktop if needed
# Troubleshoot → Reset to factory defaults
```

### Windows Defender Blocking

**Problem**: Windows Defender blocking tool execution

**Solution:**
```powershell
# Add exclusion for project directory
Add-MpPreference -ExclusionPath "C:\path\to\zen-ai-pentest"

# Or disable real-time protection (not recommended for production)
Set-MpPreference -DisableRealtimeMonitoring $true
```

### CRLF Line Endings

**Problem**: Scripts fail with `^M: bad interpreter`

**Solution:**
```bash
# Configure Git to handle line endings
git config --global core.autocrlf false

# Convert existing files
dos2unix scripts/*.sh

# Or use sed
sed -i 's/\r$//' script.sh
```

---

## Linux-Specific Issues

### Permission Denied (Nmap)

**Problem**: `You don't have permission to capture on that device`

**Solution:**
```bash
# Option 1: Run with sudo (not recommended)
sudo python -m modules.super_scanner -t target.com

# Option 2: Add capabilities
sudo setcap cap_net_raw,cap_net_admin=eip $(which nmap)

# Option 3: Add user to wireshark group
sudo usermod -aG wireshark $USER
newgrp wireshark
```

### PostgreSQL Connection Issues

**Problem**: `psycopg2.OperationalError: connection refused`

**Solution:**
```bash
# 1. Check PostgreSQL status
sudo systemctl status postgresql

# 2. Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 3. Check logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# 4. Allow local connections
sudo nano /etc/postgresql/15/main/pg_hba.conf
# Change: local all all peer -> local all all md5
sudo systemctl restart postgresql
```

### Missing System Libraries

**Problem**: Compilation errors during pip install

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    build-essential \
    git

# CentOS/RHEL
sudo yum install -y \
    python3-devel \
    postgresql-devel \
    openssl-devel \
    libffi-devel \
    gcc \
    git
```

### AppArmor/SELinux Blocking

**Problem**: Permission denied despite correct permissions

**Solution:**
```bash
# For AppArmor (Ubuntu)
sudo aa-status
sudo ln -s /etc/apparmor.d/usr.sbin.nginx /etc/apparmor.d/disable/
sudo apparmor_parser -R /etc/apparmor.d/usr.sbin.nginx

# For SELinux (CentOS/RHEL)
# Check status
getenforce

# Temporarily disable
sudo setenforce 0

# Check audit logs
sudo ausearch -m avc -ts recent
```

---

## macOS-Specific Issues

### Xcode Command Line Tools

**Problem**: `xcrun: error: invalid active developer path`

**Solution:**
```bash
# Install Xcode command line tools
xcode-select --install

# If already installed, reset
sudo xcode-select --reset

# Or specify path
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

### OpenSSL Issues

**Problem**: OpenSSL version conflicts

**Solution:**
```bash
# Install OpenSSL via Homebrew
brew install openssl

# Set environment variables
export LDFLAGS="-L/opt/homebrew/opt/openssl/lib"
export CPPFLAGS="-I/opt/homebrew/opt/openssl/include"
export PKG_CONFIG_PATH="/opt/homebrew/opt/openssl/lib/pkgconfig"

# Reinstall cryptography package
pip uninstall cryptography
pip install cryptography
```

### Intel vs Apple Silicon

**Problem**: Rosetta 2 required but not installed

**Solution:**
```bash
# Install Rosetta 2
softwareupdate --install-rosetta

# Run x86_64 architecture
arch -x86_64 /bin/bash

# Or install x86 Python
arch -x86_64 brew install python@3.11
```

---

## Docker Issues

### Cannot Connect to Docker Daemon

**Problem**: `Cannot connect to Docker daemon`

**Solution:**
```bash
# Linux: Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker info

# macOS/Windows: Check Docker Desktop is running
```

### Port Already Allocated

**Problem**: `port is already allocated`

**Solution:**
```bash
# Find container using port
docker ps | grep 8000

# Stop container
docker stop <container_id>
docker rm <container_id>

# Or use different ports
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

### No Space Left on Device

**Problem**: Docker disk full

**Solution:**
```bash
# Clean up unused data
docker system prune -a --volumes

# Check disk usage
docker system df

# Remove specific images
docker rmi $(docker images -q --filter "dangling=true")

# Increase disk size (Docker Desktop)
# Preferences → Resources → Disk image size
```

### Container Exits Immediately

**Problem**: Container starts then exits

**Solution:**
```bash
# Check logs
docker-compose logs <service_name>

# Run interactively
docker-compose run --rm api bash

# Check exit code
docker-compose ps
docker inspect <container_id> --format='{{.State.ExitCode}}'

# Check entrypoint
ENTRYPOINT=$(docker inspect <container_id> --format='{{.Config.Entrypoint}}')
echo "Entrypoint: $ENTRYPOINT"
```

---

## Database Issues

### Database Does Not Exist

**Problem**: `FATAL: database "zen_pentest" does not exist`

**Solution:**
```bash
# Create database
sudo -u postgres psql -c "CREATE DATABASE zen_pentest;"

# Or with createdb
createdb -U postgres zen_pentest

# Run migrations
alembic upgrade head

# Initialize database
python scripts/init_db.py
```

### Password Authentication Failed

**Problem**: `FATAL: password authentication failed`

**Solution:**
```bash
# Reset password
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'newpassword';"

# Or create new user
sudo -u postgres psql -c "CREATE USER zen WITH PASSWORD 'password' SUPERUSER;"
sudo -u postgres psql -c "CREATE DATABASE zen_pentest OWNER zen;"

# Update .env
DATABASE_URL=postgresql://zen:password@localhost:5432/zen_pentest
```

### Connection Pool Exhausted

**Problem**: `FATAL: sorry, too many clients already`

**Solution:**
```bash
# Check active connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Increase max connections
psql $DATABASE_URL -c "ALTER SYSTEM SET max_connections = 200;"

# Or restart PostgreSQL
sudo systemctl restart postgresql
```

---

## Authentication Issues

### 401 Unauthorized

**Problem**: JWT token invalid or expired

**Solution:**
```bash
# 1. Login again to get new token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# 2. Check token expiry
# Decode JWT at https://jwt.io

# 3. Verify JWT_SECRET_KEY matches
# Check .env on all services
```

### 403 Forbidden

**Problem**: Valid token but insufficient permissions

**Solution:**
```bash
# Check user role
psql $DATABASE_URL -c "SELECT username, role FROM users WHERE username='admin';"

# Update user role
psql $DATABASE_URL -c "UPDATE users SET role='admin' WHERE username='admin';"

# Or create admin user
python scripts/create_admin.py --username admin --password secure_password
```

### CORS Errors

**Problem**: `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution:**
```python
# In api/main.py or .env
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,https://yourdomain.com

# For development only (not production)
CORS_ORIGINS=*
```

---

## Tool Execution Problems

### Tool Not Found

**Problem**: `nmap: command not found`

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install -y nmap nikto sqlmap

# macOS
brew install nmap nikto sqlmap

# Verify
which nmap
nmap --version
```

### Timeout Waiting for Tool

**Problem**: Tool execution times out

**Solution:**
```python
# In .env or configuration
TOOL_TIMEOUT=600  # 10 minutes
SCAN_TIMEOUT=3600  # 1 hour

# For specific tools
NMAP_TIMEOUT=300
SQLMAP_TIMEOUT=1800
```

### Private IP Blocked

**Problem**: `Private IP blocked by safety controls`

**Solution:**
```python
# This is expected behavior for safety
# To allow internal scanning (not recommended for production):

# 1. Set in .env
ALLOW_PRIVATE_IPS=true

# 2. Or modify guardrails.py
# WARNING: Only for isolated test environments
```

---

## WebSocket Issues

### Connection Failed

**Problem**: WebSocket connection fails

**Solution:**
```bash
# 1. Verify WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Host: localhost:8000" \
  -H "Origin: http://localhost:8000" \
  http://localhost:8000/ws/scans/1

# 2. Check nginx configuration
location /ws/ {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;
}

# 3. Check firewall
sudo ufw allow 8000/tcp
sudo ufw status
```

### Frequent Disconnections

**Solution:**
```python
# Increase ping timeout
PING_INTERVAL = 20
PING_TIMEOUT = 60

# Client-side reconnection
const ws = new WebSocket(url);
ws.onclose = () => {
    setTimeout(() => reconnect(), 5000);
};
```

---

## Performance Issues

### High CPU Usage

**Solution:**
```bash
# Identify CPU-intensive processes
top -p $(pgrep -d',' -f zen)

# Profile Python code
python -m cProfile -o profile.stats api/main.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"

# Limit workers
uvicorn api.main:app --workers 2
```

### High Memory Usage

**Solution:**
```bash
# Check memory usage
ps aux --sort=-%mem | head -20

# Enable garbage collection
import gc
gc.collect()

# Limit container memory
docker run -m 2g --memory-swap 2g zen-ai-pentest
```

### Slow Database Queries

**Solution:**
```bash
# Check slow queries
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# Add indexes
psql $DATABASE_URL -c "CREATE INDEX CONCURRENTLY idx_findings_severity ON findings(severity);"

# Analyze tables
psql $DATABASE_URL -c "VACUUM ANALYZE;"
```

---

## Memory Issues

### Redis Memory Exhaustion

**Solution:**
```bash
# Check memory usage
redis-cli INFO memory

# Set maxmemory policy
redis-cli CONFIG SET maxmemory 1gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Clear cache
redis-cli FLUSHDB
```

### Python Memory Leaks

**Solution:**
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

## Network Issues

### VPN Connection Problems

**Solution:**
```bash
# Check VPN status
python -c "from tools.vpn_integration import check_vpn; print(check_vpn())"

# Force VPN requirement
REQUIRE_VPN=true

# Disable VPN check (not recommended)
REQUIRE_VPN=false
```

### Proxy Configuration

**Solution:**
```bash
# Set proxy environment variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1

# In Python requests
proxies = {
    'http': 'http://proxy.company.com:8080',
    'https': 'http://proxy.company.com:8080',
}
```

---

## Getting Help

If issues persist:

1. **Check Logs:**
   ```bash
   tail -f logs/zen_ai_pentest.log
   docker-compose logs -f
   ```

2. **Enable Debug Mode:**
   ```bash
   export LOG_LEVEL=DEBUG
   python api/main.py
   ```

3. **Run Diagnostics:**
   ```bash
   python scripts/health_check.py
   ```

4. **Contact Support:**
   - GitHub Issues: https://github.com/SHAdd0WTAka/zen-ai-pentest/issues
   - Discord: https://discord.gg/zJZUJwK9AC
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
