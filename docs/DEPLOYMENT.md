# ChurnLens — Production Deployment Guide

## 1. Architecture Overview
```
                 INTERNET
                    │
                    ▼
          ┌──────────────────┐
          │  Vite/React App  │  (Static SPA on CDN/Vercel/Cloudflare)
          └────────┬─────────┘
                   │ HTTPS API calls
                   ▼
          ┌──────────────────┐
          │ FastAPI Backend  │  (Container on Railway/Fly/AWS/Render)
          └────────┬─────────┘
                   │
          ┌────────┴─────────┐
          ▼                  ▼
    Review Service      Sentiment Validator
    (LocalLLM / Cloud)  (CardiffNLP RoBERTa)
```

---

## 2. Environment Configuration

### Development (`.env.development`)
```env
ENVIRONMENT=development
FRONTEND_BASE_URL=http://localhost:5173
API_BASE_URL=http://localhost:8000
LLM_PROVIDER=local
GOOGLE_REVIEW_URL=https://maps.google.com
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Production (`.env.production`)
```env
ENVIRONMENT=production
FRONTEND_BASE_URL=https://your-restaurant-app.com
API_BASE_URL=https://api.your-restaurant-app.com
LLM_PROVIDER=local
GOOGLE_REVIEW_URL=https://g.page/r/your-restaurant/review
CORS_ORIGINS=https://your-restaurant-app.com
```

> **IMPORTANT**: Never hardcode `http://localhost:5173` into generated QR codes in production. Set `FRONTEND_BASE_URL` to your live domain so table QR codes resolve reliably for guests.

---

## 3. Running Locally

### Backend
```bash
# In churnlens repository root
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend
```bash
# In frontend/ directory
npm install
npm run dev
```

---

## 4. Building for Production

### Frontend
```bash
cd frontend
npm run build
# Outputs production-ready static assets to frontend/dist/
```

### Backend Container (Docker)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
