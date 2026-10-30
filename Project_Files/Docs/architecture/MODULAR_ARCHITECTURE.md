# Vraja Modular Architecture — Backend + Independent Product Frontends

## 1. Executive Summary

This repository organizes the multi-product hospitality technology suite into:
1. **Authoritative Shared Backend**: Single backend service under `Backend/app/` containing all business logic, SQLite persistence, authentication, and product entitlement gating.
2. **NastaGhar Product Frontend**: Located under `nastaghar/frontend/` with restaurant-specific presentation and review experience.
3. **Product B (Digital Business Card) Frontend**: Located under `product-b/frontend/` with public card view and card studio editor.
4. **Product C (Mastercard Future Product)**: Located under `product-c-mastercard/` as a documented architectural placeholder.
5. **Shared Operational Tooling**: Operational scripts, migrations, tests, release packaging, and deployment configurations at the root.

---

## 2. Directory Layout

```text
Customer_Churn_Predection_NLP/
│
├── Backend/
│   ├── app/
│   │   ├── api/                # API routers, document storage, review service
│   │   ├── config/             # Model and pipeline settings
│   │   ├── core/
│   │   │   ├── auth/           # Multi-tenant auth, session tokens, passwords
│   │   │   ├── database/       # SQLite storage engine & migrations
│   │   │   ├── entitlements/   # Tenant product entitlement validation
│   │   │   └── tenants/        # Tenant configurations & Google links
│   │   ├── fusion/             # Sentiment-sarcasm fusion engine
│   │   ├── models/             # CardiffNLP RoBERTa model loaders
│   │   ├── preprocessing/      # Text normalization and cleaning
│   │   ├── schemas.py          # Data schemas and validation contracts
│   │   └── main.py             # Canonical FastAPI application entrypoint
│   └── README.md
│
├── nastaghar/
│   ├── frontend/
│   │   ├── src/
│   │   ├── public/
│   │   ├── package.json
│   │   ├── package-lock.json
│   │   └── vite.config.js
│   ├── assets/
│   └── README.md
│
├── product-b/
│   ├── frontend/
│   │   ├── src/
│   │   ├── public/
│   │   ├── package.json
│   │   ├── package-lock.json
│   │   └── vite.config.js
│   ├── assets/
│   └── README.md
│
├── product-c-mastercard/
│   ├── frontend/
│   ├── assets/
│   └── README.md
│
├── chrome-extension/
├── data/
├── docker/
├── docs/
├── logs/
├── artifacts/
├── reports/
├── releases/
├── scripts/
├── tests/
│
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── .env.example
├── staging.env.example
├── .dockerignore
├── .gitignore
├── README.md
├── start_app.command
├── start_app.bat
└── stop_app.bat
```

---

## 3. Product Ownership & Responsibilities

| Component | Directory | Purpose |
|---|---|---|
| **Shared Backend** | `Backend/app/` | Single source of truth for database, authentication, entitlements, review generation, and PDF document storage. |
| **NastaGhar Review Assistant** | `nastaghar/frontend/` | Guest review draft generation, star rating validation, Google review redirection, and restaurant owner portal. |
| **Product B (Digital Card)** | `product-b/frontend/` | Public digital card (`/b/:tenant/card`), owner card editor (`/owner/:tenant/card`), PDF menu downloads, and distinct QR destinations. |
| **Product C (Mastercard)** | `product-c-mastercard/` | Architectural foundation reserved for future Mastercard integration. |

---

## 4. Local Development & Startup

```bash
# Backend startup
uvicorn Backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# NastaGhar Frontend
cd nastaghar/frontend && npm run dev

# Product B Frontend
cd product-b/frontend && npm run dev
```
