@echo off
chcp 65001 >nul
title VRAJA AI - Digital Business Card Launcher
color 0B

echo.
echo  ======================================================
echo   VRAJA AI - Digital Business Card (Product B)
echo   Port 5174 (Frontend) + Port 8000 (Backend API)
echo  ======================================================
echo.

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"
cd /d "%ROOT_DIR%"

echo  [1/4] Checking environment dependencies...

:: Select Python Executable
if exist "%ROOT_DIR%\.venv\Scripts\python.exe" (
    set "PY_CMD=%ROOT_DIR%\.venv\Scripts\python.exe"
) else if exist "%ROOT_DIR%\venv\Scripts\python.exe" (
    set "PY_CMD=%ROOT_DIR%\venv\Scripts\python.exe"
) else (
    set "PY_CMD=python"
)

:: Validate Python
"%PY_CMD%" --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python was not found! Please ensure Python is in your PATH.
    pause
    exit /b 1
)

:: Validate npm
call npm --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Node.js / npm was not found! Please ensure Node.js is in your PATH.
    pause
    exit /b 1
)

:: Free ports 8000 and 5174 if left open by previous sessions
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000, 5174 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1

:: Ensure frontend dependencies are installed
if not exist "%ROOT_DIR%\Digital_Card\frontend\node_modules" (
    echo  Frontend dependencies missing. Installing npm packages...
    cd /d "%ROOT_DIR%\Digital_Card\frontend"
    call npm install
    cd /d "%ROOT_DIR%"
)

echo.
echo  [2/4] Starting FastAPI Backend on port 8000...
start "VRAJA AI Shared Backend" cmd /k "title VRAJA AI Shared Backend && cd /d "%ROOT_DIR%" && set PYTHONCASEOK=1 && "%PY_CMD%" -m uvicorn Backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo  [3/4] Starting Digital Card Frontend on port 5174...
start "VRAJA AI Digital Card" cmd /k "title VRAJA AI Digital Card && cd /d "%ROOT_DIR%\Digital_Card\frontend" && call npm run dev"

echo.
echo  [4/4] Waiting for backend and frontend to initialize...
set /a ATTEMPTS=0
:wait_servers
timeout /t 2 /nobreak >nul
set /a ATTEMPTS+=1

:: Check both backend (8000) and frontend (5174)
"%PY_CMD%" -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2); urllib.request.urlopen('http://127.0.0.1:5174', timeout=2)" >nul 2>&1
if errorlevel 1 (
    if %ATTEMPTS% lss 15 (
        echo   - Loading ML models and initializing servers... (attempt %ATTEMPTS%/15)
        goto :wait_servers
    ) else (
        echo   - Servers are taking longer than usual. Launching browser now...
    )
) else (
    echo   - Both Backend (8000) and Frontend (5174) are online and healthy! ✓
)

echo.
echo  ======================================================
echo   Digital Business Card is running!
echo   Public Card:  http://127.0.0.1:5174/b/default_business/card
echo   Owner Studio: http://127.0.0.1:5174/owner
echo  ======================================================
echo.

timeout /t 1 >nul
start http://127.0.0.1:5174/b/default_business/card
