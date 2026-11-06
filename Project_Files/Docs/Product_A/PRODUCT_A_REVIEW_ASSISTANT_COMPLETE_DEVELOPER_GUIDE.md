# VRAJA AI — PRODUCT A: GOOGLE REVIEW MANAGER & DINER FEEDBACK SYSTEM
## Comprehensive System Architecture, Developer Manual & Onboarding Guide

> **Document Version:** 1.0  
> **Last Updated:** November 2026  
> **Target Audience:** Backend Engineers, Frontend Engineers, Full-Stack Developers, DevOps, and Product Team Members joining the Product A development team.

---

## 1. Executive Overview

### 1.1 What is Product A?
**Product A** (branded internally and in demo as **NastaGhar** / **Vraja Review Studio**) is an enterprise-grade, multi-tenant B2B SaaS application designed for restaurants, cafes, and hospitality businesses. Its core mission is to **bridge the gap between offline dining experiences and authentic online Google Reviews**.

### 1.2 Core Problem Solved
- **Diner Friction:** Diners frequently want to leave positive Google reviews, but typing out thoughts on a mobile phone creates friction, leading to drop-offs.
- **Review Fatigue & Generic Feedback:** When diners do leave reviews, they are often just 5 stars without text, which Google's ranking algorithm values less than detailed, keyword-rich reviews.
- **Negative Feedback Escalation:** Diners with minor complaints (cold tea, slow water refill) often blast a 1-star public Google review when they lack a private, direct channel to restaurant management.
- **Google Policy Violations:** Many competing tools use dishonest "review gating" (blocking negative reviews from reaching Google), which directly violates Google's Review Guidelines and can result in business blacklisting. Product A solves this **ethically and legally** without gating.

### 1.3 Key Value Propositions
1. **Zero-Friction Review Synthesis:** Diners scan a table QR code, tap their rating, select 1–2 dining aspects (e.g., *Special Chai*, *Friendly Staff*), and our AI generator produces 3–5 humanized, grounded candidate review ideas in **English, Hindi, or Gujarati**.
2. **1-Click Copy & Google Maps Handoff:** Tapping a candidate copies the text straight to the mobile clipboard and opens the restaurant's authentic Google Maps review dialog.
3. **Private Diner Note Channel:** For negative or sensitive feedback, diners can directly message management in real time (`TICK-XXXXXX`), de-escalating customer dissatisfaction before it turns into a public 1-star review.
4. **Owner QR Code Studio:** Dynamic, table-specific, and location-specific QR code generator with live standee preview and printable assets.
5. **AI Manager Reply Engine:** Empowers restaurant managers to instantly synthesize gracious, empathetic responses to guest reviews using sentiment and sarcasm analysis.

---

## 2. End-to-End System Architecture

```mermaid
flowchart TD
    subgraph Diner Experience (Frontend)
        A["Diner Scans Table QR Code"] --> B["CustomerReview.jsx (/review?table=Table+4)"]
        B --> C["Select Rating (1 to 5 Stars)"]
        C --> D{"Rating >= 4?"}
        D -- "Yes" --> E["Select Topics & Language (EN/HI/GU)"]
        E --> F["AI Review Generator (/api/reviews/ideas)"]
        F --> G["Diner Selects Preferred Review Draft"]
        G --> H["1-Click Clipboard Copy & Redirect to Google Maps"]
        D -- "No (1-3 Stars)" --> I["Alternative: Direct Private Diner Note"]
        I --> J["Submit to Management Inbox (/api/reviews/private-feedback)"]
        I -.->|Google Policy Compliant: Still Allowed| H
    end

    subgraph Owner & Admin Console
        K["OwnerPortal.jsx (/owner/:tenant_id)"] --> L["1. Home (KPIs, Peaks, Insights)"]
        K --> M["2. Review Setup (Profile, Google URL, Topics, Languages)"]
        K --> N["3. Review Activity & Analytics (Hourly, Weekly, Seasonal, Festivals)"]
        K --> O["4. Private Feedback Inbox (Tickets, Status Updates)"]
        K --> P["5. Settings (Account, Password Management, Preview)"]
        Q["VrajaAdmin.jsx (/admin)"] --> R["Super Admin: Multi-Tenant Onboarding & Entitlements"]
        X["Internal VRAJA AI Operations"] --> Y["Standalone Internal QR Management Tool"]
    end

    subgraph Backend Core (FastAPI & SQLite)
        S["FastAPI Routes (/api/...)"]
        T["ReviewService (Business Logic)"]
        U["ReviewStore (SQLite WAL Mode)"]
        V["LLM Provider (Review & Reply Synthesis)"]
        W["NLP Fusion Engine (Sentiment & Sarcasm Models)"]
        
        S --> T
        T --> U
        T --> V
        T --> W
    end

    B -.->|API Calls| S
    K -.->|API Calls| S
    Q -.->|API Calls| S
```

