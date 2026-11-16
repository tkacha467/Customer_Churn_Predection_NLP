# PRODUCT A — DYNAMIC INDUSTRY TEMPLATE MANAGEMENT SYSTEM
## PHASE 1: SOURCE AUDIT & ARCHITECTURAL IMPLEMENTATION PLAN
**Project:** VRAJA AI / NastaGhar (Product A)  
**Date:** November 13, 2026  
**Auditor:** Senior Software Architect & Product Reliability Specialist  
**Repository Branch:** `main` (Working tree clean)

---

## 1. Executive Summary & Protection Rule Compliance

In strict compliance with the **Absolute Project Protection Rules**:
- **Product B (Digital Business Card) is 100% OUT OF SCOPE and READ-ONLY.**
  - `Digital_Card/` frontend will not be modified or refactored.
  - Shared backend routes for Product B (`/api/business-profile/...`, `/api/documents/...`, `/api/businesses/{id}/card/qr-info`) and database tables (`business_profiles`, `tenant_documents`) will remain completely untouched.
  - Product B automated tests (`Project_Files/Tests/test_profile_and_document_apis.py`) pass 100% and will be rerun as regression safety gates.
- **Product A (NastaGhar / VRAJA Review Studio)** will receive a database-driven, multi-tenant Dynamic Industry Template Management System.
- **Phase 1 Execution Only:** This audit documents existing capabilities, identified gaps, schema design, API contracts, frontend architecture, and verification plans. **No implementation code has been written.** Implementation will commence only upon explicit user approval.

---

## 2. Existing Repository Architecture Audit

### 2.1. File System & Component Layout

| Area | Current Path | Status & Role |
|---|---|---|
| **Product A Customer Frontend** | `NastaGhar/frontend/src/components/CustomerReview.jsx` | Active single-business review UI. Currently toggles between hardcoded NastaGhar branding (`<RestaurantWorld />`) and a minimal emoji card. |
| **Product A Admin Console** | `NastaGhar/frontend/src/components/VrajaAdmin.jsx` | Platform admin dashboard managing tenants, onboarding, packages, and entitlements. Currently lacks a Template Management section. |
| **Product A Admin Design System** | `NastaGhar/frontend/src/components/admin/` | Contains `AdminHeader`, `AdminSidebar`, `AdminTable`, `AdminModal`, `AdminCard`, `tokens.js`. Reusable for Template Library. |
| **Product B Frontend (Protected)** | `Digital_Card/frontend/` | **READ-ONLY.** Independent React application on port 5174 for Digital Business Cards. |
| **Shared FastAPI Backend** | `Backend/app/` | Single entry point `Backend.app.main:app`. Hosts all API routers, database managers, and LLM services. |
| **Database Engine** | `Backend/app/core/database/storage.py` | SQLite database with WAL mode (`ReviewStore`). Manages `tenants`, `users`, `sessions`, `analytics_events`, `private_tickets`, etc. |
| **Public Review Route** | `Backend/app/api/routes.py` (`/api/businesses/{id}/review-link`) | Returns public config (`business_name`, `category`, `topics`, `primary_accent`, `review_url`). |

### 2.2. Existing Database Schema Analysis

The SQLite database (`ReviewStore`) currently defines the following tables:
1. `tenants`: Stores `id`, `business_name`, `status`, `platform`, `review_url`, `branch`, `category`, `description`, `topics_json`, `primary_accent`, `domain`, `entitlements_json`, `created_at`, `updated_at`.
2. `users`: Stores admin/manager credentials, `is_platform_admin`.
3. `tenant_memberships`: Maps `user_id` to `tenant_id` with roles.
4. `sessions`: HMAC-signed authentication sessions.
5. `business_profiles`: Stores Digital Card (Product B) and shared profile fields (`logo_path`, `cover_image_path`, `tagline`, `opening_hours`, `contact_links`).
6. `tenant_documents`: Stores PDF menus and business documents.
7. `analytics_events`: Tracks QR scans, review selections, handoffs.
8. `private_tickets`: Stores direct customer private feedback.

**Audit Finding:** There are currently **NO tables** for `industries`, `templates`, `template_versions`, `business_template_assignments`, or template-specific `business_configurations`.

### 2.3. Product A Existing Review Capabilities (All Preserved)

