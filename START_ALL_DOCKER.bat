@echo off
setlocal enabledelayedexpansion
title DocAssistIQ - Portable Docker Launcher
color 0A

echo ===============================================================================
echo                DocAssistIQ - Autonomous Medical Intelligence Hub
echo                     [Portable 1-Click Docker Startup]
echo ===============================================================================
echo.

:: 1. Check if Docker is running
echo [1/4] Checking Docker Desktop status...
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo [ERROR] Docker is not running or not installed!
    echo Please make sure Docker Desktop is installed and running on this machine.
    echo Once Docker Desktop is running, run this script again.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker daemon is running and ready.
echo.

:: 2. Check and initialize environment file
echo [2/4] Verifying configuration (.env)...
if not exist .env (
    echo [INFO] .env not found. Initializing from .env.example...
    copy .env.example .env >nul
    echo [OK] .env created successfully.
) else (
    echo [OK] Existing .env verified.
)
echo.

:: 3. Check bundled AI Models
echo [3/4] Verifying bundled AI Models (Ollama)...
if exist models\ollama\models (
    echo [OK] Local models directory detected at models\ollama\models.
) else (
    echo [NOTICE] models\ollama\models directory is empty or missing.
    echo If models were exported, ensure they are placed inside models\ollama\models.
    echo Any missing models can also be pulled automatically via Ollama.
)
echo.

:: 4. Start all Docker containers
echo [4/4] Starting all DocAssistIQ services via Docker Compose...
echo [INFO] Orchestrating: PostgreSQL (pgvector), Redis, MinIO, Ollama, Backend, Celery, Frontend...
docker compose up -d --remove-orphans

if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo [ERROR] Failed to start Docker services.
    echo Please check the error output above.
    pause
    exit /b 1
)

echo.
echo ===============================================================================
echo                      ALL SERVICES STARTED SUCCESSFULLY!
echo ===============================================================================
echo.
echo  * Frontend Portal:        http://localhost:3000
echo  * Backend REST API:       http://localhost:8000
echo  * Swagger API Docs:       http://localhost:8000/docs
echo  * Ollama LLM Service:     http://localhost:11434
echo  * MinIO Storage Console:  http://localhost:9011 (admin: minioadmin / minioadmin)
echo.
echo Opening DocAssistIQ in your web browser...
start http://localhost:3000

echo.
echo ===============================================================================
echo To stop all services gracefully, double-click STOP_ALL_DOCKER.bat.
echo Keep this window or close it at any time.
echo ===============================================================================
pause
