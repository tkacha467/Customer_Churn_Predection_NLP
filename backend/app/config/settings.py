import os
from pydantic import BaseModel

class ModelConfig(BaseModel):
    sentiment_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    sarcasm_model: str = "cardiffnlp/twitter-roberta-base-irony"
    device: int = -1  # -1 for CPU, 0 for GPU
    max_length: int = 512

class FusionConfig(BaseModel):
    # Sarcasm probability must exceed this to trigger fusion re-weighting
    sarcasm_activation_threshold: float = 0.65
    
    # If the literal sentiment is Positive but Sarcasm > threshold, 
    # the Negative sentiment probability will be boosted by this multiplier
    sarcasm_penalty_multiplier: float = 1.5

class ThresholdConfig(BaseModel):
    # If the highest probability class is below this threshold, return Neutral
    adaptive_neutral_threshold: float = 0.55

class AppSettings(BaseModel):
    models: ModelConfig = ModelConfig()
    fusion: FusionConfig = FusionConfig()
    thresholds: ThresholdConfig = ThresholdConfig()

# Global settings instance
settings = AppSettings()
