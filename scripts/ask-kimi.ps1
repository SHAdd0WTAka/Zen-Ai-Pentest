# Kimi CLI mit Personas/Skills (PowerShell Version)
param(
    [Parameter(Position=0)]
    [string]$Mode = "recon",

    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$PromptArgs
)

$PersonaDir = if ($env:KIMI_PERSONA_DIR) { $env:KIMI_PERSONA_DIR } else { "$env:USERPROFILE\.config\kimi\personas" }
$PersonaFile = Join-Path $PersonaDir "$Mode.md"

# Lade System Prompt
if (Test-Path $PersonaFile) {
    $SystemPrompt = Get-Content $PersonaFile -Raw
    Write-Host "[Mode: $Mode aktiviert]" -ForegroundColor Cyan
} else {
    Write-Host "[Warnung: Persona $Mode nicht gefunden, nutze Standard]" -ForegroundColor Yellow
    $SystemPrompt = "Du bist ein hilfreicher Assistent."
}

# Kombiniere System Prompt mit User Input
$UserPrompt = $PromptArgs -join " "
$FullPrompt = @"
$SystemPrompt

---
User Anfrage:
$UserPrompt
"@

# An kimi-cli senden
if (Get-Command kimi -ErrorAction SilentlyContinue) {
    $FullPrompt | kimi ask -
} else {
    Write-Error "Fehler: kimi-cli nicht gefunden. Bitte installieren: pip install kimi-cli"
    exit 1
}
