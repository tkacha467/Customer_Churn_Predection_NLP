from api.models.model_loader import loader, no_grad_inference
import time

class SentimentAnalyzer:
    def predict(self, text: str):
        model = loader.get_sentiment()
        
        t0 = time.time()
        # model(text) returns [[{'label': 'positive', 'score': 0.8}, ...]] because top_k=None
        raw_res = no_grad_inference(model, text)[0] 
        inference_time_ms = int((time.time() - t0) * 1000)
        
        probs = {}
        for x in raw_res:
            lbl = str(x['label']).lower()
            if lbl in ['positive', 'label_1']:
                probs['positive'] = x['score']
            elif lbl in ['negative', 'label_0']:
                probs['negative'] = x['score']
            elif lbl in ['neutral']:
                probs['neutral'] = x['score']
                
        pos = probs.get("positive", 0.0)
        neg = probs.get("negative", 0.0)
        neu = probs.get("neutral", 0.0)
        
        # If binary model without explicit neutral class, support neutral for balanced scores
        if "neutral" not in probs:
            if abs(pos - neg) < 0.35:
                neu = 0.5
                pos = 0.25
                neg = 0.25

        return {
            "positive": round(pos, 4),
            "neutral": round(neu, 4),
            "negative": round(neg, 4),
            "inference_time_ms": inference_time_ms
        }

sentiment_model = SentimentAnalyzer()