---

## 3. Tech Stack Breakdown

### Backend Stack
- **Runtime:** Python 3.12+
- **API Framework:** FastAPI (Asynchronous REST API)
- **Database:** SQLite 3 with **WAL mode** (`PRAGMA journal_mode=WAL`)
- **Indexing & Multi-Tenancy:** Composite indexes on `(tenant_id, created_at DESC)`, strict tenant-isolation query boundaries.
- **NLP & AI Engine:**
  - Hugging Face Transformers / PyTorch (Sentiment Analysis & Sarcasm Classification models in `Backend/app/models/`).
  - Provider Abstraction (`Backend/app/api/llm_provider.py`): Supports Cloud LLM APIs (Gemini/OpenAI) and local deterministic synthesis fallback.
  - Sarcasm & Sentiment Fusion Explainer (`Backend/app/fusion/`).
- **Security & Validation:**
  - `defusedxml` & hardened SVG sanitization (`svg_sanitizer.py`).
  - Strict Content Security Policy (`CSP`), rate-limiting sliding windows.
  - PBKDF2 / SHA-256 session token hashing (`Backend/app/core/auth/auth.py`).
- **Testing:** `pytest` (178 backend unit/integration tests passing).

### Frontend Stack
- **Framework:** React 19 (Hooks-based architecture)
- **Bundler:** Vite 8 (Ultra-fast build, ~60ms bundle time)
- **Styling:** Modular CSS + Tailwind CSS utilities
- **QR Generation:** `qrcode` npm package (client-side dynamic SVG & Canvas to PNG data URL)
- **Routing:** Hybrid URL routing (Path-based `/b/:tenant/review`, query-based `?view=owner`, and subdomain routing)

---

## 4. Repository & Directory Structure (Product A Focus)

```text
Customer_Churn_Predection_NLP/
├── Backend/                              # Backend FastAPI Application
│   └── app/
│       ├── api/                          # REST API Endpoints & Logic
│       │   ├── routes.py                 # All HTTP route definitions
│       │   ├── service.py                # ReviewService orchestration
│       │   ├── generator.py              # Review & GM reply generation
│       │   ├── prompts.py                # Humanized prompt engineering
│       │   ├── validator.py              # Review grounding & safety validator
│       │   ├── llm_provider.py           # Multi-provider LLM abstraction
│       │   ├── svg_sanitizer.py          # Adversarially hardened SVG sanitizer
│       │   └── document_storage.py       # PDF/Asset tenant storage
│       ├── core/                         # Core Database & Security
│       │   ├── database/
│       │   │   ├── storage.py            # ReviewStore (SQLite WAL, queries, indexes)
│       │   │   └── migration.py          # Database migrations
│       │   ├── auth/
│       │   │   └── auth.py               # Password hashing, tokens, RBAC
│       │   ├── entitlements/
│       │   │   └── entitlements.py       # Feature flags ('review_manager', 'digital_card')
│       │   └── tenants/
│       │       ├── google_reviews.py     # Tenant configuration store
│       │       └── business_links.json   # Seed configs & Google review URLs
│       ├── models/                       # Machine Learning Models
│       │   ├── sentiment.py              # RoBERTa / DistilBERT Sentiment classifier
│       │   ├── sarcasm.py                # Sarcasm detection pipeline
│       │   └── model_loader.py           # Lazy model weight loader
│       ├── fusion/                       # NLP Fusion Engine
│       │   ├── engine.py                 # Multi-signal decision fusion
│       │   └── explainer.py              # Explains sentiment & sarcasm scores
│       └── main.py                       # FastAPI entrypoint, CORS, middleware
│
├── NastaGhar/frontend/                   # Product A Frontend Application
│   ├── src/
│   │   ├── components/
│   │   │   ├── CustomerReview.jsx        # Public diner-facing review journey
│   │   │   ├── OwnerPortal.jsx           # Owner admin console & QR studio
│   │   │   ├── VrajaAdmin.jsx            # Platform super-admin console
│   │   │   ├── RestaurantWorld.jsx       # Interactive 3D/Isometric restaurant scene
│   │   │   └── NastaGharRestaurantScene.jsx
│   │   ├── lib/
│   │   │   └── api.js                    # Authenticated fetch wrapper (apiFetch)
│   │   ├── App.jsx                       # Main routing & view switcher
│   │   ├── main.jsx                      # React 19 root mount
│   │   └── index.css                     # Global styles, variables & themes
│   ├── package.json                      # Frontend dependencies (React, Vite, qrcode)
│   └── vite.config.js                    # Vite bundler configuration
│
└── Project_Files/
    ├── Data/nasta-ghar/reviews.sqlite3   # Relational SQLite database
    ├── Scripts/backup_restore.py         # Hot WAL backup & restore utility
    └── Tests/                            # Complete automated test suite
        ├── test_database_tenant_optimization.py
        ├── test_multi_client_isolation.py
        ├── test_review_assistant.py
        └── test_svg_sanitization_security.py
```

