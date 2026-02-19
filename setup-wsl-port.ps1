# WSL Port Forwarding Setup für Zen-AI-Pentest
# Dieses Skript richtet die Port-Weiterleitung von Windows zu WSL ein

param(
    [int]$Port = 8000,
    [switch]$Remove
)

# WSL IP-Adresse ermitteln
$wslIp = (wsl hostname -I).Trim().Split(' ')[0]

if (-not $wslIp) {
    Write-Error "Konnte WSL IP-Adresse nicht ermitteln. Ist WSL installiert und läuft?"
    exit 1
}

Write-Host "WSL IP-Adresse: $wslIp" -ForegroundColor Cyan

if ($Remove) {
    # Port-Proxy Regel entfernen
    netsh interface portproxy delete v4tov4 listenport=$Port listenaddress=0.0.0.0 2>$null
    netsh interface portproxy delete v4tov4 listenport=$Port listenaddress=127.0.0.1 2>$null
    
    # Firewall-Regel entfernen
    netsh advfirewall firewall delete rule name="WSL Port $Port" 2>$null
    
    Write-Host "Port-Weiterleitung für Port $Port entfernt." -ForegroundColor Green
} else {
    # Bestehende Regeln löschen
    netsh interface portproxy delete v4tov4 listenport=$Port listenaddress=0.0.0.0 2>$null
    netsh interface portproxy delete v4tov4 listenport=$Port listenaddress=127.0.0.1 2>$null
    
    # Neue Port-Proxy Regel erstellen (von Windows localhost zu WSL IP)
    netsh interface portproxy add v4tov4 listenport=$Port listenaddress=127.0.0.1 connectport=$Port connectaddress=$wslIp
    netsh interface portproxy add v4tov4 listenport=$Port listenaddress=0.0.0.0 connectport=$Port connectaddress=$wslIp
    
    # Firewall-Regel erstellen
    $firewallRule = netsh advfirewall firewall show rule name="WSL Port $Port" 2>&1
    if ($firewallRule -match "Keine Regeln") {
        netsh advfirewall firewall add rule name="WSL Port $Port" dir=in action=allow protocol=tcp localport=$Port
    }
    
    Write-Host "Port-Weiterleitung eingerichtet:" -ForegroundColor Green
    Write-Host "  Windows: http://localhost:$Port" -ForegroundColor Yellow
    Write-Host "  WSL IP:  http://${wslIp}:$Port" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Aktive Port-Proxy Regeln:" -ForegroundColor Cyan
    netsh interface portproxy show all | Select-String $Port
}
