# VRAJA AI — PRODUCT A: OWNER PORTAL SPECIFICATION
## Permanent Multi-Tenant Architecture, Client Template Standard & Technical Reference

> **Document Status:** Permanent Standard & Single Source of Truth  
> **Target Products:** Product A (`NastaGhar` / Vraja Review Studio)  
> **Applicability:** All restaurant tenants, development teams, and AI coding agents.

---

## 1. Architectural Invariants

### 1.1 Universal Client Template
Every restaurant client receives the **identical Owner Portal template**, navigation structure, visual layout, and feature set. Never create customized or bespoke forks of `OwnerPortal.jsx` for individual clients.

Only tenant-specific variables change dynamically based on the authenticated session context:
- Restaurant Name (`business_name`)
- Branch Name (`branch`)
- Business Category (`category`)
- Restaurant Tagline & Description (`description`)
- Google Review URL / Place ID (`review_url`)
- Topic Keywords & Aspect Chips (`topics`)
- Primary Accent Color (`primary_accent`)
- Tenant-Scoped Analytics & Activity Events
- Tenant-Scoped Private Feedback Tickets

### 1.2 Fixed Five-Section Structure
The client-facing Owner Portal (`NastaGhar/frontend/src/components/OwnerPortal.jsx`) strictly contains **five sections**:

```text
├── 1. Home                     (KPIs, Peak Times, Busiest Day, Business Insights, Activity Feed)
├── 2. Review Setup             (Profile, Logo, Google URL, Topics, Supported Languages, Accent Color)
├── 3. Review Activity & Analytics (Hourly, Weekly, Monthly, Seasonal, Festival, Heatmap, Ratings)
├── 4. Private Feedback Inbox   (Ticket List, Star Rating, Diner Notes, Table Tag, Resolution Actions)
└── 5. Settings                 (Account Email, Role, Profile, Password Management, Preview)
```

---

## 2. QR System Separation Policy — Internal Only

1. **Exclusively Internal Responsibility**: QR code generation, design, table numbering, standee printing, and asset distribution are internal VRAJA AI operational workflows handled by VRAJA AI's team.
2. **Zero Client-Facing QR Access**:
   - The `Review QR` tab is permanently removed from `OwnerPortal.jsx`.
   - Restaurant clients have no controls to generate, customize, preview, or download QR codes.
3. **No Super Admin Merging**:
   - The QR generation system is maintained as a separate internal tool. It is **not** merged into `VrajaAdmin.jsx`.
4. **Preservation of Customer Review Flow**:
   - Customer review URLs supplied on physical tent cards (e.g. `https://app.vraja.ai/review?table=Table+4&business_id=<tenant>` or `https://app.vraja.ai/b/<tenant>/review?table=Table+4`) remain 100% functional.
   - The customer review journey seamlessly logs table parameters (`table_number`) without requiring the diner to install an app.

---

## 3. Detailed Section Specifications

### 3.1 Section 1: Home
- **Restaurant & Branch Header**: Displays `business_name`, `branch`, category tag, and greeting badge.
- **Performance KPI Cards**:
  - `AI Review Generations`: Total candidate review drafts created by diners.
  - `Google Review Clicks`: Customer journeys directed to the restaurant's Google Maps review dialog.
  - `Customer Rating Overview`: Weighted average rating (e.g. `5.0★`) and total customer ratings count.
  - `Private Feedback Summary`: Total feedback tickets and count of currently open complaints.
- **Operational Timing Insights**:
  - `Peak Usage Window`: Calculated 1-hour window with the highest recorded digital review interactions (e.g. `13:00 – 14:00`).
  - `Busiest Day of Week`: Day of the week with the maximum recorded activity (e.g. `Wednesday` or `Sunday`).
  - `Conversion Rate %`: `(google_clicks / total_generations) * 100`.
- **Factual Business Insights**: Dynamically synthesized facts derived exclusively from authentic database events (e.g. conversion rates, peak hours, top praised keywords, unresolved tickets).
- **Recent Customer Activity Feed**: Chronological feed of the 10 most recent customer interactions.
- **Customer Preview Action**: One-click preview launcher to inspect the customer journey as a guest.