---

## 5. How the Customer Review Flow Works (Diner Journey)

### 5.1 Scanning & Context Injection
1. The diner sits at a table and scans the custom tent card or sticker QR code.
2. The QR URL points to:
   ```text
   https://app.vraja.ai/b/<tenant_id>/review?table=Table+4
   ```
3. `CustomerReview.jsx` automatically parses:
   - `tenant_id` from the path (`/b/:tenant_id/review`) or query (`?business_id=...`).
   - `table_number` from `?table=Table+4`.
4. A session is initialized via `POST /api/reviews/session`, binding diner actions to that specific table without requiring them to log in or download an app.

### 5.2 Dynamic Aspect/Topic Selection
- The diner selects 1 to 5 stars.
- If 4 or 5 stars:
  - Topics configured by the restaurant owner (e.g., *Authentic Chai*, *Fast Service*, *Clean Tables*, *Breakfast Combos*) appear as clickable chips.
  - Diners can select a language: **English**, **हिंदी (Hindi)**, or **ગુજરાતી (Gujarati)**.
  - Diners can optionally type a short personal note (e.g., *"Loved the poha and ginger tea"*).

### 5.3 Review Candidate Generation
- `POST /api/reviews/ideas` triggers `ReviewGenerator.generate_ideas()`.
- The engine synthesizes 3 to 5 natural, authentic variations:
  - Variation 1: Food taste & quality emphasis.
  - Variation 2: Ambience & service hospitality emphasis.
  - Variation 3: Concise 1-liner with warm emojis.
- **Zero-Fabrication Policy:** The AI never invents dishes that were not selected or mentions false discounts. Word count is strictly kept between 15 and 45 words.

### 5.4 1-Click Clipboard Handoff
- The customer taps **"Select & Post Review"**.
- `copyTextToClipboard()` executes immediately during the user gesture to satisfy browser security requirements.
- The browser opens the restaurant's authentic Google Maps review dialog:
  ```text
  https://search.google.com/local/writereview?placeid=<PLACE_ID>
  ```
- The customer simply pastes into Google Reviews and hits submit.
- The conversion event `google_review_link_clicked` is logged to `analytics_events`.

### 5.5 Ethical Anti-Gating Policy (Google Review Compliance)
- If the customer taps 1, 2, or 3 stars:
  - The UI presents a friendly option: *"Tell Management Privately What Went Wrong"*.
  - **Crucial:** The option to *"Continue to Google Reviews anyway"* is **never hidden or blocked**. This ensures 100% compliance with Google's Anti-Review-Gating policy.

---

## 6. Standardized Multi-Tenant Owner Portal (`OwnerPortal.jsx`)

The Owner Portal is accessed at `/owner` or `/owner/:tenant_id`. Every restaurant client receives **the exact same standardized 5-section template**, navigation structure, and functionality. Only tenant-specific configuration and data vary dynamically.

> [!IMPORTANT]
> **Internal QR Application Separation Policy:**
> Restaurant clients MUST NOT have access to the QR Code Generator. QR generation, design, table numbering, and asset distribution are internal VRAJA AI operational responsibilities. The client-facing Owner Portal has NO QR tab or generator. Customers scan QR codes distributed by VRAJA AI pointing to `/review?table=Table+4&business_id=...`.

