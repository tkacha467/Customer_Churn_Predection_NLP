# Project Migration Record — Phase 9.0

## Source Path → Canonical Path

| Previous source | Canonical path | Purpose |
|---|---|---|
| `api/main.py` | `Backend/app/main.py` | FastAPI application, CORS, lifecycle and entrypoint |
| `api/review_assistant/storage.py` | `Backend/app/core/database/storage.py` | SQLite storage and tenant data |
| `api/review_assistant/auth.py` | `Backend/app/core/auth/auth.py` | Tenant auth, signed sessions and role checks |
| `api/review_assistant/entitlements.py` | `Backend/app/core/entitlements/entitlements.py` | Product entitlement enforcement |
| `api/review_assistant/google_reviews.py` | `Backend/app/core/tenants/google_reviews.py` | Tenant review configuration |
| `api/review_assistant/migration.py` | `Backend/app/core/database/migration.py` | Idempotent database migration utility |
| `api/review_assistant/document_storage.py` | `Backend/app/api/document_storage.py` | PDF storage, validation and tenant isolation |
| `api/review_assistant/routes.py` | `Backend/app/api/routes.py` | Review, profile, document and admin routes |
| `api/review_assistant/service.py` | `Backend/app/api/service.py` | Review assistant business logic |
| `api/review_assistant/schemas.py` | `Backend/app/schemas.py` | Pydantic API schemas |
| `api/review_assistant` services | `Backend/app/api/` | Review generation, prompts, LLM and validation |
| `api/config`, `api/models`, `api/fusion`, `api/preprocessing` | matching `Backend/app/` packages | Model configuration, NLP and text preprocessing |
| `frontend/` | `nastaghar/frontend/` | NastaGhar frontend application |
| Restaurant images under `frontend/public/restaurant/` | `nastaghar/assets/` and `nastaghar/frontend/public/restaurant/` | Product assets retained in the NastaGhar app |
| Digital Card React UI from the shared frontend | `product-b/frontend/` | Independent Digital Business Card frontend |
| — | `product-c-mastercard/` | Documentation-only future placeholder |

The old `api/`, lowercase `backend/`, and shared root `frontend/` paths have been retired. Runtime modules, tests, tools and startup commands use `Backend.app.*`. There is one backend implementation and no compatibility shim package.

## Deployment

Start the API with `uvicorn Backend.app.main:app`. Build frontend artifacts independently from `nastaghar/frontend/` and `product-b/frontend/`. Each app uses relative `/api` requests behind a reverse proxy; the local Vite proxy target is configurable with `VITE_BACKEND_URL`. `VITE_API_BASE_URL` may specify a public API origin and must not contain credentials.

## Safety

This was a source/configuration reorganization only. The active database at `data/nasta-ghar/reviews.sqlite3` was fingerprinted before the migration and was not opened by the migration steps. No production service, DNS record, or deployment was modified. The previously verified release archive was left in place; new release checks use a separate path.
