import os
import warnings
import ipaddress

# Suppress HF Hub unauthenticated warnings and progress bars
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*HF_TOKEN.*")
warnings.filterwarnings("ignore", message=".*unauthenticated requests.*")
warnings.filterwarnings("ignore", message=".*RobertaForSequenceClassification.*")

from dotenv import load_dotenv

load_dotenv()

from typing import Any
import logging
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
import time

logger = logging.getLogger("backend.app")

GENERIC_500_DETAIL = "An internal server error occurred. Please contact support if the issue persists."

def _is_safe_500_detail(detail: Any) -> bool:
    """Checks if an error detail string is safe for client exposure without leaking internal info."""
    if not isinstance(detail, str) or not detail.strip():
        return False
    lowered = detail.lower()
    leak_indicators = [
        "traceback", "exception:", "syntaxerror", "operationalerror",
        "select *", "select ", "insert into", "delete from", "sqlite3.",
        "/", "\\", "c:\\", "token=", "secret=", "password=", "errno",
        "failed to load business configuration: ", "failed to archive template: ",
        "failed to persist document: ", "failed to save image: "
    ]
    return not any(ind in lowered for ind in leak_indicators)

def get_allowed_hosts() -> list[str]:
    """
    Configures trusted hostnames for TrustedHostMiddleware (SEC-05).
    - In staging and production, ALLOWED_HOSTS must be explicitly configured.
      Missing configuration or wildcard '*' fails closed immediately.
    - In development and test, defaults to safe local and test hosts
      ('localhost', '127.0.0.1', 'testserver', '::1') if unconfigured.
    """
    env = os.getenv("ENVIRONMENT", "development").strip().lower()
    raw = os.getenv("ALLOWED_HOSTS", "").strip()
    hosts = [h.strip() for h in raw.split(",") if h.strip()] if raw else []

    if env in ("production", "staging"):
        if not hosts:
            raise RuntimeError(
                f"ALLOWED_HOSTS must be explicitly configured in '{env}' environment. "
                "Specify a comma-separated list of trusted hostnames without wildcards."
            )
        if "*" in hosts:
            raise RuntimeError(
                f"Wildcard '*' is strictly prohibited in ALLOWED_HOSTS for '{env}' environment."
            )
        return hosts

    # Development and test environments
    if not hosts:
        return ["localhost", "127.0.0.1", "testserver", "::1"]

    return hosts

# Import Canonical Modular Architecture
from backend.app.config.settings import settings
from backend.app.preprocessing.text_cleaner import text_cleaner
from backend.app.models.sentiment import sentiment_model
from backend.app.models.sarcasm import sarcasm_model
from backend.app.fusion.engine import fusion_engine
from backend.app.fusion.explainer import explainer

from backend.app.api import review_router
from backend.app.core.auth.auth import require_owner
from backend.app.api.routes import get_client_ip
from backend.app.api.service import review_service

app = FastAPI(title="NLP Integrity API", description="Modular Context-Aware Sentiment Pipeline")

