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

echo  [1/3] Checking environment dependencies...

if exist "%ROOT_DIR%\.venv\Scripts\python.exe" (
    set "PY_CMD=%ROOT_DIR%\.venv\Scripts\python.exe"
) else if exist "%ROOT_DIR%\venv\Scripts\python.exe" (
    set "PY_CMD=%ROOT_DIR%\venv\Scripts\python.exe"
) else (
    set "PY_CMD=python"
)

:: Check if port 8000 is running
netstat -ano | findstr :8000 | findstr LISTENING >nul 2>&1
if errorlevel 1 (
    echo  [2/3] Starting backend API on port 8000...
    start "VRAJA AI Shared Backend" cmd /k "cd /d "%ROOT_DIR%" && set HF_HUB_OFFLINE=1 && "%PY_CMD%" -m uvicorn Backend.app.main:app --host 127.0.0.1 --port 8000 --reload"
) else (
    echo  [2/3] Backend API is already running on port 8000.
)

:: Check if port 5174 is running
netstat -ano | findstr :5174 | findstr LISTENING >nul 2>&1
if errorlevel 1 (
    echo  [3/3] Starting Digital Card frontend on port 5174...
    start "VRAJA AI Digital Card" cmd /k "cd /d "%ROOT_DIR%\Digital_Card\frontend" && npm run dev"
) else (
    echo  [3/3] Digital Card frontend is already running on port 5174.
)

echo.
echo  ======================================================
echo   Digital Business Card is running!
echo   Public Card:  http://127.0.0.1:5174/b/default_business/card
echo   Owner Studio: http://127.0.0.1:5174/owner
echo  ======================================================
echo.
timeout /t 2 >nul
start http://127.0.0.1:5174/b/default_business/card
