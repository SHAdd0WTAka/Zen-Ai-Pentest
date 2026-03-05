#!/bin/bash
# Cloudflare Tunnel Setup for Zen-AI-Pentest
# ==========================================
# Secure external access with Kimi Device Authentication

set -e

echo "🌐 Zen-AI-Pentest + Cloudflare Tunnel Setup"
echo "============================================"

# Check requirements
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Run from zen-ai-pentest root directory"
    exit 1
fi

# Install cloudflared if needed
if ! command -v cloudflared &> /dev/null; then
    echo "📦 Installing cloudflared..."
    wget -q "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb" -O /tmp/cloudflared.deb
    sudo dpkg -i /tmp/cloudflared.deb 2>/dev/null || sudo apt-get install -f -y
    rm /tmp/cloudflared.deb
fi

# Configuration
read -p "Cloudflare domain (e.g., example.com): " DOMAIN
read -p "Subdomain [zen-ai]: " SUBDOMAIN
SUBDOMAIN=${SUBDOMAIN:-zen-ai}
read -p "Web UI port [3000]: " WEB_PORT
WEB_PORT=${WEB_PORT:-3000}
read -p "API port [8000]: " API_PORT
API_PORT=${API_PORT:-8000}

HOSTNAME="${SUBDOMAIN}.${DOMAIN}"

echo ""
echo "🔑 Login to Cloudflare (browser will open)..."
cloudflared tunnel login

# Create tunnel
echo "🚇 Creating tunnel..."
TUNNEL_NAME="zen-ai-pentest"
TUNNEL_OUTPUT=$(cloudflared tunnel create "$TUNNEL_NAME" 2>&1 || true)

# Extract tunnel ID
TUNNEL_ID=$(echo "$TUNNEL_OUTPUT" | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)

if [ -z "$TUNNEL_ID" ]; then
    # Try to get existing tunnel
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}' | head -1)
fi

if [ -z "$TUNNEL_ID" ]; then
    echo "❌ Failed to create/get tunnel"
    exit 1
fi

echo "✅ Tunnel ID: $TUNNEL_ID"

# Create config
sudo mkdir -p /etc/cloudflared

sudo tee /etc/cloudflared/config.yml > /dev/null << EOF
tunnel: ${TUNNEL_ID}
credentials-file: ${HOME}/.cloudflared/${TUNNEL_ID}.json

ingress:
  # Zen-AI Web UI
  - hostname: ${HOSTNAME}
    service: http://localhost:${WEB_PORT}

  # API
  - hostname: api.${HOSTNAME}
    service: http://localhost:${API_PORT}

  # Fallback
  - service: http_status:404
EOF

# Create DNS records
echo "📡 Creating DNS records..."
cloudflared tunnel route dns "$TUNNEL_NAME" "$HOSTNAME" 2>/dev/null || true
cloudflared tunnel route dns "$TUNNEL_NAME" "api.$HOSTNAME" 2>/dev/null || true

# Install systemd service
echo "🔧 Installing service..."
sudo cloudflared service install 2>/dev/null || true
sudo systemctl restart cloudflared 2>/dev/null || true

echo ""
echo "✅ Setup complete!"
echo ""
echo "URLs:"
echo "  Web UI: https://${HOSTNAME}"
echo "  API:    https://api.${HOSTNAME}"
echo ""
echo "Services:"
echo "  sudo systemctl start cloudflared"
echo "  sudo systemctl stop cloudflared"
echo ""
echo "Kimi Device Auth:"
echo "  1. Ensure 'kimi login' was run locally"
echo "  2. Access https://${HOSTNAME} from mobile"
echo "  3. Scan QR code with Kimi app"
