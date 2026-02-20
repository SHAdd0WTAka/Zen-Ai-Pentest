#
# Pentest Tools Installation Script for Windows
# Run as Administrator
#

param(
    [switch]$All,
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\install-tools.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -All    Install all tools (required + optional)"
    Write-Host "  -Help   Show this help message"
    exit 0
}

# Check if running as admin
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Please run as Administrator!"
    exit 1
}

Write-Host "===============================================" -ForegroundColor Blue
Write-Host "  Zen-AI-Pentest Tool Installer (Windows)" -ForegroundColor Blue
Write-Host "===============================================" -ForegroundColor Blue
Write-Host ""

# Helper functions
function Test-Command($Command) {
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Install-Chocolatey {
    if (-not (Test-Command choco)) {
        Write-Host "Installing Chocolatey..." -ForegroundColor Yellow
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    }
}

function Install-Nmap {
    Write-Host "Installing Nmap..." -ForegroundColor Yellow

    if (Test-Command nmap) {
        Write-Host "Nmap already installed: $(nmap -V 2>&1 | Select-Object -First 1)" -ForegroundColor Green
        return
    }

    choco install nmap -y
    Write-Host "Nmap installed successfully" -ForegroundColor Green
}

function Install-SQLMap {
    Write-Host "Installing SQLMap..." -ForegroundColor Yellow

    if (Test-Command sqlmap) {
        Write-Host "SQLMap already installed" -ForegroundColor Green
        return
    }

    $sqlmapPath = "C:\Tools\sqlmap"
    New-Item -ItemType Directory -Force -Path $sqlmapPath | Out-Null

    git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git $sqlmapPath

    # Add to PATH
    [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$sqlmapPath", "Machine")
    $env:Path += ";$sqlmapPath"

    Write-Host "SQLMap installed successfully" -ForegroundColor Green
}

function Install-Nuclei {
    Write-Host "Installing Nuclei..." -ForegroundColor Yellow

    if (Test-Command nuclei) {
        Write-Host "Nuclei already installed" -ForegroundColor Green
        return
    }

    # Download latest release
    $url = "https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_windows_amd64.zip"
    $output = "$env:TEMP\nuclei.zip"

    Invoke-WebRequest -Uri $url -OutFile $output
    Expand-Archive -Path $output -DestinationPath "C:\Tools\nuclei" -Force

    # Add to PATH
    [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Tools\nuclei", "Machine")

    # Update templates
    & "C:\Tools\nuclei\nuclei.exe" -update-templates

    Write-Host "Nuclei installed successfully" -ForegroundColor Green
}

function Install-GoBuster {
    Write-Host "Installing GoBuster..." -ForegroundColor Yellow

    if (Test-Command gobuster) {
        Write-Host "GoBuster already installed" -ForegroundColor Green
        return
    }

    choco install gobuster -y
    Write-Host "GoBuster installed successfully" -ForegroundColor Green
}

function Install-Go {
    if (-not (Test-Command go)) {
        Write-Host "Installing Go..." -ForegroundColor Yellow
        choco install golang -y
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        Write-Host "Go installed: $(go version)" -ForegroundColor Green
    }
}

# Main installation
Write-Host "Installing required tools..." -ForegroundColor Yellow

Install-Chocolatey
Install-Nmap
Install-SQLMap

if ($All) {
    Write-Host "Installing optional tools..." -ForegroundColor Yellow

    Install-Go
    Install-Nuclei
    Install-GoBuster
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""

# Check installation
Write-Host "Installed tools:" -ForegroundColor Blue
if (Test-Command nmap) {
    Write-Host "  ✓ Nmap: $(nmap -V 2>&1 | Select-Object -First 1)"
}
if (Test-Command sqlmap) {
    Write-Host "  ✓ SQLMap: Installed"
}
if ($All -and (Test-Command nuclei)) {
    Write-Host "  ✓ Nuclei: Installed"
}

Write-Host ""
Write-Host "Please restart your terminal to use the installed tools." -ForegroundColor Yellow
