# Product A — Review System: Architecture & Workflows

## 1. System Architecture Overview

Product A (Review System) is a multi-tenant customer feedback, AI-assisted review generation, and Google Maps review acceleration platform. It connects on-premise diners/customers via QR codes to a dynamic, industry-templated web interface, and provides business owners and platform administrators with analytics and configuration capabilities.

```mermaid
flowchart TB
    subgraph ClientTier["Client Tier (React + Vite SPA)"]
        CR["Customer Review Experience<br/>(CustomerReview.jsx)"]
        OP["Owner Portal<br/>(OwnerPortal.jsx)"]
        VA["Platform Admin Console<br/>(VrajaAdmin.jsx)"]
        TM["Dynamic Template Manager<br/>(TemplateManager.jsx)"]
    end

    subgraph APITier["FastAPI Backend Tier (Python 3.12)"]
        AuthMiddleware["Session & RBAC Middleware<br/>(require_auth_context / require_platform_admin)"]
        PublicAPI["Public Config & Review Endpoints<br/>(/api/public/..., /api/reviews/...)"]
        OwnerAPI["Tenant Management & Analytics<br/>(/api/businesses/..., /api/reviews/analytics)"]
        PlatformAPI["Platform Template & Tenant Engine<br/>(/api/platform/...)"]
        
        subgraph ReviewEngine["Core Review & AI Pipeline"]
            PromptMgr["Trilingual Prompt Manager<br/>(prompts.py - EN / GU / HI)"]
            LLMClient["LLM Provider Adapter<br/>(llm_provider.py - Gemini / Fallback)"]
            SentimentModel["RoBERTa Sentiment Engine<br/>(sentiment.py)"]
            SarcasmModel["DistilBERT Sarcasm Classifier<br/>(sarcasm.py)"]
            ContradictionGuard["Contradiction & Validation Filter<br/>(validator.py / service.py)"]
        end
        
        subgraph StorageLayer["Data Access & Storage Repository"]
            StoreRepo["ReviewStore & Tenant Repo<br/>(storage.py)"]
            TemplateRepo["TemplateRepository & Engine<br/>(template_storage.py)"]
        end
    end

    subgraph DataTier["Data Persistence Tier (SQLite WAL)"]
        DB[("reviews.sqlite3<br/>11 Multi-Tenant Tables")]
    end

    subgraph ExternalTier["External Services"]
        GoogleMaps["Google Local WriteReview<br/>(PlaceID Redirect)"]
        GeminiAPI["Google Gemini LLM API<br/>(Optional Cloud Inference)"]
    end

    %% Client to Backend
    CR -->|GET config / POST events / POST generate| PublicAPI
    OP -->|GET analytics / POST config| OwnerAPI
    VA -->|Platform management| PlatformAPI
    TM -->|Version & Assignment APIs| PlatformAPI

    %% Backend internal routing
    PublicAPI --> ReviewEngine
    PublicAPI --> StorageLayer
    OwnerAPI --> AuthMiddleware
    PlatformAPI --> AuthMiddleware
    AuthMiddleware --> StorageLayer

    ReviewEngine --> LLMClient
    ReviewEngine --> SentimentModel
    ReviewEngine --> SarcasmModel
    ReviewEngine --> ContradictionGuard
    LLMClient -.-> GeminiAPI

    StorageLayer --> StoreRepo
    StorageLayer --> TemplateRepo
    StoreRepo --> DB
    TemplateRepo --> DB

    CR -->|Direct Handoff on 1-5 Stars| GoogleMaps
```

---

## 2. Database Entity-Relationship (ER) Architecture

The persistence model is implemented in SQLite with `PRAGMA foreign_keys = ON` and `PRAGMA journal_mode = WAL`. Product A manages 11 core tables categorized into multi-tenant identity, telemetry, feedback tickets, and dynamic industry template governance.

