# ChurnLens — Product Information Architecture

## 1. Information Architecture Overview
ChurnLens provides two distinct, focused user experiences:

```
                            CHURNLENS
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
PUBLIC CUSTOMER EXPERIENCE                      RESTAURANT OWNER PORTAL
  Route: /review or /?table=Table+4               Route: /owner
  (Mobile-first QR guest flow)                    (Restaurant management SaaS)
```

---

## 2. Public Customer Experience (`/review`)

Target flow duration: **30 to 60 seconds**.

```
[ Step 1: Welcome & Star Rating ]
  - Restaurant name, category, and table badge
  - 5 large interactive accessible stars (1 to 5)
  - Rating descriptor ("Loved it! ⭐", "Really good 😊", etc.)
            │
            ▼
[ Step 2: What Stood Out? ]
  - Selected highlights from restaurant setup (Food, Coffee, Service, Atmosphere, etc.)
  - Multiselect animated chips
  - "Nothing specific" fallback
  - Optional short note: "Want to make it more personal?"
            │
            ▼
[ Step 3: Review Idea Cards ]
  - 3 candidate review cards generated via /api/reviews/ideas:
    * Option 1: Food & Quality focus
    * Option 2: Atmosphere & Staff focus
    * Option 3: Overall experience
  - [ Pick this idea → ] on each card
  - [ Write my own review ] option
            │
            ▼
[ Step 4: Customer Editor ]
  - Clean textarea with editable text
  - Character counter
  - [ ✨ Make it more natural ] tool (re-phrases without inventing facts)
  - [ 🔄 Try another idea ]
  - [ ⭐ Copy & Continue to Google ] primary CTA
  - Optional: [ Share private feedback ] link
            │
            ▼
[ Step 5: Google Handoff & Confirmation ]
  - Review text copied to clipboard
  - Telemetry event `google_review_link_opened` logged
  - Google Maps official review URL opened in new tab
  - Friendly confirmation modal with 3 quick instructions:
    1. Select stars on Google
    2. Paste review text
    3. Post review
```

---

## 3. Restaurant Owner Portal (`/owner`)

Designed with zero technical jargon. Structured into 5 practical tabs:

1. **Home**:
   - Greeting & restaurant branch status
   - Connected Google Review Link status
   - Active QR system status
   - Monthly activity summary (drafts created, Google journeys started, reviews copied)
   - Quick Actions: `[ View & Print QR Codes ]` and `[ Test Customer Flow ]`
   - Setup checklist
2. **Review Setup**:
   - Restaurant name, branch, category, description
   - Official Google review link with `[ Test Link ↗ ]`
   - Manageable review topics with `+ Add custom topic`
3. **QR Codes**:
   - Generator for Table (1-12+), Counter, Receipt, or General placement
   - Configurable base URL (development vs. production domain)
   - Instant live table standee preview
   - Download individual QR (PNG) or select common tables
4. **Review Activity**:
   - Authentic event metrics (no fake data)
   - Drafts created vs. Google review links opened
   - Top customer highlights breakdown
   - Real-time recent activity feed
5. **Settings**:
   - Restaurant identifier, Google URL status, customer preview trigger
