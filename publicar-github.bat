@echo off
chcp 65001 >nul
cd /d "%~dp0"

where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Git nao encontrado. Instale em: https://git-scm.com/download/win
    pause
    exit /b 1
)

if not exist ".git" (
    echo Inicializando repositorio Git...
    git init
    git add .
    git commit -m "Projeto 2: Sistema de Controle de Estoque"
    git branch -M main
    echo Commit inicial criado.
) else (
    git add .
    git status --short | findstr /r "." >nul 2>&1
    if %errorlevel% equ 0 (
        git commit -m "Atualizacao: Projeto 2 Controle de Estoque"
        echo Commit criado.
    ) else (
        echo Nenhuma alteracao pendente.
    )
)

git remote get-url origin >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    git push -u origin main
    echo Push concluido.
    pause
    exit /b 0
)

echo.
echo Nenhum remote configurado.
echo 1. Crie um repo em https://github.com/new
echo 2. Nao marque "Initialize with README"
echo 3. Copie a URL e execute:
echo.
echo   git remote add origin https://github.com/SEU_USUARIO/SEU_REPO.git
echo   git push -u origin main
echo.
pause
