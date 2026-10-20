import os
import tempfile
from pathlib import Path

import pytest

# Stable local credentials for isolated API tests; never used by app deployments.
os.environ["ENVIRONMENT"] = "test"
os.environ["OWNER_PASSWORD"] = "test-only-owner-password"
os.environ["OWNER_SESSION_SECRET"] = "test-only-signing-secret-at-least-32-characters"
os.environ["REVIEW_DB_PATH"] = str(Path(tempfile.gettempdir()) / f"nasta-gh-test-{os.getpid()}.sqlite3")
os.environ["BUSINESS_LINKS_PATH"] = str(Path(tempfile.gettempdir()) / f"nasta-gh-links-{os.getpid()}.json")


def pytest_addoption(parser):
    parser.addoption(
        "--run-model-tests",
        action="store_true",
        default=False,
        help="run tests marked model_dependent (may download large models)",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-model-tests"):
        return
    skip_model_tests = pytest.mark.skip(
        reason="model_dependent: rerun with --run-model-tests after models are available"
    )
    for item in items:
        if "model_dependent" in item.keywords:
            item.add_marker(skip_model_tests)


@pytest.fixture(autouse=True)
def isolate_nlp_models(monkeypatch, request):
    """Keep ordinary tests offline while preserving real-model tests as explicit opt-in."""
    if "model_dependent" in request.node.keywords:
        return

    from api.models.sentiment import sentiment_model
    from api.models.sarcasm import sarcasm_model

    def sentiment_prediction(text):
        lowered = text.lower()
        positive_terms = ("wonderful", "excellent", "great", "good", "love", "delicious", "enjoyed", "fresh", "fantastic", "lovely", "tasty", "friendly", "amazing", "best")
        negative_terms = ("terrible", "poor", "horrible", "disappointed", "cold", "rude", "never again", "wasting", "broke", "bad", "slow")
        pos = any(term in lowered for term in positive_terms)
        neg = any(term in lowered for term in negative_terms)
        if pos and neg:
            return {"positive": 0.25, "neutral": 0.5, "negative": 0.25, "inference_time_ms": 0}
        if pos:
            return {"positive": 0.9, "neutral": 0.05, "negative": 0.05, "inference_time_ms": 0}
        if neg:
            return {"positive": 0.05, "neutral": 0.05, "negative": 0.9, "inference_time_ms": 0}
        return {"positive": 0.1, "neutral": 0.8, "negative": 0.1, "inference_time_ms": 0}

    monkeypatch.setattr(sentiment_model, "predict", sentiment_prediction)
    monkeypatch.setattr(
        sarcasm_model,
        "predict",
        lambda text: {"sarcasm_probability": 0.0, "inference_time_ms": 0},
    )
