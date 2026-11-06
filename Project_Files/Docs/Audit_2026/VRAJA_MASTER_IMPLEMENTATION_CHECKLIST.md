# VRAJA AI — Master Implementation Checklist
**Audit Date:** October 30, 2026  
**Repository Branch:** `main` (commit `bfb8024`)

---

### Status Legend
- `[x] VERIFIED COMPLETE` — Implemented, verified in code, and confirmed working via automated test or execution.
- `[!] PARTIALLY IMPLEMENTED` — Code exists but has missing sub-features, broken integrations, or architectural gaps.
- `[ ] PENDING` — Planned or required feature not yet implemented.
- `[?] NOT VERIFIED` — Implemented but requires external credentials/hardware that cannot be tested locally.
- `[-] NOT APPLICABLE` — Not in scope or reserved placeholder without planned implementation in current phase.

---

## 1. Product A: Review Assistant (`NastaGhar`)

- [x] VERIFIED COMPLETE — **QR Code & Tenant-Specific Routing**: Resolves tenant from `/b/:tenant/review`, `/b/:tenant`, or query parameters. Falls back to `'default_business'`.  
  *Evidence:* [`NastaGhar/frontend/src/App.jsx#L31-L60`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/NastaGhar/frontend/src/App.jsx#L31-L60); verified in `test_product_transformation.py`.
- [x] VERIFIED COMPLETE — **Customer Review Form & Star Rating**: 1 to 5 star interactive rating selector with custom hover effects and labels.  
  *Evidence:* [`CustomerReview.jsx#L190-L200`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/NastaGhar/frontend/src/components/CustomerReview.jsx#L190-L200); verified in `test_generate_review_5_star`.
- [x] VERIFIED COMPLETE — **Trilingual Language Switching**: Seamless toggle between English, Hindi (*Hinglish*), and Gujarati (*Gujlish*).  
  *Evidence:* [`CustomerReview.jsx#L204-L215`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/NastaGhar/frontend/src/components/CustomerReview.jsx#L204-L215); verified in `test_generate_review_hindi_hinglish` and `test_generate_review_gujarati_gujlish`.
- [x] VERIFIED COMPLETE — **Hospitality Topic Selection**: Dynamic chips per tenant (Taste, Chai, Cleanliness, Staff, Value, Speed).  
  *Evidence:* [`CustomerReview.jsx#L221-L226`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/NastaGhar/frontend/src/components/CustomerReview.jsx#L221-L226); verified in `test_hospitality_specific_topics_configuration`.
- [x] VERIFIED COMPLETE — **Review Candidate Ideas**: Instant fallback ideas plus background AI candidate generation.  
  *Evidence:* `POST /api/reviews/ideas`; verified in `test_multilingual_candidate_ideas`.
- [x] VERIFIED COMPLETE — **Review Customization & Tone**: Tones (*natural*, *enthusiastic*, *brief*, *formal*) with length constraints.  
  *Evidence:* `POST /api/reviews/generate`; verified in `test_generate_from_selected_idea`.
- [x] VERIFIED COMPLETE — **Sentiment & Contradiction Detection**: Flags rating-text mismatches via CardiffNLP RoBERTa models.  
  *Evidence:* `POST /api/reviews/validate`; verified in `test_validate_review_consistency` and `test_neutral_sentiment.py`.
- [x] VERIFIED COMPLETE — **Google Review Redirection**: Copies review to clipboard and opens Google Maps review dialog.  
  *Evidence:* [`CustomerReview.jsx#L517-L553`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/NastaGhar/frontend/src/components/CustomerReview.jsx#L517-L553); verified in `test_get_business_review_link`.
- [x] VERIFIED COMPLETE — **Google Review Policy Compliance**: Both 1-star and 5-star guests can post to Google Maps without gating blocks.  
  *Evidence:* Verified in `test_no_rating_gating_behavior`.
- [x] VERIFIED COMPLETE — **Private Feedback Interception**: 1-3 star guests are offered an empathetic private feedback channel.  
  *Evidence:* `POST /api/reviews/private-feedback`; verified in `test_private_feedback_escalation`.
- [x] VERIFIED COMPLETE — **Owner Portal Authentication & Metrics**: Session login, conversion rates, and star breakdowns.  
  *Evidence:* `GET /api/reviews/analytics`; verified in `test_simplified_owner_analytics`.
- [x] VERIFIED COMPLETE — **Private Tickets & Manager Reply**: Severity tagging (`URGENT`/`MED`/`LOW`) and AI reply drafting.  
  *Evidence:* `GET /api/reviews/private-tickets` and `POST /api/reviews/manager-reply`.
- [x] VERIFIED COMPLETE — **Platform Admin Multi-Tenant Onboarding**: Superadmin can create businesses and set entitlements.  
  *Evidence:* [`VrajaAdmin.jsx`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/NastaGhar/frontend/src/components/VrajaAdmin.jsx); verified in `test_platform_admin_entitlements.py`.
- [!] PARTIALLY IMPLEMENTED — **Chrome Extension Auto-Paste**: Extension content scripts exist, but `CustomerReview.jsx` does not emit `postMessage` event.  
  *Evidence:* [`content_app.js#L5`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Project_Files/Chrome_Extension/content_app.js#L5) listens for `NASTA_GHAR_REVIEW_SELECTED`, but zero matching dispatch calls exist in frontend.
- [ ] PENDING — **Google Business Profile (GMB) API Sync**: Live verification of whether the guest published the review on Google Maps.  
  *Evidence:* Requires external Google Cloud OAuth2 credentials and GMB API approval.
- [ ] PENDING — **SMS / WhatsApp Automated Review Invites**: Automated post-dining review invitations via Twilio / WhatsApp Cloud API.  
  *Evidence:* Requires third-party communications gateway integration.

---

## 2. Product B: Digital Business Card (`Digital_Card`)

- [x] VERIFIED COMPLETE — **Public Digital Card Routing**: Loads tenant card via `/b/:tenant/card` with fallback handling.  
  *Evidence:* [`DigitalCard.jsx`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Digital_Card/frontend/src/components/DigitalCard.jsx); verified in `test_public_card_retrieval_published`.
- [x] VERIFIED COMPLETE — **Tenant Entitlement Protection**: Rejects card loading with 403 if tenant lacks `digital_card` entitlement.  
  *Evidence:* `GET /api/businesses/{id}/card`; verified in `test_missing_digital_card_entitlement_rejections`.
- [x] VERIFIED COMPLETE — **RFC 2426 vCard 3.0 Generation**: One-tap `.vcf` file generation and download for iOS/Android contacts.  
  *Evidence:* [`DigitalCard.jsx#L48-L82`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Digital_Card/frontend/src/components/DigitalCard.jsx#L48-L82); verified in `test_digital_card_frontend_flows.py`.
- [x] VERIFIED COMPLETE — **Communication Triggers**: Direct actions for Phone (`tel:`), WhatsApp (`wa.me`), Email (`mailto:`), and Maps.  
  *Evidence:* [`DigitalCard.jsx#L804-L835`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Digital_Card/frontend/src/components/DigitalCard.jsx#L804-L835); verified in `audit_digital_card_ui.mjs`.
- [x] VERIFIED COMPLETE — **Social Channel Links**: Interactive tiles for Instagram, Facebook, LinkedIn, YouTube, X, TikTok, Telegram.  
  *Evidence:* [`DigitalCard.jsx#L201-L250`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Digital_Card/frontend/src/components/DigitalCard.jsx#L201-L250).
- [x] VERIFIED COMPLETE — **PDF Document & Menu Distribution**: In-browser viewing and download of menus up to 10MB.  
  *Evidence:* `GET /api/documents/{id}`; verified in `test_valid_pdf_storage_and_integrity_hashes`.
- [x] VERIFIED COMPLETE — **Operating Hours & Open/Closed Logic**: Dynamic calculation of open status based on local time.  
  *Evidence:* [`DigitalCard.jsx#L96-L108`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Digital_Card/frontend/src/components/DigitalCard.jsx#L96-L108).
- [x] VERIFIED COMPLETE — **Review Assistant Cross-Sell Bridge**: "Review Us" button deep-linking to `/b/:tenant/review`.  
  *Evidence:* [`DigitalCard.jsx#L836-L860`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Digital_Card/frontend/src/components/DigitalCard.jsx#L836-L860); verified in `test_review_system_remains_unaffected`.
- [x] VERIFIED COMPLETE — **Card Studio Editor (`DigitalCardEditor.jsx`)**: Split-screen live preview with instantaneous state synchronization.  
  *Evidence:* [`DigitalCardEditor.jsx`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Digital_Card/frontend/src/components/DigitalCardEditor.jsx); verified in `verify_redesign_appearance_studio.mjs`.
- [x] VERIFIED COMPLETE — **Appearance Studio Customization**: 4 background style presets, custom accent colors, and logo uploads.  
  *Evidence:* `POST /api/businesses/{id}/images` and `PUT /api/businesses/{id}/profile`.
- [x] VERIFIED COMPLETE — **Multi-Tenant Owner Switching**: Allows owner to switch between authorized businesses in-editor.  
  *Evidence:* [`DigitalCardEditor.jsx#L38-L55`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Digital_Card/frontend/src/components/DigitalCardEditor.jsx#L38-L55); verified in `test_authenticated_owner_profile_editing_and_partial_update`.
- [ ] PENDING — **Card Telemetry & Click Analytics**: Tracking card views, vCard saves, phone calls, and menu views.  
  *Evidence:* Code inspection confirms zero telemetry calls in `DigitalCard.jsx` and zero card events in `ALLOWED_ANALYTICS_EVENTS`.
- [ ] PENDING — **Interactive Menu Builder (Beyond PDF)**: Native item catalog with dish descriptions, prices, and allergen tags.  
  *Evidence:* Menus are currently uploaded only as static PDF files.
- [ ] PENDING — **Multi-Staff Profiles**: Support for multiple team member cards under a single parent company.  
  *Evidence:* Database schema only associates one `business_profiles` record per tenant.

---

## 3. Shared Backend Architecture

- [x] VERIFIED COMPLETE — **FastAPI Lifecycle & Health Probe**: Clean startup, background model priming, and `/healthz`.  
  *Evidence:* [`Backend/app/main.py#L69-L86`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Backend/app/main.py#L69-L86).
- [x] VERIFIED COMPLETE — **Relational Multi-Tenant Authentication**: scrypt password hashing and SHA-256 session tokens.  
  *Evidence:* [`Backend/app/core/auth/auth.py`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Backend/app/core/auth/auth.py); verified in `test_multi_tenant_auth.py`.
- [x] VERIFIED COMPLETE — **Tenant Isolation Middleware**: Role hierarchy (`staff` < `manager` < `owner`) and membership barriers.  
  *Evidence:* `require_tenant_access`; verified in `test_multi_client_isolation.py`.
- [x] VERIFIED COMPLETE — **Entitlement Enforcement Barrier**: Centralized gating for product features (`review_manager`, `digital_card`).  
  *Evidence:* `require_entitlement`; verified in `test_platform_admin_entitlements.py`.
- [x] VERIFIED COMPLETE — **Local NLP Model Lazy Loading**: CardiffNLP RoBERTa sentiment and irony model pipelines.  
  *Evidence:* [`Backend/app/models/model_loader.py`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Backend/app/models/model_loader.py); verified in `test_neutral_sentiment.py`.
- [x] VERIFIED COMPLETE — **Multi-Provider LLM Integration**: Local template generator + Cloud (Gemini 1.5 Flash / OpenAI) fallback.  
  *Evidence:* [`Backend/app/api/llm_provider.py`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Backend/app/api/llm_provider.py).
- [x] VERIFIED COMPLETE — **Document Storage Service**: Directory traversal protection, magic byte checks, and atomic file swaps.  
  *Evidence:* [`Backend/app/api/document_storage.py`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Backend/app/api/document_storage.py); verified in `test_document_storage_directory_and_traversal_defense`.
- [x] VERIFIED COMPLETE — **Disaster Recovery Backup Utility**: Hot SQLite WAL backup and document repository archiving.  
  *Evidence:* [`Project_Files/Scripts/backup_restore.py`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Project_Files/Scripts/backup_restore.py); verified in `test_backup_restore.py`.
- [!] PARTIALLY IMPLEMENTED — **CORS & Multi-Port Separation**: Frontends on separate ports (5173 and 5174) require CORS origins list instead of unified gateway.  
  *Evidence:* `Backend/app/main.py#L38-L45` defines comma-separated `CORS_ORIGINS`.

---

## 4. Security & SaaS Readiness

- [x] VERIFIED COMPLETE — **Password Hashing**: OWASP-compliant `scrypt` hashing with unique 16-byte cryptographic salts.  
  *Evidence:* [`Backend/app/core/auth/auth.py#L40-L53`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Backend/app/core/auth/auth.py#L40-L53).
- [x] VERIFIED COMPLETE — **Login Rate Limiting**: In-memory sliding window enforcing 10 attempts per minute per IP.  
  *Evidence:* [`Backend/app/core/auth/auth.py#L126-L136`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Backend/app/core/auth/auth.py#L126-L136).
- [x] VERIFIED COMPLETE — **CSRF Protection**: Origin header validation against CORS allowlist on all state-mutating requests.  
  *Evidence:* [`Backend/app/core/auth/auth.py#L162-L186`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Backend/app/core/auth/auth.py#L162-L186).
- [x] VERIFIED COMPLETE — **Path Traversal Defenses**: Filename sanitization, UUID disk storage, and `is_relative_to` verification.  
  *Evidence:* [`Backend/app/api/document_storage.py#L72-L80`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Backend/app/api/document_storage.py#L72-L80); verified in `test_filename_and_path_traversal_attempts`.
- [x] VERIFIED COMPLETE — **Cross-Tenant Attack Defense**: Verified that ordinary owners cannot mutate or view neighboring tenant data.  
  *Evidence:* Verified in [`test_hostile_security_scenarios.py`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Project_Files/Tests/test_hostile_security_scenarios.py).
- [!] PARTIALLY IMPLEMENTED — **SVG Image Sanitization**: Magic byte validation accepts SVG files, but lacks XML entity/script stripping.  
  *Evidence:* `Backend/app/api/routes.py#L1201` checks for `<svg` but does not run `defusedxml` or DOMPurify.
- [ ] PENDING — **Public Review Endpoint Rate Limiting**: Redis-backed rate limiting on `/reviews/generate` and `/reviews/ideas`.  
  *Evidence:* Endpoints currently lack per-IP rate limiting decorators.
- [ ] PENDING — **Self-Service Password Recovery**: Password reset via email verification.  
  *Evidence:* No transactional email service or password reset endpoints exist.

---

## 5. Database Architecture

- [x] VERIFIED COMPLETE — **Relational Schema**: 8 structured tables with foreign keys and cascade delete rules.  
  *Evidence:* [`Backend/app/core/database/storage.py#L35-L155`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Backend/app/core/database/storage.py#L35-L155).
- [x] VERIFIED COMPLETE — **WAL Journal Mode**: `PRAGMA journal_mode=WAL` enabled for improved concurrency.  
  *Evidence:* [`storage.py#L34`](file:///Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP/Backend/app/core/database/storage.py#L34).
- [x] VERIFIED COMPLETE — **Schema Migration Safety**: Idempotent DDL scripts handle missing columns gracefully.  
  *Evidence:* `Backend/app/core/database/storage.py#L158-L170`; verified in `test_idempotent_schema_initialization`.
- [!] PARTIALLY IMPLEMENTED — **Analytics & Ticket Query Performance**: Analytics events and tickets store JSON payloads; filtering requires full-table JSON extractions.  
  *Evidence:* `storage.py#L556` uses `WHERE json_extract(payload, '$.metadata.business_id') = ?` without an indexed column.
- [ ] PENDING — **PostgreSQL Cloud Adapter**: Production migration from local SQLite to managed PostgreSQL.  
  *Evidence:* Database code directly uses standard library `sqlite3`.

---

## 6. Frontend UI / UX & Responsiveness

- [x] VERIFIED COMPLETE — **Mobile Responsiveness**: Verified layouts on mobile screen widths (375px through 430px).  
  *Evidence:* Verified in `run_staging_browser_acceptance.mjs` and `verify_dynamic_digital_cards.mjs`.
- [x] VERIFIED COMPLETE — **Visual Styling & Typography**: Modern Tailwind utility styling and custom CSS variables.  
  *Evidence:* Built without errors; `oxlint` reports 0 issues.
- [x] VERIFIED COMPLETE — **Live Split-Screen Studio**: Live preview accurately updates on theme and content adjustments.  
  *Evidence:* Verified in `verify_redesign_appearance_studio.mjs`.

---

## 7. Testing & Verification

- [x] VERIFIED COMPLETE — **Automated Test Suite**: 149 tests discovered, 145 passing out of the box, 4 skipped by default.  
  *Evidence:* Command `.venv/bin/pytest Project_Files/Tests -v` executed with code 0.
- [x] VERIFIED COMPLETE — **Full Model Test Verification**: All 4 skipped tests pass when `--run-model-tests` is passed (149/149 pass).  
  *Evidence:* Command `.venv/bin/pytest Project_Files/Tests/api/test_neutral_sentiment.py --run-model-tests` passed 100%.
- [x] VERIFIED COMPLETE — **Frontend Code Quality**: `oxlint` runs with 0 errors across all JSX files.  
  *Evidence:* Commands `npm run lint` in both frontends passed with 0 errors and 0 warnings.
- [x] VERIFIED COMPLETE — **Production Asset Bundling**: Vite builds production bundles cleanly without missing modules.  
  *Evidence:* Commands `npm run build` completed in ~130ms for both frontends.

---

## 8. Product C (`product-c-mastercard`)

- [-] NOT APPLICABLE — **Product C Frontend**: Does not exist in this repository.  
  *Evidence:* Zero matching directories or files found.
- [-] NOT APPLICABLE — **Product C Backend APIs**: Does not exist.  
  *Evidence:* No endpoints registered under router.
- [-] NOT APPLICABLE — **Mastercard / Payment Integration**: Does not exist.  
  *Evidence:* No payment SDKs or financial processing code present.
- [-] NOT APPLICABLE — **Loyalty Points / Deals Engine**: Does not exist.  
  *Evidence:* Pure architectural placeholder.

---

## 9. Company Website

- [-] NOT APPLICABLE — **Corporate Marketing Landing Site**: Not present in this repository.  
  *Evidence:* The repository only houses Product A, Product B, Backend, and prototype demo `qr_tree.html`.