### 3.2 Section 2: Review Setup
- **Business Profile**: Business name, branch location, business category, and welcome description.
- **Google Review URL / Place ID**:
  - Official Google Business Profile review destination URL.
  - Real-time link validation and `"Test Open in New Tab"` quick-action.
- **Supported Languages Configuration**:
  - Toggles for customer synthesis languages:
    - `🇬🇧 English (Default)`
    - `🇮🇳 हिंदी (Hindi)`
    - `🇮🇳 ગુજરાતી (Gujarati)`
- **Review Highlights & Topics**:
  - Dynamic chip list representing praise keywords (e.g. *Special Chai*, *Breakfast Combos*, *Clean Tables*, *Fast Service*).
  - Ability to add new keywords and delete existing ones.
- **Branding & Accent Color**:
  - Color picker and hex input updating the primary accent across customer UI.
- **Save Action**: Submits updates to `POST /api/businesses/{business_id}/config`.

### 3.3 Section 3: Review Activity & Analytics
- **Data Integrity Disclaimers (Mandatory)**:
  - *Data Integrity Notice: Review-system usage measures customer interactions with the digital review assistant and does not represent actual restaurant footfall. Google Review link clicks represent customer journeys directed to Google Maps; external verification of published reviews requires direct Google Business Profile API OAuth integration.*
  - Prominent display of the restaurant's local timezone (e.g. `Timezone: Asia/Kolkata`).
- **Timezone-Accurate Hourly Distribution**:
  - Visual 24-hour bar chart (00:00 to 23:00 local time) showing interaction volume.
  - Distinctly highlights the peak interaction hour.
- **Weekly Usage Distribution**:
  - Monday through Sunday distribution identifying the busiest day of the week.
- **Monthly Historical Trends**:
  - Month-by-month event volume comparison (`YYYY-MM`).
- **Configurable Seasonal Analysis**:
  - Categorizes events into regional seasons:
    - `Summer (Mar–Jun)`
    - `Monsoon (Jul–Sep)`
    - `Autumn & Festive (Oct–Nov)`
    - `Winter (Dec–Feb)`
  - Displays event counts and percentage proportions.
- **Year-Specific Festival Comparisons**:
  - Tracks specific festival date windows by year (e.g. Holi, Navratri, Diwali, New Year for 2025, 2026, 2027).
  - Compares festival daily rates against non-festival baselines.
  - **Data Disclosure**: When historical records are low (<15 total events or 0 festival events), explicitly flags `insufficient_historical_data: true` with notice `"Insufficient historical data for statistically significant comparison"`.
- **Customer Rating Distribution**:
  - Detailed breakdown of 5-star, 4-star, 3-star, 2-star, and 1-star selections.
- **Top Appreciated Highlights**:
  - Ranked list of most-selected dining aspects.

