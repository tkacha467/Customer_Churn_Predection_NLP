from api.config.settings import settings

class FusionEngine:
    def fuse(self, sentiment_probs: dict, sarcasm_prob: float):
        pos = sentiment_probs.get("positive", 0.0)
        neu = sentiment_probs.get("neutral", 0.0)
        neg = sentiment_probs.get("negative", 0.0)
        
        pos_after = pos
        neg_after = neg
        
        debug_info = {
            "activation_threshold": settings.fusion.sarcasm_activation_threshold,
            "sarcasm_prob": sarcasm_prob,
            "positive_before": pos,
            "negative_before": neg,
            "neutral_before": neu,
            "sarcasm_activated": False
        }
        
        if sarcasm_prob > settings.fusion.sarcasm_activation_threshold:
            debug_info["sarcasm_activated"] = True
            
            # Contextual modifier prevents false positives on genuine 5-star reviews
            context_modifier = (1.0 - pos) if pos > 0.85 else 1.0
            
            penalty = pos * sarcasm_prob * context_modifier
            boost = pos * sarcasm_prob * context_modifier
            
            pos_after = max(0.0, pos - penalty)
            neg_after = min(1.0, neg + boost)
            
            # Re-normalize
            total = pos_after + neg_after + neu
            if total > 0:
                pos_after /= total
                neg_after /= total
                neu /= total
                
            debug_info["contextual_modifier"] = context_modifier
            debug_info["positive_penalty"] = -penalty
            debug_info["negative_boost"] = boost
            
        debug_info["positive_after"] = pos_after
        debug_info["negative_after"] = neg_after
        debug_info["neutral_after"] = neu
            
        final_probs = {
            "positive": pos_after,
            "neutral": neu,
            "negative": neg_after
        }
        
        # Apply neutral thresholds
        if max(final_probs.values()) < settings.thresholds.adaptive_neutral_threshold:
            final_pred = "NEUTRAL"
        else:
            final_pred = max(final_probs, key=final_probs.get).upper()
            
        return {
            "prediction": final_pred,
            "probabilities": final_probs,
            "debug": debug_info
        }

fusion_engine = FusionEngine()
