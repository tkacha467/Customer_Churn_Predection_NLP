import os
import sys
import types
import tempfile
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[2]
_scripts_dir = _repo_root / "Project_Files" / "Scripts"
_root_scripts_dir = _repo_root / "scripts"
if "scripts" not in sys.modules:
    scripts_mod = types.ModuleType("scripts")
    scripts_mod.__path__ = [str(_scripts_dir), str(_root_scripts_dir)]
    sys.modules["scripts"] = scripts_mod
elif hasattr(sys.modules["scripts"], "__path__") and str(_root_scripts_dir) not in sys.modules["scripts"].__path__:
    sys.modules["scripts"].__path__.append(str(_root_scripts_dir))

# Support case-insensitive import compatibility for 'Backend'
import importlib
import importlib.abc
import importlib.util
import types

class _AliasModule(types.ModuleType):
    """Non-destructive module proxy for Backend.* -> backend.* imports."""
    def __init__(self, alias_name, target_module):
        super().__init__(alias_name)
        object.__setattr__(self, "_target_module", target_module)

    def __getattr__(self, item):
        return getattr(object.__getattribute__(self, "_target_module"), item)

    def __setattr__(self, key, value):
        setattr(object.__getattribute__(self, "_target_module"), key, value)

    def __delattr__(self, item):
        delattr(object.__getattribute__(self, "_target_module"), item)

    def __dir__(self):
        return dir(object.__getattribute__(self, "_target_module"))

class _AliasLoader(importlib.abc.Loader):
    def __init__(self, alias_name, target_module):
        self.alias_name = alias_name
        self.target_module = target_module
    def create_module(self, spec):
        proxy = _AliasModule(self.alias_name, self.target_module)
        if hasattr(self.target_module, "__path__"):
            object.__setattr__(proxy, "__path__", self.target_module.__path__)
        return proxy
    def exec_module(self, module):
        pass

class BackendAliasFinder(importlib.abc.MetaPathFinder):
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        if fullname == "Backend" or fullname.startswith("Backend."):
            real_name = "backend" + fullname[len("Backend"):]
            real_mod = importlib.import_module(real_name)
            return importlib.util.spec_from_loader(fullname, _AliasLoader(fullname, real_mod))
        return None

sys.meta_path.insert(0, BackendAliasFinder())
import backend.app

import pytest

@pytest.fixture(autouse=True)
def _reset_auth_rate_limits_per_test():
    try:
        from backend.app.core.auth.auth import reset_rate_limits
        reset_rate_limits()
    except Exception:
        pass
    try:
        from backend.app.api.service import review_service
        review_service._rate_limits.clear()
    except Exception:
        pass
    try:
        import asyncio
        from backend.app.core.auth.security_store import SecurityStore
        asyncio.run(SecurityStore.clear_all_security_keys())
    except Exception:
        pass
    yield
    try:
        from backend.app.core.auth.auth import reset_rate_limits
        reset_rate_limits()
    except Exception:
        pass
    try:
        from backend.app.api.service import review_service
        review_service._rate_limits.clear()
    except Exception:
        pass
    try:
        import asyncio
        from backend.app.core.auth.security_store import SecurityStore
        asyncio.run(SecurityStore.clear_all_security_keys())
    except Exception:
        pass

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

    from backend.app.models.sentiment import sentiment_model
    from backend.app.models.sarcasm import sarcasm_model

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
