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

:: Set clean working directory without trailing backslash
set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"
cd /d "%ROOT_DIR%"
set "PYTHONPATH=%ROOT_DIR%"

echo  [1/4] Checking environment dependencies...

:: Select Python Executable (supports .venv, venv in current and parent directory)
if exist "%ROOT_DIR%\.venv\Scripts\python.exe" (
    set "PY_CMD=%ROOT_DIR%\.venv\Scripts\python.exe"
) else if exist "%ROOT_DIR%\venv\Scripts\python.exe" (
    set "PY_CMD=%ROOT_DIR%\venv\Scripts\python.exe"
) else if exist "%ROOT_DIR%\..\.venv\Scripts\python.exe" (
    set "PY_CMD=%ROOT_DIR%\..\.venv\Scripts\python.exe"
) else if exist "%ROOT_DIR%\..\venv\Scripts\python.exe" (
    set "PY_CMD=%ROOT_DIR%\..\venv\Scripts\python.exe"
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
if not exist "%ROOT_DIR%\frontend\node_modules" (
    echo  Frontend dependencies missing. Running npm install...
    cd /d "%ROOT_DIR%\frontend"
    call npm install
    cd /d "%ROOT_DIR%"
)

:: Free ports 8000 and 5173 if left open by previous sessions to prevent conflicts
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 " ^| findstr "LISTENING" 2^>nul') do (
    if not "%%a"=="0" taskkill /F /T /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173 " ^| findstr "LISTENING" 2^>nul') do (
    if not "%%a"=="0" taskkill /F /T /PID %%a >nul 2>&1
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
start "Nasta Ghar API Backend" /D "%ROOT_DIR%" cmd /k "title Nasta Ghar API Backend && set PYTHONPATH=%ROOT_DIR% && "%PY_CMD%" -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

:: Start React Frontend in a new dedicated window
echo  [3/4] Starting React Frontend on http://0.0.0.0:5173 ...
start "Nasta Ghar React Frontend" /D "%ROOT_DIR%\frontend" cmd /k "title Nasta Ghar React Frontend && call npm run dev -- --host 0.0.0.0"

:: Wait for servers to initialize with dynamic health polling
echo.
echo  [4/4] Waiting for backend API to be ready on http://127.0.0.1:8000/healthz ...
set /a ATTEMPTS=0
:wait_backend
timeout /t 2 /nobreak >nul
set /a ATTEMPTS+=1
"%PY_CMD%" -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)" >nul 2>&1
if errorlevel 1 (
    if %ATTEMPTS% lss 12 (
        echo   - Loading ML models and priming server... (attempt %ATTEMPTS%/12)
        goto :wait_backend
    ) else (
        echo   - Backend is taking a bit longer to load. Proceeding...
    )
) else (
    echo   - Backend is online and healthy! ✓
)

:: Detect Chrome, Brave, or Edge executable
set "BROWSER_EXE="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    set "BROWSER_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
) else if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    set "BROWSER_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
) else if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    set "BROWSER_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe"
) else if exist "%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe" (
    set "BROWSER_EXE=%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"
) else if exist "%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe" (
    set "BROWSER_EXE=%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe"
) else if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
    set "BROWSER_EXE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
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
echo   Local:   http://localhost:5173/owner
if defined LOCAL_IP (
    echo   Mobile:  http://%LOCAL_IP%:5173/owner
)
echo.
echo   API Docs ^& Health:
echo   http://127.0.0.1:8000/docs
echo   http://127.0.0.1:8000/healthz
echo  ======================================================
echo.
echo   To stop all servers cleanly, run stop_app.bat
echo.
pause
