# VRAJA AI — Complete API & Database Architecture Reference
**Document Version:** 2.1.0  
**Audit Reference:** October 30, 2026  
**Backend Framework:** FastAPI / Python 3.12  
**Storage Engine:** SQLite3 (WAL Mode)

---

## 1. Complete API Route Reference

### 1.1 Core Engine Endpoints

#### `GET /healthz`
- **Purpose:** Service health monitoring probe for load balancers and container orchestrators.
- **Auth:** Public.
- **Request Parameters:** None.
- **Response `200 OK`:**
  ```json
  { "status": "ok" }
  ```

#### `GET /api/stats`
- **Purpose:** Pipeline operational metrics and model health.
- **Auth:** Public.
- **Response `200 OK`:**
  ```json
  {
    "uptime_seconds": 12450.5,
    "sentiment_model_loaded": true,
    "sarcasm_model_loaded": true,
    "llm_provider": "local"
  }
  ```

#### `POST /api/predict`
- **Purpose:** Raw context-aware sentiment analysis combining CardiffNLP sentiment and irony classification.
- **Auth:** Public.
- **Request Body:**
  ```json
  {
    "review": "The food arrived cold after 50 minutes. Fantastic service!",
    "rating": 1
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "sentiment": "Negative",
    "sarcasm_detected": true,
    "rating_review_consistency": "Match",
    "integrity": "Genuine",
    "confidence_scores": {
      "positive": 0.08,
      "neutral": 0.12,
      "negative": 0.80
    }
  }
  ```

---

### 1.2 Multi-Tenant Authentication & Session Management

#### `POST /api/auth/login`
- **Purpose:** Authenticates business owners and sets secure HTTP-only session cookie.
- **Auth:** Public (Rate-limited to 10 requests/min per IP).
- **Request Body:**
  ```json
  {
    "email": "owner@artisancoffee.com",
    "password": "Password123!"
  }
  ```
- **Response `200 OK`:** Sets cookie `nasta_owner_session=<token>`
  ```json
  {
    "status": "authenticated",
    "user_id": "usr_9124a",
    "email": "owner@artisancoffee.com",
    "display_name": "Tushar Kacha",
    "active_tenant_id": "artisan_coffee",
    "role": "owner",
    "is_platform_admin": false
  }
  ```

#### `GET /api/auth/session`
- **Purpose:** Inspects current session, active tenant, and user privileges.
- **Auth:** Session Cookie or `Authorization: Bearer <token>`.
- **Response `200 OK`:**
  ```json
  {
    "authenticated": true,
    "user_id": "usr_9124a",
    "email": "owner@artisancoffee.com",
    "display_name": "Tushar Kacha",
    "active_tenant_id": "artisan_coffee",
    "role": "owner",
    "is_platform_admin": false
  }
  ```

#### `POST /api/auth/logout`
- **Purpose:** Revokes active session token in database and clears client cookie.
- **Auth:** Session Cookie or Bearer Token.
- **Response `200 OK`:**
  ```json
  { "status": "logged_out" }
  ```

#### `GET /api/auth/tenants`
- **Purpose:** Lists all business tenants the authenticated user has active memberships in.
- **Auth:** Authenticated User.
- **Response `200 OK`:**
  ```json
  [
    {
      "tenant_id": "artisan_coffee",
      "business_name": "Artisan Coffee Roasters",
      "role": "owner",
      "status": "active"
    }
  ]
  ```

#### `POST /api/auth/switch-tenant`
- **Purpose:** Switches the user's active tenant session to another authorized tenant.
- **Auth:** Authenticated User.
- **Request Body:**
  ```json
  { "tenant_id": "cuore_bistro" }
  ```
- **Response `200 OK`:**
  ```json
  {
    "status": "tenant_switched",
    "active_tenant_id": "cuore_bistro",
    "role": "manager"
  }
  ```

---

### 1.3 Product A: Review Assistant Endpoints

