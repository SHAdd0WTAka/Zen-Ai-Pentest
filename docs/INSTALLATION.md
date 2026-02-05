# Installation Guide

Complete installation instructions for Zen AI Pentest on various platforms and deployment methods.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Start (Docker)](#quick-start-docker)
3. [Local Installation](#local-installation)
4. [Production Deployment](#production-deployment)
5. [VirtualBox VM Setup](#virtualbox-vm-setup)
6. [Cloud Deployment](#cloud-deployment)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements

| Component | Specification |
|-----------|--------------|
| CPU | 4 cores (8 recommended) |
| RAM | 8 GB (16 GB recommended) |
| Storage | 20 GB free space |
| OS | Linux, macOS, or Windows 10/11 |
| Python | 3.9 or higher |
| Docker | 20.10+ (for containerized deployment) |

### Recommended for Production

| Component | Specification |
|-----------|--------------|
| CPU | 8+ cores |
| RAM | 32 GB |
| Storage | 100 GB SSD |
| Network | 1 Gbps |
| PostgreSQL | Dedicated instance |

---

## Quick Start (Docker)

The fastest way to get started with Zen AI Pentest.

### Prerequisites

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
cd zen-ai-pentest

# Copy environment configuration
cp .env.example .env

# Edit .env with your settings
nano .env
```

### Environment Configuration

Edit `.env` file:

```env
# Required Settings
SECRET_KEY=your-secret-key-here-change-in-production
DATABASE_URL=postgresql://postgres:password@db:5432/zen_pentest

# AI Provider (choose at least one)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Optional: Local LLM
OLLAMA_BASE_URL=http://ollama:11434

# Security Settings
JWT_SECRET=your-jwt-secret
ENCRYPTION_KEY=your-encryption-key

# Optional: Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

### Start Services

```bash
# Start all services
docker-compose up -d

# Or use the full stack
docker-compose -f docker-compose.full.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Web Dashboard | http://localhost:3000 | React UI |
| API Documentation | http://localhost:8000/docs | Swagger UI |
| API Base | http://localhost:8000 | REST API |
| PostgreSQL | localhost:5432 | Database |

---

## Local Installation

For development or running without Docker.

### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv postgresql redis-server nmap
```

**macOS:**
```bash
brew install python postgresql redis nmap
```

**Windows:**
```powershell
# Install Python from python.org
# Install PostgreSQL from postgresql.org
# Install Npcap for nmap support
choco install nmap redis-64
```

### Step 2: Setup Database

```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE zen_pentest;"
sudo -u postgres psql -c "CREATE USER zen_user WITH PASSWORD 'zen_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE zen_pentest TO zen_user;"
```

### Step 3: Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### Step 4: Initialize Application

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your database credentials

# Run database migrations
alembic upgrade head

# Create initial admin user
python scripts/create_admin.py --username admin --password admin123
```

### Step 5: Start Services

```bash
# Terminal 1: Start API
python api/main.py

# Terminal 2: Start worker (in another terminal)
celery -A tasks worker --loglevel=info

# Terminal 3: Start Redis (if not running as service)
redis-server
```

---

## Production Deployment

### Docker Compose (Production)

```bash
# Use production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale workers
docker-compose up -d --scale worker=5
```

### Security Hardening

```bash
# Generate secure secrets
python -c "import secrets; print(secrets.token_hex(32))"

# Set proper permissions
chmod 600 .env
chown root:root .env

# Enable firewall
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp
sudo ufw enable
```

### SSL/TLS with Nginx

```nginx
server {
    listen 443 ssl http2;
    server_name pentest.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/pentest.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/pentest.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## VirtualBox VM Setup

For isolated penetration testing environments.

### Automated Setup

```bash
# Setup Kali Linux VM
python scripts/setup_vms.py --kali --vm-name kali-pentest

# Setup Ubuntu VM
python scripts/setup_vms.py --ubuntu --vm-name ubuntu-target
```

### Manual VM Configuration

1. **Download Kali Linux VM**:
   ```bash
   wget https://kali.download/virtual-images/kali-linux-2024.1-vmware-amd64.7z
   ```

2. **Import to VirtualBox**:
   - File → Import Appliance
   - Select downloaded .ova file
   - Adjust memory (4GB minimum)

3. **Configure Network**:
   ```bash
   # Host-Only Network for isolated testing
   VBoxManage hostonlyif create
   VBoxManage modifyvm "kali-pentest" --nic2 hostonly --hostonlyadapter2 vboxnet0
   ```

4. **Install Guest Additions**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y virtualbox-guest-additions-iso
   sudo mount /usr/share/virtualbox/VBoxGuestAdditions.iso /mnt
   sudo /mnt/VBoxLinuxAdditions.run
   ```

---

## Cloud Deployment

### AWS Deployment

```bash
# Using ECS
aws ecs create-cluster --cluster-name zen-pentest

# Deploy with CloudFormation
aws cloudformation create-stack \
  --stack-name zen-pentest \
  --template-file aws/ecs-template.yaml \
  --parameters ParameterKey=Environment,ParameterValue=production
```

### Azure Deployment

```bash
# Using AKS
az aks create \
  --resource-group zen-pentest-rg \
  --name zen-pentest-cluster \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Deploy
kubectl apply -f k8s/
```

### Google Cloud Deployment

```bash
# Using GKE
gcloud container clusters create zen-pentest-cluster \
  --num-nodes=3 \
  --zone=us-central1-a

# Deploy
gcloud apply -f k8s/
```

---

## Troubleshooting

### Common Issues

#### Database Connection Failed

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Verify connection
psql -h localhost -U zen_user -d zen_pentest

# Check logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

#### Redis Connection Error

```bash
# Start Redis
redis-server --daemonize yes

# Test connection
redis-cli ping
# Should return: PONG
```

#### Permission Denied

```bash
# Fix permissions
sudo chown -R $USER:$USER .
chmod +x scripts/*.sh

# Docker permission
sudo usermod -aG docker $USER
# Logout and login again
```

#### Port Already in Use

```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>

# Or use different port
python api/main.py --port 8080
```

### Health Check

```bash
# Run health check script
python scripts/health_check.py

# Check API health
curl http://localhost:8000/health

# Check all services
docker-compose ps
```

### Getting Help

If you encounter issues not covered here:

1. Check [GitHub Issues](https://github.com/SHAdd0WTAka/zen-ai-pentest/issues)
2. Join our [Discord Community](https://discord.gg/zen-ai-pentest)
3. Read [SUPPORT.md](../SUPPORT.md) for more options

---

## Next Steps

After installation:

1. **[Getting Started](tutorials/getting-started.md)** - Run your first scan
2. **[API Documentation](API.md)** - Learn the API
3. **[Architecture Overview](ARCHITECTURE.md)** - Understand the system

---

<p align="center">
  <b>Installation complete! Happy pentesting! 🛡️</b><br>
  <sub>© 2026 Zen AI Pentest. All rights reserved.</sub>
</p>