```mermaid
erDiagram
    tenants ||--o{ tenant_memberships : "has members"
    users ||--o{ tenant_memberships : "belongs to"
    users ||--o{ sessions : "authenticates"
    tenants ||--o{ sessions : "scoped context"
    tenants ||--o{ analytics_events : "generates telemetry"
    tenants ||--o{ private_tickets : "receives feedback"
    tenants ||--o| business_configurations : "visual overrides"
    tenants ||--o{ business_template_assignments : "pinned template"
    
    industries ||--o{ templates : "categorizes"
    templates ||--o{ template_versions : "versions (draft/pub/arch)"
    template_versions ||--o{ business_template_assignments : "exact version pinned"

    tenants {
        string id PK "Unique tenant slug / ID"
        string business_name "Display name of business"
        string status "active / inactive"
        string platform "google / custom"
        string review_url "Google PlaceID review URL"
        string category "Industry category string"
        string primary_accent "Brand hex color"
        json topics_json "Default topics array"
        json entitlements_json "Allowed modules array"
        real created_at "Unix epoch timestamp"
        real updated_at "Unix epoch timestamp"
    }

    users {
        string id PK "User UUID"
        string email UK "User login email"
        string password_hash "PBKDF2/Argon2 hash"
        string display_name "Human readable name"
        int is_active "1 = active, 0 = disabled"
        int is_platform_admin "1 = superadmin, 0 = regular"
        real created_at "Timestamp"
        real updated_at "Timestamp"
    }

    tenant_memberships {
        string id PK "Membership UUID"
        string user_id FK "References users(id)"
        string tenant_id FK "References tenants(id)"
        string role "owner / manager / staff"
        real created_at "Timestamp"
    }

    sessions {
        string token_hash PK "SHA256 session token hash"
        string user_id FK "References users(id)"
        string active_tenant_id FK "References tenants(id)"
        real created_at "Created timestamp"
        real expires_at "Expiry timestamp"
        real revoked_at "Revocation timestamp"
    }

    analytics_events {
        string event_id PK "Event UUID"
        string tenant_id FK "Scoped tenant"
        json payload "Event payload details"
        real created_at "Event timestamp"
    }

    private_tickets {
        string ticket_id PK "Ticket UUID"
        string tenant_id FK "Scoped tenant"
        json payload "Feedback text, rating, status"
        real created_at "Created timestamp"
    }

    industries {
        string id PK "ind_restaurant, ind_hotel, etc."
        string slug UK "restaurant, hotel, salon, clinic"
        string name "Industry name"
        string icon "Visual unicode emoji"
        string status "active / archived"
        real created_at "Timestamp"
        real updated_at "Timestamp"
    }

    templates {
        string id PK "Unique template slug / ID"
        string industry_id FK "References industries(id)"
        string slug UK "URL-safe slug"
        string name "Template presentation title"
        string status "active / archived"
        real created_at "Timestamp"
        real updated_at "Timestamp"
    }

    template_versions {
        string id PK "ver_<slug>_<version>_<hash>"
        string template_id FK "References templates(id)"
        string version "Semantic version e.g. 1.0.0"
        json configuration_json "Full theme, layout, topics DTO"
        string schema_version "1.0"
        string publication_status "draft / published / archived"
        real published_at "Publish timestamp"
        real created_at "Timestamp"
        string created_by "Admin email"
    }

    business_template_assignments {
        string id PK "Assignment UUID"
        string business_id FK "References tenants(id)"
        string template_id FK "References templates(id)"
        string template_version_id FK "References template_versions(id)"
        string assigned_by "Admin email"
        real assigned_at "Timestamp"
        string status "active / superseded"
    }

    business_configurations {
        string id PK "Override UUID"
        string business_id UK FK "References tenants(id)"
        string logo_url "Custom logo URL"
        string cover_image_url "Custom cover URL"
        string primary_accent "Tenant accent HEX"
        json custom_topics_json "Custom topics array"
        json localized_content_json "Trilingual string overrides"
        string google_review_url "Custom Google review link"
        string status "active / disabled"
        real created_at "Timestamp"
        real updated_at "Timestamp"
    }
```

---

## 3. End-to-End Application Workflows

### 3.1 Customer Review Journey & Anti-Gating Review Handoff

The customer review flow is deliberately anti-gating compliant: whether a customer selects 1 star or 5 stars, Google Review handoff is never blocked or obscured.

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer / Diner
    participant UI as CustomerReview.jsx
    participant API as FastAPI Backend
    participant AI as AI Engine & NLP Models
    participant GMap as Google Maps (Local Place)

    Customer->>UI: Scan QR / Open Review URL (/review?biz=...)
    UI->>API: GET /api/public/businesses/{business_id}/config
    API-->>UI: Sanitized Public Config (Theme, Topics, AntiGating=true, GoogleReviewUrl)
    UI->>UI: Render Dynamic Industry Template & Detect Language (EN/GU/HI)
    
    Customer->>UI: Select Star Rating (1 to 5 Stars)
    UI->>API: POST /api/reviews/events {event: "rating_selected", rating: 5}
    
    Customer->>UI: Tap Highlight Topics (e.g. Food Quality, Ambiance)
    Customer->>UI: Type Personal Note (Optional)
    
    alt Customer Requests AI Review Generation
        Customer->>UI: Click "Generate Suggestions"
        UI->>API: POST /api/reviews/ideas (topics, note, language, rating)
        API->>AI: Generate Ideas & Check Sentiment/Sarcasm Contradictions
        AI-->>API: 3 Formatted Review Candidates (short, standard, detailed)
        API-->>UI: Return Curated Review Suggestions
        UI->>Customer: Render Suggestions Cards with Typing Animation
        Customer->>UI: Tap Preferred Suggestion (Copies to Clipboard)
    else Customer Writes Custom Review
        Customer->>UI: Enter text directly in Review Editor
    end

    alt Direct Google Maps Handoff (Ratings 1-5 Available)
        Customer->>UI: Click "Post to Google Review"
        UI->>UI: Copy Review to Clipboard & Set LocalStorage Recovery Draft
        UI->>API: POST /api/reviews/events {event: "google_redirect_clicked"}
        UI->>GMap: Open Google Place WriteReview in New Tab
    else Private Anonymous Feedback (Optional for Any Rating)
        Customer->>UI: Click "Send Private Note to Manager"
        UI->>UI: Open Private Feedback Modal
        Customer->>UI: Submit Message & Contact (Optional)
        UI->>API: POST /api/reviews/private-feedback {rating, message, contact}
        API->>API: Create private_ticket in DB
        API-->>UI: 200 OK (Ticket ID)
        UI->>Customer: Render Success Screen with Confirmation
    end
