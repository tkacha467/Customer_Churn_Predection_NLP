import pandas as pd
import numpy as np
import os
import torch
from transformers import pipeline
from deep_translator import GoogleTranslator

def analyze_review_integrity(raw_data_path='../data/raw/', processed_data_path='../data/processed/', limit=None):
    print("Starting DistilBERT NLP Integrity Analysis...")
    
    reviews_file = os.path.join(raw_data_path, 'olist_order_reviews_dataset.csv')
    try:
        reviews = pd.read_csv(reviews_file)
    except FileNotFoundError:
        print(f"Reviews file not found at {reviews_file}")
        return None

    # Filter to reviews that actually have text
    reviews = reviews.dropna(subset=['review_comment_message']).copy()
    
    if limit:
        print(f"Limiting to {limit} reviews for speed...")
        reviews = reviews.head(limit)
        
    print(f"Processing {len(reviews)} reviews...")
    
    # Initialize the sentiment pipeline
    # We use a pre-trained DistilBERT model for sentiment analysis
    # If the user trains their own in Colab, they can change this path to models/distilbert/
    try:
        sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    except Exception as e:
        print(f"Failed to load HuggingFace pipeline: {e}")
        return None

    translator = GoogleTranslator(source='pt', target='en')
    
    results = []
    
    for idx, row in reviews.iterrows():
        original_text = row['review_comment_message']
        star_rating = row['review_score']
        
        # 1. Translate Portuguese to English
        try:
            english_text = translator.translate(original_text)
        except Exception:
            # Fallback if translation fails (e.g. rate limit)
            english_text = original_text
            
        # 2. Get BERT Sentiment
        try:
            # Truncate to 512 characters to avoid BERT length errors
            prediction = sentiment_pipeline(english_text[:512])[0]
            sentiment_label = prediction['label']
            sentiment_score = prediction['score']
        except Exception:
            sentiment_label = 'NEUTRAL'
            sentiment_score = 0.5
            
        # 3. Calculate Integrity Mismatch
        # Rule: Rating >= 4 but Sentiment is NEGATIVE -> Mismatch (1)
        # Rule: Rating <= 2 but Sentiment is POSITIVE -> Mismatch (1)
        is_mismatch = 0
        if star_rating >= 4 and sentiment_label == 'NEGATIVE':
            is_mismatch = 1
        elif star_rating <= 2 and sentiment_label == 'POSITIVE':
            is_mismatch = 1
            
        results.append({
            'review_id': row['review_id'],
            'order_id': row['order_id'],
            'english_text': english_text,
            'star_rating': star_rating,
            'bert_sentiment': sentiment_label,
            'bert_confidence': sentiment_score,
            'integrity_mismatch': is_mismatch,
            # Assign an integrity score (1.0 = perfect integrity, 0.0 = total mismatch)
            'integrity_score': 1.0 - is_mismatch 
        })
        
        if len(results) % 100 == 0:
            print(f"Processed {len(results)} / {len(reviews)} reviews...")

    nlp_df = pd.DataFrame(results)
    
    os.makedirs(processed_data_path, exist_ok=True)
    save_file = os.path.join(processed_data_path, 'nlp_integrity_scores.csv')
    nlp_df.to_csv(save_file, index=False)
    
    print(f"\nNLP Integrity Analysis Complete! Saved to {save_file}")
    print(f"Total Mismatches Found: {nlp_df['integrity_mismatch'].sum()}")
    
    return nlp_df

if __name__ == "__main__":
    # For local testing, we limit to 500 rows to avoid waiting hours. 
    # Remove limit=500 to process the full dataset.
    analyze_review_integrity(limit=500)