The Product A customer review journey has seven verified features that will be preserved 100%:
1. **Automatic Browser Language Detection:** Uses `navigator.languages` with English fallback (`gu`, `hi`, `en`) and zero manual language-selection UI.
2. **AI Writing Assistant:** Up to 3 distinct styles (`Short & Natural`, `Detailed & Expressive`, `Simple & Personal`), strictly grounded in customer facts with zero hallucinations.
3. **Automatic Draft Recovery:** Session-scoped draft persistence isolated by business ID (`nastaGhar_draft_${businessId}`), with 2-hour TTL and cleanup on handoff.
4. **Fast-Loading Experience:** Vite bundle (335 kB uncompressed / 98 kB gzip) with instantaneous 0ms fallback suggestion rendering.
5. **Duplicate Submission Protection:** Submit locks (`isSubmittingPrivate`) and 60-second in-memory idempotency deduplication in `ReviewService`.
6. **Anonymous Private Feedback:** Direct feedback with optional contact info routed to `private_tickets`.
7. **Accessible Customer Experience:** Full keyboard navigation, `aria-pressed`, `aria-expanded`, and >= 44px touch targets.
8. **Google Anti-Gating Policy:** Unrestricted, equal Google Maps review handoff regardless of rating (1–5 stars).

---

## 3. Product B Dependency & Impact Assessment

| Product B Surface | Audit Finding | Safeguard & Impact |
|---|---|---|
| **Frontend Code (`Digital_Card/`)** | Zero shared frontend components between Product A and Product B. Both have separate `package.json`, `vite.config.js`, and component trees. | **Zero Impact.** `Digital_Card/` will not be opened or edited. |
| **Backend API Contracts** | Endpoints under `/api/business-profile/...`, `/api/documents/...`, and `/api/businesses/{id}/card/qr-info` belong to Product B. | **Zero Impact.** No Product B endpoints or schemas will be touched. |
| **Database Tables** | `business_profiles` and `tenant_documents` serve Product B. | **Zero Impact.** New template tables will be isolated with foreign keys to `tenants(id)`. Existing tables remain untouched. |
| **Regression Testing** | `test_profile_and_document_apis.py` contains 20 comprehensive Product B test cases. | **Safety Gate.** Will be executed after backend modifications to guarantee 100% pass rate. |

---

## 4. Target Architecture: Dynamic Industry Template System

```
                         ┌──────────────────────────────────────────────┐
                         │              VRAJA Admin UI                  │
                         │  (Template Library, Versioning, Assignment)  │
                         └──────────────────────┬───────────────────────┘
                                                │
                                    REST APIs (FastAPI)
                                                │
                         ┌──────────────────────▼───────────────────────┐
                         │           Template Registry Service          │
                         │      (Industry, Template & Version Ops)      │
                         └──────────────────────┬───────────────────────┘
                                                │
       ┌────────────────────────────────────────┴────────────────────────────────────────┐
       │                                        │                                        │
┌──────▼─────────────────────┐   ┌──────────────▼─────────────┐   ┌──────────────────────▼───────┐
│     SQLite Database        │   │   Public Config Endpoint   │   │     Product A Customer UI     │
│ - industries               │   │ GET /api/public/businesses │   │ (CustomerReview.jsx)         │
│ - templates                │   │     /{id}/config           │   │ - Dynamic Hero / Theme       │
│ - template_versions        │   │ - Resolves Tenant & Status │   │ - Component Registry         │
│ - template_assignments     │   │ - Merges Published Version │   │ - Industry Topics & Icons    │
│ - business_configurations  │   │ - Returns Safe Client DTO  │   │ - Preserved 7 Core Features  │
└────────────────────────────┘   └────────────────────────────┘   └──────────────────────────────┘
```

### 4.1. Supported Industries & Initial Template Catalog

| Industry | Slug | Initial Templates | Theme Accent & Aesthetic | Default Review Topics |
|---|---|---|---|---|
| **Restaurant** | `restaurant` | 1. `restaurant_classic`<br>2. `restaurant_premium`<br>3. `restaurant_minimal` | `#f97316` (Warm amber/orange), homestyle hero illustration / culinary pattern | Breakfast, Chai & Tea, Snacks, Taste & Flavour, Quick Service, Ambience, Cleanliness, Value |
| **Hotel** | `hotel` | 1. `hotel_classic`<br>2. `hotel_premium` | `#0f766e` (Deep teal / emerald), luxury hospitality hero banner | Room Comfort, Cleanliness, Staff & Hospitality, Check-in, Amenities, Breakfast, Location |
| **Salon** | `salon` | 1. `salon_classic`<br>2. `salon_premium` | `#be185d` (Rose / berry gold), elegant boutique wellness hero | Hair Styling, Skin Treatment, Stylist Care, Cleanliness & Hygiene, Ambience, Value, Punctuality |
| **Clinic** | `clinic` | 1. `clinic_classic`<br>2. `clinic_premium` | `#0284c7` (Clean clinical blue), healthcare reassuring hero | Doctor Consultation, Caring Staff, Wait Time, Clean Clinic, Treatment Explanation, Hygiene |