### 6.1 Section 1: Home (`home`)
- **Restaurant & Branch Header**: Displays restaurant name, branch location, category, and description.
- **Quick Performance Statistics**:
  - AI Review Generations (customer review drafts created).
  - Google Review Link Clicks (handoff journeys to Google Maps).
  - Customer Rating Overview (weighted average rating and total ratings count).
  - Private Feedback Summary (total tickets and open complaints count).
  - Conversion Rate % (`google_clicks / total_generations * 100`).
- **Operational Timing Insights**:
  - **Peak Usage Window**: Automatically calculated 1-hour window with highest digital review engagement (e.g., `13:00 – 14:00`).
  - **Busiest Day of Week**: Day with maximum recorded customer interaction (e.g., `Sunday`).
- **Factual Business Insights**: Synthesized dynamically and strictly from authentic database events.
- **Recent Customer Activity Feed**: Chronological timeline of the latest 10 customer interactions.
- **Customer Preview Action**: One-click preview launcher to inspect the diner flow.

### 6.2 Section 2: Review Setup (`setup`)
- **Restaurant Profile**: Business name, branch, category, description, and primary accent color.
- **Google Review URL / Place ID**: Destination URL with test-open verification.
- **Supported Languages Configuration**: Multi-language toggles:
  - English (`english`)
  - Hindi (`hindi`)
  - Gujarati (`gujarati`)
- **Review Topic Keywords**: Tag chips for customer aspects (e.g. *Special Chai*, *Homestyle Breakfast*, *Clean Tables*, *Fast Billing*), with add and delete controls.

### 6.3 Section 3: Review Activity & Analytics (`activity`)
- **Data Integrity Disclaimers (Mandatory)**:
  - *Data Integrity Notice: Review-system usage measures digital interactions with our review assistant and does not represent restaurant dining footfall. Google Review link clicks represent customer journeys directed to Google Maps; verified published reviews require Google Business Profile API OAuth integration.*
  - Timezone badge indicating local aggregations (e.g. `Timezone: Asia/Kolkata`).
- **Timezone-Accurate Hourly Distribution**: 24-hour distribution bar chart (00:00 to 23:00 local time) highlighting peak hours.
- **Weekly Usage Distribution**: Monday through Sunday distribution highlighting the busiest day.
- **Monthly Engagement Trends**: Historical month-by-month event volume comparison (`YYYY-MM`).
- **Configurable Seasonal Analysis**: Hospitality seasons breakdown (`Summer`, `Monsoon`, `Autumn & Festive`, `Winter`) with proportion bars.
- **Year-Specific Festival Comparisons**: Year-mapped festival periods (Holi, Navratri, Diwali & New Year, Christmas) compared against non-festival baselines, with explicit `insufficient_historical_data` disclosures when event volume is low.
- **Customer Rating Distribution**: Breakdown of 5★, 4★, 3★, 2★, and 1★ customer ratings.

### 6.4 Section 4: Private Feedback Inbox (`feedback`)
- **Status Summary Cards**: Total Tickets, Open Complaints (amber), Escalated / Urgent (red), Resolved (green).
- **Status Filter Bar**: `All`, `Open`, `Escalated`, `Resolved`.
- **Ticket Cards**:
  - Ticket ID (`TICK-A1B2C3`).
  - Star rating badge.
  - Diner's written feedback note.
  - Selected aspect tags.
  - Associated table / source tag (e.g. `Table 4`, `Counter`, `Walk-in`).
  - Timestamp.
  - Guest contact information (phone/email or `Anonymous`).
  - Current status pill (`OPEN`, `ESCALATED`, `RESOLVED`).
  - Resolution Action Buttons: `✓ Mark Resolved`, `⚠️ Escalate`, `🔄 Re-open`. Persists via `PATCH /api/reviews/private-tickets/{ticket_id}/status`.

### 6.5 Section 5: Settings (`settings`)
- **Account & Security Information**: Email, display name, tenant identifier, membership role badge (`owner`, `manager`).
- **Profile Management**: Display name and account info.
- **Password Management**: Form to update owner/manager password requiring current password and new password confirmation (`POST /api/auth/change-password`).
- **Customer Experience Preview**: Quick launch button for guest flow testing.
- **Sign Out**: Clears session cookie and invalidates server token.
- The manager selects the rating and desired tone (*Gracious*, *Empathetic*, *Professional*).
- The AI runs sentiment analysis and generates a personalized, polished response for the manager to paste back into Google Business Profile.

