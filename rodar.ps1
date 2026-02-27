# API Controle de Estoque - Iniciar automaticamente
$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  API de Controle de Estoque" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$py = $null
if (Get-Command python -ErrorAction SilentlyContinue) { $py = "python" }
elseif (Get-Command py -ErrorAction SilentlyContinue) { $py = "py" }

if (-not $py) {
    Write-Host "[ERRO] Python nao encontrado." -ForegroundColor Red
    Write-Host ""
    Write-Host "Instale em: https://www.python.org/downloads/"
    Write-Host 'Marque "Add Python to PATH" na instalacao.'
    Write-Host ""
    Read-Host "Pressione Enter para sair"
    exit 1
}

Write-Host "[1/2] Instalando dependencias..." -ForegroundColor Yellow
& $py -m pip install -r requirements.txt -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "Falha ao instalar." -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}
Write-Host "OK." -ForegroundColor Green
Write-Host ""

Write-Host "[2/2] Iniciando servidor..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Interface:  http://127.0.0.1:8000/static/index.html" -ForegroundColor White
Write-Host "  Documentacao: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Pressione Ctrl+C para parar." -ForegroundColor Gray
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

& $py -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

