# PRODUCTION_DEPLOYMENT_INVENTORY.md — Minimal Production Payload & Setup

**Generated Date:** September 29, 2026  
**Project:** ChurnLens / Nasta Ghar AI Review Assistant (`v2.4.0`)  

---

## 1. Minimal Production File Manifest

To deploy Nasta Ghar reliably without shipping multi-gigabyte training datasets or intermediate checkpoints, only the following core files are required:

```
/app/
├── api/                             # Complete active backend package
│   ├── main.py
│   ├── config/settings.py
│   ├── preprocessing/text_cleaner.py
│   ├── models/model_loader.py
│   ├── models/sentiment.py
│   ├── models/sarcasm.py
│   ├── fusion/engine.py
│   ├── fusion/explainer.py
│   └── review_assistant/
│       ├── __init__.py
│       ├── routes.py
│       ├── schemas.py
│       ├── service.py
│       ├── auth.py
│       ├── generator.py
│       ├── validator.py
│       ├── storage.py
│       ├── google_reviews.py
│       ├── llm_provider.py
│       ├── prompts.py
│       └── business_links.json
├── frontend/                        # Frontend source (if built inside container) OR
│   └── dist/                        # Pre-compiled static assets (if built in CI)
│       ├── index.html
│       ├── assets/index-*.js
│       ├── assets/index-*.css
│       └── restaurant/
│           ├── darshan-host.png
│           ├── scene-phone.webp
│           └── scene-wide.webp
├── requirements.txt                 # Pinned backend dependencies
└── pyproject.toml                   # Python project specification
```

---

## 2. Measured vs. Estimated Sizing

| Component | Source of Measurement | Measured Payload | Compressed / Estimated Disk |
| :--- | :--- | :---: | :---: |
| **Backend Source Code (`api/`)** | Local Filesystem Inspection | 253.26 KB | ~75 KB (gzip) |
| **Frontend Static Assets (`frontend/dist/`)** | `npm run build` Output | 361.91 KB (JS + CSS + HTML) | 103.18 KB (gzip) |
| **Frontend Media Assets (`public/restaurant/`)**| Image files | 916.29 KB | 916.29 KB (WebP/PNG) |
| **Base Python Container (`python:3.11-slim`)** | Official Docker Hub image | 130 MB | ~50 MB (compressed) |
| **Python Packages (`requirements.txt`)** | Pip installed dependencies (PyTorch CPU, Transformers) | 850 MB | ~300 MB (compressed) |
| **CardiffNLP RoBERTa Model Weights** | Hugging Face Hub cache (`~/.cache/huggingface`) | 996 MB | ~450 MB (compressed) |
| **Total Production Image Size** | **Calculated Sum** | **~2.2 GB uncompressed** | **~850 MB image download** |

*Crucial Comparison:* The full local repository is **4.64 GB**, but the production deployment bundle requires **zero files from `data/` (1.85 GB)** and **zero files from `models/checkpoints/` (766 MB)**.

---

## 3. Production Environment Configuration

The backend startup assertions strictly validate these environment variables when `ENVIRONMENT=production`:

```env
# Runtime Environment
ENVIRONMENT=production

# Application URLs (Must use HTTPS in production)
FRONTEND_BASE_URL=https://nasta-ghar.yourdomain.com
API_BASE_URL=https://api.nasta-ghar.yourdomain.com
CORS_ORIGINS=https://nasta-ghar.yourdomain.com

# Owner Security (Enforced: Password >= 20 chars, Secret >= 32 chars)
OWNER_PASSWORD=<generate-at-least-20-character-secret>
OWNER_SESSION_SECRET=<generate-at-least-32-character-random-secret>

# Persistent Volume Paths (Must be stored on attached disk)
REVIEW_DB_PATH=/data/reviews.sqlite3
BUSINESS_LINKS_PATH=/data/business_links.json

# Review Generation Provider (local by default; optional cloud keys)
LLM_PROVIDER=local
GOOGLE_REVIEW_URL=https://g.page/r/your-google-place-id/review
```

---

## 4. Production Multi-Stage Dockerfile

```dockerfile
# -------------------------------------------------------------
# Stage 1: Build React Frontend
# -------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# -------------------------------------------------------------
# Stage 2: Production Python Backend Container
# -------------------------------------------------------------
FROM python:3.11-slim AS production-runtime

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-cache Hugging Face CardiffNLP models into container image to prevent cold-start download errors
ENV HF_HOME=/root/.cache/huggingface
RUN python -c "from transformers import pipeline; \
    pipeline('text-classification', model='cardiffnlp/twitter-roberta-base-sentiment-latest'); \
    pipeline('text-classification', model='cardiffnlp/twitter-roberta-base-irony')"

# Copy application source code
COPY api/ ./api
COPY pyproject.toml .

# Copy built frontend assets
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose backend port
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 5. Storage Persistence Strategy

1. **Volume Attachment:** Mount a persistent volume at `/data` (e.g. Railway Volume, Render Persistent Disk, or Docker Named Volume `nasta_data:/data`).
2. **SQLite Auto-Trimming:** The backend auto-limits analytics records to 2,000 events and private feedback tickets to 5,000 records, capping SQLite database size at under **15 MB** regardless of continuous usage.
3. **Atomic Configuration Updates:** Business updates (`google_reviews.py`) write to `/data/business_links.json.tmp` and execute an atomic rename (`replace()`), ensuring zero file corruption if the server restarts during a write.
