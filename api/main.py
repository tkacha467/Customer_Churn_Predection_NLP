from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

# Import New Modular Architecture
from api.config.settings import settings
from api.preprocessing.text_cleaner import text_cleaner
from api.models.sentiment import sentiment_model
from api.models.sarcasm import sarcasm_model
from api.fusion.engine import fusion_engine
from api.fusion.explainer import explainer

app = FastAPI(title="NLP Integrity API", description="Modular Context-Aware Sentiment Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    # Load models into memory on startup
    print(f"Loaded sentiment model: {settings.models.sentiment_model}")
    print(f"Loaded sarcasm model: {settings.models.sarcasm_model}")
    # Prime the models
    sentiment_model.predict("test")
    sarcasm_model.predict("test")
    print("Models primed and ready.")

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
        "amazon": {"total_reviews": "3,600,000", "classes": "Binary (1=Negative, 2=Positive)"},
        "flipkart": {"total_reviews": "363,261", "classes": "Stars (1-5)"}
    }

@app.post("/api/predict")
def predict_integrity(req: ReviewRequest):
    return run_inference_pipeline(req, debug=False)

@app.post("/api/debug")
def debug_inference(req: ReviewRequest):
    return run_inference_pipeline(req, debug=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
