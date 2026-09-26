from api.models.model_loader import loader, no_grad_inference
import time

class SarcasmAnalyzer:
    def predict(self, text: str):
        model = loader.get_sarcasm()
        if model is None:
            return {"sarcasm_probability": 0.0, "inference_time_ms": 0}
        
        t0 = time.time()
        # default pipeline returns [{'label': 'irony', 'score': 0.8}] or [{'label': 'non_irony', 'score': 0.8}]
        raw_res = no_grad_inference(model, text)[0]
        inference_time_ms = int((time.time() - t0) * 1000)
        
        lbl = str(raw_res.get('label', '')).lower()
        prob = raw_res['score'] if lbl in ['irony', 'label_1'] else (1.0 - raw_res['score'])
        
        return {
            "sarcasm_probability": prob,
            "inference_time_ms": inference_time_ms
        }

sarcasm_model = SarcasmAnalyzer()
