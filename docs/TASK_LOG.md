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

Files intentionally not modified:
- [api/preprocessing/text_cleaner.py](file:///d:/churnlens/api/preprocessing/text_cleaner.py)
- [api/models/model_loader.py](file:///d:/churnlens/api/models/model_loader.py)
- [api/fusion/engine.py](file:///d:/churnlens/api/fusion/engine.py)
- [api/fusion/explainer.py](file:///d:/churnlens/api/fusion/explainer.py)
- [dashboard/app.py](file:///d:/churnlens/dashboard/app.py)
- Custom trained model binaries under `models/distilbert_amazon`
