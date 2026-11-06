# VRAJA AI — PERMANENT AGENT INSTRUCTIONS & ARCHITECTURAL INVARIANTS

> **CRITICAL NOTICE FOR ALL AI CODING AGENTS AND DEVELOPERS:**  
> This file defines the permanent architectural rules, invariants, and operational boundaries for the VRAJA AI multi-tenant SaaS repository (`tkacha467/Customer_Churn_Predection_NLP`).  
> All future coding tasks, refactorings, and feature implementations MUST strictly adhere to these guidelines.

---

## 1. Product A Owner Portal Invariant: Fixed 5-Section Standard

Every restaurant client receives **exactly the same** Owner Portal template, component structure, navigation, features, and user experience. Never create per-client portal forks or variants.

The client-facing Owner Portal (`NastaGhar/frontend/src/components/OwnerPortal.jsx`) must contain **only** these five sections:

1. **Home**
   - Welcome section with restaurant name, branch, and category.
   - Performance statistics cards: Total AI review generations, Google Review link clicks, Customer rating overview, Private feedback summary, Conversion rate %.
   - Peak review-system usage time window (e.g. `13:00 – 14:00`).
   - Busiest day of week (e.g. `Wednesday` or `Sunday`).
   - Key business insights (derived strictly from factual data).
   - Recent customer activity feed (chronological timeline of latest interactions).

2. **Review Setup**
   - Restaurant profile (name, branch, category, description, logo preview).
   - Google Review URL / Place ID validation and test launcher.
   - Supported languages configuration (English, Hindi, Gujarati).
   - Review topic keywords and aspect chips management.
   - Primary accent color customization.

3. **Review Activity & Analytics**
   - Timezone-accurate hourly usage analysis (24-hour distribution in local restaurant timezone).
   - Weekly usage analysis (Monday through Sunday distribution identifying busiest day).
   - Monthly engagement trends.
   - Configurable seasonal analysis (Summer, Monsoon, Autumn & Festive, Winter).
   - Year-specific festival and special occasion comparisons with baseline disclosure.
   - Customer engagement calendar heatmap.
   - Customer rating distribution (5★ to 1★).
   - Mandatory data integrity disclaimers prominently displayed.

4. **Private Feedback Inbox**
   - Dedicated management inbox for direct diner complaints and notes.
   - Status filters: `All`, `Open`, `Escalated`, `Resolved`.
   - Displays Ticket ID, Customer Rating, Diner Note, Selected Aspects, Table/Source, Timestamp, Guest Contact.
   - Status transitions (`OPEN`, `ESCALATED`, `RESOLVED`) tracked and updated via API (`PATCH /api/reviews/private-tickets/{ticket_id}/status`).

5. **Settings**
   - Account email, display name, tenant identifier, and membership role badge.
   - Profile management.
   - Password management (`POST /api/auth/change-password`).
   - Customer review flow preview launcher.
   - Secure sign-out.

---

## 2. QR System Separation — Internal Only

- **No Client-Facing QR Controls**: Restaurant clients MUST NOT have access to QR code generation, QR downloading, or QR configuration in `OwnerPortal.jsx`.
- **Standalone Internal Tool**: VRAJA AI's QR management system is a separate internal tool operated by the internal VRAJA AI team.
- **Do Not Merge with Super Admin**: Do NOT merge internal QR generation into `VrajaAdmin.jsx`.
- **Preserve Review URLs**: The customer review endpoints (`/review?table=Table+4&business_id=...` and `/b/:tenant/review?table=...`) must remain fully functional so customers can scan QR codes supplied by VRAJA AI.

---

## 3. Analytics Data Integrity Rules

1. **No Footfall Representation**: Review-system usage reflects digital review assistant interactions and must **never** be represented as actual dining footfall.
2. **No False Review Confirmation**: Google Review link clicks represent customer journeys directed to Google Maps; they must **never** be represented as confirmed published reviews.
3. **Metric Categorization**: Always distinguish:
   - QR Session Scans (`session_created`).
   - AI Review Drafts Generated (`review_generation_completed` / `review_ideas_generated`).
   - Selected Ratings (`rating`).
   - Google Review Link Clicks (`google_review_link_clicked` / `google_maps_redirect`).
   - Verified Published Reviews (only if independently verified through official Google Business Profile API OAuth integration).
   - Private Feedback Submissions (`private_feedback_submitted`).
4. **Timezone Accuracy**: All hourly, daily, and monthly aggregations must be computed in the tenant's configured timezone (default `Asia/Kolkata`), never raw UTC.
5. **Festival Baselines**: Festival comparisons must use year-specific festival dates (e.g. 2025, 2026, 2027 calendar dates). When historical event volume is insufficient for statistical significance, the system must clearly display an `insufficient_historical_data` disclosure.
6. **No Data Fabrication**: Never fabricate synthetic historical analytics or hallucinate business metrics.

---

## 4. Multi-Tenant Database & Performance Standards

1. **Strict Tenant Scoping**: All queries for analytics and private tickets must filter on indexed `tenant_id` columns:
   - `analytics_events` indexed by `(tenant_id, created_at DESC)`.
   - `private_tickets` indexed by `(tenant_id, created_at DESC)`.
2. **Zero Table Scans**: Never use `json_extract(payload, '$.metadata.business_id')` or `json_extract(payload, '$.business_id')` in SQL `WHERE` clauses.
3. **Unassigned Records**: Any historical record with missing or unresolvable tenant ownership must remain `tenant_id IS NULL`. Never reassign unmapped records to `default_business`.
4. **SQLite WAL Mode**: Always preserve SQLite Write-Ahead Logging (`PRAGMA journal_mode=WAL`) and hot online backup compatibility (`scripts/backup_restore.py`).

---

## 5. Security & Testing Verification Invariants

Before completing any task or claiming success:
1. All automated backend tests must pass without regressions:
   ```bash
   .venv/bin/pytest Project_Files/Tests/
   ```
2. Both frontend production builds must succeed with zero errors:
   ```bash
   npm --prefix NastaGhar/frontend run build
   npm --prefix Digital_Card/frontend run build
   ```
3. Preserve all documentation integrity and keep specifications synchronized.