#### `POST /api/reviews/ideas`
- **Purpose:** Generates 3-5 quick review candidate ideas based on rating, topics, and language.
- **Auth:** Public / Guest.
- **Request Body:**
  ```json
  {
    "business_id": "artisan_coffee",
    "rating": 5,
    "aspects": ["Taste & Flavour", "Friendly Staff"],
    "user_note": "Great cortado",
    "language": "english",
    "category": "Cafe"
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "ideas": [
      {
        "id": "idea_1",
        "text": "The cortado had incredible taste & flavour, and the staff was so friendly!",
        "aspects": ["Taste & Flavour", "Friendly Staff"]
      }
    ]
  }
  ```

#### `POST /api/reviews/generate`
- **Purpose:** Synthesizes a natural, customer-grounded review draft with chosen tone.
- **Auth:** Public / Guest.
- **Request Body:**
  ```json
  {
    "business_id": "artisan_coffee",
    "rating": 5,
    "aspects": ["Taste & Flavour"],
    "tone": "enthusiastic",
    "language": "english"
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "review": "Absolutely loved the coffee here! The taste & flavour was exceptional! ☕",
    "provider": "local-hospitality-engine"
  }
  ```

#### `POST /api/reviews/validate`
- **Purpose:** Verifies that review text sentiment matches the customer's star rating.
- **Auth:** Public / Guest.
- **Request Body:**
  ```json
  {
    "review": "Worst coffee ever, tasted like mud.",
    "rating": 5
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "valid": false,
    "reason": "Text sentiment appears negative but rating is 5 stars."
  }
  ```

#### `POST /api/reviews/session`
- **Purpose:** Initializes a tracked customer review session.
- **Auth:** Public / Guest.
- **Request Body:**
  ```json
  {
    "business_id": "artisan_coffee",
    "table_number": "Table 4",
    "dining_type": "dine_in"
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "session_id": "ses_4b892a01",
    "business_id": "artisan_coffee",
    "table_number": "Table 4",
    "created_at": "2026-10-30T17:20:00Z"
  }
  ```

#### `POST /api/reviews/events`
- **Purpose:** Records telemetry events from the guest review journey.
- **Auth:** Public / Guest.
- **Request Body:**
  ```json
  {
    "session_id": "ses_4b892a01",
    "event_name": "rating_selected",
    "metadata": { "rating": 5, "business_id": "artisan_coffee" }
  }
  ```
- **Response `200 OK`:**
  ```json
  { "status": "recorded" }
  ```

#### `POST /api/reviews/private-feedback`
- **Purpose:** Captures private feedback notes from guests who had unsatisfactory experiences.
- **Auth:** Public / Guest.
- **Request Body:**
  ```json
  {
    "business_id": "artisan_coffee",
    "table_number": "Table 4",
    "rating": 2,
    "diner_note": "Coffee took 25 minutes to arrive.",
    "aspects": ["Quick Service"],
    "guest_contact": "+919876543210"
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "status": "received",
    "ticket_id": "tkt_81a2f"
  }
  ```

#### `GET /api/businesses/{business_id}/review-link`
- **Purpose:** Retrieves public review URL, branding colors, and topic chips.
- **Auth:** Public.
- **Response `200 OK`:**
  ```json
  {
    "business_name": "Artisan Coffee Roasters",
    "review_url": "https://g.page/r/artisan-coffee/review",
    "category": "Cafe",
    "topics": ["Taste & Flavour", "Friendly Staff", "Cleanliness"],
    "primary_accent": "#f97316"
  }
  ```

#### `GET /api/reviews/analytics`
- **Purpose:** Aggregates performance metrics, star distributions, and conversion rates.
- **Auth:** Owner / Manager session.
- **Response `200 OK`:**
  ```json
  {
    "total_sessions": 340,
    "reviews_generated": 290,
    "reviews_copied": 240,
    "google_maps_opened": 215,
    "conversion_rate": 0.63,
    "average_rating": 4.8,
    "rating_breakdown": { "5": 280, "4": 30, "3": 10, "2": 5, "1": 15 },
    "topic_mentions": { "Taste & Flavour": 180, "Friendly Staff": 140 }
  }
  ```

