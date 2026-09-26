# Change Log

## Neutral Sentiment Enhancement

Status: Completed

Changes:
- Added three-class sentiment handling.
- Added explicit NEUTRAL output.
- Preserved existing POSITIVE and NEGATIVE behavior.
- Preserved existing churn pipeline.
- Preserved existing risk scoring.
- Preserved existing dashboard architecture.
- Added regression tests.

Files modified:
- [api/main.py](file:///d:/churnlens/api/main.py)
- [scripts/flipkart_integrity.py](file:///d:/churnlens/scripts/flipkart_integrity.py)
- [tests/api/test_neutral_sentiment.py](file:///d:/churnlens/tests/api/test_neutral_sentiment.py)
- [start_app.bat](file:///d:/churnlens/start_app.bat)

## Interactive Showcase Webpage (PPT Showcase)

Status: Completed

Changes:
- Created a standalone premium interactive presentation webpage explaining ChurnLens.
- Built-in slide sections covering Data Ingestion, RFM, XGBoost, and the NLP Fusion Pipeline.
- Added a client-side Interactive Risk Engine Simulator to adjust Recency, Frequency, Sentiment, and Star Ratings, recalculating risk scores dynamically.
- Integrated background Canvas particle networking and fluid CSS animations.
- Configured `start_app.bat` to automatically open `showcase/index.html` on platform startup.

Files created:
- [showcase/index.html](file:///d:/churnlens/showcase/index.html)
- [showcase/index.css](file:///d:/churnlens/showcase/index.css)
- [showcase/index.js](file:///d:/churnlens/showcase/index.js)

Files modified:
- [start_app.bat](file:///d:/churnlens/start_app.bat)
- [docs/TASK_LOG.md](file:///d:/churnlens/docs/TASK_LOG.md)

## AI-Assisted Customer Review & Intelligence Platform Productization

Status: Completed

Changes:
- Added isolated `api/review_assistant/` module for calibrated review generation and rating-consistency validation.
- Built strict anti-fabrication prompt engine and natural synthesizer (never invents unmentioned dishes, staff actions, or facts).
- Integrated sentiment & sarcasm fusion validation layer with rating calibration.
- Added official Google Review request URL management and explicit customer approval handoff workflow.
- Added privacy-conscious product analytics and session tracking endpoints.
- Upgraded React frontend into a unified tabbed SaaS interface featuring Customer Review Assistant, Integrity Engine Playground, and Merchant Business Console.
- Added comprehensive unit tests in `tests/test_review_assistant.py` with 100% test pass rate.

Files created:
- `api/review_assistant/__init__.py`
- `api/review_assistant/schemas.py`
- `api/review_assistant/prompts.py`
- `api/review_assistant/generator.py`
- `api/review_assistant/validator.py`
- `api/review_assistant/google_reviews.py`
- `api/review_assistant/service.py`
- `api/review_assistant/routes.py`
- `frontend/src/components/ReviewAssistant.jsx`
- `frontend/src/components/IntegrityPlayground.jsx`
- `frontend/src/components/BusinessConsole.jsx`
- `tests/test_review_assistant.py`

Files modified:
- `api/main.py`
- `frontend/src/App.jsx`
- `frontend/src/index.css`
- `requirements.txt`
- `docs/TASK_LOG.md`
