@echo off
title Nasta Ghar — Review Assistant Launcher
color 0E

echo.
echo  ==========================================
echo   NASTA GHAR — Google Review Assistant
echo   Breakfast ^& Snacks . Rajkot
echo  ==========================================
echo.

:: Set working directory and Python path
cd /d "%~dp0"
set PYTHONPATH=%cd%

:: Kill anything already on port 8000 or 5173 to avoid conflicts
echo  [1/2] Checking for port conflicts...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173 " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: Start FastAPI backend
echo  [1/2] Starting FastAPI backend on http://127.0.0.1:8000 ...
if exist .venv\Scripts\activate.bat (
    start "Nasta Ghar — API Backend" cmd /k "title Nasta Ghar API ^& color 02 ^& echo. ^& echo  Nasta Ghar — FastAPI Backend ^& echo  http://127.0.0.1:8000 ^& echo. ^& call .venv\Scripts\activate.bat ^& python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload"
) else (
    start "Nasta Ghar — API Backend" cmd /k "title Nasta Ghar API ^& color 02 ^& echo. ^& echo  Nasta Ghar — FastAPI Backend ^& echo  http://127.0.0.1:8000 ^& echo. ^& python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload"
)

:: Wait for backend to initialize
echo  Waiting for backend to load models...
timeout /t 4 /nobreak >nul

:: Start React frontend
echo  [2/2] Starting React frontend on http://localhost:5173 ...
cd frontend
start "Nasta Ghar — Customer UI" cmd /k "title Nasta Ghar Frontend ^& color 06 ^& echo. ^& echo  Nasta Ghar — React Frontend ^& echo  http://localhost:5173 ^& echo. ^& npm run dev"
cd ..

:: Wait for frontend to spin up
timeout /t 4 /nobreak >nul

:: Detect Google Chrome executable to ensure opening in Chrome (not Edge)
set "CHROME_EXE="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
) else if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
) else if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe"
)

:: Open the customer-facing review page
if defined CHROME_EXE (
    echo  Opening Nasta Ghar Review Page in Google Chrome...
    start "" "%CHROME_EXE%" "http://localhost:5173/review"
) else (
    echo  Opening Nasta Ghar Review Page in default browser...
    start "" "http://localhost:5173/review"
)

echo.
echo  ==========================================
echo   Both servers are running!
echo.
echo   Customer Review Page:
echo   http://localhost:5173/review
echo.
echo   Owner Dashboard:
echo   http://localhost:5173/owner
echo.
echo   API Docs:
echo   http://127.0.0.1:8000/docs
echo  ==========================================
echo.
pause
