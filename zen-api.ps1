# Zen-AI-Pentest API Client fuer Windows
# Dieses Skript bietet einfachen Zugriff auf die API ueber WSL/Docker

param(
    [string]$Endpoint = "health",
    [switch]$Docs,
    [switch]$Open,
    [switch]$Status,
    [switch]$Logs,
    [string]$Service = "api",
    [switch]$Help
)

$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host @"
Zen-AI-Pentest API Client
========================

Verwendung:
  .\zen-api.ps1 [Optionen]

Optionen:
  -Endpoint <path>    API Endpunkt aufrufen (default: health)
  -Docs               API Dokumentation anzeigen
  -Open               Dokumentation im Browser oeffnen
  -Status             Container-Status anzeigen
  -Logs               Logs eines Services anzeigen (mit -Service)
  -Service <name>     Service fuer Logs (api, db, redis, nginx)
  -Help               Diese Hilfe anzeigen

Beispiele:
  .\zen-api.ps1                    # Health Check
  .\zen-api.ps1 -Endpoint scans    # Scans-Endpunkt aufrufen
  .\zen-api.ps1 -Docs              # API Docs anzeigen
  .\zen-api.ps1 -Docs -Open        # API Docs im Browser oeffnen
  .\zen-api.ps1 -Status            # Container-Status
  .\zen-api.ps1 -Logs -Service api # API Logs anzeigen
"@ -ForegroundColor Cyan
}

function Get-ContainerStatus {
    Write-Host "`nContainer Status:" -ForegroundColor Green
    Write-Host "==================" -ForegroundColor Green

    $containers = @("zen-pentest-api", "zen-pentest-db", "zen-pentest-redis", "zen-pentest-nginx", "zen-pentest-agent")

    foreach ($container in $containers) {
        $status = wsl docker inspect -f '{{.State.Status}}' $container 2>$null
        $health = wsl docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' $container 2>$null

        if ($status) {
            $color = if ($status -eq "running") { "Green" } else { "Red" }
            $healthColor = if ($health -eq "healthy") { "Green" }
                          elseif ($health -eq "none") { "Gray" }
                          else { "Yellow" }
            $healthStr = if ($health -and $health -ne "none") { " (Health: $health)" } else { "" }
            Write-Host "  $container`: " -NoNewline
            Write-Host $status -ForegroundColor $color -NoNewline
            if ($healthStr) {
                Write-Host $healthStr -ForegroundColor $healthColor
            } else {
                Write-Host ""
            }
        } else {
            Write-Host "  $container`: " -NoNewline
            Write-Host "not found" -ForegroundColor Red
        }
    }
    Write-Host ""
}

function Show-Logs {
    param([string]$ServiceName)

    $containerMap = @{
        "api" = "zen-pentest-api"
        "db" = "zen-pentest-db"
        "redis" = "zen-pentest-redis"
        "nginx" = "zen-pentest-nginx"
        "agent" = "zen-pentest-agent"
    }

    $containerName = $containerMap[$ServiceName]
    if (-not $containerName) {
        Write-Error "Unbekannter Service: $ServiceName. Verfuegbar: api, db, redis, nginx, agent"
        return
    }

    Write-Host "Logs fuer $containerName (letzte 50 Zeilen, Ctrl+C zum Beenden)..." -ForegroundColor Yellow
    wsl docker logs --tail=50 -f $containerName
}

function Invoke-ApiRequest {
    param([string]$Path)

    # Versuche ueber Nginx (Port 8080) - funktioniert mit Invoke-WebRequest
    $url = "http://localhost:8080/api/$Path"
    Write-Host "Rufe API auf: $url" -ForegroundColor Cyan

    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
        Write-Host "HTTP $($response.StatusCode)" -ForegroundColor Green

        try {
            # Versuche JSON zu formatieren
            $json = $response.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
            $json | ConvertTo-Json -Depth 10
        } catch {
            Write-Host $response.Content
        }
    } catch {
        Write-Error "Fehler beim Aufruf: $_"
        Write-Host "`nVersuche alternativen Zugriff ueber WSL..." -ForegroundColor Yellow

        # Fallback zu WSL
        $result = wsl curl -s "http://localhost:8000/$Path" 2>&1
        if ($result) {
            Write-Host $result
        } else {
            Write-Error "API nicht erreichbar. Pruefe ob Container laufen: wsl docker-compose ps"
        }
    }
}

function Open-Docs {
    param([switch]$InBrowser)

    # Pruefe ob Nginx laeuft
    $nginxStatus = wsl docker inspect -f '{{.State.Status}}' zen-pentest-nginx 2>$null

    if ($nginxStatus -eq "running") {
        Write-Host "Zen-AI-Pentest ist verfuegbar unter:" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Frontend:       http://localhost:8080/" -ForegroundColor Cyan
        Write-Host "  API Docs:       http://localhost:8080/docs" -ForegroundColor Yellow
        Write-Host "  API (direct):   http://localhost:8080/api/" -ForegroundColor Gray
        Write-Host "  Health Check:   http://localhost:8080/health" -ForegroundColor Gray
        Write-Host ""

        if ($InBrowser) {
            Start-Process "http://localhost:8080/"
        }
    } else {
        Write-Warning "Nginx laeuft nicht. Starte mit: wsl docker-compose up -d nginx"
        Write-Host "`nAlternative Zugriffsmethoden:" -ForegroundColor Cyan
        Write-Host "  1. WSL Terminal: wsl curl http://localhost:8000/docs" -ForegroundColor White
        Write-Host "  2. Container IP: wsl curl http://172.18.0.2:8000/docs" -ForegroundColor White
    }
}

# Hauptlogik
if ($Help) {
    Show-Help
    exit 0
}

if ($Status) {
    Get-ContainerStatus
    exit 0
}

if ($Logs) {
    Show-Logs -ServiceName $Service
    exit 0
}

if ($Docs) {
    Open-Docs -InBrowser:$Open
    exit 0
}

# Standard: API-Endpunkt aufrufen
Invoke-ApiRequest -Path $Endpoint
