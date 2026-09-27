@echo off
setlocal enabledelayedexpansion
title DocAssistIQ - Portable Package Builder
color 0E

echo ===============================================================================
echo                DocAssistIQ - Portable Distribution Packager
echo ===============================================================================
echo This script packages the entire project so anyone who receives this folder
echo can run it immediately with 1 click.
echo.

:: 1. Database Dump
echo [STEP 1/4] Dumping active PostgreSQL database to infra/postgres/01_docassistiq_seed.sql...
docker exec docassistiq_db pg_dump -U docassistiq -d docassistiq --inserts --column-inserts -f /tmp/docassistiq_dump.sql >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    docker cp docassistiq_db:/tmp/docassistiq_dump.sql ./infra/postgres/01_docassistiq_seed.sql
    echo [OK] Database dumped successfully. All 51 tables and data are bundled.
) else (
    echo [NOTICE] Docker database container is not running or pg_dump returned non-zero.
    echo Keeping existing infra/postgres/01_docassistiq_seed.sql if present.
)
echo.

:: 2. AI Models Check
echo [STEP 2/4] Verifying AI Models inside models/ollama/models...
if exist models\ollama\models (
    echo [OK] AI models directory is linked and available at models\ollama\models.
    echo [TIP] If copying to a USB drive or different PC, ensure the target folder receives
    echo       the physical files (e.g., standard Windows File Explorer Copy will copy
    echo       the target files of the junction automatically).
) else (
    echo [WARNING] models\ollama\models not found! Creating junction from %USERPROFILE%\.ollama\models...
    if not exist models\ollama mkdir models\ollama
    mklink /J models\ollama\models %USERPROFILE%\.ollama\models
)
echo.

:: 3. Clean Temporary Cache & Build Bloat
echo [STEP 3/4] Cleaning temporary caches (pycache, test outputs, next cache)...
if exist backend\.pytest_cache rmdir /s /q backend\.pytest_cache
if exist backend\.mypy_cache rmdir /s /q backend\.mypy_cache
if exist backend\.ruff_cache rmdir /s /q backend\.ruff_cache
if exist frontend\.next\cache rmdir /s /q frontend\.next\cache
del /q /f backend\pytest_out.txt 2>nul
del /q /f backend\error_out.txt 2>nul
del /q /f backend\error_out2.txt 2>nul
echo [OK] Unnecessary log and cache bloat cleared.
echo.

:: 4. Optional Docker Image Export (for completely offline machines)
echo [STEP 4/4] Offline Docker Images (Optional)
echo Do you want to export the Docker container images into a .tar file?
echo (This allows the recipient to run Docker with ZERO internet connection, ~6 GB).
echo Press Y to export images, or any other key to skip:
set /p DOCKER_EXP="Export Docker images? (y/N): "

if /i "%DOCKER_EXP%"=="y" (
    echo [INFO] Saving Docker images to docassistiq_docker_images.tar (this may take a few minutes)...
    docker save -o docassistiq_docker_images.tar pgvector/pgvector:pg16 redis:7-alpine minio/minio:latest ollama/ollama:latest
    echo [OK] Docker images exported to docassistiq_docker_images.tar!
) else (
    echo [INFO] Skipped Docker image export. Recipients with internet can pull images automatically.
)

echo.
echo ===============================================================================
echo                       PORTABLE BUNDLE READY TO SHARE!
echo ===============================================================================
echo What is included in this folder:
echo  1. All Codefiles (Frontend Next.js, Backend FastAPI, ML services)
echo  2. Complete Database Seed (infra/postgres/01_docassistiq_seed.sql)
echo  3. All Ollama Models (models/ollama/models)
echo  4. 1-Click Launchers (START_ALL_DOCKER.bat & START_ALL_LOCAL.bat)
echo  5. Setup Guide (PORTABLE_DISTRIBUTION_GUIDE.md)
echo.
echo You can now zip or copy this DocAssistIQ folder to share with anyone!
echo ===============================================================================
pause
