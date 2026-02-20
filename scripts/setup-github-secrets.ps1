# PowerShell Script für GitHub Secrets Setup
# Verwendet GitHub CLI (gh)

Write-Host "☁️  GitHub Secrets Setup für Cloudflare" -ForegroundColor Cyan
Write-Host "=" * 50

# Prüfe ob gh installiert ist
$ghPath = Get-Command gh -ErrorAction SilentlyContinue
if (-not $ghPath) {
    Write-Host "❌ GitHub CLI (gh) nicht gefunden!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Installiere es zuerst:"
    Write-Host "  winget install --id GitHub.cli" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "ODER manuelles Setup:"
    Write-Host "  1. Gehe zu: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/secrets/actions"
    Write-Host "  2. Füge hinzu:"
    Write-Host "     Name: CLOUDFLARE_API_TOKEN"
    Write-Host "     Value: [Dein Cloudflare Token]"
    Write-Host "  3. Füge hinzu:"
    Write-Host "     Name: CLOUDFLARE_ACCOUNT_ID"
    Write-Host "     Value: [Deine Account ID]"
    exit 1
}

# Prüfe gh Auth
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "🔐 Du musst dich zuerst bei GitHub CLI anmelden:" -ForegroundColor Yellow
    Write-Host "  gh auth login" -ForegroundColor Cyan
    exit 1
}

Write-Host "✅ GitHub CLI ist bereit!" -ForegroundColor Green
Write-Host ""

# Secrets abfragen
$cfToken = Read-Host "🔑 Cloudflare API Token" -AsSecureString
$cfAccount = Read-Host "🔑 Cloudflare Account ID" -AsSecureString

# Konvertiere SecureString zu PlainText (notwendig für gh)
$BSTRToken = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($cfToken)
$plainToken = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTRToken)

$BSTRAccount = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($cfAccount)
$plainAccount = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTRAccount)

Write-Host ""
Write-Host "📝 Setze Secrets in GitHub..." -ForegroundColor Cyan

# Setze CLOUDFLARE_API_TOKEN
$plainToken | gh secret set CLOUDFLARE_API_TOKEN --repo SHAdd0WTAka/Zen-Ai-Pentest
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ CLOUDFLARE_API_TOKEN gesetzt" -ForegroundColor Green
} else {
    Write-Host "❌ Fehler beim Setzen von CLOUDFLARE_API_TOKEN" -ForegroundColor Red
}

# Setze CLOUDFLARE_ACCOUNT_ID
$plainAccount | gh secret set CLOUDFLARE_ACCOUNT_ID --repo SHAdd0WTAka/Zen-Ai-Pentest
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ CLOUDFLARE_ACCOUNT_ID gesetzt" -ForegroundColor Green
} else {
    Write-Host "❌ Fehler beim Setzen von CLOUDFLARE_ACCOUNT_ID" -ForegroundColor Red
}

# Aufräumen
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTRToken)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTRAccount)
$plainToken = $null
$plainAccount = $null

Write-Host ""
Write-Host "🎉 Fertig!" -ForegroundColor Green
Write-Host ""
Write-Host "Überprüfe die Secrets hier:" -ForegroundColor Cyan
Write-Host "  https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/secrets/actions" -ForegroundColor Yellow
Write-Host ""
Write-Host "🚀 Nächster Schritt: Push auf main branch auslösen:" -ForegroundColor Cyan
Write-Host "  git push origin main" -ForegroundColor Yellow
