import re
import emoji
import contractions
import unicodedata

class TextCleaner:
    def __init__(self):
        # We preserve punctuation that carries semantic meaning for sentiment/sarcasm
        self.semantic_punctuation = r'[!?]'
        
    def clean(self, text: str) -> str:
        """
        Advanced text normalization pipeline for sentiment and sarcasm detection.
        """
        if not text or not isinstance(text, str):
            return ""

        # 1. Unicode Normalization
        # Converts fancy quotes, weird dashes, etc. to standard ascii approximations
        text = unicodedata.normalize('NFKC', text)
        
        # 2. Emoji Conversion
        # Translates '👍' to 'thumbs_up', removing colons for better contextual understanding
        text = emoji.demojize(text, delimiters=(" ", " "))
        text = text.replace("_", " ")

        # 3. Contraction Expansion
        # "wouldn't" -> "would not" (crucial for negations)
        try:
            text = contractions.fix(text)
        except Exception:
            pass # fallback if contraction parsing fails on weird edge cases

        # 4. Repeated Character Normalization (Letters)
        # "amaaaazing" -> "amazing", "sooo" -> "so"
        # We leave up to 2 characters to preserve words like "good", "too"
        text = re.sub(r'([a-zA-Z])\1{2,}', r'\1\1', text)
        
        # 5. Repeated Punctuation Normalization
        # "!!!!!" -> "!"
        # "???" -> "?"
        text = re.sub(r'(!)\1+', r'\1', text)
        text = re.sub(r'(\?)\1+', r'\1', text)
        text = re.sub(r'(\.)\1{3,}', r'...', text) # Normalize excessive dots to standard ellipsis
        
        # 6. Whitespace Cleanup
        # Remove extra spaces, tabs, and newlines
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

# Singleton instance for easy import
text_cleaner = TextCleaner()
