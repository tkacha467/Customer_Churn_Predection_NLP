# Phase 9.0 — Project Structure Migration Record

## Canonical layout

- `api/` → `Backend/app/`: single FastAPI implementation, with auth, database/migrations, entitlements and tenants under `Backend/app/core/`.
- `frontend/` → `nastaghar/frontend/`: NastaGhar React/Vite application; restaurant assets live in `nastaghar/assets/` and `nastaghar/frontend/public/`.
- Digital Business Card UI → `product-b/frontend/`: independent React/Vite app using the shared backend APIs.
- `product-c-mastercard/` remains a documentation-only placeholder.
- Shared scripts, docs, tests, data, configuration and release operations remain at repository root.

The temporary old-path snapshots created before retiring duplicate source trees are in `/private/tmp/churn-phase9-original-api` and `/private/tmp/churn-phase9-original-frontend`. They are recovery copies, not runtime source. The original path inventory is `/private/tmp/churn-phase9-original-tree.txt`.

## Runtime configuration

Use `Backend.app.main:app` for Uvicorn. Backend imports are package-qualified; no `PYTHONPATH` or `sys.path` injection is required. Each frontend retains relative `/api` paths by default. Vite's local proxy target can be set with `VITE_BACKEND_URL`; `VITE_API_BASE_URL` is an optional public API origin and must never contain secrets.

## Data safety

The active local SQLite file is `data/nasta-ghar/reviews.sqlite3`. Its SHA-256 was recorded before source relocation in `/private/tmp/churn-phase9-active-db.sha256`; Phase 9 must not modify it. No database migration is part of this source-only restructuring. The existing verified release archive under `releases/` is preserved; new verification archives use a distinct output path.
