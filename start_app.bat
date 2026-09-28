@echo off
chcp 65001 >nul
title Nasta Ghar - Review Assistant Launcher
color 0E

echo.
echo  ==========================================
echo   NASTA GHAR - Google Review Assistant
echo   Breakfast ^& Snacks . Rajkot
echo  ==========================================
echo.

:: Set working directory and Python path
cd /d "%~dp0"
set PYTHONPATH=%cd%

echo  [1/3] Preparing local development servers...

:: Select Python Executable
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_CMD=%~dp0.venv\Scripts\python.exe"
) else (
    set "PY_CMD=python"
)

:: Start FastAPI backend in a new dedicated window
echo  [2/3] Starting FastAPI Backend on http://0.0.0.0:8000 ...
start "Nasta Ghar API Backend" cmd /k "cd /d "%~dp0" && set PYTHONPATH=%cd% && "%PY_CMD%" -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

:: Start React Frontend in a new dedicated window
echo  [3/3] Starting React Frontend on http://0.0.0.0:5173 ...
start "Nasta Ghar React Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev -- --host 0.0.0.0"

:: Wait for servers to initialize
echo.
echo  Waiting for backend models and frontend to initialize...
timeout /t 5 /nobreak >nul

:: Detect Google Chrome executable
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
echo  ======================================================
echo   ALL SERVERS RUNNING SUCCESSFULLY!
echo.
echo   Customer Review Page:
echo   http://localhost:5173/review
echo.
echo   Owner Dashboard:
echo   http://localhost:5173/owner
echo.
echo   API Docs (FastAPI):
echo   http://127.0.0.1:8000/docs
echo  ======================================================
echo.
echo  Keep the server windows open while using the app.
echo.
pause
