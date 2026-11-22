# Product A — Review System: Developer Handover & Onboarding Guide

## 1. Project Identification & Critical Invariants

Welcome to **Product A (Review System)**. Before making any code modifications, understand these core project boundaries:

1. **Product A is the Review System:**
   - A multi-tenant, AI-powered customer feedback, sentiment analysis, and Google Maps review acceleration engine.
   - **Product A is NOT Nasta Ghar.** Nasta Ghar is simply an initial seed tenant / demo restaurant brand (`default_business`) in the multi-tenant database. Do not treat Nasta Ghar branding, colors, or snacks as Product A's system identity.
2. **Product B (Digital Business Card) is Read-Only:**
   - Located in `Digital_Card/`. It has separate frontend routes and backend dependencies. Never modify Product B components, routes, or database tables (`business_profiles`, `tenant_documents`).
3. **Google Anti-Gating is Non-Negotiable:**
   - Every rating from 1 through 5 must have unconditional, direct access to the business's Google Maps review link. Never hide, disable, or gate the Google Review button for lower ratings.
4. **Template Version Immutability:**
   - Published template versions (`template_versions`) cannot be modified in place. To change a template, create a new draft version, edit it, and publish it.

---

## 2. Technology Stack & Key Dependencies

| Layer | Technology | Version | Location / Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | React + Vite | React 18, Vite 5 | `NastaGhar/frontend/` |
| **Styling & Design** | Pure CSS3 + Design System | BEM / CSS Variables | `NastaGhar/frontend/src/index.css`, `AdminDesignSystem.css` |
| **Icons & Visuals** | Lucide React | ^0.344 | Navigation, status badges, and action buttons |
| **Backend Framework** | FastAPI + Uvicorn | FastAPI 0.110+ | `Backend/app/main.py` |
| **Language & Runtime** | Python | 3.12.x | Root environment |
| **Database** | SQLite 3 (WAL mode) | SQLite 3.40+ | `Project_Files/Data/nasta-ghar/reviews.sqlite3` |
| **Data Validation** | Pydantic v2 | ^2.6.0 | `Backend/app/schemas.py`, `template_schemas.py` |
| **AI / NLP Models** | RoBERTa & DistilBERT | PyTorch / Transformers | `Backend/app/models/` (Local sentiment & sarcasm models) |
| **LLM Provider** | Google Gemini API / Fallback | HTTP REST | `Backend/app/api/llm_provider.py` |
| **Test Runner** | pytest | ^9.2.0 | `Project_Files/Tests/` |

---

## 3. Local Environment Setup

### 3.1 Prerequisites
- **Python 3.12+** installed and available in your `PATH`.
- **Node.js 18+** and `npm` installed.
- **Git** (latest version).

### 3.2 Backend Setup
Open a terminal in the project root (`Customer_Churn_Predection_NLP`):

```bash
# 1. Verify Python environment
python --version  # Must be 3.12.x

# 2. Install Python dependencies
pip install -r requirements.txt
pip install python-docx  # Documentation tooling
```

### 3.3 Frontend Setup
```bash
# Navigate to Product A frontend directory
cd NastaGhar/frontend

# Install Node dependencies
npm install
```

---

## 4. Configuration & Environment Variables

### Backend Configuration (`Backend/.env` or root `.env`)
Create or verify `.env` in the root repository directory:

```env
# Application Settings
ENVIRONMENT=development
PORT=8000
HOST=127.0.0.1
DEBUG=true

# Database Path
REVIEW_DB_PATH=Project_Files/Data/nasta-ghar/reviews.sqlite3

# Security & Sessions
SECRET_KEY=dev_insecure_vraja_review_secret_key_change_in_prod_123456
SESSION_COOKIE_NAME=vraja_session_token
SESSION_MAX_AGE_SECONDS=604800

# Optional: Google Gemini API Key (If omitted, uses built-in rule generator)
GEMINI_API_KEY=your_gemini_api_key_here
```

### Frontend Configuration (`NastaGhar/frontend/.env`)
```env
VITE_API_URL=http://127.0.0.1:8000/api
```

---

## 5. Running the Application

### Starting the Backend Server
From the `Customer_Churn_Predection_NLP` root directory:

```bash
python -m uvicorn Backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base URL: `http://127.0.0.1:8000/api`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
- Healthcheck: `http://127.0.0.1:8000/healthz`

### Starting the Frontend Development Server
From the `NastaGhar/frontend` directory:

```bash
npm run dev
```
- Local Frontend URL: `http://localhost:5173/`

### Application Entry Routes:
- **Customer Review Journey (Default Demo Tenant):**  
  `http://localhost:5173/?biz=default_business`
