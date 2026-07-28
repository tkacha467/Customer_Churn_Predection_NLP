import warnings
warnings.filterwarnings('ignore')
import sys
import numpy as np
from transformers import pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import emoji
import time

def clean_text(text):
    text = emoji.demojize(text, delimiters=(' ', ' '))
    return text.replace('_', ' ')

dataset = [
    # Genuine Positive
    ("I absolutely love this product, it works perfectly.", "POSITIVE"),
    ("Great customer service, very helpful.", "POSITIVE"),
    ("This is the best phone I've ever owned.", "POSITIVE"),
    ("Amazing quality, highly recommend!", "POSITIVE"),
    
    # Genuine Negative
    ("Terrible experience, it broke immediately.", "NEGATIVE"),
    ("Do not buy this, complete waste of money.", "NEGATIVE"),
    ("The battery life is awful.", "NEGATIVE"),
    ("Very disappointed with the support team.", "NEGATIVE"),
    
    # Genuine Neutral
    ("The package arrived on Tuesday.", "NEUTRAL"),
    ("It comes with a charger and manual.", "NEUTRAL"),
    ("I bought the black version.", "NEUTRAL"),
    ("The screen size is 6 inches.", "NEUTRAL"),
    
    # Sarcastic Negative (Looks positive, actually negative)
    ("Five stars for teaching me patience 🥱", "NEGATIVE"),
    ("Perfect... now nothing works 🤩", "NEGATIVE"),
    ("10/10, would never buy this again.", "NEGATIVE"),
    ("Fantastic! It broke within five minutes.", "NEGATIVE"),
    ("Wow, another amazing update that broke everything.", "NEGATIVE"),
    ("Great customer service! I only had to explain my issue six times.", "NEGATIVE"),
    ("This phone battery is incredible. It dies before lunch.", "NEGATIVE"),
    ("Wonderful! The app crashes every time I open it.", "NEGATIVE"),
]

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
        # Fusion Eq
        penalty = pos * sarcasm_prob
        boost = pos * sarcasm_prob
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

y_true = [x[1] for x in dataset]
y_old = []
y_new = []

print("Running benchmarks...")
for text, label in dataset:
    y_old.append(run_old(text))
    y_new.append(run_new(text))

def print_metrics(name, y_true, y_pred):
    print(f"\n--- {name} ---")
    print(f"Accuracy:  {accuracy_score(y_true, y_pred):.4f}")
    # using macro average because classes are slightly imbalanced and we care about all equally
    print(f"Precision: {precision_score(y_true, y_pred, average='macro', zero_division=0):.4f}")
    print(f"Recall:    {recall_score(y_true, y_pred, average='macro', zero_division=0):.4f}")
    print(f"F1 Score:  {f1_score(y_true, y_pred, average='macro', zero_division=0):.4f}")
    
print_metrics("OLD DistilBERT Zero-Shot", y_true, y_old)
print_metrics("NEW Fusion Engine", y_true, y_new)

print("\nNEW Confusion Matrix (Labels: NEGATIVE, NEUTRAL, POSITIVE):")
labels = ['NEGATIVE', 'NEUTRAL', 'POSITIVE']
cm = confusion_matrix(y_true, y_new, labels=labels)
print(cm)
