#!/bin/bash
# Auto-deployment script for Zen-Alpha Frontend

LOG_FILE="/tmp/auto-deploy.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "═══════════════════════════════════════════════════════════"
echo "  ZEN-ALPHA AUTO-DEPLOY - $(date)"
echo "═══════════════════════════════════════════════════════════"
echo ""

cd /home/atakan/zen-ai-pentest/web_ui/frontend

# Step 1: Fix permissions
echo "🔧 Step 1: Fixing permissions..."
sudo chown -R $USER:$USER dist/ 2>/dev/null || true
sudo chmod -R u+w dist/ 2>/dev/null || true

# Step 2: Clean build directory
echo "🧹 Step 2: Cleaning old build..."
rm -rf dist
mkdir -p dist

# Step 3: Build
echo "🔨 Step 3: Building..."
export VITE_API_URL="https://unleniently-hauriant-laurel.ngrok-free.dev"
npm run build

if [ ! -f "dist/index.html" ]; then
  echo "❌ Build failed!"
  exit 1
fi

echo "✅ Build complete!"

# Step 4: Deploy
echo ""
echo "🚀 Step 4: Deploying to Cloudflare..."
npx wrangler pages deploy dist --project-name=zen-alpha-pentest --branch=main --commit-dirty=true

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅ DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🌐 Your Frontend: https://zen-alpha-pentest.pages.dev"
echo "🔗 API Endpoint:  https://unleniently-hauriant-laurel.ngrok-free.dev"
echo ""
echo "📋 Log saved to: $LOG_FILE"