_environment = os.getenv("ENVIRONMENT", "development").lower()
_cors_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
    ).split(",")
    if origin.strip()
]
def validate_environment_config(env: str | None = None) -> None:
    """
    Validates required production and staging security invariants at boot time.
    Enforces strict fail-closed policy, Cloudflare Turnstile bot challenge configuration,
    persistent database paths, and secure CORS origins.
    """
    _env = (env or os.getenv("ENVIRONMENT", "development")).strip().lower()
    if _env not in ("production", "staging"):
        return

    # 1. Session secret length
    session_secret = os.getenv("OWNER_SESSION_SECRET", "").strip()
    if len(session_secret) < 32:
        raise RuntimeError(f"OWNER_SESSION_SECRET must contain at least 32 characters in {_env}")

    # 2. Redis / Valkey URL
    redis_url = os.getenv("REDIS_URL", "").strip() or os.getenv("VALKEY_URL", "").strip()
    if not redis_url:
        raise RuntimeError(f"REDIS_URL must be configured in '{_env}' for distributed security state")

    # 3. Security HMAC secret
    hmac_secret = os.getenv("SECURITY_HMAC_SECRET", "").strip()
    if len(hmac_secret) < 32:
        raise RuntimeError(f"SECURITY_HMAC_SECRET must contain at least 32 characters in '{_env}'")

    # 4. Redis failure policy
    redis_policy = os.getenv("REDIS_FAILURE_POLICY", "fail_closed").strip().lower()
    if not redis_policy or redis_policy != "fail_closed":
        raise RuntimeError(
            f"REDIS_FAILURE_POLICY must be set to 'fail_closed' in '{_env}' (received '{redis_policy}')"
        )

    # 5. Cloudflare Turnstile bot protection
    turnstile_enabled = os.getenv("TURNSTILE_ENABLED", "true").strip().lower()
    if turnstile_enabled not in ("true", "1", "yes"):
        raise RuntimeError(
            f"TURNSTILE_ENABLED must be explicitly enabled ('true') in '{_env}'"
        )

    site_key = os.getenv("TURNSTILE_SITE_KEY", "").strip()
    if not site_key:
        raise RuntimeError(f"TURNSTILE_SITE_KEY must be configured in '{_env}'")
    if site_key in ("1x00000000000000000000AA", "2x00000000000000000000AB", "3x00000000000000000000AA"):
        raise RuntimeError(f"TURNSTILE_SITE_KEY cannot use Cloudflare dummy test keys in '{_env}'")

    secret_key = os.getenv("TURNSTILE_SECRET_KEY", "").strip()
    if not secret_key:
        raise RuntimeError(f"TURNSTILE_SECRET_KEY must be configured in '{_env}'")
    if secret_key in ("1x0000000000000000000000000000000AA", "2x0000000000000000000000000000000AB", "3x0000000000000000000000000000000AA"):
        raise RuntimeError(f"TURNSTILE_SECRET_KEY cannot use Cloudflare dummy test keys in '{_env}'")

    allowed_hostnames = os.getenv("TURNSTILE_ALLOWED_HOSTNAMES", "").strip()
    if not allowed_hostnames:
        raise RuntimeError(
            f"TURNSTILE_ALLOWED_HOSTNAMES must be configured with valid deployment hostnames in '{_env}'"
        )

    verify_url = os.getenv("TURNSTILE_VERIFY_URL", "https://challenges.cloudflare.com/turnstile/v0/siteverify").strip()
    if not verify_url.startswith("https://") or "challenges.cloudflare.com" not in verify_url:
        raise RuntimeError(
            f"TURNSTILE_VERIFY_URL must use HTTPS and Cloudflare Siteverify endpoint in '{_env}'"
        )

    # 6. Trusted proxies validation in staging/production
    trusted_proxies_raw = os.getenv("TRUSTED_PROXIES", "").strip()
    if trusted_proxies_raw:
        raw_entries = [p.strip() for p in trusted_proxies_raw.split(",") if p.strip()]
        if "*" in raw_entries:
            raise RuntimeError(f"TRUSTED_PROXIES cannot contain wildcard '*' in '{_env}'")
        for entry in raw_entries:
            try:
                if "/" in entry:
                    ipaddress.ip_network(entry, strict=False)
                else:
                    ipaddress.ip_address(entry)
            except ValueError:
                raise RuntimeError(f"Invalid IP address or CIDR network in TRUSTED_PROXIES: '{entry}'")

    # 7. Additional production-only requirements
    if _env == "production":
        if "127.0.0.1" in redis_url.lower() or "localhost" in redis_url.lower():
            if os.getenv("ALLOW_LOCALHOST_REDIS_IN_PRODUCTION", "false").lower() not in ("true", "1"):
                raise RuntimeError(
                    "Production REDIS_URL cannot point to localhost/127.0.0.1 without explicit ALLOW_LOCALHOST_REDIS_IN_PRODUCTION=true override"
                )
        if len(os.getenv("OWNER_PASSWORD", "")) < 20:
            raise RuntimeError("OWNER_PASSWORD must contain at least 20 characters in production")
        cors_raw = [
            origin.strip().rstrip("/")
            for origin in os.getenv("CORS_ORIGINS", "").split(",")
            if origin.strip()
        ]
        if not cors_raw or "*" in cors_raw:
            raise RuntimeError("CORS_ORIGINS must list exact trusted HTTPS origins in production")
        if any(not origin.startswith("https://") for origin in cors_raw):
            raise RuntimeError("Production CORS_ORIGINS must use HTTPS")
        if not os.getenv("REVIEW_DB_PATH") or not os.getenv("BUSINESS_LINKS_PATH"):
            raise RuntimeError("Production must configure persistent REVIEW_DB_PATH and BUSINESS_LINKS_PATH")


