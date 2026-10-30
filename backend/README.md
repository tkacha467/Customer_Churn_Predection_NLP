# Backend Service

Canonical FastAPI backend service powering the multi-tenant hospitality platform.

## Architecture

```text
Backend/app/
├── api/                  # API routers, business services, document storage & LLM providers
├── config/               # Settings and configuration management
├── core/
│   ├── auth/             # Multi-tenant authentication, session management, HMAC & password hashing
│   ├── database/         # SQLite storage engine, WAL management, and migrations
│   ├── entitlements/     # Product entitlement authorization engine
│   └── tenants/          # Tenant configuration and Google Review management
├── fusion/               # Sarcasm and sentiment fusion logic
├── models/               # CardiffNLP RoBERTa model loaders and inference pipelines
├── preprocessing/        # Advanced text normalization and cleaning
├── schemas.py            # Pydantic data schemas and API contracts
└── main.py               # Canonical FastAPI application entrypoint
```

## Running the Backend

From the repository root:
```bash
uvicorn Backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

`Backend.app.main:app` is the sole application entry point. Backend code imports through `Backend.app.*`; the retired root `api/` package is not part of runtime imports.