- **Customer Review Journey (Specific Tenant):**  
  `http://localhost:5173/?biz=test_cafe`
- **Tenant Owner Portal:**  
  Toggle "Owner Portal" in header or login at `/owner` (Credentials: `owner@nastaghar.com` / `Owner123!`)
- **Platform Admin Control Plane:**  
  Toggle "Vraja Admin" in header (Credentials: `owner@nastaghar.com` / `Owner123!`)
- **Template Manager:**  
  Accessible via Vraja Admin -> "Templates" tab.

---

## 6. Database Architecture & Initial Seeding

The SQLite database is located at:
`Project_Files/Data/nasta-ghar/reviews.sqlite3`

### Automatic Startup Initialization:
When FastAPI boots (`Backend/app/main.py` -> `ReviewStore.__init__`):
1. `init_template_schema(db)` creates the 5 template tables and indexes if missing.
2. `seed_default_templates(db)` idempotently seeds:
   - 4 platform industries: `restaurant`, `hotel`, `salon`, `clinic`
   - 8 multi-industry templates (hotel, salon, clinic, and legacy restaurant)
   - 4 approved modern restaurant presets (`restaurant_classic_bistro`, `restaurant_modern_urban`, `restaurant_luxury_dining`, `restaurant_cafe_playful`)
   - Default business assignment for `default_business` to `tpl_restaurant_classic`.

### Resetting Test Database (If Needed):
If you ever need to reset the database to a clean state:
```bash
# Delete reviews.sqlite3 (it will be regenerated automatically on next server start)
del "Project_Files\Data\nasta-ghar\reviews.sqlite3"
```

---

## 7. Running the Automated Test Suites

Product A includes comprehensive pytest suites verifying schemas, immutability, tenant isolation, and anti-gating:

```bash
# 1. Run Phase 4.1 Foundation Suite (15 tests)
python -m pytest Project_Files/Tests/test_phase4_template_foundation.py -v

# 2. Run Dynamic Templates Backward-Compatibility Suite (6 tests)
python -m pytest Project_Files/Tests/test_dynamic_templates.py -v

# 3. Run Product B Non-Interference Regression Suite (20 active tests)
python -m pytest Project_Files/Tests/test_profile_and_document_apis.py -v

# 4. Run Review Assistant AI Validation Suite
python -m pytest Project_Files/Tests/test_review_assistant.py -v
```

---

## 8. Key Architectural Files & Responsibilities

| File Path | Responsibility |
| :--- | :--- |
| `Backend/app/api/template_schemas.py` | Strict Pydantic v2 schemas: HEX colors, fonts, layout variants, component allowlists, injection filtering. |
| `Backend/app/api/template_routes.py` | Admin versioning APIs (`/api/platform/templates/...`) & Public config resolution (`/api/public/businesses/{id}/config`). |
| `Backend/app/core/database/template_storage.py` | Database storage engine: Version immutability state machine, business assignment version pinning, and public config resolution. |
| `Backend/app/api/prompts.py` | Multilingual prompt templates (English, Gujarati, Hindi) for AI review generation. |
| `Backend/app/api/service.py` | Review idea generation orchestrator: handles prompt formatting, LLM invocation, and contradiction checking. |
| `Backend/app/core/auth/auth.py` | Cookie session auth, password hashing, and in-memory rate limiting (5 attempts/min). |
| `NastaGhar/frontend/src/components/CustomerReview.jsx` | Primary customer review experience: ratings, topic chips, AI generator, Google handoff, private feedback modal. |
| `NastaGhar/frontend/src/components/OwnerPortal.jsx` | Store owner analytics, telemetry funnels, private feedback tickets, and QR code downloads. |
| `NastaGhar/frontend/src/components/VrajaAdmin.jsx` | Superadmin console: tenant management, platform metrics, and system controls. |
| `NastaGhar/frontend/src/components/admin/TemplateManager.jsx` | Administrative UI for template library, live interactive preview, and tenant version pinning. |

---

## 9. Next Steps for Continuing Development (Phase 4.2)

With the Phase 4.1 Configuration Foundation complete and patched:
- **Phase 4.2 Objective:** Implement customer-facing template rendering in `CustomerReview.jsx`.
- **Key Task:** Connect the visual tokens (`theme`), layout variants (`layout`), and typography resolved from `GET /api/public/businesses/{id}/config` to dynamic CSS classes and layout wrappers, rendering the 4 distinct restaurant styles (`Classic Bistro`, `Modern Urban`, `Luxury Dining`, `Café & Playful`) while maintaining the identical review engine underneath.
