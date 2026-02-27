@echo off
chcp 65001 >nul
title API Controle de Estoque
cd /d "%~dp0"

echo.
echo ============================================
echo   API de Controle de Estoque
echo ============================================
echo.

REM Tenta python, depois py
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PY=python
    goto :install
)
where py >nul 2>&1
if %errorlevel% equ 0 (
    set PY=py
    goto :install
)

echo [ERRO] Python nao encontrado.
echo.
echo Instale o Python em: https://www.python.org/downloads/
echo Marque a opcao "Add Python to PATH" na instalacao.
echo Feche e abra o terminal depois de instalar.
echo.
pause
exit /b 1

:install
echo [1/2] Instalando dependencias...
%PY% -m pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo Falha ao instalar. Tente: %PY% -m pip install -r requirements.txt
    pause
    exit /b 1
)
echo OK.
echo.

:run
echo [2/2] Iniciando servidor...
echo.
echo   Interface: http://127.0.0.1:8000/static/index.html
echo   Documentacao: http://127.0.0.1:8000/docs
echo.
echo Pressione Ctrl+C para parar.
echo ============================================
echo.
%PY% -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

pause

