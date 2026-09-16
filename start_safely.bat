@echo off
echo ========================================================
echo DocAssistIQ - Safe Startup Protocol
echo ========================================================
echo.

echo [1/4] Preparing Backend Environment...
cd backend
if not exist .\.venv (
    echo [INFO] Virtual environment not found. Please ensure it is created.
) else (
    echo [INFO] Updating Python dependencies...
    call .\.venv\Scripts\python -m pip install -r requirements.txt --quiet
)

echo.
echo [2/4] Preparing Frontend Environment...
cd ..\frontend
echo [INFO] Clearing Next.js Turbopack Cache...
if exist .next rmdir /s /q .next

echo [INFO] Enforcing Frontend Dependency Integrity...
call npm install --quiet

echo.
echo [3/4] Launching Systems...
echo ========================================================

:: Start Backend in a new terminal window
echo [INFO] Starting Backend (FastAPI)...
start "DocAssistIQ - Backend" cmd /c "cd ..\backend & call .\.venv\Scripts\activate & uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: Start Celery Worker & Beat in a new terminal window
echo [INFO] Starting Celery Worker and Beat...
start "DocAssistIQ - Celery Worker" cmd /c "cd ..\backend & call .\.venv\Scripts\activate & celery -A app.celery_app worker -l info -B"


:: Start Frontend in the current terminal window
echo [INFO] Starting Frontend (Next.js)...
call npm run dev

echo.
echo All systems are running. Close this window to stop the frontend.
pause