#### `GET /api/reviews/private-tickets`
- **Purpose:** Lists private customer feedback tickets with severity tags.
- **Auth:** Owner / Manager session.
- **Response `200 OK`:**
  ```json
  [
    {
      "ticket_id": "tkt_81a2f",
      "timestamp": 1793361600.0,
      "rating": 2,
      "severity": "MEDIUM",
      "diner_note": "Coffee took 25 minutes to arrive.",
      "guest_contact": "+919876543210",
      "table_number": "Table 4"
    }
  ]
  ```

#### `POST /api/reviews/manager-reply`
- **Purpose:** Generates an AI-assisted resolution draft for customer complaints.
- **Auth:** Owner / Manager session.
- **Request Body:**
  ```json
  {
    "ticket_id": "tkt_81a2f",
    "tone": "empathetic"
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "reply_text": "Dear Guest, thank you for visiting Artisan Coffee. We sincerely apologize for the delay you experienced. We have addressed this with our barista team and would love to welcome you back for a complimentary coffee on your next visit."
  }
  ```

---

### 1.4 Platform Superadmin Endpoints

#### `POST /api/platform/tenants`
- **Purpose:** Provisions a new tenant business in the multi-tenant registry.
- **Auth:** Platform Admin (`is_platform_admin = 1`).
- **Request Body:**
  ```json
  {
    "business_id": "downtown_grill",
    "business_name": "Downtown Grill & Bar",
    "category": "Restaurant",
    "google_review_url": "https://g.page/r/downtown-grill/review",
    "entitlements": ["review_manager", "digital_card"]
  }
  ```
- **Response `201 Created`:**
  ```json
  {
    "status": "created",
    "tenant_id": "downtown_grill",
    "business_name": "Downtown Grill & Bar"
  }
  ```

#### `GET /api/platform/tenants`
- **Purpose:** Lists all business tenants across the entire platform.
- **Auth:** Platform Admin.
- **Response `200 OK`:** Array of tenant records with status and entitlements.

#### `PATCH /api/platform/tenants/{business_id}/status`
- **Purpose:** Suspends or activates a business tenant.
- **Auth:** Platform Admin.
- **Request Body:**
  ```json
  { "status": "suspended" }
  ```
- **Response `200 OK`:** Status update confirmation.

#### `PATCH /api/platform/tenants/{business_id}/entitlements`
- **Purpose:** Updates enabled product modules for a tenant.
- **Auth:** Platform Admin.
- **Request Body:**
  ```json
  { "entitlements": ["review_manager", "digital_card"] }
  ```
- **Response `200 OK`:** Entitlement update confirmation.

---

### 1.5 Product B: Digital Business Card Endpoints

#### `GET /api/businesses/{business_id}/card`
- **Purpose:** Returns public business card information, contact actions, appearance, and published PDF documents.
- **Auth:** Public.
- **Entitlement Barrier:** Requires `digital_card` entitlement.
- **Response `200 OK`:**
  ```json
  {
    "tenant_id": "artisan_coffee",
    "display_name": "Artisan Coffee Roasters",
    "tagline": "Specialty Coffee & European Bakery",
    "category": "Cafe",
    "opening_hours": "Mon-Sun: 7:00 AM - 10:00 PM",
    "welcome_message": "Welcome to Artisan Coffee. Tap below to save our contact or view our seasonal menu.",
    "phone_number": "+919876543210",
    "whatsapp_url": "https://wa.me/919876543210",
    "email": "hello@artisancoffee.com",
    "website_url": "https://artisancoffee.com",
    "address": "108 Heritage Blvd, Ahmedabad, Gujarat",
    "map_url": "https://maps.google.com/?q=Artisan+Coffee+Ahmedabad",
    "instagram_url": "https://instagram.com/artisancoffee",
    "primary_accent": "#f97316",
    "background_preset": "modern_gradient",
    "logo_path": "/api/businesses/artisan_coffee/images/logo_a12f.png",
    "cover_image_path": "",
    "show_review_button": true,
    "review_url": "/b/artisan_coffee/review",
    "documents": [
      {
        "id": "doc_991a",
        "display_name": "Autumn Beverage & Bakery Menu",
        "document_type": "food_menu",
        "file_size_bytes": 1845120,
        "download_url": "/api/businesses/artisan_coffee/documents/doc_991a/file",
        "sha256_hash": "a1b2c3..."
      }
    ]
  }
  ```