### 4.2. Database Schema Specification (Non-Destructive SQLite Migration)

```sql
-- 1. Industries catalog
CREATE TABLE IF NOT EXISTS industries (
    id TEXT PRIMARY KEY,                       -- e.g. 'restaurant', 'hotel', 'salon', 'clinic'
    name TEXT NOT NULL,                        -- e.g. 'Restaurant & Cafe'
    slug TEXT UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    icon TEXT DEFAULT '🍽️',
    status TEXT NOT NULL DEFAULT 'active',     -- 'active', 'inactive'
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

-- 2. Templates catalog
CREATE TABLE IF NOT EXISTS templates (
    id TEXT PRIMARY KEY,                       -- e.g. 'tmpl_restaurant_classic'
    industry_id TEXT NOT NULL REFERENCES industries(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,                        -- e.g. 'Restaurant Classic'
    slug TEXT UNIQUE NOT NULL,                 -- e.g. 'restaurant_classic'
    description TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'published',  -- 'draft', 'published', 'archived'
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

-- 3. Immutable Template Versions
CREATE TABLE IF NOT EXISTS template_versions (
    id TEXT PRIMARY KEY,                       -- e.g. 'ver_restaurant_classic_v1'
    template_id TEXT NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
    version TEXT NOT NULL,                     -- e.g. '1.0.0'
    configuration_json TEXT NOT NULL,          -- Validated JSON: layout, components, theme, content, topics
    schema_version TEXT NOT NULL DEFAULT '1.0',
    publication_status TEXT NOT NULL DEFAULT 'published', -- 'draft', 'published', 'archived'
    published_at REAL,
    created_at REAL NOT NULL,
    created_by TEXT DEFAULT 'system',
    UNIQUE(template_id, version)
);

-- 4. Business Template Assignments
CREATE TABLE IF NOT EXISTS business_template_assignments (
    id TEXT PRIMARY KEY,
    business_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    template_id TEXT NOT NULL REFERENCES templates(id) ON DELETE RESTRICT,
    template_version_id TEXT NOT NULL REFERENCES template_versions(id) ON DELETE RESTRICT,
    assigned_by TEXT DEFAULT 'admin',
    assigned_at REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',     -- 'active', 'superseded'
    UNIQUE(business_id, status)
);

-- 5. Business Configuration Overrides (Branding, Logo, Topics, Google Review URL)
CREATE TABLE IF NOT EXISTS business_configurations (
    id TEXT PRIMARY KEY,
    business_id TEXT UNIQUE NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    logo_url TEXT DEFAULT '',
    cover_image_url TEXT DEFAULT '',
    primary_accent TEXT DEFAULT '',
    custom_topics_json TEXT DEFAULT '[]',
    localized_content_json TEXT DEFAULT '{}',
    google_review_url TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

-- Indexes for lightning fast lookups (< 2ms)
CREATE INDEX IF NOT EXISTS idx_templates_industry ON templates(industry_id);
CREATE INDEX IF NOT EXISTS idx_template_versions_template ON template_versions(template_id);
CREATE INDEX IF NOT EXISTS idx_assignments_business ON business_template_assignments(business_id);
```

### 4.3. Template JSON Configuration Specification

Templates will be stored as validated structured JSON complying with the existing Product A component model:

```json
{
  "template_id": "restaurant_classic",
  "industry": "restaurant",
  "version": "1.0.0",
  "schema_version": "1.0",
  "layout": {
    "show_hero_banner": true,
    "hero_style": "ambient_scene",
    "compact_header": false,
    "rating_style": "stars",
    "topics_layout": "chips_grid",
    "suggestions_style": "cards_vertical",
    "show_private_feedback": true
  },
  "theme": {
    "primary_accent": "#f97316",
    "background_gradient": "linear-gradient(135deg, #f9731615, #f9731630)",
    "card_background": "#1e293b",
    "border_radius": "16px"
  },
  "approved_components": [
    "business_header",
    "rating_selector",
    "topics_selector",
    "personal_note",
    "review_suggestions",
    "custom_editor",
    "google_handoff",
    "private_feedback"
  ],
  "default_topics": [
    { "label": "Breakfast", "icon": "🍳" },
    { "label": "Chai & Tea", "icon": "☕" },
    { "label": "Snacks", "icon": "🥪" },
    { "label": "Taste & Flavour", "icon": "😋" },
    { "label": "Quick Service", "icon": "⚡" },
    { "label": "Cleanliness", "icon": "✨" },
    { "label": "Ambience", "icon": "🌟" },
    { "label": "Value for Money", "icon": "💰" }
  ],
  "supported_languages": ["en", "hi", "gu"],
  "localized_defaults": {
    "en": { "hero_subtitle": "Homestyle Breakfast & Chai" },
    "hi": { "hero_subtitle": "स्वादिष्ट नाश्ता और चाय" },
    "gu": { "hero_subtitle": "સ્વાદિષ્ટ નાસ્તો અને ચા" }
  }
}
```

