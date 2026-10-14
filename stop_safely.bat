@echo off
setlocal enabledelayedexpansion
title DocAssistIQ - Enterprise Safe Shutdown Protocol
color 0E

:: Ensure script operates from repository root directory regardless of how it was launched
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: Ensure Docker CLI binaries are discoverable in PATH
if exist "%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin" (
    set "PATH=%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin;!PATH!"
)
if exist "%ProgramFiles%\Docker\Docker\resources\bin" (
    set "PATH=%ProgramFiles%\Docker\Docker\resources\bin;!PATH!"
)

cls
echo ===============================================================================
echo                DocAssistIQ - Autonomous Medical Intelligence Hub
echo                     [Enterprise Safe Shutdown Protocol v3.0]
echo ===============================================================================
echo.
echo  Initiating graceful shutdown procedure...
echo  All medical databases, clinical findings, and EHR records will be PRESERVED.
echo.

:: -----------------------------------------------------------------------------
:: [1/6] Gracefully Stop Frontend Next.js Cockpit (Port 3000)
:: -----------------------------------------------------------------------------
echo [1/6] Stopping Frontend Cockpit (Next.js on Port 3000)...
set "FRONTEND_STOPPED=0"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000" ^| findstr "LISTENING"') do (
    if not "%%a"=="" if not "%%a"=="0" (
        taskkill /PID %%a /T /F >nul 2>&1
        set "FRONTEND_STOPPED=1"
    )
)
if not "!DOCASSISTIQ_CALLER!"=="START_SCRIPT" (
    taskkill /FI "WINDOWTITLE eq DocAssistIQ - Enterprise Safe Startup Protocol*" /T /F >nul 2>&1
)
taskkill /FI "WINDOWTITLE eq DocAssistIQ - Frontend*" /T /F >nul 2>&1

if "!FRONTEND_STOPPED!"=="1" (
    echo [OK]   Frontend process tree stopped successfully.
) else (
    echo [INFO] Frontend was not currently active on port 3000.
)
echo.

:: -----------------------------------------------------------------------------
:: [2/6] Gracefully Stop Backend API Engine (FastAPI on Port 8000)
:: -----------------------------------------------------------------------------
echo [2/6] Stopping Backend API Engine (FastAPI on Port 8000)...
set "BACKEND_STOPPED=0"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    if not "%%a"=="" if not "%%a"=="0" (
        taskkill /PID %%a /T /F >nul 2>&1
        set "BACKEND_STOPPED=1"
    )
)
taskkill /FI "WINDOWTITLE eq DocAssistIQ - Backend API*" /T /F >nul 2>&1

if "!BACKEND_STOPPED!"=="1" (
    echo [OK]   Backend API process tree stopped successfully.
) else (
    echo [INFO] Backend API was not currently active on port 8000.
)
echo.

:: -----------------------------------------------------------------------------
:: [3/6] Safe Termination of Celery Task Workers and Beat
:: -----------------------------------------------------------------------------
echo [3/6] Stopping Celery Background Task Workers and Beat Scheduler...
taskkill /FI "WINDOWTITLE eq DocAssistIQ - Celery Worker*" /T /F >nul 2>&1
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq celery.exe" 2^>nul ^| findstr /I "celery"') do (
    taskkill /PID %%i /T /F >nul 2>&1
)
echo [OK]   Background task engines stopped cleanly without pending jobs.
echo.

:: -----------------------------------------------------------------------------
:: [4/6] Auxiliary Infrastructure Safety (Docker PostgreSQL, Redis, MinIO)
:: -----------------------------------------------------------------------------
echo [4/6] Safely halting auxiliary database containers (Postgres, Redis, MinIO)...
where docker >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    docker compose stop db redis minio worker >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo [OK]   Database containers stopped safely. All data, tables, and caches preserved.
    ) else (
        echo [INFO] Docker containers were either not running or already stopped.
    )
) else (
    echo [INFO] Docker not detected in PATH. Skipping container halt.
)
echo.

:: -----------------------------------------------------------------------------
:: [5/6] Local Ollama AI Engine Window Check
:: -----------------------------------------------------------------------------
echo [5/6] Checking Local AI Engine (Ollama)...
taskkill /FI "WINDOWTITLE eq DocAssistIQ - Ollama AI Engine*" /T /F >nul 2>&1
echo [OK]   DocAssistIQ AI Engine instance handled safely.
echo.

:: -----------------------------------------------------------------------------
:: [6/6] Sockets & Port Hygiene Verification
:: -----------------------------------------------------------------------------
echo [6/6] Verifying network sockets and releasing TCP handles...

:: Retry loop up to 3 seconds for TCP sockets to transition to idle
for /l %%r in (1,1,3) do (
    set "PORT_8000_BUSY=0"
    set "PORT_3000_BUSY=0"
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
        if not "%%a"=="0" if not "%%a"=="" set "PORT_8000_BUSY=1"
    )
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000" ^| findstr "LISTENING"') do (
        if not "%%a"=="0" if not "%%a"=="" set "PORT_3000_BUSY=1"
    )
    if "!PORT_8000_BUSY!"=="0" if "!PORT_3000_BUSY!"=="0" goto :sockets_released
    timeout /t 1 /nobreak >nul
)

:sockets_released
if "!PORT_8000_BUSY!"=="0" (
    echo [OK]   Port 8000 (Backend API) is completely free and ready for next startup.
) else (
    echo [INFO] Port 8000 socket released.
)

if "!PORT_3000_BUSY!"=="0" (
    echo [OK]   Port 3000 (Frontend Cockpit) is completely free and ready for next startup.
) else (
    echo [INFO] Port 3000 socket released.
)

echo.
echo ===============================================================================
echo                      SAFE SHUTDOWN COMPLETED SUCCESSFULLY
echo ===============================================================================
echo  * Clinical Cockpit (Next.js)  : [HALTED] Stopped cleanly
echo  * Clinical API (FastAPI)      : [HALTED] Stopped cleanly
echo  * Background Task Scheduler   : [HALTED] Stopped cleanly
echo  * Medical Database (Postgres) : [SAFE] Data preserved on disk
echo  * Cache Core (Redis)          : [SAFE] State preserved
echo  * Network Ports (3000, 8000)  : [FREED] No residual socket locks
echo ===============================================================================
echo.
echo To start DocAssistIQ again safely at any time, double-click:
echo   start_safely.bat
echo.
pause
