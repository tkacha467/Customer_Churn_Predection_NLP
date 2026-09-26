import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"

import torch
from transformers import pipeline
import time
import threading
from api.config.settings import settings

class ModelLoader:
    def __init__(self):
        self._sentiment_model = None
        self._sarcasm_model = None
        self._lock = threading.Lock()
        
    def _load_sentiment(self):
        with self._lock:
            if self._sentiment_model is None:
                t0 = time.time()
                from pathlib import Path
                local_model = Path("models/distilbert")
                if not local_model.exists():
                    local_model = Path(__file__).resolve().parent.parent.parent / "models" / "distilbert"

                try:
                    self._sentiment_model = pipeline(
                        'text-classification', 
                        model=settings.models.sentiment_model, 
                        framework="pt",
                        device=settings.models.device,
                        top_k=None # Get all scores
                    )
                except Exception as e:
                    # Fallback to local model if remote pipeline had issues
                    if (local_model / "model.safetensors").exists():
                        print(f"Falling back to local DistilBERT model due to: {e}")
                        self._sentiment_model = pipeline(
                            'text-classification', 
                            model=str(local_model), 
                            framework="pt",
                            device=settings.models.device,
                            top_k=None
                        )
                    else:
                        raise e
                print(f"Loaded Sentiment Model in {time.time() - t0:.2f}s")
            return self._sentiment_model

    def _load_sarcasm(self):
        with self._lock:
            if self._sarcasm_model is None:
                t0 = time.time()
                try:
                    self._sarcasm_model = pipeline(
                        'text-classification', 
                        model=settings.models.sarcasm_model, 
                        framework="pt",
                        device=settings.models.device
                    )
                except Exception as e:
                    print(f"Warning loading sarcasm model: {e}")
                    self._sarcasm_model = None
                print(f"Loaded Sarcasm Model in {time.time() - t0:.2f}s")
            return self._sarcasm_model

    def get_sentiment(self):
        return self._load_sentiment()
        
    def get_sarcasm(self):
        return self._load_sarcasm()

# Global singleton
loader = ModelLoader()

def no_grad_inference(model, text):
    """
    Helper function to run inference efficiently on CPU without gradient overhead.
    """
    with torch.no_grad():
        return model(text)