---

## 5. Backend API Endpoints & Contracts

### 5.1. Admin Template Management Endpoints (Require Platform Admin Session)

1. `GET /api/platform/industries`  
   Returns list of active industries (`restaurant`, `hotel`, `salon`, `clinic`).
2. `GET /api/platform/templates?industry={slug}`  
   Returns templates filtered by industry (defaults to published, supports `status=all` for admins).
3. `GET /api/platform/templates/{template_id}`  
   Returns template metadata, version history, and active published configuration.
4. `POST /api/platform/templates`  
   Creates a new template draft.
5. `POST /api/platform/templates/{template_id}/versions`  
   Creates a new draft version for a template.
6. `POST /api/platform/templates/{template_id}/publish`  
   Publishes an approved version, making it immutable.
7. `POST /api/platform/templates/{template_id}/archive`  
   Safely archives a template.
8. `POST /api/platform/businesses/{business_id}/assign-template`  
   Assigns an approved published template and version to a business.
9. `PUT /api/platform/businesses/{business_id}/template-config`  
   Updates business branding, overrides, topics, and Google review URL.
10. `POST /api/platform/businesses/{business_id}/activate`  
    Validates assignment and activates the business for customer QR scans.

### 5.2. Public Customer Endpoint (Public Access, Cached & Sanitized)

`GET /api/public/businesses/{business_id}/config`
- **Security & Tenant Validation:**
  - Validates `business_id` format.
  - Verifies business exists and status is `active`.
  - Verifies entitlement `review_manager` is granted.
  - Resolves active template assignment and assigned published `template_version`.
- **Public DTO Response:** Returns ONLY safe, customer-facing fields (NO passwords, admin flags, or internal secrets):
  ```json
  {
    "business_id": "cafe_alpha",
    "business_name": "Cafe Alpha",
    "industry": "restaurant",
    "template_id": "restaurant_classic",
    "template_version": "1.0.0",
    "theme": {
      "primary_accent": "#f97316",
      "background_gradient": "linear-gradient(135deg, #f9731615, #f9731630)",
      "card_background": "#1e293b",
      "border_radius": "16px"
    },
    "layout": {
      "show_hero_banner": true,
      "hero_style": "ambient_scene",
      "show_private_feedback": true
    },
    "topics": [
      { "label": "Breakfast", "icon": "🍳" },
      { "label": "Chai & Tea", "icon": "☕" }
    ],
    "google_review_url": "https://search.google.com/local/writereview?placeid=...",
    "logo_url": "",
    "description": "Authentic homestyle breakfast and chai in Rajkot"
  }
  ```
- **Backward Compatibility:** Existing endpoint `GET /api/businesses/{business_id}/review-link` will be retained and enriched with resolved template data so legacy QR codes continue functioning without interruption.

---

## 6. Frontend Dynamic Template Architecture (Product A Only)

### 6.1. Component Architecture & Safe Component Registry

Inside `NastaGhar/frontend/src/`:
- **`components/CustomerReview.jsx`:**
  - Fetches public configuration from `/api/public/businesses/{business_id}/config` on mount.
  - Resolves assigned industry template.
  - Applies dynamic theme variables (`--primary-accent`, `--bg-gradient`, etc.).
  - Replaces hardcoded `if (businessId === 'default_business')` checks with dynamic industry renderer:
    - `restaurant`: Ambient illustration scene or culinary hero.
    - `hotel`: Hospitality luxury card hero.
    - `salon`: Boutique styling hero.
    - `clinic`: Clean wellness hero.
  - Feeds dynamic industry topics into topic chips while preserving all 7 customer experience features.
- **`components/admin/TemplateManager.jsx` (New Modular Component):**
  - Integrated into `VrajaAdmin.jsx`.
  - Provides:
    1. **Industry Filter Bar:** Restaurant, Hotel, Salon, Clinic.
    2. **Template Grid:** Cards showing template status, version, and preview trigger.
    3. **Live Interactive Preview Modal:** Toggles Mobile (390px) and Desktop (1200px) customer review view using representative mock data.
    4. **Business Assignment Panel:** Select business -> Pick approved template -> Customize branding -> Validate Google URL -> Activate.

