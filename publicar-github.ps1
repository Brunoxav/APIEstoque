# Publicar projeto2_estoque no GitHub
# Execute na pasta projeto2_estoque (ou a partir dela)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[ERRO] Git nao encontrado. Instale em: https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}

$isRepo = Test-Path ".git"

if (-not $isRepo) {
    Write-Host "Inicializando repositorio Git..." -ForegroundColor Cyan
    git init
    git add .
    git commit -m "Projeto 2: Sistema de Controle de Estoque"
    git branch -M main
    Write-Host "Commit inicial criado." -ForegroundColor Green
} else {
    $status = git status --short
    if ($status) {
        Write-Host "Adicionando alteracoes e criando commit..." -ForegroundColor Cyan
        git add .
        git commit -m "Atualizacao: Projeto 2 Controle de Estoque"
        Write-Host "Commit criado." -ForegroundColor Green
    } else {
        Write-Host "Nenhuma alteracao pendente. Repositorio em dia." -ForegroundColor Gray
    }
}

$remote = git remote get-url origin 2>$null
if ($remote) {
    Write-Host ""
    Write-Host "Remote atual: $remote" -ForegroundColor Gray
    $push = Read-Host "Fazer push para origin/main? (s/n)"
    if ($push -eq 's' -or $push -eq 'S') {
        git push -u origin main
        Write-Host "Push concluido." -ForegroundColor Green
    }
    exit 0
}

Write-Host ""
Write-Host "Nenhum remote 'origin' configurado." -ForegroundColor Yellow
Write-Host "1. Crie um repositorio novo no GitHub (https://github.com/new)" -ForegroundColor White
Write-Host "2. Nao marque 'Initialize with README' (voce ja tem os arquivos)" -ForegroundColor White
Write-Host "3. Cole a URL do repositorio abaixo (ex: https://github.com/seu-usuario/estoque-api.git)" -ForegroundColor White
Write-Host ""
$url = Read-Host "URL do repositorio no GitHub"

if ([string]::IsNullOrWhiteSpace($url)) {
    Write-Host "URL vazia. Configure depois com:" -ForegroundColor Yellow
    Write-Host "  git remote add origin https://github.com/SEU_USUARIO/SEU_REPO.git" -ForegroundColor Gray
    Write-Host "  git push -u origin main" -ForegroundColor Gray
    exit 0
}

git remote add origin $url.Trim()
Write-Host "Remote 'origin' adicionado. Enviando para GitHub..." -ForegroundColor Cyan
git push -u origin main
Write-Host "Projeto publicado no GitHub." -ForegroundColor Green
