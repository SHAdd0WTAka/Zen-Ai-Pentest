# Install all dependencies for Zen AI Pentest (PowerShell)
# Run this script on Windows: .\install-all-dependencies.ps1

$ErrorActionPreference = "Stop"

Write-Host "🚀 Installing all dependencies for Zen AI Pentest..." -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion found" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed" -ForegroundColor Red
    Write-Host "Please install Python 3.9+ from https://python.org"
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js $nodeVersion found" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Node.js is not installed" -ForegroundColor Yellow
    Write-Host "Some features (Postman tests) will not be available"
    Write-Host "Install from: https://nodejs.org"
}

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "`n📦 Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`n🔄 Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "`n⬆️  Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# Install main requirements
Write-Host "`n📥 Installing main Python dependencies..." -ForegroundColor Cyan
python -m pip install -r requirements.txt
Write-Host "✓ Main dependencies installed" -ForegroundColor Green

# Install dev requirements
Write-Host "`n🛠️  Installing development dependencies..." -ForegroundColor Cyan
python -m pip install -r requirements-dev.txt
Write-Host "✓ Development dependencies installed" -ForegroundColor Green

# Install Zen Shield requirements
Write-Host "`n🛡️  Installing Zen Shield dependencies..." -ForegroundColor Cyan
python -m pip install -r zen_shield\requirements.txt
Write-Host "✓ Zen Shield dependencies installed" -ForegroundColor Green

# Install optional dependencies
Write-Host "`n✨ Installing optional dependencies..." -ForegroundColor Cyan
python -m pip install keyring cryptography python-dotenv -ErrorAction SilentlyContinue
Write-Host "✓ Optional dependencies installed" -ForegroundColor Green

# Node.js dependencies
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "`n📮 Installing Postman/Newman dependencies..." -ForegroundColor Cyan
    Set-Location postman
    npm install
    Set-Location ..
    Write-Host "✓ Postman dependencies installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Skipping Postman dependencies (npm not found)" -ForegroundColor Yellow
}

# Create directories
Write-Host "`n📁 Creating necessary directories..." -ForegroundColor Cyan
$directories = @("logs", "evidence", "data\sql_injection", "templates\reports", "shared\scans", "shared\reports")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "✓ Directories created" -ForegroundColor Green

# Summary
Write-Host "`n======================================================" -ForegroundColor Green
Write-Host "✅ All dependencies installed successfully!" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Virtual environment is already activated"
Write-Host "   2. Run the application:"
Write-Host "      python -m api.main" -ForegroundColor Yellow
Write-Host ""
Write-Host "   3. Or run tests:"
Write-Host "      pytest tests\" -ForegroundColor Yellow
Write-Host ""
Write-Host "📚 Documentation:"
Write-Host "   - API docs: http://localhost:8000/docs (after starting)"
Write-Host "   - README.md for more information"
