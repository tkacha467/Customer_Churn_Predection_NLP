import sys
import pandas as pd
import numpy as np
from transformers import pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score
import emoji
import warnings
warnings.filterwarnings('ignore')
import io

# Ensure UTF-8 output to avoid powershell charmap errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')

print("Loading dataset...")
# Load 500 random samples from Flipkart
df = pd.read_csv('d:\\churnlens\\data\\flipkart.csv', encoding='ISO-8859-1')
df = df.dropna(subset=['Review', 'Rate'])

def map_rate(rate_str):
    try:
        r = float(str(rate_str).split()[0])
        if r <= 2.5: return 'NEGATIVE'
        if r <= 3.5: return 'NEUTRAL'
        return 'POSITIVE'
    except:
        return None

df['True_Label'] = df['Rate'].apply(map_rate)
df = df.dropna(subset=['True_Label'])
df_sample = df.sample(n=500, random_state=42)

print("Loading Old Pipeline...")
try:
    old_pipe = pipeline("zero-shot-classification", model="cross-encoder/nli-distilroberta-base")
except Exception as e:
    print(e)

print("Loading New Pipeline...")
try:
    sarcasm_model = pipeline('text-classification', model='cardiffnlp/twitter-roberta-base-irony')
    sentiment_model = pipeline('text-classification', model='cardiffnlp/twitter-roberta-base-sentiment-latest', top_k=None)
except Exception as e:
    print(e)
    sys.exit(1)

def run_old(text):
    text = str(text)[:512]
    labels = [
        'a genuine positive review praising the product',
        'a genuine negative review complaining about the product',
        'a sarcastic positive review that actually praises the product',
        'a sarcastic negative review complaining about the product'
    ]
    pred = old_pipe(text, labels)
    best = pred['labels'][0]
    if 'positive' in best:
        return 'POSITIVE'
    return 'NEGATIVE'

def clean_text(text):
    text = emoji.demojize(str(text)[:512], delimiters=(' ', ' '))
    return text.replace('_', ' ')

def run_new(text):
    cleaned = clean_text(text)
    s_res = sarcasm_model(cleaned)[0]
    sarcasm_prob = s_res['score'] if s_res['label'] == 'irony' else 1 - s_res['score']
    
    sent_res = sentiment_model(cleaned)[0]
    sent_probs = {x['label']: x['score'] for x in sent_res}
    
    pos = sent_probs.get('positive', 0)
    neg = sent_probs.get('negative', 0)
    neu = sent_probs.get('neutral', 0)
    
    pos_after = pos
    neg_after = neg
    
    if sarcasm_prob > 0.65:
        # Contextual Modifier: If literal is > 0.85, suppress penalty to avoid false positives
        context_modifier = (1.0 - pos) if pos > 0.85 else 1.0
        penalty = pos * sarcasm_prob * context_modifier
        boost = pos * sarcasm_prob * context_modifier
        pos_after = max(0, pos - penalty)
        neg_after = min(1, neg + boost)
        
        total = pos_after + neg_after + neu
        pos_after /= total
        neg_after /= total
        neu /= total
        
    final_probs = {'POSITIVE': pos_after, 'NEUTRAL': neu, 'NEGATIVE': neg_after}
    if max(final_probs.values()) < 0.55:
        return 'NEUTRAL'
    return max(final_probs, key=final_probs.get)

y_true = df_sample['True_Label'].tolist()
y_old = []
y_new = []

print("Running inferences on 500 samples...")
for i, text in enumerate(df_sample['Review']):
    if i % 50 == 0:
        print(f"Processed {i}/500")
    y_old.append(run_old(text))
    y_new.append(run_new(text))

def print_metrics(name, y_t, y_p):
    print(f"\n--- {name} ---")
    print(f"Accuracy:  {accuracy_score(y_t, y_p):.4f}")
    print(f"Precision: {precision_score(y_t, y_p, average='macro', zero_division=0):.4f}")
    print(f"Recall:    {recall_score(y_t, y_p, average='macro', zero_division=0):.4f}")
    print(f"F1 Score:  {f1_score(y_t, y_p, average='macro', zero_division=0):.4f}")

print_metrics("OLD DistilBERT", y_true, y_old)
print_metrics("NEW Fusion Engine", y_true, y_new)

labels = ['NEGATIVE', 'NEUTRAL', 'POSITIVE']
print("\nNEW Confusion Matrix (NEGATIVE, NEUTRAL, POSITIVE):")
print(confusion_matrix(y_true, y_new, labels=labels))
