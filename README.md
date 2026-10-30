# Customer Churn Prediction NLP — Shared Backend and Product Frontends

This repository contains one tenant-aware FastAPI backend and independent frontend applications for NastaGhar and Digital Business Card. Product authorization, authentication, tenant isolation, and entitlements are enforced by the shared backend.

## Repository layout

```text
Backend/                  Shared FastAPI app, APIs, auth, database, entitlements and tenant services
nastaghar/                NastaGhar frontend and restaurant assets
product-b/                Digital Business Card frontend and assets
product-c-mastercard/     Documented placeholder for a future product
chrome-extension/         Shared browser extension
configs/ data/ docker/    Shared configuration, local data and container support
docs/ logs/ artifacts/ reports/ releases/
scripts/ tests/           Shared operations and verification
Dockerfile requirements.txt pyproject.toml
.env.example staging.env.example .dockerignore .gitignore
start_app.command start_app.bat stop_app.bat
```

`Backend.app.main:app` is the only backend entry point. The future Mastercard folder contains no active product functionality, payments, or financial processing.

## Development

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill local-only values as needed
uvicorn Backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

On Windows, activate `.venv\\Scripts\\activate` and run the same Uvicorn target. The backend defaults to local SQLite storage under `data/nasta-ghar/`; tests use temporary databases.

### NastaGhar frontend

```bash
cd nastaghar/frontend
npm ci
npm run dev
```

### Product B frontend

```bash
cd product-b/frontend
npm ci
npm run dev
```

Both frontends use the shared backend. Vite forwards `/api` and `/healthz` to `http://127.0.0.1:8000` by default. Set `VITE_BACKEND_URL` in the selected frontend's local Vite environment to target an isolated backend. For deployments behind a reverse proxy, leave `VITE_API_BASE_URL` empty so browser requests stay on the frontend origin and use `/api`. If a deployment needs a direct backend origin, set the public URL through `VITE_API_BASE_URL`; never put secrets there.

The root `start_app.command` (macOS) and `start_app.bat` (Windows) start the shared backend and NastaGhar frontend from the repository root. Product B can be started independently using its commands above.

## Verification

```bash
.venv/bin/python -m compileall -q Backend scripts
.venv/bin/pytest -q
(cd nastaghar/frontend && npm run lint && npm run build)
(cd product-b/frontend && npm run lint && npm run build)
node --experimental-websocket scripts/run_staging_browser_acceptance.mjs
.venv/bin/python scripts/package_release.py --output /private/tmp/vraja-phase9-release.tar.gz
```

Browser acceptance uses temporary rehearsal data and local services. The release packager refuses to overwrite an existing archive and excludes databases, backups, secrets, customer uploads, and local caches.

## Platform guarantees

The shared backend remains responsible for review-only, card-only, and combined entitlements; suspended tenants; platform-admin restrictions; public review/card access rules; and cross-tenant isolation. Hiding a product in a frontend does not grant or deny access by itself.

See [Backend/README.md](Backend/README.md), [nastaghar/README.md](nastaghar/README.md), [product-b/README.md](product-b/README.md), and [product-c-mastercard/README.md](product-c-mastercard/README.md) for product-specific details.