---

## 7. Backend Architecture & Database Optimization

### 7.1 Database Schema (`reviews.sqlite3`)

Product A relies on the following core SQLite tables:

```sql
-- 1. Tenants (Multi-Tenant Master)
CREATE TABLE tenants (
    id TEXT PRIMARY KEY,
    business_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    platform TEXT NOT NULL DEFAULT 'google',
    review_url TEXT NOT NULL DEFAULT '',
    branch TEXT DEFAULT '',
    category TEXT DEFAULT 'Breakfast & Snacks',
    description TEXT DEFAULT '',
    topics_json TEXT DEFAULT '[]',
    primary_accent TEXT DEFAULT '#f97316',
    domain TEXT DEFAULT '',
    entitlements_json TEXT DEFAULT '["review_manager"]',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

-- 2. Analytics Events (Indexed for high-speed tenant retrieval)
CREATE TABLE analytics_events (
    event_id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    payload TEXT NOT NULL,
    tenant_id TEXT
);
CREATE INDEX idx_analytics_tenant_created ON analytics_events(tenant_id, created_at DESC);

-- 3. Private Feedback Tickets (Indexed for manager queries)
CREATE TABLE private_tickets (
    ticket_id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    payload TEXT NOT NULL,
    tenant_id TEXT
);
CREATE INDEX idx_tickets_tenant_created ON private_tickets(tenant_id, created_at DESC);

-- 4. Users & Multi-Tenant RBAC
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 1,
    is_platform_admin INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE tenant_memberships (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'manager',
    created_at REAL NOT NULL,
    UNIQUE(user_id, tenant_id)
);

CREATE TABLE sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    active_tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    revoked_at REAL,
    ip_address TEXT DEFAULT '',
    user_agent TEXT DEFAULT ''
);
```

### 7.2 Database Performance & WAL Mode
- All database connections enable SQLite **Write-Ahead Logging (WAL)**: `PRAGMA journal_mode=WAL`.
- **Zero Full-Table Scans:** Historical filtering using `json_extract(payload, '$.metadata.business_id')` was eradicated in Phase 1 Task 3. Queries for analytics and tickets now execute using composite indexes:
  - `list_events`: Uses `SEARCH analytics_events USING INDEX idx_analytics_tenant_created (tenant_id=?)`
  - `list_tickets`: Uses `SEARCH private_tickets USING INDEX idx_tickets_tenant_created (tenant_id=?)`
  - `ticket_count`: Uses `SEARCH private_tickets USING COVERING INDEX idx_tickets_tenant_created (tenant_id=?)`
- **Per-Tenant Retention Limits:**
  - `analytics_events`: Prunes oldest records past 2,000 *per tenant*.
  - `private_tickets`: Prunes oldest records past 5,000 *per tenant*.

---

## 8. Complete API Endpoint Reference (Product A)

### 8.1 Public Customer Endpoints (Rate Limited per Client IP)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/businesses/{business_id}/review-link` | Returns business name, Google review URL, and topic chips. |
| `POST` | `/api/reviews/session` | Starts an anonymous diner session bound to a table. |
| `POST` | `/api/reviews/events` | Logs review journey events (rating selected, clipboard copy, redirect). |
| `POST` | `/api/reviews/ideas` | Synthesizes 3–5 grounded candidate review drafts. |
| `POST` | `/api/reviews/generate` | Generates or polishes a single review draft. |
| `POST` | `/api/reviews/private-feedback` | Submits a private direct diner note to management. |

