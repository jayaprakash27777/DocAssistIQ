@echo off
setlocal enabledelayedexpansion
title DocAssistIQ - Native Windows Launcher
color 0B

echo ===============================================================================
echo                DocAssistIQ - Autonomous Medical Intelligence Hub
echo                     [Portable Native Windows Startup]
echo ===============================================================================
echo.

set SCRIPT_DIR=%~dp0
set OLLAMA_MODELS=%SCRIPT_DIR%models\ollama\models
set OLLAMA_BASE_URL=http://localhost:11434

:: 1. Configuration check
echo [1/5] Verifying configuration (.env)...
if not exist .env (
    echo [INFO] Initializing .env from .env.example...
    copy .env.example .env >nul
)
echo [OK] Configuration verified.
echo.

:: 2. Ensure supporting databases (PostgreSQL, Redis, MinIO)
echo [2/5] Starting supporting databases (Postgres, Redis, MinIO)...
docker compose up -d db redis minio
echo [OK] Storage and Database backends active.
echo.

:: 3. Check and launch Ollama using portable models directory
echo [3/5] Checking Ollama AI Model Engine...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Starting Ollama server with portable models path (%OLLAMA_MODELS%)...
    start "DocAssistIQ - Ollama Engine" cmd /c "set OLLAMA_MODELS=%OLLAMA_MODELS% & ollama serve"
    timeout /t 3 /nobreak >nul
) else (
    echo [OK] Ollama is already running.
)
echo.

:: 4. Backend Environment check & start
echo [4/5] Preparing Backend (FastAPI)...
cd backend
if not exist .venv (
    echo [INFO] Python virtual environment (.venv) not found.
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate
    echo [INFO] Installing Python dependencies...
    pip install -r requirements.txt --quiet
) else (
    call .venv\Scripts\activate
)

start "DocAssistIQ - Backend API" cmd /c "set OLLAMA_BASE_URL=http://localhost:11434 & call .venv\Scripts\activate & uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
start "DocAssistIQ - Celery Worker" cmd /c "set OLLAMA_BASE_URL=http://localhost:11434 & call .venv\Scripts\activate & celery -A app.celery_app worker -l info -B"
cd ..
echo [OK] Backend and Celery launched in background terminals.
echo.

:: 5. Frontend Environment check & launch
echo [5/5] Launching Frontend (Next.js)...
cd frontend
if not exist node_modules (
    echo [INFO] Installing frontend dependencies...
    call npm install --quiet
)

echo.
echo ===============================================================================
echo                      OPENING APPLICATION IN BROWSER
echo ===============================================================================
echo  * Frontend: http://localhost:3000
echo  * Backend:  http://localhost:8000/docs
echo ===============================================================================
start http://localhost:3000
call npm run dev
pause
