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

The owner portal requires `OWNER_PASSWORD` and `OWNER_SESSION_SECRET`. Copy `.env.example` to `.env` for local development and replace both placeholders with private values. In production, inject these values from the hosting provider's secret manager; the API refuses to start if the production password, signing key, HTTPS CORS origins, or persistent data paths are missing.

Use a long random owner password (at least 20 characters) and a separate random session secret (at least 32 characters). Owner sessions use an HTTP-only, Secure, SameSite=Strict cookie in production and expire after eight hours. Configure `CORS_ORIGINS` as a comma-separated list of exact HTTPS origins. Never use `*` in production.

Set `REVIEW_DB_PATH` and `BUSINESS_LINKS_PATH` to files on a persistent volume. Back up the volume and enable the hosting provider's disk encryption because private-feedback tickets may contain contact details. SQLite keeps the latest 2,000 analytics events and 5,000 tickets. Use a managed database before scaling the API across multiple machines.

### Development (`.env.development`)
```env
ENVIRONMENT=development
FRONTEND_BASE_URL=http://localhost:5173
API_BASE_URL=http://localhost:8000
OWNER_PASSWORD=replace-with-a-long-random-development-password
OWNER_SESSION_SECRET=replace-with-at-least-32-random-characters
REVIEW_DB_PATH=./data/nasta-ghar/reviews.sqlite3
BUSINESS_LINKS_PATH=./data/nasta-ghar/business_links.json
LLM_PROVIDER=local
GOOGLE_REVIEW_URL=https://maps.google.com
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Production (`.env.production`)
```env
ENVIRONMENT=production
FRONTEND_BASE_URL=https://your-restaurant-app.com
API_BASE_URL=https://api.your-restaurant-app.com
OWNER_PASSWORD=<managed-secret-at-least-20-characters>
OWNER_SESSION_SECRET=<managed-secret-at-least-32-characters>
REVIEW_DB_PATH=/persistent/nasta-ghar/reviews.sqlite3
BUSINESS_LINKS_PATH=/persistent/nasta-ghar/business_links.json
VITE_API_BASE_URL=https://api.your-restaurant-app.com
LLM_PROVIDER=local
GOOGLE_REVIEW_URL=https://g.page/r/your-restaurant/review
CORS_ORIGINS=https://your-restaurant-app.com
```

> **IMPORTANT**: Never hardcode `http://localhost:5173` into generated QR codes in production. Set `FRONTEND_BASE_URL` to your live domain so table QR codes resolve reliably for guests.

---

The production frontend and API must be served over HTTPS. If frontend and API are on one origin, leave `VITE_API_BASE_URL` unset and configure the web server to proxy `/api` and `/healthz` to FastAPI. For separate origins, set `VITE_API_BASE_URL` at frontend build time and add the exact frontend origin to `CORS_ORIGINS`; keep both origins on the same site so the Strict owner cookie is sent.

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

The Vite development server proxies `/api` and `/healthz` to `127.0.0.1:8000`. The owner dashboard is protected; configure the local credentials in `.env` before signing in.

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