---

## 7. Implementation Plan by Phases

### Phase 2: Database & Backend Foundation
1. **Schema Migration:** Create `Backend/app/core/database/template_storage.py` and migration logic in `migration.py` defining `industries`, `templates`, `template_versions`, `business_template_assignments`, and `business_configurations`.
2. **Seed Initial Templates:** Seed approved templates for Restaurant (Classic, Premium, Minimal), Hotel (Classic, Premium), Salon (Classic, Premium), Clinic (Classic, Premium).
3. **Template Service & Validation:** Implement `TemplateService` with Pydantic JSON schema validators for template configurations.
4. **API Endpoints:** Implement admin endpoints in `Backend/app/api/template_routes.py` and public endpoint `/api/public/businesses/{business_id}/config` in `Backend/app/api/routes.py`.
5. **Safety Tests:** Run backend unit tests and Product B regression tests.

### Phase 3: VRAJA Admin Template Management
1. **Admin UI Component:** Create `NastaGhar/frontend/src/components/admin/TemplateManager.jsx` reusing the existing admin design system (`AdminTable`, `AdminModal`, `AdminBadge`, `AdminHeader`, `AdminSidebar`).
2. **Tab Integration:** Integrate Template Manager into `VrajaAdmin.jsx` with industry filtering, template library grid, version badge, and interactive preview modal.
3. **Onboarding Extension:** Extend tenant onboarding and editing in `VrajaAdmin.jsx` to assign an approved industry template during business activation.

### Phase 4: Product A Customer Frontend Template Renderer
1. **Dynamic Config Loading:** Adapt `CustomerReview.jsx` to load resolved template config from `GET /api/public/businesses/{business_id}/config`.
2. **Dynamic Hero & Theme Application:** Dynamically apply industry hero banners and primary accent themes.
3. **Topic & Content Rendering:** Render industry-specific review topics with appropriate icons.
4. **Feature Preservation Verification:** Guarantee that smart language detection, 3 grounded styles, draft recovery, duplicate protection, anonymous feedback, and anti-gating remain 100% operational.

### Phase 5: Comprehensive Automated Testing & Validation
1. **Backend Tests:** New suite `Project_Files/Tests/test_dynamic_templates.py` testing industry filtering, template versioning, assignment, public config merging, and security boundaries.
2. **Product B Safety Regression:** Execute `test_profile_and_document_apis.py` to prove Product B is completely unaffected.
3. **Playwright E2E Verification:** Automated browser suite verifying:
   - Restaurant Classic vs Restaurant Premium rendering.
   - Hotel, Salon, and Clinic template customer views.
   - Admin industry filtering and preview modal.
   - Live QR review customer flow across viewports.

---

## 8. Summary of Proposed File Modifications

### New Files to be Created (Product A & Shared Backend Only):
1. `Backend/app/core/database/template_storage.py` — Database queries and tables for industries, templates, and assignments.
2. `Backend/app/api/template_schemas.py` — Pydantic schemas for templates, versions, and configurations.
3. `Backend/app/api/template_service.py` — Business logic for template management and configuration merging.
4. `NastaGhar/frontend/src/components/admin/TemplateManager.jsx` — Admin Template Library and preview interface.
5. `Project_Files/Tests/test_dynamic_templates.py` — Automated test suite for templates and assignments.

### Existing Files to be Modified:
1. `Backend/app/core/database/storage.py` — Register new template tables in `_init_db` (additive, non-destructive).
2. `Backend/app/api/routes.py` — Add `GET /api/public/businesses/{business_id}/config` and mount template router.
3. `NastaGhar/frontend/src/components/CustomerReview.jsx` — Connect to dynamic template renderer while preserving 7 core features.
4. `NastaGhar/frontend/src/components/VrajaAdmin.jsx` — Integrate Template Management tab.

### Files Explicitly Left Untouched:
- **ALL Product B files:** `Digital_Card/**` (Frontend, clients, configs).
- **Product B backend services:** `Backend/app/api/document_storage.py`.
- **Product B database tables:** `business_profiles`, `tenant_documents`.
- **Existing deployment & auth core:** `Backend/app/core/auth/auth.py`.

---

## 9. Current Status & Confirmation

- **Phase 1 Source Audit & Implementation Plan:** **COMPLETE.**
- **Code Changes:** **NONE.** No files have been modified.
- **Git State:** `main` working tree preserved.
- **Stop Gate:** Waiting for your explicit review and approval before proceeding to Phase 2 (Database and Backend Foundation).