### 3.4 Section 4: Private Feedback Inbox
- **Header KPI Summary**: Total Tickets, Open Complaints (amber), Escalated / Urgent (red), Resolved (green).
- **Status Filters**: Tabs for `All`, `Open`, `Escalated`, and `Resolved`.
- **Ticket Cards**:
  - `Ticket ID` (e.g. `TICK-A1B2C3`).
  - `Table / Source Tag` (e.g. `Table 4`, `Counter`, `Walk-in`).
  - `Customer Rating` (visual star display).
  - `Feedback Details` (diner's unedited written message).
  - `Selected Aspects` (chips of highlighted issues/features).
  - `Guest Contact` (phone or email, or `Anonymous`).
  - `Status Badge` (`OPEN`, `ESCALATED`, `RESOLVED`).
- **Resolution Tracking Actions**:
  - `✓ Mark Resolved`: Sets ticket status to `RESOLVED`.
  - `⚠️ Escalate`: Sets ticket status to `ESCALATED`.
  - `🔄 Re-open`: Returns ticket status to `OPEN`.
  - Updates persist directly to SQLite via `PATCH /api/reviews/private-tickets/{ticket_id}/status`.

### 3.5 Section 5: Settings
- **Account & Security Overview**:
  - Account email and display name.
  - Tenant identifier (`businessId`).
  - Role badge (`owner`, `manager`).
- **Password Management**:
  - Form to update account password.
  - Requires `current_password`, `new_password` (min 8 chars), and `confirm_password`.
  - Calls `POST /api/auth/change-password` with real-time feedback.
- **Customer Experience Preview**:
  - Direct button to launch guest view.
- **Sign Out**:
  - Clears session cookie and invalidates server-side session token.

---

## 4. Backend API Contracts & Data Integrity Rules

### 4.1 Analytics Summary (`GET /api/reviews/analytics`)
- **Query Parameters**: `business_id` (optional, defaults to session active tenant), `timezone` (optional, defaults to `"Asia/Kolkata"`).
- **Authorization**: `staff`, `manager`, or `owner` for that tenant.
- **Response Contract**:
  ```json
  {
    "total_generations": 240,
    "google_clicks": 38,
    "reviews_copied": 34,
    "qr_scans": 290,
    "conversion_rate_percent": 15.8,
    "rating_overview": {
      "average_rating": 4.9,
      "total_ratings": 120,
      "distribution": { "5": 110, "4": 8, "3": 2 }
    },
    "peak_usage_time": "13:00 – 14:00",
    "busiest_day": "Sunday",
    "timezone": "Asia/Kolkata",
    "hourly_distribution": { "00:00": 2, "13:00": 45 },
    "weekly_distribution": { "Monday": 12, "Sunday": 64 },
    "monthly_trends": { "2026-10": 110, "2026-11": 130 },
    "seasonal_analysis": {
      "Summer (Mar-Jun)": 0,
      "Monsoon (Jul-Sep)": 0,
      "Autumn & Festive (Oct-Nov)": 240,
      "Winter (Dec-Feb)": 0
    },
    "festival_analysis": [
      {
        "festival": "Navratri",
        "year": 2026,
        "period": "2026-10-11 to 2026-10-20",
        "event_count": 18,
        "daily_rate": 1.8,
        "insufficient_historical_data": false,
        "notice": "Baseline comparison verified"
      }
    ],
    "business_insights": [
      "Peak digital review engagement occurs around 13:00 – 14:00.",
      "Most active engagement day of the week is Sunday."
    ],
    "private_tickets_summary": {
      "total": 3,
      "open": 1,
      "resolved": 2,
      "escalated": 0
    },
    "top_topics": [{ "topic": "Special Chai", "count": 48 }],
    "recent_activity": ["13:45 • Table 4 created a 5-star draft"]
  }
  ```

### 4.2 Ticket Status Update (`PATCH /api/reviews/private-tickets/{ticket_id}/status`)
- **Authorization**: `manager` or `owner` role required.
- **Request Body**: `{"status": "OPEN" | "RESOLVED" | "ESCALATED"}`.
- **Security Check**: Enforces tenant scoping so managers cannot modify tickets belonging to another tenant.

### 4.3 Password Management (`POST /api/auth/change-password`)
- **Authorization**: Valid session required.
- **Request Body**: `{"current_password": "...", "new_password": "..."}`.
- **Security Rules**: Verifies current password using scrypt; validates new password >= 8 characters; hashes new password using scrypt before saving.

---

## 5. Security & Isolation Invariants

1. **Zero Cross-Tenant Leakage**: All ticket queries and analytics retrievals filter on indexed `tenant_id`.
2. **Strict RBAC**: Staff role can view analytics; manager/owner role is required for configuration changes and ticket resolution.
3. **No Unsanitized Inputs**: All text inputs are trimmed and validated; SVG uploads go through `svg_sanitizer.py`.
4. **WAL Mode Persistence**: SQLite Write-Ahead Logging (`PRAGMA journal_mode=WAL`) is maintained across all environments.
