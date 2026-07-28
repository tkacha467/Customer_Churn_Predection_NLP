@echo off
echo Starting ChurnLens FastAPI Backend...
set PYTHONPATH=%cd%
start "FastAPI Backend" cmd /k "python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting ChurnLens React Frontend...
cd frontend
start "React Frontend" cmd /c "npm run dev"

echo Both servers are starting in new windows...
