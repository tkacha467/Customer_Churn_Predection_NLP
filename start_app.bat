@echo off
echo Starting ChurnLens FastAPI Backend...
set PYTHONPATH=%cd%
if exist .venv\Scripts\activate.bat (
    start "FastAPI Backend" cmd /k "call .venv\Scripts\activate.bat && python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload"
    echo Starting ChurnLens Streamlit Dashboard...
    start "Streamlit Dashboard" cmd /k "call .venv\Scripts\activate.bat && streamlit run dashboard/app.py"
) else (
    start "FastAPI Backend" cmd /k "python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload"
    echo Starting ChurnLens Streamlit Dashboard...
    start "Streamlit Dashboard" cmd /k "streamlit run dashboard/app.py"
)

echo Starting ChurnLens React Frontend...
cd frontend
start "React Frontend" cmd /c "npm run dev"

echo Opening the Interactive Project Showcase...
cd ..
start "" "showcase/index.html"

echo All servers are starting in new windows...