```

---

### 3.2 AI Generation, Sentiment & Contradiction Filtering Workflow

```mermaid
flowchart TD
    Start["User inputs rating, topics, language & personal note"] --> Req["POST /api/reviews/ideas"]
    Req --> PromptSelect{"Select Prompt by Language"}
    PromptSelect -->|English| PromptEN["English Prompt Template"]
    PromptSelect -->|Gujarati| PromptGU["Gujarati Prompt Template"]
    PromptSelect -->|Hindi| PromptHI["Hindi Prompt Template"]
    
    PromptEN & PromptGU & PromptHI --> Gen["LLM Generation Engine (Gemini / Fallback Engine)"]
    Gen --> Parse["Parse Generated Candidates (Length variants)"]
    
    Parse --> ModelCheck["Sentiment & Sarcasm Models Inference"]
    ModelCheck --> Senti["RoBERTa Sentiment Analysis (POS / NEG / NEU)"]
    ModelCheck --> Sarcasm["DistilBERT Sarcasm Classifier (Sarcastic / Genuine)"]
    
    Senti & Sarcasm --> Contra{"Contradiction Guard"}
    Contra -->|5-Star Rating + Negative Sentiment| Reject["Flag Contradiction & Re-generate / Sanitize"]
    Contra -->|1-2 Star Rating + Positive Sentiment| Reject
    Contra -->|Sarcasm Detected on High Rating| Reject
    Contra -->|Consistent Sentiment & Rating| Accept["Format Clean Review Suggestions"]
    
    Accept --> Response["Return 3 Curated Options to UI"]
```

---

### 3.3 Dynamic Template Lifecycle & Version Pinning Workflow

```mermaid
stateDiagram-v2
    [*] --> Draft : Admin creates new version (POST /versions)
    Draft --> Draft : Admin edits JSON configuration (PUT /versions/{id})
    Draft --> Published : Admin publishes version (POST /publish)
    
    state Published {
        [*] --> PinnedToTenant : Assign to Business (POST /assign-template)
        PinnedToTenant --> Superseded : Admin upgrades business to newer version
    }
    
    Published --> Archived : Admin archives template/version
    note right of Published
        Published versions are strictly IMMUTABLE.
        Direct configuration updates are rejected.
    end note
```

---

### 3.4 Multi-Tenant Authentication & Session Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Admin / Tenant Owner
    participant Web as OwnerPortal / VrajaAdmin
    participant AuthAPI as Auth Controller (/api/auth)
    participant AuthMgr as Auth Security Manager
    participant DB as SQLite DB

    Admin->>Web: Submit Email & Password
    Web->>AuthAPI: POST /api/auth/login {email, password}
    AuthAPI->>AuthMgr: Verify Rate Limiter (_login_attempts < 5/min)
    alt Rate Limit Exceeded
        AuthMgr-->>Web: 429 Too Many Requests
    else Allowed
        AuthAPI->>DB: Query user & verify password_hash (PBKDF2)
        DB-->>AuthAPI: User record (is_platform_admin, active_tenant_id)
        AuthAPI->>DB: Create session token & store in sessions table
        AuthAPI-->>Web: Set HTTP-only Cookie (`vraja_session_token`) & Return User DTO
    end

    Admin->>Web: Navigate to Protected Dashboard
    Web->>AuthAPI: GET /api/auth/session
    AuthAPI->>DB: Validate session token, check expiry & fetch tenant entitlements
    DB-->>AuthAPI: Session Context (tenant_id, role, is_platform_admin)
    AuthAPI-->>Web: 200 OK Context
```
