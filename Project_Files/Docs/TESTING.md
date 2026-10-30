# ChurnLens — Testing & Quality Assurance Suite

## 1. Overview
The ChurnLens testing suite ensures stability, zero-fabrication generation, rating consistency, Google policy compliance, and responsive user flows across both customer and owner portals.

---

## 2. Test Execution

### Backend Tests (pytest)
```bash
# Run complete test suite
python -m pytest

# Run specific product transformation suite
python -m pytest tests/test_product_transformation.py

# Run review assistant tests
python -m pytest tests/test_review_assistant.py
```

### Frontend Lint & Production Build
```bash
cd frontend

# Run linting (oxlint)
npm run lint

# Run Vite production bundle build
npm run build
```

---

## 3. Test Coverage Matrix

| Test Suite | File | Tests | Key Validations |
| :--- | :--- | :--- | :--- |
| **Product Transformation** | `tests/test_product_transformation.py` | 7 tests | - 5-star & 1-star idea generation<br>- Multi-perspective idea distinctness<br>- Zero-fabrication check<br>- 15-45 word count limits<br>- Tasteful contextual emojis (0-2)<br>- Zero rating gating<br>- Restaurant config persistence<br>- Authentic owner analytics |
| **Review Assistant Core** | `tests/test_review_assistant.py` | 8 tests | - 5-star review generation<br>- 3-star balanced generation<br>- Sentiment & star consistency<br>- Inconsistent review detection<br>- Session tracking & analytics<br>- GM response generation<br>- Private feedback handling |
| **Neutral Sentiment NLP** | `tests/api/test_neutral_sentiment.py` | 4 tests | - CardiffNLP RoBERTa 3-class classification<br>- Neutral threshold validation<br>- Sarcasm fusion rules |

Total automated test count: **19 tests (100% passing)**.
