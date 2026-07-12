import pandas as pd
import numpy as np
import os
from transformers import pipeline
import warnings
warnings.filterwarnings('ignore')

def analyze_flipkart_integrity(limit=500):
    print("Starting Flipkart Review Integrity Analysis...")
    
    # Get absolute path to the project root (D:\churnlens)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    data_path = os.path.join(project_root, 'data')
    models_path = os.path.join(project_root, 'models')
    processed_path = os.path.join(project_root, 'data', 'processed')
    
    flipkart_file = os.path.join(data_path, 'flipkart.csv')
    if not os.path.exists(flipkart_file):
        print(f"File not found: {flipkart_file}")
        return
        
    df = pd.read_csv(flipkart_file, encoding='latin-1', on_bad_lines='skip')
    print(f"Loaded {len(df)} Flipkart reviews.")
    
    # Clean the Rate column (it's 1-5 but might have strings or NaNs)
    df['Rate'] = pd.to_numeric(df['Rate'], errors='coerce')
    df = df.dropna(subset=['Rate', 'Review', 'Summary'])
    
    if limit and limit < len(df):
        print(f"Limiting to {limit} reviews for speed...")
        df = df.sample(limit, random_state=42)
        
    model_dir = os.path.join(models_path, 'distilbert_amazon')
    
    if not os.path.exists(model_dir):
        print("Local trained model not found! Using default distilbert for demonstration...")
        model_name = "distilbert-base-uncased-finetuned-sst-2-english"
    else:
        print(f"Loading custom model from {model_dir}...")
        model_name = model_dir
        
    try:
        sentiment_pipeline = pipeline("sentiment-analysis", model=model_name, device=-1) # Force CPU for safety
    except Exception as e:
        print(f"Pipeline error: {e}")
        return
        
    print("Running NLP inference on reviews...")
    results = []
    
    for idx, row in df.iterrows():
        text = str(row['Summary']) + " " + str(row['Review'])
        rating = row['Rate']
        
        try:
            # Truncate to 512 chars to avoid model limits
            pred = sentiment_pipeline(text[:512])[0]
            label = pred['label']
            score = pred['score']
            
            # If using custom model, LABEL_1 is POSITIVE, LABEL_0 is NEGATIVE
            if label == 'LABEL_1': label = 'POSITIVE'
            if label == 'LABEL_0': label = 'NEGATIVE'
            
        except Exception:
            label = 'NEUTRAL'
            score = 0.5
            
        # Integrity Logic
        mismatch = 0
        if rating >= 4 and label == 'NEGATIVE':
            mismatch = 1
        elif rating <= 2 and label == 'POSITIVE':
            mismatch = 1
            
        results.append({
            'Product_name': row['Product_name'],
            'Price': row['Price'],
            'Rate': rating,
            'Review_Text': text,
            'Sentiment': label,
            'Confidence': score,
            'Mismatch_Flag': mismatch
        })
        
        if len(results) % 100 == 0:
            print(f"Processed {len(results)} reviews...")
            
    results_df = pd.DataFrame(results)
    
    os.makedirs(processed_path, exist_ok=True)
    out_file = os.path.join(processed_path, 'flipkart_integrity_results.csv')
    results_df.to_csv(out_file, index=False)
    
    print(f"\nAnalysis Complete!")
    print(f"Total Mismatches Found: {results_df['Mismatch_Flag'].sum()}")
    print(f"Results saved to {out_file}")

if __name__ == "__main__":
    analyze_flipkart_integrity()
