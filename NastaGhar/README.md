# NastaGhar Frontend & Review System (Product A)

This directory contains the customer-facing Review Assistant experience, restaurant ambience presentation, and restaurant owner portal for **VRAJA AI / NastaGhar**.

## Key Features (Product A Customer Experience)

1. **Automatic Browser Language Detection:**
   - Automatically detects user language from `navigator.languages` (with `navigator.language` fallback).
   - Supported languages: **Gujarati (`gu`)**, **Hindi (`hi`)**, and **English (`en`)** (fallback).
   - Zero manual language-selection friction (no manual picker buttons).
   - Consistent localized UI strings across ratings, topics, suggestions, editor, private feedback, and Google Maps handoff.

2. **3-Style Grounded AI Suggestions:**
   - Up to 3 distinct suggestion styles:
     - `Short & Natural` (1 sentence, concise)
     - `Detailed & Expressive` (2 sentences, balanced experience)
     - `Simple & Personal` (1–2 sentences, first-person subjective)
   - Strict factual grounding: Zero hallucinated claims (no unverified staff politeness, cleanliness, family visits, or revisit promises).
   - Resilient offline fallback matrix with explicit `🔄 Retry` button.

3. **Automatic Draft Recovery:**
   - Real-time `sessionStorage` draft persistence for selected rating, topics, personal notes, and custom review drafts.
   - Strictly isolated by business ID (`nastaGhar_draft_${businessId}`) with 2-hour TTL expiration.
   - Cleanly purges drafts upon successful review handoff (Google Maps redirect) or completed private feedback to prevent data leakage on shared devices.

4. **Duplicate Submission Protection:**
   - Frontend submission locks (`isSubmittingPrivate`, `isFetchingIdeasRef`, debounced card clicks).
   - Backend in-memory idempotency deduplication (60-second window) in `ReviewService`.

5. **Anonymous Private Feedback:**
   - Low-friction private channel for direct feedback to restaurant management.
   - Contact info (name, phone, email) is 100% optional.
   - Ingests into backend SQLite `private_tickets` store.

6. **Accessible Customer Experience:**
   - Semantic HTML and ARIA states (`aria-pressed`, `aria-expanded`, `aria-controls`).
   - Touch targets >= 44px min-height (WCAG 2.5.5 compliance).
   - High-contrast `:focus-visible` styling for full keyboard navigation.

---

## Directory Structure

```text
NastaGhar/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CustomerReview.jsx           # Core customer review experience
│   │   │   ├── OwnerPortal.jsx              # Owner analytics and configuration
│   │   │   ├── RestaurantWorld.jsx          # Ambient visual scene presentation
│   │   │   ├── RestaurantWorld.css
│   │   │   └── NastaGharRestaurantScene.jsx
│   │   ├── lib/
│   │   │   └── api.js                       # API client utilities
│   │   ├── App.jsx                          # Main routing & view switch
│   │   ├── index.css                        # Design system & accessibility styling
│   │   └── main.jsx
│   ├── public/
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
├── assets/
│   ├── darshan-host.png
│   ├── scene-phone.webp
│   └── scene-wide.webp
└── README.md
```

---

## Development

```bash
cd NastaGhar/frontend
npm install
npm run dev
# Running on http://127.0.0.1:5173
```

Direct QR customer test URL:
```text
http://127.0.0.1:5173/review?table=Table+4&business_id=default_business
```

## Verification

```bash
# Frontend production build (< 120ms)
npm run build

# Backend review assistant tests (from repo root)
pytest Project_Files/Tests/test_review_assistant.py -v
```