#### `GET /api/businesses/{business_id}/card/qr-info`
- **Purpose:** Returns canonical card URL and QR coordinate payloads for printing storefront materials.
- **Auth:** Public.
- **Response `200 OK`:**
  ```json
  {
    "tenant_id": "artisan_coffee",
    "canonical_card_url": "http://127.0.0.1:5174/b/artisan_coffee/card",
    "business_name": "Artisan Coffee Roasters"
  }
  ```

#### `GET /api/businesses/{business_id}/profile`
- **Purpose:** Fetches full business profile for owner editing.
- **Auth:** Owner / Manager session.
- **Response `200 OK`:** Returns full `business_profiles` table record.

#### `PUT /api/businesses/{business_id}/profile`
- **Purpose:** Updates business card contact details, social links, hours, and visual presets.
- **Auth:** Owner session (`owner` role).
- **Request Body:**
  ```json
  {
    "display_name": "Artisan Coffee Roasters",
    "tagline": "Single Origin Espresso & Bakery",
    "phone_number": "+919876543210",
    "whatsapp_url": "+919876543210",
    "primary_accent": "#d97706",
    "background_preset": "dark_elegance",
    "opening_hours": "Daily 7 AM - 11 PM",
    "is_published": true
  }
  ```
- **Response `200 OK`:** Updated profile representation.

#### `POST /api/businesses/{business_id}/documents`
- **Purpose:** Uploads a PDF menu or document (up to 10 MiB).
- **Auth:** Owner session (`owner` role).
- **Request:** `multipart/form-data` with `file`, `document_type`, `display_name`.
- **Response `201 Created`:**
  ```json
  {
    "id": "doc_991a",
    "tenant_id": "artisan_coffee",
    "display_name": "Seasonal Menu",
    "document_type": "food_menu",
    "file_size_bytes": 1845120,
    "sha256_hash": "a1b2c3...",
    "is_published": true
  }
  ```

#### `PATCH /api/businesses/{business_id}/documents/{document_id}`
- **Purpose:** Updates document title, category, or published visibility state.
- **Auth:** Owner session (`owner` role).
- **Request Body:**
  ```json
  {
    "display_name": "Spring Special Menu",
    "is_published": false
  }
  ```
- **Response `200 OK`:** Updated document metadata.

#### `DELETE /api/businesses/{business_id}/documents/{document_id}`
- **Purpose:** Permanently deletes PDF document record and purges physical file from disk.
- **Auth:** Owner session (`owner` role).
- **Response `200 OK`:**
  ```json
  { "status": "deleted", "document_id": "doc_991a" }
  ```

#### `GET /api/businesses/{business_id}/documents/{document_id}/file`
- **Purpose:** Streams PDF document binary to browser with `nosniff` header.
- **Auth:** Public for published documents; Owner for draft documents.
- **Response `200 OK`:** Binary stream (`Content-Type: application/pdf`).

