@echo off
chcp 65001 >nul
title Nasta Ghar - Review Assistant Launcher
color 0E

echo.
echo  ======================================================
echo   NASTA GHAR - Google Review Assistant (Vajra Engine)
echo   Trilingual Review AI: English, Hinglish, Gujlish
echo   Hospitality-Aware Topics • Zero Fabrication
echo  ======================================================
echo.

:: Set working directory and Python path
cd /d "%~dp0"
set PYTHONPATH=%cd%

echo  [1/4] Checking environment dependencies...

:: Select Python Executable
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_CMD=%~dp0.venv\Scripts\python.exe"
) else (
    set "PY_CMD=python"
)

:: Validate Python
"%PY_CMD%" --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python was not found! Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

:: Validate Node/NPM
call npm --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Node.js / npm was not found! Please install Node.js and add it to PATH.
    pause
    exit /b 1
)

:: Check frontend node_modules
if not exist "%~dp0frontend\node_modules" (
    echo  Frontend dependencies missing. Running npm install...
    cd /d "%~dp0frontend"
    call npm install
    cd /d "%~dp0"
)

:: Detect Local LAN IP for Mobile QR Scanning
set "LOCAL_IP="
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do (
        set "LOCAL_IP=%%b"
        goto :ip_done
    )
)
:ip_done

:: Start FastAPI backend in a new dedicated window
echo.
echo  [2/4] Starting FastAPI Backend on http://0.0.0.0:8000 ...
start "Nasta Ghar API Backend" cmd /k "title Nasta Ghar API Backend && cd /d "%~dp0" && set PYTHONPATH=%cd% && "%PY_CMD%" -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

:: Start React Frontend in a new dedicated window
echo  [3/4] Starting React Frontend on http://0.0.0.0:5173 ...
start "Nasta Ghar React Frontend" cmd /k "title Nasta Ghar React Frontend && cd /d "%~dp0frontend" && npm run dev -- --host 0.0.0.0"

:: Wait for servers to initialize
echo.
echo  [4/4] Waiting for backend models and frontend server to initialize...
timeout /t 6 /nobreak >nul

:: Detect Google Chrome or Microsoft Edge executable
set "BROWSER_EXE="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    set "BROWSER_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
) else if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    set "BROWSER_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
) else if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    set "BROWSER_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe"
) else if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
    set "BROWSER_EXE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
)

:: Open the customer-facing review page
if defined BROWSER_EXE (
    echo  Opening Nasta Ghar Review Page in browser...
    start "" "%BROWSER_EXE%" "http://localhost:5173/review"
) else (
    echo  Opening Nasta Ghar Review Page in default browser...
    start "" "http://localhost:5173/review"
)

echo.
echo  ======================================================
echo   ALL SERVERS RUNNING SUCCESSFULLY!
echo.
echo   Customer Review Experience:
echo   Local:   http://localhost:5173/review
if defined LOCAL_IP (
    echo   Mobile:  http://%LOCAL_IP%:5173/review (QR scan)
) else (
    echo   Mobile:  http://^<your-wifi-ip^>:5173/review (QR scan)
)
echo.
echo   Languages: English, Hindi (Hinglish), Gujarati (Gujlish)
echo.
echo   Owner Dashboard:
echo   http://localhost:5173/owner
echo.
echo   API Docs ^& Health:
echo   http://127.0.0.1:8000/docs
echo   http://127.0.0.1:8000/healthz
echo  ======================================================
echo.
echo  Keep the server windows open while using the application.
echo.
pause
