# Review Assistant Architecture & Humanization Engine

## 1. System Architecture
```
                         GUEST BROWSER
                               │
            POST /api/reviews/ideas (rating, topics, note)
                               ▼
                        FASTAPI BACKEND
                               │
                      REVIEW LLM PROVIDER
              (LocalLLMProvider / CloudLLMProvider)
                               │
                      3 CANDIDATE IDEAS
                               │
            Guest selects idea & edits in browser
                               │
           POST /api/reviews/generate (with selected_idea)
                               │
             Zero-Fabrication Humanization Engine
                               │
                   Rating Consistency Check
             (CardiffNLP RoBERTa 3-Class Validator)
                               │
                     Final Editable Draft
                               │
               Copy to Clipboard & Google Handoff
```

---

## 2. Review Idea Generation Mechanism (`POST /api/reviews/ideas`)
Instead of overwhelming the diner with a single long AI paragraph, ChurnLens generates 3 distinct perspectives:
- **Idea 1 (Taste/Product focus)**: Celebrates coffee, food, or pastries if selected.
- **Idea 2 (Atmosphere/Staff focus)**: Highlights the vibe, seating, and friendly service.
- **Idea 3 (Overall experience)**: A warm, concise summary with a return visit intention.

Each candidate idea is grounded strictly in facts provided by the diner.

---

## 3. Humanization Engine Principles
1. **Simple Everyday English**:
   - Short sentences (1-3 sentences total).
   - Natural contractions (*"it's"*, *"wasn't"*, *"we'd"*).
   - Natural punctuation.
2. **Length Enforced**:
   - Standard 15 to 45 words.
3. **Forbidden Corporate Marketing Jargon**:
   - Strictly forbids phrases like: *"culinary excellence"*, *"exceptional hospitality"*, *"truly unforgettable experience"*, *"top-tier"*, *"delighted"*, *"artisanal craftsmanship"*.
4. **Tasteful Contextual Emoji System**:
   - Uses 0 to 2 emojis maximum.
   - Positive visits: `☕` for drinks, `🍕`/`😋` for food, `✨` for ambiance, `😊` for friendly staff, `❤️` for return visits.
   - 3-Star visits: Neutral `🙂` or no emojis.
   - 1-2 Star visits: Exactly 0 emojis (never artificially masks negative experiences).
5. **Zero Fabrication**:
   - NEVER invents dishes, staff names, prices, wait times, or facilities not provided by the diner.

---

## 4. Rating Consistency Validation
Before presentation, reviews pass through `api/review_assistant/validator.py`:
- 4-5 Stars evaluated against CardiffNLP RoBERTa: must not evaluate as `Negative`.
- 1-2 Stars: must not evaluate as `Positive`.
- 3 Stars: balanced neutrality.
- The validation check operates silently; no technical probability scores are shown to the diner.
