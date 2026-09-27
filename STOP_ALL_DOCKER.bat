@echo off
title DocAssistIQ - Stop All Services
color 0E

echo ===============================================================================
echo                DocAssistIQ - Stop All Services
echo ===============================================================================
echo.
echo Stopping all running DocAssistIQ containers (data will be safely preserved)...
docker compose stop

echo.
echo [OK] All services stopped safely.
echo Double-click START_ALL_DOCKER.bat whenever you want to resume.
pause
