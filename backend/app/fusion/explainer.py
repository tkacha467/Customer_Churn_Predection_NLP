class Explainer:
    def generate_explanation(self, fusion_result: dict, text: str) -> str:
        pred = fusion_result["prediction"]
        debug = fusion_result["debug"]
        
        if debug.get("sarcasm_activated", False):
            if debug.get("contextual_modifier", 1.0) < 0.5:
                return f"Predicted as {pred} because despite high sarcasm probability, the positive sentiment was overwhelmingly strong, preventing a false positive."
            else:
                return f"Predicted as {pred} because the Sarcasm model detected high contradiction (prob: {debug['sarcasm_prob']:.2f}), penalizing the literal positive score."
                
        # Non-sarcastic explanation
        if pred == "POSITIVE":
            return f"Predicted as POSITIVE due to strong literal positive sentiment (prob: {debug['positive_after']:.2f})."
        elif pred == "NEGATIVE":
            return f"Predicted as NEGATIVE due to strong literal negative sentiment (prob: {debug['negative_after']:.2f})."
        else:
            return f"Predicted as NEUTRAL because no single sentiment probability exceeded the confidence threshold."

explainer = Explainer()