#### `POST /api/businesses/{business_id}/images`
- **Purpose:** Uploads brand logo or cover banner image (up to 5 MiB).
- **Auth:** Owner session (`owner` role).
- **Request:** `multipart/form-data` with `file` and `image_type` (`"logo"` or `"cover"`).
- **Response `200 OK`:**
  ```json
  {
    "image_url": "/api/businesses/artisan_coffee/images/logo_b41a.png",
    "image_type": "logo",
    "filename": "logo_b41a.png",
    "size_bytes": 142050,
    "mime_type": "image/png"
  }
  ```

#### `GET /api/businesses/{business_id}/images/{filename}`
- **Purpose:** Publicly serves tenant logo or cover image with HTTP cache headers.
- **Auth:** Public.
- **Response `200 OK`:** Image binary with appropriate media type.

---

## 2. Database Schema & Relational Specifications

### 2.1 Table: `tenants`
Stores registered SaaS business tenants.
```sql
CREATE TABLE IF NOT EXISTS tenants (
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
```

### 2.2 Table: `users`
Stores user credentials and platform administrator flags.
```sql
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 1,
    is_platform_admin INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
```

### 2.3 Table: `tenant_memberships`
Binds users to tenants with specific authorization roles.
```sql
CREATE TABLE IF NOT EXISTS tenant_memberships (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'manager',
    created_at REAL NOT NULL,
    UNIQUE(user_id, tenant_id)
);
CREATE INDEX IF NOT EXISTS idx_memberships_user ON tenant_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_memberships_tenant ON tenant_memberships(tenant_id);
```

### 2.4 Table: `sessions`
Stores server-side session tokens.
```sql
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    active_tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    revoked_at REAL,
    ip_address TEXT DEFAULT '',
    user_agent TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at);
```

### 2.5 Table: `business_profiles`
Stores Product B digital card configuration and contact links.
```sql
CREATE TABLE IF NOT EXISTS business_profiles (
    tenant_id TEXT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
    tagline TEXT DEFAULT '',
    display_name TEXT DEFAULT '',
    category TEXT DEFAULT '',
    opening_hours TEXT DEFAULT '',
    welcome_message TEXT DEFAULT '',
    email TEXT DEFAULT '',
    phone_number TEXT DEFAULT '',
    website_url TEXT DEFAULT '',
    address TEXT DEFAULT '',
    map_url TEXT DEFAULT '',
    whatsapp_url TEXT DEFAULT '',
    whatsapp_group_url TEXT DEFAULT '',
    instagram_url TEXT DEFAULT '',
    facebook_url TEXT DEFAULT '',
    youtube_url TEXT DEFAULT '',
    logo_path TEXT DEFAULT '',
    cover_image_path TEXT DEFAULT '',
    background_preset TEXT DEFAULT '',
    overlay_opacity REAL DEFAULT 0.75,
    primary_accent TEXT DEFAULT '#078BFF',
    custom_links_json TEXT DEFAULT '[]',
    is_published INTEGER NOT NULL DEFAULT 0,
    show_review_button INTEGER NOT NULL DEFAULT 1,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_business_profiles_published ON business_profiles(is_published);
```

### 2.6 Table: `tenant_documents`
Stores metadata and checksums for uploaded PDF menus.
```sql
CREATE TABLE IF NOT EXISTS tenant_documents (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL DEFAULT 'food_menu',
    display_name TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    mime_type TEXT NOT NULL DEFAULT 'application/pdf',
    sha256_hash TEXT NOT NULL,
    is_published INTEGER NOT NULL DEFAULT 1,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tenant_documents_tenant ON tenant_documents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_documents_published ON tenant_documents(is_published);
```

### 2.7 Table: `analytics_events`
Stores guest telemetry and review journey progression.
```sql
CREATE TABLE IF NOT EXISTS analytics_events (
    event_id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    payload TEXT NOT NULL
);
```

### 2.8 Table: `private_tickets`
Stores customer private feedback complaints.
```sql
CREATE TABLE IF NOT EXISTS private_tickets (
    ticket_id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    payload TEXT NOT NULL
);
```