### 8.2 Protected Owner & Manager Endpoints (Requires Session Cookie)
| Method | Endpoint | Required Role | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/businesses/{business_id}/config` | `manager` | Updates business info, topics, accent color, and review URL. |
| `GET` | `/api/reviews/analytics` | `staff` | Returns conversion metrics, rating distribution, and recent activity feed. |
| `GET` | `/api/reviews/private-tickets` | `manager` | Returns list of diner feedback tickets for the tenant. |
| `POST` | `/api/reviews/manager-reply` | `manager` | Generates AI response for a guest Google review. |

### 8.3 Authentication & Session Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Authenticates owner/manager and issues signed HTTP-only session cookie. |
| `GET` | `/api/auth/session` | Verifies active session and returns user memberships & active tenant. |
| `POST` | `/api/auth/switch-tenant` | Changes the active tenant context for a multi-unit owner. |
| `POST` | `/api/auth/logout` | Revokes the current session token. |

---

## 9. Developer Onboarding & Quickstart Guide

### 9.1 Prerequisites
- **Python:** 3.12.x
- **Node.js:** 20.x or 22.x LTS with `npm`
- **Git**

### 9.2 Running the Backend Locally
1. Activate the Python virtual environment:
   ```bash
   source .venv/bin/activate
   ```
2. Install backend dependencies (if needed):
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI development server:
   ```bash
   uvicorn Backend.app.main:app --reload --port 8000
   ```
4. Access the interactive OpenAPI documentation:
   ```text
   http://localhost:8000/docs
   ```

### 9.3 Running Product A Frontend
1. Navigate to the frontend directory:
   ```bash
   cd NastaGhar/frontend
   ```
2. Install frontend dependencies:
   ```bash
   npm install
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```
4. Open the application:
   - **Customer Review Experience:** `http://localhost:5173/review?table=Table+4`
   - **Owner Portal & QR Studio:** `http://localhost:5173/owner`
   - **Super Admin Console:** `http://localhost:5173/admin`

### 9.4 Default Developer Credentials
- **Default Owner Email:** `owner@nastaghar.com`
- **Default Owner Password:** `Owner123!`
- **Platform Super Admin:** Pre-configured in database with full entitlements across all tenants.

---

## 10. Automated Testing & Quality Assurance

### 10.1 Running Backend Pytest Suite
Execute all automated backend tests:
```bash
.venv/bin/pytest Project_Files/Tests/ -v
```
*Current test status: **178 passing, 4 skipped, 0 failures**.*

### 10.2 Targeted Product A Test Suites
```bash
# Test Review Store & Assistant persistence
.venv/bin/pytest Project_Files/Tests/test_review_assistant.py -v

# Test Multi-Client Tenant Isolation
.venv/bin/pytest Project_Files/Tests/test_multi_client_isolation.py -v

# Test Database Index Optimization & Idempotent Backfill
.venv/bin/pytest Project_Files/Tests/test_database_tenant_optimization.py -v

# Test Hot WAL Backup & Restore Integrity
.venv/bin/pytest Project_Files/Tests/test_backup_restore.py -v
```

### 10.3 Building Frontend for Production
Always verify that the production build succeeds before committing code changes:
```bash
npm --prefix NastaGhar/frontend run build
```

---

## 11. Current Status & Future Development Roadmap for Product A

### 11.1 Completed & Production-Ready Features
- ✅ Multi-tenant customer review flow with aspect chips and English/Hindi/Gujarati synthesis.
- ✅ Dynamic QR Code Generator with Table, Counter, and Receipt presets, plus PNG export.
- ✅ Google Anti-Gating compliance with separate private feedback ticket inbox.
- ✅ AI Manager Reply Generator with tone and sentiment adjustment.
- ✅ Enterprise SQLite database with WAL mode, composite indexes, and zero `json_extract` table scans.
- ✅ Hot database online backup and restore verification scripts.
- ✅ Clean production builds for React 19 / Vite 8 frontend.

### 11.2 What Remains to be Developed (Product A Roadmap)
1. **Batch QR PDF Export:** Ability to download a single, formatted PDF containing pre-styled printable tent cards for all restaurant tables (e.g., Tables 1 to 20 on A4 paper) in one click.
2. **SMS / WhatsApp Review Escalation:** Real-time push alert or WhatsApp notification to the restaurant manager when a negative private feedback ticket is submitted.
3. **Google Business Profile OAuth API Integration:** Direct API sync to pull verified Google reviews automatically and post manager replies straight to Google Maps without manual copy-pasting.
4. **Custom Language Voice-to-Text Input:** Allowing diners to speak their thoughts in Gujarati or Hindi, automatically transcribing into review ideas.
5. **Staff Tip & Performance Tracking:** Tagging waitstaff names to table QR codes to analyze which servers drive the highest guest satisfaction and reviews.

---

*This document serves as the single source of truth for VRAJA AI Product A. For cross-product integrations or questions regarding Product B (Digital Business Card), consult `Project_Files/Docs/Product_B/`.*
