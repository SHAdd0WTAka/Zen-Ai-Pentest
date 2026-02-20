#!/bin/bash
# Generate Repository Status Card for Zen-AI-Pentest
# Uses SVG (no Python dependencies required)

set -e

# Colors
BG_COLOR="#1e1e28"
HEADER_COLOR="#2d2d3c"
ACCENT_COLOR="#64c8ff"
TEXT_COLOR="#f0f0f0"
SECONDARY_COLOR="#b4b4b4"
SUCCESS_COLOR="#64ff64"
WARNING_COLOR="#ffc864"
BORDER_COLOR="#3c3c50"

# Get repository statistics
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

TOTAL_COMMITS=$(git rev-list --count HEAD 2>/dev/null || echo "0")
CONTRIBUTORS=$(git log --format='%an' 2>/dev/null | sort -u | wc -l || echo "0")
TOTAL_FILES=$(git ls-files 2>/dev/null | wc -l || echo "0")
BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
LAST_COMMIT=$(git log -1 --format='%cd' --date=short 2>/dev/null || echo "N/A")
RECENT_COMMITS=$(git log --since='7 days ago' --oneline 2>/dev/null | wc -l || echo "0")

# Calculate repository age
FIRST_COMMIT=$(git log --reverse --format='%cd' --date=short 2>/dev/null | head -1 || echo "")
if [ -n "$FIRST_COMMIT" ]; then
    FIRST_DATE=$(date -d "$FIRST_COMMIT" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$FIRST_COMMIT" +%s 2>/dev/null || echo "0")
    TODAY=$(date +%s)
    AGE_DAYS=$(( (TODAY - FIRST_DATE) / 86400 ))
    if [ $AGE_DAYS -lt 365 ]; then
        AGE_DISPLAY="${AGE_DAYS} days"
    else
        AGE_YEARS=$(( AGE_DAYS / 365 ))
        AGE_MONTHS=$(( (AGE_DAYS % 365) / 30 ))
        AGE_DISPLAY="${AGE_YEARS}y ${AGE_MONTHS}m"
    fi
else
    AGE_DISPLAY="N/A"
fi

# Count tools
TOOL_COUNT=$(find tools -name "*_integration.py" 2>/dev/null | wc -l || echo "0")

# Determine evolution phase
if [ "$TOTAL_COMMITS" -lt 50 ]; then
    EVOLUTION_PHASE="🌱 Phase 1: Foundation"
    PHASE_COLOR="#90EE90"
elif [ "$TOTAL_COMMITS" -lt 150 ]; then
    EVOLUTION_PHASE="🔧 Phase 2: Real Tools"
    PHASE_COLOR="#87CEEB"
elif [ "$TOTAL_COMMITS" -lt 300 ]; then
    EVOLUTION_PHASE="🤖 Phase 3: Multi-Agent"
    PHASE_COLOR="#DDA0DD"
elif [ "$TOTAL_COMMITS" -lt 500 ]; then
    EVOLUTION_PHASE="🛡️ Phase 4: Security Engine"
    PHASE_COLOR="#F0E68C"
elif [ "$TOTAL_COMMITS" -lt 700 ]; then
    EVOLUTION_PHASE="🏢 Phase 5: Enterprise"
    PHASE_COLOR="#FFA07A"
elif [ "$TOTAL_COMMITS" -lt 900 ]; then
    EVOLUTION_PHASE="🧠 Phase 6: AI Personas"
    PHASE_COLOR="#98FB98"
else
    EVOLUTION_PHASE="🚀 Phase 7: Mature (v2.3.9)"
    PHASE_COLOR="#64ff64"
fi

# Activity status
if [ "$RECENT_COMMITS" -ge 10 ]; then
    ACTIVITY_STATUS="🔥 Very Active"
    ACTIVITY_COLOR="#64ff64"
elif [ "$RECENT_COMMITS" -ge 5 ]; then
    ACTIVITY_STATUS="✅ Active"
    ACTIVITY_COLOR="#ffc864"
elif [ "$RECENT_COMMITS" -gt 0 ]; then
    ACTIVITY_STATUS="⚡ Maintained"
    ACTIVITY_COLOR="#ffff64"
else
    ACTIVITY_STATUS="⏸️ Dormant"
    ACTIVITY_COLOR="#b4b4b4"
fi

# Timestamp
TIMESTAMP=$(date -u "+%Y-%m-%d %H:%M UTC")

# Create output directory
mkdir -p docs/status

# Generate SVG
cat > docs/status/repo_status_card.svg << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1e1e28"/>
      <stop offset="100%" style="stop-color:#252535"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="800" height="600" fill="url(#bgGradient)" rx="10" ry="10"/>
  <rect x="10" y="10" width="780" height="580" fill="none" stroke="#3c3c50" stroke-width="2" rx="8" ry="8"/>

  <!-- Header -->
  <rect x="10" y="10" width="780" height="70" fill="#2d2d3c" stroke="#3c3c50" stroke-width="1" rx="8"/>
  <text x="400" y="45" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="#64c8ff" text-anchor="middle">Zen-AI-Pentest Repository Status</text>
  <text x="400" y="68" font-family="Arial, sans-serif" font-size="12" fill="#b4b4b4" text-anchor="middle">Last Updated: TIMESTAMP_PLACEHOLDER</text>

  <!-- Evolution Phase -->
  <text x="30" y="115" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="PHASE_COLOR_PLACEHOLDER">EVOLUTION_PHASE_PLACEHOLDER</text>
  <line x1="30" y1="130" x2="770" y2="130" stroke="#3c3c50" stroke-width="1"/>

  <!-- Statistics Section -->
  <text x="30" y="165" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#64c8ff">📊 Repository Statistics</text>

  <!-- Stats Grid -->
  <text x="50" y="200" font-family="Arial, sans-serif" font-size="14" fill="#b4b4b4">📝 Total Commits:</text>
  <text x="200" y="200" font-family="Arial, sans-serif" font-size="14" fill="#f0f0f0" font-weight="bold">COMMITS_PLACEHOLDER</text>

  <text x="420" y="200" font-family="Arial, sans-serif" font-size="14" fill="#b4b4b4">👥 Contributors:</text>
  <text x="570" y="200" font-family="Arial, sans-serif" font-size="14" fill="#f0f0f0" font-weight="bold">CONTRIBUTORS_PLACEHOLDER</text>

  <text x="50" y="230" font-family="Arial, sans-serif" font-size="14" fill="#b4b4b4">📁 Total Files:</text>
  <text x="200" y="230" font-family="Arial, sans-serif" font-size="14" fill="#f0f0f0" font-weight="bold">FILES_PLACEHOLDER</text>

  <text x="420" y="230" font-family="Arial, sans-serif" font-size="14" fill="#b4b4b4">🔧 Integrated Tools:</text>
  <text x="570" y="230" font-family="Arial, sans-serif" font-size="14" fill="#f0f0f0" font-weight="bold">TOOLS_PLACEHOLDER</text>

  <text x="50" y="260" font-family="Arial, sans-serif" font-size="14" fill="#b4b4b4">⏱️ Repository Age:</text>
  <text x="200" y="260" font-family="Arial, sans-serif" font-size="14" fill="#f0f0f0" font-weight="bold">AGE_PLACEHOLDER</text>

  <text x="420" y="260" font-family="Arial, sans-serif" font-size="14" fill="#b4b4b4">🌿 Branch:</text>
  <text x="570" y="260" font-family="Arial, sans-serif" font-size="14" fill="#f0f0f0" font-weight="bold">BRANCH_PLACEHOLDER</text>

  <text x="50" y="290" font-family="Arial, sans-serif" font-size="14" fill="#b4b4b4">📅 Last Commit:</text>
  <text x="200" y="290" font-family="Arial, sans-serif" font-size="14" fill="#f0f0f0" font-weight="bold">LAST_COMMIT_PLACEHOLDER</text>

  <!-- Recent Activity -->
  <line x1="30" y1="315" x2="770" y2="315" stroke="#3c3c50" stroke-width="1"/>
  <text x="30" y="345" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#64c8ff">📈 Recent Activity</text>
  <text x="50" y="375" font-family="Arial, sans-serif" font-size="14" fill="#b4b4b4">Commits in last 7 days:</text>
  <text x="230" y="375" font-family="Arial, sans-serif" font-size="14" fill="#f0f0f0" font-weight="bold">RECENT_COMMITS_PLACEHOLDER</text>
  <text x="50" y="400" font-family="Arial, sans-serif" font-size="14" fill="#b4b4b4">Status:</text>
  <text x="120" y="400" font-family="Arial, sans-serif" font-size="14" fill="ACTIVITY_COLOR_PLACEHOLDER" font-weight="bold">ACTIVITY_STATUS_PLACEHOLDER</text>

  <!-- Legal Notice -->
  <line x1="30" y1="430" x2="770" y2="430" stroke="#3c3c50" stroke-width="1"/>
  <text x="30" y="460" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#ff6464">⚖️ Legal Notice for AI Agents</text>
  <text x="50" y="485" font-family="Arial, sans-serif" font-size="12" fill="#b4b4b4">• Only scan systems you OWN or have EXPLICIT WRITTEN permission to test</text>
  <text x="50" y="505" font-family="Arial, sans-serif" font-size="12" fill="#b4b4b4">• Unauthorized scanning is ILLEGAL and can result in criminal prosecution</text>
  <text x="50" y="525" font-family="Arial, sans-serif" font-size="12" fill="#b4b4b4">• The USER is solely responsible for their actions, NOT the AI</text>
  <text x="50" y="545" font-family="Arial, sans-serif" font-size="12" fill="#b4b4b4">• This tool is for authorized security testing and educational purposes only</text>

  <!-- Footer -->
  <text x="400" y="580" font-family="Arial, sans-serif" font-size="11" fill="#808080" text-anchor="middle">🤖 Auto-generated | Updates on every push | Enable GitHub Actions for auto-updates</text>
</svg>
EOF

# Replace placeholders
sed -i "s/TIMESTAMP_PLACEHOLDER/${TIMESTAMP}/g" docs/status/repo_status_card.svg
sed -i "s/EVOLUTION_PHASE_PLACEHOLDER/${EVOLUTION_PHASE}/g" docs/status/repo_status_card.svg
sed -i "s/PHASE_COLOR_PLACEHOLDER/${PHASE_COLOR}/g" docs/status/repo_status_card.svg
sed -i "s/COMMITS_PLACEHOLDER/${TOTAL_COMMITS}/g" docs/status/repo_status_card.svg
sed -i "s/CONTRIBUTORS_PLACEHOLDER/${CONTRIBUTORS}/g" docs/status/repo_status_card.svg
sed -i "s/FILES_PLACEHOLDER/${TOTAL_FILES}/g" docs/status/repo_status_card.svg
sed -i "s/TOOLS_PLACEHOLDER/${TOOL_COUNT}/g" docs/status/repo_status_card.svg
sed -i "s/AGE_PLACEHOLDER/${AGE_DISPLAY}/g" docs/status/repo_status_card.svg
sed -i "s/BRANCH_PLACEHOLDER/${BRANCH}/g" docs/status/repo_status_card.svg
sed -i "s/LAST_COMMIT_PLACEHOLDER/${LAST_COMMIT}/g" docs/status/repo_status_card.svg
sed -i "s/RECENT_COMMITS_PLACEHOLDER/${RECENT_COMMITS}/g" docs/status/repo_status_card.svg
sed -i "s/ACTIVITY_STATUS_PLACEHOLDER/${ACTIVITY_STATUS}/g" docs/status/repo_status_card.svg
sed -i "s/ACTIVITY_COLOR_PLACEHOLDER/${ACTIVITY_COLOR}/g" docs/status/repo_status_card.svg

echo "✅ Status card generated: docs/status/repo_status_card.svg"
echo ""
echo "Statistics:"
echo "  - Evolution Phase: ${EVOLUTION_PHASE}"
echo "  - Total Commits: ${TOTAL_COMMITS}"
echo "  - Tools: ${TOOL_COUNT}"
echo "  - Recent Activity: ${ACTIVITY_STATUS} (${RECENT_COMMITS} commits)"
