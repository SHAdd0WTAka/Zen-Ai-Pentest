#!/bin/bash
case "$1" in
  start)
    echo "🚀 Starting Zen-Alpha..."
    sudo systemctl start zen-alpha-backend
    sudo systemctl start zen-alpha-tunnel
    echo "✅ Services started"
    echo "🌐 API: https://unleniently-hauriant-laurel.ngrok-free.dev"
    ;;
  stop)
    echo "🛑 Stopping Zen-Alpha..."
    sudo systemctl stop zen-alpha-tunnel
    sudo systemctl stop zen-alpha-backend
    echo "✅ Services stopped"
    ;;
  restart)
    echo "🔄 Restarting Zen-Alpha..."
    sudo systemctl restart zen-alpha-backend
    sudo systemctl restart zen-alpha-tunnel
    echo "✅ Services restarted"
    ;;
  status)
    echo "📊 Zen-Alpha Status:"
    echo ""
    echo "Backend: $(sudo systemctl is-active zen-alpha-backend 2>/dev/null)"
    echo "Tunnel:  $(sudo systemctl is-active zen-alpha-tunnel 2>/dev/null)"
    echo ""
    echo "URLs:"
    echo "  API:   https://unleniently-hauriant-laurel.ngrok-free.dev"
    echo "  Web:   https://zen-alpha-pentest.pages.dev"
    ;;
  logs)
    sudo journalctl -u zen-alpha-backend -u zen-alpha-tunnel -f
    ;;
  deploy)
    echo "🚀 Deploying Zen-Alpha Frontend..."
    cd /home/atakan/zen-ai-pentest/web_ui/frontend
    export VITE_API_URL="https://unleniently-hauriant-laurel.ngrok-free.dev"
    rm -rf dist 2>/dev/null
    npm run build 2>&1 | tail -5
    npx wrangler pages deploy dist --project-name=zen-alpha-pentest --branch=main --commit-dirty=true 2>&1 | tail -5
    echo "✅ Deployment complete!"
    echo "🔗 https://zen-alpha-pentest.pages.dev"
    ;;
  *)
    echo "Usage: zen-alpha {start|stop|restart|status|logs|deploy}"
    ;;
esac
