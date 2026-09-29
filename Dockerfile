# =============================================================
# Stage 1: Build React/Vite Frontend
# =============================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# =============================================================
# Stage 2: Production Python Backend Runtime
# =============================================================
FROM python:3.11-slim AS production-runtime

# Install system dependencies for PyTorch/tokenizers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-cache Hugging Face CardiffNLP RoBERTa models during build
# This guarantees 100% offline runtime availability and zero cold-start download delay.
ENV HF_HOME=/root/.cache/huggingface
RUN python -c "from transformers import pipeline; \
    pipeline('text-classification', model='cardiffnlp/twitter-roberta-base-sentiment-latest'); \
    pipeline('text-classification', model='cardiffnlp/twitter-roberta-base-irony')"

# Copy application source code
COPY api/ ./api
COPY pyproject.toml .

# Copy compiled frontend assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create persistent storage directory mount point
RUN mkdir -p /data/nasta-ghar

# Default environment configuration
ENV PORT=8000
ENV ENVIRONMENT=production
ENV REVIEW_DB_PATH=/data/nasta-ghar/reviews.sqlite3
ENV BUSINESS_LINKS_PATH=/data/nasta-ghar/business_links.json

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT:-8000}/healthz || exit 1

# Start Uvicorn with support for cloud dynamic $PORT (Railway, Render, Fly, Cloud Run)
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
