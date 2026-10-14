import os
import warnings

# Suppress noisy environment and framework warnings
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Filter out unauthenticated HF Hub warning and model pooler unexpected keys notices
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*HF_TOKEN.*")
warnings.filterwarnings("ignore", message=".*unauthenticated requests.*")
warnings.filterwarnings("ignore", message=".*RobertaForSequenceClassification.*")

import torch
from transformers import pipeline, logging as hf_logging
hf_logging.set_verbosity_error()
hf_logging.disable_progress_bar()

try:
    from huggingface_hub.utils import disable_progress_bars, logging as hub_logging
    disable_progress_bars()
    hub_logging.set_verbosity_error()
except ImportError:
    pass
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

