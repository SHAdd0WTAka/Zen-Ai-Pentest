#!/bin/bash
# Dead Man's Switch Setup Script
# ==============================
# Sets up automatic credential lock when Cloudflare Tunnel disconnects

set -e

echo "☠️ Dead Man's Switch Setup"
echo "=========================="

# Check requirements
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Run from zen-ai-pentest root directory"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install cryptography -q 2>/dev/null || true

# Setup directories
echo "📁 Setting up directories..."
mkdir -p ~/.secure
chmod 700 ~/.secure

mkdir -p ~/obsidian-vault
chmod 700 ~/obsidian-vault

# Create systemd service for kill switch monitor
echo "🔧 Creating systemd service..."

SERVICE_FILE="$HOME/.config/systemd/user/deadman-switch.service"
mkdir -p "$HOME/.config/systemd/user"

cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=Dead Man's Switch Monitor
After=network.target

[Service]
Type=simple
ExecStart=%h/zen-ai-pentest/.venv/bin/python -m core.kill_switch monitor
Restart=always
RestartSec=10
Environment=PYTHONPATH=%h/zen-ai-pentest

[Install]
WantedBy=default.target
EOF

# Create wrapper script
WRAPPER="$HOME/.local/bin/deadman-switch"
mkdir -p "$HOME/.local/bin"

cat > "$WRAPPER" << 'EOF'
#!/bin/bash
# Dead Man's Switch CLI Wrapper

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZEN_DIR="$HOME/zen-ai-pentest"

case "$1" in
    status)
        cd "$ZEN_DIR" && python -m core.kill_switch status
        ;;
    lock)
        cd "$ZEN_DIR" && python -m core.kill_switch lock
        ;;
    monitor)
        cd "$ZEN_DIR" && python -m core.kill_switch monitor
        ;;
    enable)
        systemctl --user enable deadman-switch.service
        systemctl --user start deadman-switch.service
        echo "✅ Dead Man's Switch enabled"
        ;;
    disable)
        systemctl --user stop deadman-switch.service
        systemctl --user disable deadman-switch.service
        echo "🛑 Dead Man's Switch disabled"
        ;;
    *)
        echo "Dead Man's Switch Control"
        echo ""
        echo "Usage: deadman-switch [command]"
        echo ""
        echo "Commands:"
        echo "  status    Show current status"
        echo "  lock      Manually trigger lock"
        echo "  monitor   Start monitoring (foreground)"
        echo "  enable    Enable auto-start"
        echo "  disable   Disable auto-start"
        ;;
esac
EOF

chmod +x "$WRAPPER"

# Create initial vault
echo "🔐 Creating initial vault..."
python3 << 'PYTHON'
import asyncio
import os
from pathlib import Path

async def setup():
    from core.vault_manager import SecureVaultManager, VaultConfig

    config = VaultConfig()

    # Create sample credentials file
    sample_creds = Path.home() / "obsidian-vault" / "credentials.json"
    if not sample_creds.exists():
        sample_creds.parent.mkdir(mode=0o700, exist_ok=True)
        sample_creds.write_text('{}')
        os.chmod(sample_creds, 0o600)
        print("✅ Created credentials file")

    # Create encrypted vault placeholder
    encrypted = config.encrypted_vault_path
    if not encrypted.exists():
        encrypted.parent.mkdir(mode=0o700, exist_ok=True)
        print("ℹ️  Encrypted vault will be created on first unlock")

asyncio.run(setup())
PYTHON

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Add $HOME/.local/bin to your PATH"
echo "  2. Start Cloudflare Tunnel"
echo "  3. deadman-switch enable"
echo "  4. Scan QR code with mobile"
echo ""
echo "Commands:"
echo "  deadman-switch status    - Check status"
echo "  deadman-switch lock      - Manual lock"
echo "  deadman-switch enable    - Auto-start"
echo ""
echo "Security:"
echo "  • Vault location: ~/obsidian-vault"
echo "  • Encrypted vault: ~/.secure/vault.enc"
echo "  • Kill switch triggers after 60s without heartbeat"
