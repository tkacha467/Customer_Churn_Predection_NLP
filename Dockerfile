# Build NastaGhar and Digital Card frontends independently from their product roots.
FROM node:20-alpine AS nastaghar-builder
WORKDIR /app/NastaGhar/frontend
COPY NastaGhar/frontend/package*.json ./
RUN npm ci
COPY NastaGhar/frontend/ ./
ARG NASTAGHAR_VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=$NASTAGHAR_VITE_API_BASE_URL
RUN npm run build

FROM node:20-alpine AS digital-card-builder
WORKDIR /app/Digital_Card/frontend
COPY Digital_Card/frontend/package*.json ./
RUN npm ci
COPY Digital_Card/frontend/ ./
ARG DIGITAL_CARD_VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=$DIGITAL_CARD_VITE_API_BASE_URL
RUN npm run build

FROM python:3.11-slim AS production-runtime
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-cache required sentiment models for offline runtime.
ENV HF_HOME=/root/.cache/huggingface
RUN python -c "from transformers import pipeline; \
    pipeline('text-classification', model='cardiffnlp/twitter-roberta-base-sentiment-latest'); \
    pipeline('text-classification', model='cardiffnlp/twitter-roberta-base-irony')"

COPY Backend/ ./Backend
COPY NastaGhar/ ./NastaGhar
COPY Digital_Card/ ./Digital_Card
COPY Project_Files/ ./Project_Files
COPY pyproject.toml .
COPY --from=nastaghar-builder /app/NastaGhar/frontend/dist ./NastaGhar/frontend/dist
COPY --from=digital-card-builder /app/Digital_Card/frontend/dist ./Digital_Card/frontend/dist

RUN mkdir -p /data/nasta-ghar /data/documents
ENV PORT=8000 ENVIRONMENT=production \
    REVIEW_DB_PATH=/data/nasta-ghar/reviews.sqlite3 \
    BUSINESS_LINKS_PATH=/data/nasta-ghar/business_links.json \
    DOCUMENTS_PATH=/data/documents
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT:-8000}/healthz || exit 1
CMD ["sh", "-c", "uvicorn Backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
