#!/bin/bash
# Run from project root: bash diagnose_and_fix.sh
set -e
PROJ="/home/atakan/Schreibtisch/Zen-Ai-Pentest"
cd "$PROJ"

echo "════════════════════════════════════════"
echo "Step 1: Check which real modules import"
echo "════════════════════════════════════════"
for mod in \
  "core.cache" \
  "core.orchestrator" \
  "core.tool_executor" \
  "autonomous.agent_loop" \
  "autonomous.memory" \
  "autonomous.exploit_validator" \
  "risk_engine.false_positive_engine" \
  "agents.agent_base" \
  "modules.cve_database" \
  "tools.zap_integration" \
  "tools.trufflehog_integration" \
  "tools.tool_registry"
do
  python3 -c "import $mod; print('OK: $mod')" 2>&1 | head -2
done

echo ""
echo "════════════════════════════════════════"
echo "Step 2: Copy fixed conftest + coveragerc"
echo "════════════════════════════════════════"
# BACK UP originals
cp conftest.py conftest.py.bak2 2>/dev/null || true
cp .coveragerc .coveragerc.bak 2>/dev/null || true

# Copy new versions (assumes you downloaded them here)
cp ~/Downloads/conftest.py . 2>/dev/null || echo "Copy conftest.py manually"
cp ~/Downloads/.coveragerc . 2>/dev/null || echo "Copy .coveragerc manually"

echo ""
echo "════════════════════════════════════════"
echo "Step 3: Quick import health check"
echo "════════════════════════════════════════"
pytest --collect-only -q --log-cli-level=ERROR 2>&1 | tail -5

echo ""
echo "════════════════════════════════════════"
echo "Step 4: Run coverage on SCOPED modules only"
echo "════════════════════════════════════════"
pytest \
  --ignore=tests/unit/test_modules.py \
  --ignore=tests/e2e \
  --ignore=tests/massive \
  --cov=core \
  --cov=autonomous \
  --cov=risk_engine \
  --cov=agents \
  --cov=modules \
  --cov=tools \
  --cov-report=term-missing \
  --cov-report=html \
  -q --tb=no --log-cli-level=ERROR \
  2>&1 | grep -E "(PASSED|FAILED|ERROR|coverage|TOTAL|%)" | tail -30

echo ""
echo "Open htmlcov/index.html to see per-file breakdown"
