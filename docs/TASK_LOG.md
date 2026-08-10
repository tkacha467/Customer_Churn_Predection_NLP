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

Files intentionally not modified:
- [api/preprocessing/text_cleaner.py](file:///d:/churnlens/api/preprocessing/text_cleaner.py)
- [api/models/model_loader.py](file:///d:/churnlens/api/models/model_loader.py)
- [api/fusion/engine.py](file:///d:/churnlens/api/fusion/engine.py)
- [api/fusion/explainer.py](file:///d:/churnlens/api/fusion/explainer.py)
- [dashboard/app.py](file:///d:/churnlens/dashboard/app.py)
- Custom trained model binaries under `models/distilbert_amazon`
