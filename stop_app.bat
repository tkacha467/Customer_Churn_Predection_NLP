@echo off
chcp 65001 >nul
title Nasta Ghar - Stop Application Servers
color 0C

echo.
echo  ======================================================
echo   Stopping Nasta Ghar / Vajra Development Servers
echo  ======================================================
echo.

echo  Stopping FastAPI Backend (port 8000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
    echo   - Stopped PID %%a on port 8000
)

echo.
echo  Stopping React Frontend (port 5173)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173 " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
    echo   - Stopped PID %%a on port 5173
)

echo.
echo  All Nasta Ghar servers stopped cleanly.
echo.
pause
