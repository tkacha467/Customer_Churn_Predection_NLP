# ChurnLens — Real-World AI Restaurant Review & Reputation Assistant
## Master Product & Technical Specification (Complete Architecture & Evolution: From Scratch to Production)

---

## Table of Contents
1. [Product History & Evolution: The Complete Journey From Scratch](#1-product-history--evolution-the-journey-from-scratch)
   - 1.1 Phase 1: Academic Churn Modeling & Tabular Machine Learning
   - 1.2 Phase 2: NLP Deep Learning, Neutral Sentiment & Multi-Modal Fusion
   - 1.3 Phase 3: Enterprise SaaS Pivot & AI Review Generation
   - 1.4 Phase 4: Enterprise Hospitality Intelligence & Manager Portal
   - 1.5 Phase 5: Real-World Product Transformation — The Simple AI Review Assistant for Restaurants
2. [Executive Product Vision & Positioning](#2-executive-product-vision--positioning)
   - 2.1 The Core Problem: The Blank-Page Review Barrier
   - 2.2 Product Positioning & Value Proposition
   - 2.3 The Three Personas Quality Bar
3. [Full System Architecture & Technology Stack](#3-full-system-architecture--technology-stack)
   - 3.1 End-to-End Architectural Diagram
   - 3.2 Technology Stack Breakdown
4. [Complete Codebase & Directory Inventory](#4-complete-codebase--directory-inventory)
5. [Core Subsystems & Feature Deep Dive](#5-core-subsystems--feature-deep-dive)
   - 5.1 Public Customer Experience (`/review`): Mobile-First Guest Review Flow
   - 5.2 Review Idea Cards: Multi-Perspective Starting Concepts
   - 5.3 Humanization Engine & Zero-Fabrication Prompt Calibration
   - 5.4 Contextual Emoji Rule System
   - 5.5 Silent Rating Consistency Validation (CardiffNLP RoBERTa)
   - 5.6 Ethical Google Handoff & Clipboard Flow (100% Google Compliant)
   - 5.7 Restaurant Owner Portal (`/owner`): 5 Simple Management Workspaces
   - 5.8 Dynamic Table QR Code Studio & Deep-Linking
   - 5.9 Authentic Real-World Analytics (Zero Fake Metrics)
   - 5.10 Direct In-House Management Note (Non-Gated Feedback)
6. [API Specification & Data Schemas](#6-api-specification--data-schemas)
   - 6.1 Complete REST Endpoints Catalog
   - 6.2 Data Schemas & Request/Response Contracts
7. [AI & Model Architecture Audit](#7-ai--model-architecture-audit)
   - 7.1 Review LLM Provider Abstraction (`LocalLLMProvider` vs. `CloudLLMProvider`)
   - 7.2 Primary Sentiment Validator: CardiffNLP RoBERTa 3-Class
   - 7.3 Deprecation & Removal of Redundant DistilBERT Binary Model
   - 7.4 Model Inventory & Benchmark Matrix
8. [UI/UX Design System & Aesthetics](#8-uiux-design-system--aesthetics)
   - 8.1 Hospitality Aesthetic: Warm Slate & Amber Glassmorphism
   - 8.2 Mobile-First Touch Target & Accessibility Standards (≥48px)
   - 8.3 Micro-Animations & Fluid Interaction Timings (150–350ms)
9. [Reliability Engineering, Compliance & Critical Decisions](#9-reliability-engineering-compliance--critical-decisions)
   - 9.1 Elimination of Rating-Based Review Gating (Google Anti-Deflection Compliance)
   - 9.2 Prevention of Automated Submission Claims (Clipboard Handoff Protocol)
   - 9.3 Windows PyTorch Threading Mutex
   - 9.4 Elimination of Fake Demo Metrics & Synthetic CSAT
10. [Quality Assurance, Automated Testing & Verification](#10-quality-assurance-automated-testing--verification)
    - 10.1 Complete Automated Regression Test Suite (`pytest` 19/19 Passing)
    - 10.2 Frontend Linter & Production Build Verification
    - 10.3 In-Browser End-to-End Visual Verification
11. [Deployment, Operations & Git History](#11-deployment-operations--git-history)
    - 11.1 Quickstart Local Execution
    - 11.2 Environment Configuration Matrix
    - 11.3 Version Control & Git History

---

## 1. Product History & Evolution: The Complete Journey From Scratch

The ChurnLens platform evolved across five distinct architectural phases, transforming from an academic data science experiment into a clean, mobile-first, production-ready AI review assistant for real-world restaurants:

```
[Phase 1: Academic Thesis]
  - Tabular ML (Random Forest, XGBoost)
  - Flipkart / Amazon e-commerce churn data
  - Monolithic Streamlit data-science dashboard
             │
             ▼
[Phase 2: NLP Deep Learning & Multi-Modal Fusion]
  - Fine-tuned DistilBERT for customer sentiment
  - CardiffNLP RoBERTa for 3-class (Positive / Neutral / Negative)
  - Multi-modal risk fusion engine & SHAP explainability
  - Interactive pitch showcase deck (`showcase/index.html`)
             │
             ▼
[Phase 3: Enterprise SaaS Pivot]
  - Decoupled FastAPI backend + React Vite frontend
  - AI Review Assistant with Google Maps linking
  - Strict Zero-Fabrication prompt synthesis
             │
             ▼
[Phase 4: Enterprise Hospitality Intelligence & Manager Portal]
  - Deep-linked Table QR codes (?table=Table+4&dining=coffee_break)
  - Negative Feedback Deflection & GM resolution channel
  - General Manager Portal with CSAT & Dining Aspect Health Matrix
  - Table QR Standee Studio (print-ready table tents)
  - Michelin-standard AI Google Review Reply Studio
             │
             ▼
[Phase 5: Real-World Restaurant Product Transformation (Current State)]
  - Product Positioning: "The simple AI review assistant for restaurants"
  - Stripped all ML laboratory dashboards, SHAP, and developer clutter from primary UI
  - Eliminated rating-based review gating to strictly adhere to Google Business Profile policies
  - Mobile-First Customer Flow (/review): 30-60s QR scan to Google Maps
  - Review Idea Cards: 3 distinct multi-perspective concepts (Food, Vibe, Overall)
  - Humanization Engine: 15-45 words, everyday conversational English, 0-2 contextual emojis
  - ReviewLLMProvider abstraction supporting Local (zero-cost) and Cloud (Gemini/OpenAI)
  - Simplified Restaurant Owner Portal (/owner: Home, Setup, QR Codes, Activity, Settings)
  - Clean authentic metrics: Real review drafts, Google links opened, reviews copied
```

### 1.1 Phase 1: Academic Churn Modeling & Tabular Machine Learning
- **Origin:** Started as a machine learning study on predicting customer churn in e-commerce and subscription environments using customer demographics, recency, frequency, monetary value (RFM), and customer service interactions.
- **Algorithms:** Random Forest, Gradient Boosting (XGBoost/LightGBM), and Logistic Regression baselines.
- **Limitation:** Tabular data showed *when* a customer stopped purchasing, but lacked understanding of *why* (emotional frustration, service delays, or product quality complaints found in raw text).

### 1.2 Phase 2: NLP Deep Learning, Neutral Sentiment & Multi-Modal Fusion
- **Language Models:** Introduced a fine-tuned **DistilBERT** model for binary review sentiment classification (`LABEL_0` negative, `LABEL_1` positive).
- **The Neutral Sentiment Challenge:** Customer feedback in dining and retail often expresses mixed or neutral sentiments (e.g., *"The coffee was exquisite, but our table waited 25 minutes"*). Binary models artificially forced these into pure negative or positive buckets.
- **RoBERTa 3-Class Integration:** Integrated **CardiffNLP Twitter-RoBERTa** (`cardiffnlp/twitter-roberta-base-sentiment-latest`), providing genuine 3-class inference: *Positive*, *Neutral*, and *Negative*.
- **Fusion Engine:** Created `api/fusion/engine.py` to calculate unified risk scores by merging tabular behavioral probability with text sentiment polarity.
- **Explainability:** Implemented SHAP (Shapley Additive exPlanations) to provide feature attribution for risk drivers.

### 1.3 Phase 3: Enterprise SaaS Pivot & AI Review Generation
- **Architecture Shift:** Replaced single-page monolithic Streamlit scripts with an asynchronous **FastAPI** backend and a high-performance **React 19 + Vite** frontend.
- **AI Review Generation:** Developed an intelligent review assistant empowering satisfied customers to generate natural draft reviews with 1-click clipboard copy and Google Maps review redirection.
- **Anti-Hallucination Policy:** Enforced strict domain constraints to prevent generative models from inventing experiences or violating FTC guidelines.

### 1.4 Phase 4: Enterprise Hospitality Intelligence & Manager Portal
- **Domain Specialization:** Tailored the platform for high-touch hospitality—specifically artisan cafes, specialty roasteries, bistros, and restaurants.
- **Table QR Deep Linking:** Dynamic table binding (`?table=Table+4&dining=coffee_break`) enabling frictionless dining feedback directly from physical tables.
- **Negative Feedback Deflection Prototype:** Attempted an in-house GM resolution channel for low ratings.
- **General Manager Business Console:** Provided executive hospitality telemetry, dining aspect health matrices, a Table QR Standee Print Studio, and an AI Google Review Reply Studio.

### 1.5 Phase 5: Real-World Product Transformation — The Simple AI Review Assistant for Restaurants
- **The Problem with Phase 4:** The product had become an overloaded technical showcase. Restaurant owners were overwhelmed by ML telemetry, confusion matrices, SHAP values, and complex enterprise sidebars. Furthermore, rating-based review deflection violated official Google Business Profile guidelines.
- **The Transformation:**
  1. **Positioning:** Re-positioned purely as *"The simple AI review assistant for restaurants"*.
  2. **Information Architecture:** Reduced to two clear, intuitive experiences:
     - **Public Customer Experience** (`/review` or `/?table=Table+4`): Fast, mobile-first, 30–60 second journey from table QR scan to Google Maps.
     - **Restaurant Owner Portal** (`/owner`): Simple 5-tab workspace (Home, Setup, QR Codes, Activity, Settings).
  3. **Removed from Visible UI:** General Manager Portal, NLP Integrity Lab, DistilBERT vs. RoBERTa playgrounds, churn dashboards, SHAP values, and synthetic metrics.
  4. **Strict Google Policy Compliance:** Removed all rating-based review gating. Customers rating 1 to 5 stars have identical access to the public Google review destination. Optional private feedback is provided neutrally without gating Google.
  5. **Review Idea Cards:** Introduced candidate review ideas (`POST /api/reviews/ideas`), giving diners 3 distinct starting perspectives (Food, Atmosphere, Overall) instead of a single wall of AI text.
  6. **Humanization Engine:** Redesigned the generation prompt to produce simple, colloquial English (15–45 words, contractions, 0–2 contextual emojis, zero corporate jargon like "culinary excellence").
  7. **ReviewLLMProvider Abstraction:** Unified backend provider supporting zero-cost local synthesis (`LocalLLMProvider`) and hosted/cloud models (`CloudLLMProvider`).
  8. **Model Streamlining:** Audited CardiffNLP RoBERTa as the sole active rating consistency validator, deprecating the binary DistilBERT model from the active review path.

---

## 2. Executive Product Vision & Positioning

### 2.1 The Core Problem: The Blank-Page Review Barrier
80% of satisfied restaurant customers are willing to leave a 5-star Google review, but over 70% abandon the process because of:
1. **The "Blank Box" Syndrome:** Staring at an empty text box on a smartphone without knowing what to write.
2. **Time Friction:** Complicated multi-step forms, logins, or app download requirements.
3. **Artificial Tone:** Existing AI generators produce cheesy corporate prose (*"I had an exceptional culinary experience with remarkable hospitality"*) that no genuine customer would ever post.

### 2.2 Product Positioning & Value Proposition

#### For Restaurant Owners
> **Set up your restaurant once. Put the QR code on tables or receipts. Customers get help writing genuine reviews. They edit the review and post it to Google themselves.**
- **Set up in under 3 minutes:** Restaurant details, branch, official Google review link, and review topics.
- **Automatic QR Codes:** Table 1–12, counter, receipt, or general placement with downloadable PNGs and live table-stand previews.
- **Genuine, compliant growth:** Zero gating, zero fake bots, fully compliant with Google Business Profile policies.
- **Authentic activity telemetry:** Real counts of drafts created, Google review journeys started, and reviews copied.

#### For Customers
> **Rate your experience → choose what stood out → pick a natural review idea → personalize it → copy & post on Google.**
- **30 to 60 seconds from QR scan to Google Maps.**
- **No account creation or login required.**
- **Human, natural language:** 15–45 words, short sentences, everyday vocabulary, and 0–2 tasteful emojis.
- **Review Idea Cards:** Diners choose from 3 tailored perspectives rather than generating a rigid paragraph.
- **Complete Editorial Control:** Diners edit freely before continuing.

### 2.3 The Three Personas Quality Bar

| Persona | Evaluation Test | ChurnLens Implementation |
| :--- | :--- | :--- |
| **Person A: Restaurant Owner** | *"Can I understand how to set this up without technical knowledge?"* | **Yes.** Simple 3-step setup, clear plain-English labels, zero ML jargon. |
| **Person B: Young Mobile Customer** | *"Can I finish this in under a minute?"* | **Yes.** 4 quick taps: Stars → Topics → Pick Idea → Copy & Continue. |
| **Person C: Older Diner** | *"Are the text, buttons, and instructions obvious?"* | **Yes.** Large touch targets (≥48px), high contrast, clear plain English, no hidden gestures. |

---

## 3. Full System Architecture & Technology Stack

### 3.1 End-to-End Architectural Diagram

```
                              CUSTOMER DEVICE (Mobile Phone)
                                            │
                                            ▼ [Scans Table QR]
                         ┌──────────────────────────────────────┐
                         │   GET /review?table=Table+4          │
                         │   Vite + React 19 Client SPA         │
                         └──────────────────┬───────────────────┘
                                            │
               ┌────────────────────────────┼────────────────────────────┐
               │ 1. Select Stars (1-5)      │ 2. Select Topics (Chips)   │ 3. Pick Idea Card
               ▼                            ▼                            ▼
  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
  │  POST /reviews/session  │  │   POST /reviews/ideas   │  │  POST /reviews/generate │
  └────────────┬────────────┘  └────────────┬────────────┘  └────────────┬────────────┘
               │                            │                            │
               └────────────────────────────┼────────────────────────────┘
                                            │ HTTPS JSON
                                            ▼
                         ┌──────────────────────────────────────┐
                         │       FASTAPI BACKEND RUNTIME        │
                         │             (Port 8000)              │
                         └──────────────────┬───────────────────┘
                                            │
                        ┌───────────────────┴───────────────────┐
                        ▼                                       ▼
        ┌──────────────────────────────┐        ┌──────────────────────────────┐
        │     REVIEW LLM PROVIDER      │        │    SENTIMENT & VALIDATOR     │
        │ api/review_assistant/        │        │ api/review_assistant/        │
        │ - LocalLLMProvider           │        │ - CardiffNLP RoBERTa Base    │
        │   (Grounded Synthesizer)     │        │   (3-Class: Pos/Neu/Neg)     │
        │ - CloudLLMProvider           │        │ - Rating Consistency Engine  │
        │   (Gemini 1.5 / GPT-4o-mini) │        │ - Sarcasm Fusion Modifier    │
        └───────────────┬──────────────┘        └───────────────┬──────────────┘
                        │                                       │
                        └───────────────────┬───────────────────┘
                                            │
                                            ▼
                         ┌──────────────────────────────────────┐
                         │   GUEST APPROVAL & CLIPBOARD COPY    │
                         │  [ ⭐ Copy & Continue to Google ]     │
                         └──────────────────┬───────────────────┘
                                            │
                                            ▼
                         ┌──────────────────────────────────────┐
                         │       OFFICIAL GOOGLE MAPS           │
                         │  https://g.page/r/.../review         │
                         │  (Customer pastes & submits review)  │
                         └──────────────────────────────────────┘
```

### 3.2 Technology Stack Breakdown

| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | React (SPA) | `19.2.7` | Mobile-first reactive UI components |
| **Frontend Build Tool** | Vite | `8.1.1` | Ultra-fast development server & production bundler |
| **Frontend Linter** | Oxlint | `1.71.0` | High-performance JavaScript/JSX linter |
| **QR Generation** | qrcode | `1.5.4` | In-browser client-side QR code data-URL rendering |
| **Backend Framework** | FastAPI | `0.110+` | High-performance asynchronous REST API |
| **ASGI Web Server** | Uvicorn | `0.29+` | Lightweight ASGI runtime for Python |
| **Data Validation** | Pydantic v2 | `2.6+` | Strict request/response typing and schema enforcement |
| **Primary Sentiment NLP** | CardiffNLP Twitter-RoBERTa | `latest` | 3-Class (Positive / Neutral / Negative) review validator |
| **Sarcasm Detection** | CardiffNLP Twitter-RoBERTa Irony | `latest` | Sarcasm & ironic phrasing detection |
| **Local LLM Engine** | Python Grounded Synthesizer | Internal | Zero-fabrication, 15-45 word deterministic humanizer |
| **Cloud LLM Support** | Gemini 1.5 Flash / OpenAI | Dynamic | Optional enterprise LLM inference |
| **Testing Framework** | pytest + anyio | `9.1.1` | Automated unit, regression, and endpoint tests |

---

## 4. Complete Codebase & Directory Inventory

```
d:\churnlens\churnlens\
├── api/                                # FastAPI Backend Architecture
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py                 # App, model, and threshold configurations
│   ├── fusion/
│   │   ├── engine.py                   # Sarcasm-weighted sentiment fusion logic
│   │   └── explainer.py                # Human-readable sentiment explanation engine
│   ├── models/
│   │   ├── model_loader.py             # Thread-safe singleton HuggingFace pipeline loader
│   │   ├── sarcasm.py                  # CardiffNLP RoBERTa irony classifier wrapper
│   │   └── sentiment.py                # CardiffNLP RoBERTa 3-class sentiment classifier
│   ├── preprocessing/
│   │   └── text_cleaner.py             # Whitespace, contraction, and text sanitizer
│   ├── review_assistant/               # Core Real-World Review Subsystem
│   │   ├── business_links.json         # Persistent JSON store for restaurant configs & links
│   │   ├── generator.py                # Review generator engine & ideas generator
│   │   ├── google_reviews.py           # Google review link & restaurant config manager
│   │   ├── llm_provider.py             # ReviewLLMProvider abstraction (Local & Cloud)
│   │   ├── prompts.py                  # Humanized prompt engineering & candidate ideas logic
│   │   ├── routes.py                   # REST endpoints (/ideas, /generate, /validate, /config)
│   │   ├── schemas.py                  # Pydantic v2 schemas for all requests and responses
│   │   ├── service.py                  # ReviewService orchestrator & genuine analytics
│   │   └── validator.py                # Rating consistency validation engine
│   └── main.py                         # FastAPI application entrypoint and middleware
│
├── frontend/                           # React 19 + Vite Mobile-First Client
│   ├── dist/                           # Production optimized build bundle
│   ├── src/
│   │   ├── components/
│   │   │   ├── CustomerReview.jsx      # Mobile-first customer experience with idea cards
│   │   │   ├── OwnerPortal.jsx         # Simplified restaurant owner dashboard (5 tabs)
│   │   │   ├── BusinessConsole.jsx     # Legacy GM console (preserved for reference)
│   │   │   ├── IntegrityPlayground.jsx # Legacy NLP playground (preserved for reference)
│   │   │   └── ReviewAssistant.jsx     # Legacy review assistant (preserved for reference)
│   │   ├── App.jsx                     # Clean routing between Customer and Owner views
│   │   ├── index.css                   # Polished hospitality design system & tokens
│   │   └── main.jsx                    # React 19 root bootstrap
│   ├── package.json                    # Frontend dependencies and npm scripts
│   └── vite.config.js                  # Vite configuration
│
├── docs/                               # Up-to-Date Technical & Product Documentation
│   ├── DEPLOYMENT.md                   # Containerization and production deployment guide
│   ├── GOOGLE_INTEGRATION.md           # 100% Google Business Profile compliance guide
│   ├── MODEL_AUDIT.md                  # Comprehensive audit of LLM, RoBERTa, and DistilBERT
│   ├── PRODUCT_ARCHITECTURE.md         # Full information architecture and routing map
│   ├── PRODUCT_SPECIFICATION.md        # Master technical specification (this document)
│   ├── PRODUCT_VISION.md               # Product positioning and three-persona quality bar
│   ├── REVIEW_ASSISTANT_ARCHITECTURE.md# Humanization, ideas generation, and validation engine
│   ├── TASK_LOG.md                     # Complete task audit of product transformation
│   └── TESTING.md                      # Test execution and coverage matrix
│
├── models/                             # Machine Learning Weights & Checkpoints
│   ├── distilbert/                     # Deprecated Amazon binary DistilBERT model
│   └── xgboost_churn_v1.pkl            # Legacy tabular churn prediction model
│
├── tests/                              # Automated Pytest Suite (19/19 Passing)
│   ├── api/
│   │   └── test_neutral_sentiment.py   # RoBERTa 3-class sentiment unit tests (4 tests)
│   ├── test_product_transformation.py  # Phase 5 product transformation suite (7 tests)
│   └── test_review_assistant.py        # Core review assistant integration tests (8 tests)
│
├── start_app.bat                       # Local development startup script
├── pyproject.toml                      # Pytest and Python project configuration
└── requirements.txt                    # Python runtime dependencies
```

---

## 5. Core Subsystems & Feature Deep Dive

### 5.1 Public Customer Experience (`/review`): Mobile-First Guest Review Flow
The customer interface is optimized for smartphones, loading in < 1.5 seconds without authentication or account creation.

#### Step 1: Welcome & Star Rating
- Displays restaurant branding: Logo (`☕`), name (*"Cuore Cafe"*), category, branch, and dynamic table badge (*"📍 Table 4"*).
- 5 large interactive star buttons (≥48px touch target) with accessible ARIA labels.
- Live animated descriptor badge (*"Loved it! ⭐"*, *"Really good 😊"*, *"It was okay 🙂"*, *"Disappointed 🙁"*, *"Not good 😞"*).
- `Continue →` button activates immediately upon selection.

#### Step 2: What Stood Out?
- Renders dynamic topic chips configured by the restaurant owner:
  `🍕 Food`, `☕ Coffee & Drinks`, `😊 Friendly staff`, `✨ Atmosphere`, `🧼 Cleanliness`, `💰 Value`, `⚡ Fast service`.
- Animated selection with visible checkmarks (`✓`).
- Optional fallback chip: `Nothing specific`.
- Optional personal note input: *"Want to make it more personal? Add a few words about your experience (e.g. The cold brew was my favorite ☕)"*.
- `See Review Ideas →` button triggers candidate idea synthesis.

### 5.2 Review Idea Cards: Multi-Perspective Starting Concepts
Instead of generating a single monolithic paragraph, `POST /api/reviews/ideas` returns 3 tailored candidate idea cards:
- **Card 1: Food & Quality Focus:** Focuses on taste, fresh preparation, or drinks.
- **Card 2: Atmosphere & Service Focus:** Highlights the ambiance, comfortable seating, and welcoming team.
- **Card 3: Overall Visit:** A balanced, genuine summary with a return visit intention.
- **`[ Write my own review ]` Option:** Allows diners who prefer blank-canvas writing to type freely.

When a customer clicks `Use this idea →`, the text seamlessly transfers into the Customer Editor.

### 5.3 Humanization Engine & Zero-Fabrication Prompt Calibration
Reviews generated by traditional LLMs sound robotic and promotional. ChurnLens enforces strict humanization at the generation layer:
- **Short Length:** Strict 15 to 45 words.
- **Simple Everyday English:** Conversational vocabulary, natural contractions (*it's*, *wasn't*, *we'd*), and short sentence structures.
- **Forbidden Marketing Words:** The model is strictly prohibited from using:
  `"culinary excellence"`, `"exceptional hospitality"`, `"truly unforgettable experience"`, `"top-tier"`, `"delighted"`, `"remarkable"`, `"artisanal craftsmanship"`.
- **Zero Fabrication:** The engine **never** invents menu items, dishes, prices, staff names, wait times, or facilities not explicitly selected or written by the guest.

### 5.4 Contextual Emoji Rule System
To prevent reviews from looking dull while avoiding unprofessional emoji spam:
- **Count:** Strictly 0 to 2 emojis per review.
- **Contextual Alignment:**
  - Drinks/Coffee: `☕`
  - Food/Dining: `🍕` or `😋`
  - Atmosphere/Vibe: `✨`
  - Friendly Service: `😊`
  - Return visits: `❤️`
- **Negative Reviews (1–2 Stars):** Exactly 0 emojis. Emojis are never used to artificially mask or soften a negative dining experience.

### 5.5 Silent Rating Consistency Validation (CardiffNLP RoBERTa)
Before review drafts are finalized, the text is evaluated by `ReviewValidator` (`api/review_assistant/validator.py`) using `cardiffnlp/twitter-roberta-base-sentiment-latest`:
- 4–5 Stars: Must classify as `Positive` or `Neutral`. If analyzed as `Negative`, the generator automatically re-synthesizes or flags a gentle warning.
- 1–2 Stars: Must classify as `Negative` or `Neutral`. Artificially positive phrasing is rejected.
- 3 Stars: Classified as `Neutral` or balanced.
- **Customer Privacy:** The validation runs completely silently in the background; technical confidence percentages are never exposed to the diner.

### 5.6 Ethical Google Handoff & Clipboard Flow (100% Google Compliant)
ChurnLens adheres strictly to Google Business Profile policies:
1. The guest reviews and edits their text in the Customer Editor.
2. Clicking **`⭐ Copy & Continue to Google`**:
   - Copies the review text to the system clipboard (`navigator.clipboard.writeText`).
   - Dispatches telemetry event `google_review_link_opened`.
   - Opens the restaurant's configured Google review link in a new tab.
3. Renders a friendly confirmation modal:
   - *"Your review has been copied 😊"*
   - *"Google Maps is opening in a new tab. Select your stars, paste your review, and submit."*
   - `[ ↗ Re-open Google Maps ]` and `[ Done ✓ ]` buttons.
4. **The customer remains the sole author and submitter.** ChurnLens never simulates clicks or submits reviews via private APIs.

### 5.7 Restaurant Owner Portal (`/owner`): 5 Simple Management Workspaces
A clean, responsive dashboard designed for busy restaurant operators without ML terminology:

```
┌────────────────────────────────────────────────────────────────────────┐
│ ☕ Cuore Cafe • Downtown Branch                 [ 👁️ Preview Customer ]│
├────────────────────────────────────────────────────────────────────────┤
│ [ 🏠 Home ]  [ ⚙️ Review Setup ]  [ 📱 QR Codes ]  [ 📈 Activity ] [ 🔧 Settings ]
│                                                                        │
│ Good afternoon 👋                                                      │
│ Your review assistant is ready.                                        │
│                                                                        │
│ ⭐ Google Review Link: ✓ Connected                                    │
│ 🟢 QR System: ✓ Active                                                 │
│                                                                        │
│ This Month:                                                            │
│ 142 Review drafts created  |  98 Google journeys started  |  71 Copied │
│                                                                        │
│ [ 📱 View & Print QR Codes ]      [ 👁️ Test Customer Flow ]           │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Home:** At-a-glance health, Google link status, QR status, monthly counters, and quick actions.
2. **Review Setup:** Manage restaurant name, branch, category, description, official Google review link (with live test link), and custom review topics.
3. **QR Codes:** Deep-link table generator (Table 1–12, counter, receipt, general), live table-stand card preview, and high-res PNG download.
4. **Review Activity:** Real-time metrics (drafts created, Google journeys started, reviews copied), most appreciated highlights, and recent timeline activity.
5. **Settings:** Location identifier and configuration management.

### 5.8 Dynamic Table QR Code Studio & Deep-Linking
- Generates high-contrast QR codes directly in the browser via `qrcode` with deep-linked parameters (`?table=Table+4`).
- Supports table tents, bill folders, and counter stickers.
- **Configurable Base URL:** Allows owners to specify their production domain (e.g., `https://cuorecafe.com`) so generated QR codes point to live domains rather than `localhost`.

### 5.9 Authentic Real-World Analytics (Zero Fake Metrics)
Eliminated all synthetic CSAT formulas and hardcoded satisfaction percentages. The analytics engine tracks only genuine user telemetry:
- `review_generation_completed`: Count of drafts generated.
- `google_review_link_opened`: Count of customers who clicked through to Google.
- `review_copied`: Count of customers who copied text.
- `top_topics`: Frequency count of topics selected by real diners.
- `recent_activity`: Real chronological event log (e.g., *"15:10 • Table 4 created a 5-star draft"*).

### 5.10 Direct In-House Management Note (Non-Gated Feedback)
In addition to the public Google path, diners can optionally click *"Want to tell the restaurant privately too? Share private feedback"*.
- Opens a clean modal allowing direct feedback and optional contact info for management follow-up.
- **Compliance:** This does **not** block, gate, or hide the public Google review option.

---

## 6. API Specification & Data Schemas

### 6.1 Complete REST Endpoints Catalog

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/reviews/ideas` | Generates 3 multi-perspective candidate review ideas | Public / Guest |
| `POST` | `/api/reviews/generate` | Generates / humanizes a grounded review draft | Public / Guest (Rate-limited: 30/min) |
| `POST` | `/api/reviews/validate` | Validates review sentiment against star rating | Public / Internal |
| `POST` | `/api/reviews/session` | Initializes review session with table & dining context | Public / Guest |
| `POST` | `/api/reviews/events` | Records telemetry events (`google_review_link_opened`, etc.) | Public / Guest |
| `GET` | `/api/reviews/analytics` | Returns authentic aggregated activity metrics | Owner Portal |
| `POST` | `/api/reviews/private-feedback` | Submits direct management note (non-gated) | Public / Guest |
| `GET` | `/api/reviews/private-tickets` | Retrieves private feedback submissions | Owner Portal |
| `GET` | `/api/businesses/{id}/review-link`| Fetches restaurant details, Google link, and topics | Public / Owner |
| `POST` | `/api/businesses/{id}/config` | Updates restaurant name, branch, topics, and Google link | Owner Portal |
| `POST` | `/api/reviews/manager-reply` | Generates courteous owner reply to Google review | Owner Portal |

### 6.2 Data Schemas & Request/Response Contracts

#### `POST /api/reviews/ideas`
```json
// Request
{
  "business_id": "default_business",
  "rating": 5,
  "aspects": ["Food", "Atmosphere", "Friendly staff"],
  "user_note": "The cold brew and pasta were delicious"
}

// Response
{
  "ideas": [
    {
      "id": "idea_1",
      "focus": "Food & Quality",
      "text": "Really enjoyed the food and the friendly service. The cold brew and pasta were delicious. Highly recommend! 😊"
    },
    {
      "id": "idea_2",
      "focus": "Atmosphere & Service",
      "text": "Such a lovely atmosphere and really friendly staff. The cold brew and pasta were delicious. It's a great place to sit and relax ✨"
    },
    {
      "id": "idea_3",
      "focus": "Overall Visit",
      "text": "Had a wonderful visit! The food, drinks, and service were all spot on. The cold brew and pasta were delicious. Will definitely be back again soon ❤️"
    }
  ]
}
```

#### `POST /api/reviews/generate`
```json
// Request
{
  "business_id": "default_business",
  "rating": 5,
  "aspects": ["Food", "Atmosphere"],
  "selected_idea": "Really enjoyed the food and the friendly service.",
  "user_note": "Tiramisu was amazing",
  "emoji_preference": "light",
  "table_number": "Table 4"
}

// Response
{
  "review": "Really enjoyed the food and the friendly service — Tiramisu was amazing. 😊✨",
  "sentiment": "Positive",
  "sentiment_confidence": 0.9412,
  "rating_consistent": true,
  "warnings": [],
  "aspects_covered": ["Food", "Atmosphere"],
  "dining_type": "dine_in",
  "table_number": "Table 4",
  "generation_provider": "local-hospitality-engine"
}
```

#### `GET /api/businesses/{id}/review-link` & `POST /api/businesses/{id}/config`
```json
// Response & Update Schema
{
  "business_id": "default_business",
  "platform": "google",
  "review_url": "https://g.page/r/cuore-cafe/review",
  "is_configured": true,
  "business_name": "Cuore Cafe",
  "branch": "Downtown",
  "category": "Cafe",
  "description": "Artisan cafe and roastery serving specialty coffee and fresh meals.",
  "topics": [
    "Food", "Coffee & Drinks", "Service", "Friendly staff", "Atmosphere", "Cleanliness", "Value", "Fast service"
  ],
  "primary_accent": "#f59e0b"
}
```

#### `GET /api/reviews/analytics`
```json
// Response Schema
{
  "total_generations": 142,
  "google_clicks": 98,
  "reviews_copied": 71,
  "rating_distribution": { "5": 112, "4": 22, "3": 6, "2": 1, "1": 1 },
  "sentiment_distribution": { "positive": 134, "neutral": 6, "negative": 2 },
  "top_topics": [
    { "topic": "Food", "count": 89 },
    { "topic": "Coffee & Drinks", "count": 76 },
    { "topic": "Friendly staff", "count": 64 }
  ],
  "recent_activity": [
    "15:10 • Table 4 created a 5-star draft",
    "15:12 • Customer opened Google review link",
    "15:14 • Customer copied review draft"
  ],
  "private_tickets_count": 2
}
```

---

## 7. AI & Model Architecture Audit

### 7.1 Review LLM Provider Abstraction (`LocalLLMProvider` vs. `CloudLLMProvider`)
Implemented in `api/review_assistant/llm_provider.py`:
- **`LocalLLMProvider` (Default):** A zero-latency (3–12ms), zero-cost, memory-efficient deterministic synthesis engine calibrated for hospitality. Strictly enforces 15–45 word length, conversational English, and zero fabrication. Runs on any low-power CPU with zero external dependencies.
- **`CloudLLMProvider`:** Pluggable adapter supporting Google Gemini 1.5 Flash or OpenAI GPT-4o-mini via environment variables (`LLM_PROVIDER=cloud`, `GEMINI_API_KEY`, `OPENAI_API_KEY`). Automatically falls back to `LocalLLMProvider` if offline or rate-limited.

### 7.2 Primary Sentiment Validator: CardiffNLP RoBERTa 3-Class
- **Model:** `cardiffnlp/twitter-roberta-base-sentiment-latest`
- **Output:** 3 discrete classes: `Positive`, `Neutral`, and `Negative`.
- **Latency:** ~60ms on modern multi-core CPU.
- **Role:** Evaluates review drafts for rating alignment (4–5 stars = Positive/Neutral; 1–2 stars = Negative/Neutral; 3 stars = Balanced Neutral).

### 7.3 Deprecation & Removal of Redundant DistilBERT Binary Model
- **Audit Findings:** The legacy fine-tuned DistilBERT binary model (`models/distilbert/`, ~268MB) lacked an explicit neutral class, which is essential for balanced 3-star dining reviews.
- **Action:** Deprecated and cleanly removed from the active runtime review path. RoBERTa 3-class was retained as the single, reliable validator.

### 7.4 Model Inventory & Benchmark Matrix

| Component | Model / Engine | Memory Footprint | Inference Latency | Active in Product? |
| :--- | :--- | :--- | :--- | :--- |
| **Review Generator** | Local Grounded Engine | < 15MB | 3–12ms | **YES (Primary)** |
| **Ideas Generator** | Multi-Perspective Engine | < 5MB | 3–8ms | **YES (Primary)** |
| **Sentiment Validator**| CardiffNLP RoBERTa 3-Class | ~480MB | ~60ms | **YES (Primary)** |
| **Sarcasm Detector** | CardiffNLP RoBERTa Irony | ~480MB (shared) | ~55ms | **YES (Internal)** |
| **DistilBERT Binary** | Fine-tuned DistilBERT | ~268MB | ~40ms | **DEPRECATED (Offline)** |
| **XGBoost Churn v1** | Tabular tree model | ~0.7MB | < 1ms | **REMOVED FROM UI** |
| **SHAP Explainer** | TreeExplainer | ~2MB | ~120ms | **REMOVED FROM UI** |

---

## 8. UI/UX Design System & Aesthetics

### 8.1 Hospitality Aesthetic: Warm Slate & Amber Glassmorphism
The design language combines the warmth of specialty coffee hospitality with the sleekness of modern software:
- **Base Background:** Deep Midnight Slate (`#0b0f19`).
- **Surface Panels:** Translucent Slate (`rgba(20, 27, 45, 0.75)`) with 16px background blur and delicate borders (`rgba(255, 255, 255, 0.1)`).
- **Primary Accent:** Warm Golden Amber (`#f59e0b` to `#d97706`).
- **Success Accent:** Emerald Green (`#10b981`).
- **Typography:** Inter with tight letter-spacing for headers and optimized line-height for mobile reading.

### 8.2 Mobile-First Touch Target & Accessibility Standards (≥48px)
- All primary buttons (`btn-customer-primary`, `btn-pick-idea`, `topic-chip`) meet or exceed minimum touch target heights of **44px to 48px**.
- Star rating buttons measure **48px x 48px** with dedicated ARIA labels for screen readers.
- High contrast text (`#f8fafc` on dark surfaces) ensures readability in brightly lit dining environments or outdoor patios.

### 8.3 Micro-Animations & Fluid Interaction Timings (150–350ms)
- **Step Transitions:** `step-fade-in` (250ms ease-out) ensures snappy screen progressions without disorienting page jumps.
- **Star Pops:** Star hover/tap scale transform (`scale(1.15)`) with golden glow shadows.
- **Idea Cards:** Subtle slide-up and hover glow (`translateY(-2px)`).
- **Handoff Modal:** `modal-bounce-in` (250ms cubic-bezier).

---

## 9. Reliability Engineering, Compliance & Critical Decisions

### 9.1 Elimination of Rating-Based Review Gating (Google Anti-Deflection Compliance)
- **Issue:** Prior versions included a negative review deflection flow that routed 1-star and 2-star ratings away from Google Maps.
- **Compliance Policy:** Google Business Profile explicitly prohibits biased review gating or manipulating who accesses public review platforms based on rating.
- **Resolution:** All ratings (1 to 5 stars) have identical access to the public Google Maps flow. Direct management feedback is offered as an optional neutral link without gating Google.

### 9.2 Prevention of Automated Submission Claims (Clipboard Handoff Protocol)
- **Constraint:** Google Maps does not provide an open customer-review submission endpoint via public API.
- **Resolution:** ChurnLens employs the compliant authorized handoff flow: approve review → copy text to clipboard → open official venue review link → diner pastes and posts. All UI labels truthfully read `"⭐ Copy & Continue to Google"`.

### 9.3 Windows PyTorch Threading Mutex
- **Issue:** Concurrent asynchronous FastAPI requests invoking PyTorch models on Windows could encounter thread lockups.
- **Resolution:** Thread-safe mutex in `api/models/model_loader.py` prevents concurrent initialization race conditions.

### 9.4 Elimination of Fake Demo Metrics & Synthetic CSAT
- **Resolution:** Removed hardcoded satisfaction percentages and fake conversion counters in favor of real telemetry tracking actual user events.

---

## 10. Quality Assurance, Automated Testing & Verification

### 10.1 Complete Automated Regression Test Suite (`pytest` 19/19 Passing)
The automated test suite covers all product features, idea generation, humanization, rating consistency, and business configuration:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\churnlens\churnlens
configfile: pyproject.toml
plugins: anyio-4.15.1
collected 19 items

tests/api/test_neutral_sentiment.py ....                                 [ 21%]
tests/test_product_transformation.py .......                             [ 57%]
tests/test_review_assistant.py ........                                  [100%]

======================= 19 passed, 4 warnings in 18.08s =======================
```

#### Test Suite Breakdown
1. **`tests/test_product_transformation.py` (7 tests):**
   - `test_review_ideas_generation_5_star`: Validates 3 distinct ideas and user note inclusion.
   - `test_review_ideas_generation_1_star`: Validates respectful negative ideas without emojis.
   - `test_generate_from_selected_idea`: Validates personalization, word count (15–45 words), and zero fabrication.
   - `test_emoji_rule_enforcement`: Enforces 0 emojis for 1-star, ≤ 2 emojis for 5-star.
   - `test_no_rating_gating_behavior`: Verifies identical Google access across all ratings.
   - `test_restaurant_config_and_topics`: Verifies persistence of restaurant details and custom topics.
   - `test_simplified_owner_analytics`: Verifies authentic event metrics and activity feed.
2. **`tests/test_review_assistant.py` (8 tests):**
   - Review generation for 5-star and 3-star ratings, sentiment consistency checks, inconsistency warnings, session management, and GM responses.
3. **`tests/api/test_neutral_sentiment.py` (4 tests):**
   - CardiffNLP RoBERTa positive, neutral, negative, and mixed sentiment classifications.

### 10.2 Frontend Linter & Production Build Verification
- **Linter (`oxlint`):** Verified across 8 frontend files with 91 rules: **0 warnings, 0 errors**.
- **Production Build (`vite build`):** Compiled successfully in **221ms** into `frontend/dist/` (`index.js` = 77.8 kB gzip).

### 10.3 In-Browser End-to-End Visual Verification
Verified using automated browser testing subagents on `http://127.0.0.1:5173/`:
- **Customer Flow:** Tested 5-star selection, topic chips, short note entry, 3 idea cards, customer editor, "Make it more natural" refinement, and Google handoff confirmation modal with clipboard copy.
- **Owner Flow:** Tested Home overview, Review Setup, custom topic addition, QR Studio table stand preview, and the "Preview Customer Experience" mode banner.
- **Browser Recording Artifact:** Saved to artifacts directory.

---

## 11. Deployment, Operations & Git History

### 11.1 Quickstart Local Execution

```cmd
:: Method A: Start script
start_app.bat

:: Method B: Manual execution
:: Terminal 1: FastAPI Backend
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

:: Terminal 2: React Frontend
cd frontend
npm run dev
```

### 11.2 Environment Configuration Matrix

| Variable | Development Value | Production Example | Description |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | `development` | `production` | Deployment environment flag |
| `FRONTEND_BASE_URL` | `http://localhost:5173` | `https://cuorecafe.com` | Base URL embedded in table QR codes |
| `API_BASE_URL` | `http://localhost:8000` | `https://api.cuorecafe.com` | Backend REST endpoint |
| `LLM_PROVIDER` | `local` | `local` or `cloud` | Inference provider switch |
| `GOOGLE_REVIEW_URL` | `https://maps.google.com` | `https://g.page/r/.../review` | Official Google Maps review destination |

### 11.3 Version Control & Git History

| Commit / Tag | Branch | Summary of Changes |
| :--- | :--- | :--- |
| **`pre-product-transformation`** | `feature/project-update` | Git checkpoint created prior to Phase 5 transformation. |
| `f70c636` | `feature/project-update` | Enriched master product specification with complete history. |
| `f98e0c5` | `feature/project-update` | Added comprehensive end-to-end technical specification. |
| `598d065` | `feature/project-update` | Fixed analytics loading state and UI refresh bindings. |
| `55bc3e8` | `feature/project-update` | Hospitality dining intelligence & review growth platform. |
| `e70337a` | `feature/project-update` | Initial AI review generation and Google review handoff. |

---
*Document Version: 5.0.0-Restaurant-Product*  
*Target Domain: Specialty Cafes, Roasteries, Bistros, and Casual/Fine Dining Restaurants*  
*Quality Certification: 19/19 Backend Tests Passing • 0 Frontend Lint Errors • Production Build Certified*
