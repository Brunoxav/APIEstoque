# Publicar projeto2_estoque no GitHub (totalmente automatico com GITHUB_TOKEN ou -Url)
# Uso: .\publicar-github.ps1
#      .\publicar-github.ps1 -Url "https://github.com/SEU_USUARIO/estoque-api.git"
#      $env:GITHUB_TOKEN = "ghp_xxx"; .\publicar-github.ps1   # cria o repo na API e faz push

param([string]$Url)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$gitExe = "git"
if (Test-Path "C:\Program Files\Git\bin\git.exe") { $gitExe = "C:\Program Files\Git\bin\git.exe" }

function Run-Git { & $gitExe @args }

function Get-GitRemoteOrigin {
    $ErrorActionPreference = 'SilentlyContinue'
    $out = & $gitExe remote get-url origin 2>&1
    $ErrorActionPreference = 'Stop'
    if ($out -is [System.Management.Automation.ErrorRecord]) { return $null }
    $s = [string]$out
    if ($s -match 'error:') { return $null }
    return $s.Trim()
}

if (-not (Get-Command $gitExe -ErrorAction SilentlyContinue) -and -not (Test-Path $gitExe)) {
    Write-Host "[ERRO] Git nao encontrado. Instale em: https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}

$isRepo = Test-Path ".git"
if (-not $isRepo) {
    Write-Host "Inicializando repositorio Git..." -ForegroundColor Cyan
    Run-Git init
    Run-Git add .
    Run-Git commit -m "Projeto 2: Sistema de Controle de Estoque"
    Run-Git branch -M main
    Write-Host "Commit inicial criado." -ForegroundColor Green
} else {
    Run-Git add -A
    $status = Run-Git status --short
    if ($status) {
        Write-Host "Criando commit..." -ForegroundColor Cyan
        Run-Git commit -m "Atualizacao: Projeto 2 Controle de Estoque"
        Write-Host "Commit criado." -ForegroundColor Green
    }
}

# Se foi passada URL por parametro, usar
if ($Url) { $urlToUse = $Url.Trim() }

# Se tem GITHUB_TOKEN, criar repo na API e obter URL
if (-not $urlToUse -and $env:GITHUB_TOKEN) {
    Write-Host "Criando repositorio no GitHub via API..." -ForegroundColor Cyan
    $repoName = "estoque-api"
    $body = @{ name = $repoName; description = "Projeto 2 - Sistema de Controle de Estoque com FastAPI e SQLite"; private = $false } | ConvertTo-Json
    try {
        $resp = Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Method Post -Headers @{
            Authorization = "Bearer $env:GITHUB_TOKEN"
            Accept = "application/vnd.github.v3+json"
        } -Body $body -ContentType "application/json"
        $urlToUse = $resp.clone_url
        Write-Host "Repositorio criado: $($resp.html_url)" -ForegroundColor Green
    } catch {
        Write-Host "Erro ao criar repo: $_" -ForegroundColor Red
        exit 1
    }
}

$remote = Get-GitRemoteOrigin
if ($remote -and -not $urlToUse) {
    Write-Host "Fazendo push para origin/main..." -ForegroundColor Cyan
    Run-Git push -u origin main
    Write-Host "Push concluido." -ForegroundColor Green
    exit 0
}

if ($urlToUse) {
    if ($remote) { Run-Git remote remove origin }
    Run-Git remote add origin $urlToUse
    Write-Host "Enviando para GitHub..." -ForegroundColor Cyan
    Run-Git push -u origin main
    Write-Host "Projeto publicado no GitHub." -ForegroundColor Green
    exit 0
}

# Interativo: pedir URL
$remote = Get-GitRemoteOrigin
if ($remote) {
    Write-Host "Remote: $remote" -ForegroundColor Gray
    $r = Read-Host "Fazer push? (s/n)"
    if ($r -eq 's' -or $r -eq 'S') { Run-Git push -u origin main; Write-Host "Push concluido." -ForegroundColor Green }
    exit 0
}

Write-Host ""
Write-Host "Para publicar automaticamente:" -ForegroundColor Yellow
Write-Host "  1. Passe a URL: .\publicar-github.ps1 -Url 'https://github.com/SEU_USUARIO/estoque-api.git'" -ForegroundColor White
Write-Host "  2. Ou crie um token em https://github.com/settings/tokens e execute:" -ForegroundColor White
Write-Host "     `$env:GITHUB_TOKEN='ghp_xxx'; .\publicar-github.ps1" -ForegroundColor White
Write-Host ""