if _environment in ("production", "staging"):
    validate_environment_config(_environment)

_allowed_hosts = get_allowed_hosts()

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=_allowed_hosts,
)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    Passes through client-safe 4xx errors unchanged.
    Intercepts 500+ server errors to ensure no raw exceptions, stack traces,
    or internal path details leak to clients, while preserving internal diagnostic logging (SEC-08).
    """
    if exc.status_code >= 500:
        logger.error(
            f"Internal server error ({exc.status_code}) on {request.method} {request.url.path}: {exc.detail}"
        )
        safe_detail = exc.detail if _is_safe_500_detail(exc.detail) else GENERIC_500_DETAIL
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": safe_detail},
            headers=getattr(exc, "headers", None),
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Catches any unhandled Python exception, logs the full exception and traceback internally,
    and returns a clean, generic 500 response without internal details (SEC-08).
    """
    logger.exception(f"Unhandled server error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": GENERIC_500_DETAIL},
    )


# Register Review Assistant endpoints
app.include_router(review_router, prefix="/api", tags=["review_assistant"])

# Register Dynamic Industry Template Management System endpoints (Product A)
from backend.app.api.template_routes import template_router
app.include_router(template_router, prefix="/api", tags=["industry_templates"])

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

import threading

@app.on_event("startup")
def startup_event():
    print(f"Loaded sentiment model: {settings.models.sentiment_model}")
    print(f"Loaded sarcasm model: {settings.models.sarcasm_model}")
    def prime():
        try:
            sentiment_model.predict("test")
            sarcasm_model.predict("test")
            print("Models primed and ready.")
        except Exception as e:
            print(f"Background model priming warning: {e}")
    threading.Thread(target=prime, daemon=True).start()

    # Start decoupled Security Shield alert notification worker
    try:
        from backend.app.core.security.alert_mailer import alert_dispatcher
        alert_dispatcher.start()
        print("Security Shield alert dispatcher worker started.")
    except Exception as e:
        print(f"Background alert dispatcher startup warning: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    try:
        from backend.app.core.security.alert_mailer import alert_dispatcher
        alert_dispatcher.stop(timeout=2.0)
        print("Security Shield alert dispatcher worker stopped.")
    except Exception as e:
        print(f"Alert dispatcher shutdown warning: {e}")

    try:
        from backend.app.core.auth.security_store import close_redis_client
        await close_redis_client()
    except Exception as e:
        print(f"Security store shutdown warning: {e}")

class ReviewRequest(BaseModel):
    review: str
    rating: int

def detect_contradiction(text: str) -> bool:
    text_lower = text.lower()
    positive_phrases = ["perfect", "amazing", "five stars", "love", "best purchase"]
    negative_phrases = ["nothing works", "broke", "teaching me patience", "wasting my money", "never again", "crashes", "terrible"]
    
    has_pos = any(p in text_lower for p in positive_phrases)
    has_neg = any(p in text_lower for p in negative_phrases)
    
    return has_pos and has_neg

def check_consistency(rating: int, sentiment: str, is_sarcastic: bool):
    consistency = "Match"
    integrity = "Genuine"
    
    if sentiment == "NEUTRAL":
        consistency = "No Strong Sentiment"
        integrity = "No Clear Mismatch"
    elif rating >= 4 and sentiment == "NEGATIVE":
        consistency = "Mismatch"
        integrity = "Suspicious"
    elif rating <= 2 and sentiment == "POSITIVE":
        consistency = "Mismatch"
        integrity = "Suspicious"
    elif rating == 3 and is_sarcastic:
        consistency = "Suspicious"
        integrity = "Suspicious"
        
    return consistency, integrity

def run_inference_pipeline(req: ReviewRequest, debug=False):
    text = req.review.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Review text cannot be empty")
        
    cleaned_text = text_cleaner.clean(text)
    
    # 1. Contradiction Detection
    has_contradiction = detect_contradiction(text)
    
    # 2. Sarcasm Model
    sarcasm_res = sarcasm_model.predict(cleaned_text)
    sarcasm_prob = sarcasm_res["sarcasm_probability"]
    
    if has_contradiction:
        # Boost sarcasm probability artificially if contradiction patterns are detected
        sarcasm_prob = min(1.0, sarcasm_prob + 0.3)
        
    print(f"Sarcasm confidence: {sarcasm_prob:.4f}")
    print(f"Sarcasm label: {'Sarcastic' if sarcasm_prob > settings.fusion.sarcasm_activation_threshold else 'Genuine'}")
    
    # 3. Sentiment Model
    sentiment_res = sentiment_model.predict(cleaned_text)
    
    print("Probabilities BEFORE fusion:")
    print(f"  Positive: {sentiment_res['positive']:.4f}")
    print(f"  Neutral:  {sentiment_res['neutral']:.4f}")
    print(f"  Negative: {sentiment_res['negative']:.4f}")
    
    # 4. Fusion Engine
    print("Fusion Engine Started")
    fusion_res = fusion_engine.fuse(sentiment_res, sarcasm_prob)
    print("Fusion Engine Finished")
    
    fused_probs = fusion_res["probabilities"]
    
    print("Probabilities AFTER fusion:")
    print(f"  Positive: {fused_probs['positive']:.4f}")
    print(f"  Neutral:  {fused_probs['neutral']:.4f}")
    print(f"  Negative: {fused_probs['negative']:.4f}")
    
    final_prediction = fusion_res["prediction"]
    is_sarcastic = fusion_res["debug"]["sarcasm_activated"]
    
    # 5. Rating Consistency
    consistency, integrity = check_consistency(req.rating, final_prediction, is_sarcastic)
    
    # 6. Explanations
    reasons = []
    if has_contradiction:
        reasons.append("Positive wording followed by contradiction")
    if is_sarcastic:
        reasons.append("Sarcasm detected")
    if consistency != "Match":
        reasons.append("Rating inconsistent with review")
        
    if not reasons:
        reasons.append(explainer.generate_explanation(fusion_res, text))
        
    # Get highest confidence after fusion
    confidence = fused_probs[final_prediction.lower()]
    
    response = {
        "rating": req.rating,
        "sentiment": final_prediction.capitalize(),
        "sarcasm": is_sarcastic,
        "confidence": round(confidence, 4),
        "rating_review_consistency": consistency,
        "integrity": integrity,
        "reason": reasons
    }
    
    if debug:
        response["debug_info"] = {
            "original_text": text,
            "cleaned_text": cleaned_text,
            "sarcasm_model_prob": sarcasm_res["sarcasm_probability"],
            "boosted_sarcasm_prob": sarcasm_prob,
            "has_contradiction": has_contradiction,
            "sentiment_before": sentiment_res,
            "sentiment_after": fused_probs,
            "fusion_math": fusion_res["debug"]
        }
        
    return response

@app.get("/api/stats")
def get_stats():
    return {
        "amazon": {"total_reviews": "3,600,000", "test_reviews": "400,000", "classes": "Binary (1=Negative, 2=Positive)"},
        "flipkart": {"total_reviews": "363,261", "classes": "Stars (1-5)"}
    }

@app.post("/api/predict")
def predict_integrity(req: ReviewRequest, request: Request):
    if not review_service.check_rate_limit(f"predict:{get_client_ip(request)}", max_per_minute=30):
        raise HTTPException(status_code=429, detail="Rate limit reached. Please wait a moment.")
    return run_inference_pipeline(req, debug=False)

@app.post("/api/debug")
def debug_inference(req: ReviewRequest, _: None = Depends(require_owner)):
    return run_inference_pipeline(req, debug=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
