import sys
from transformers import pipeline
import emoji
import warnings
warnings.filterwarnings('ignore')

print('Loading models for diagnostic...')
try:
    sarcasm_model = pipeline('text-classification', model='cardiffnlp/twitter-roberta-base-irony')
    sentiment_model = pipeline('text-classification', model='cardiffnlp/twitter-roberta-base-sentiment-latest', top_k=None)
except Exception as e:
    print('Failed to load models:', e)
    sys.exit(1)

reviews = [
    'Five stars for teaching me patience 🥱',
    'Perfect... now nothing works 🤩'
]

def clean_text(text):
    text = emoji.demojize(text, delimiters=(' ', ' '))
    text = text.replace('_', ' ')
    return text

for r in reviews:
    print('\n' + '='*50)
    print('Original Text:', r)
    cleaned = clean_text(r)
    print('Preprocessed Text:', cleaned)
    
    s_res = sarcasm_model(cleaned)[0]
    sarcasm_prob = s_res['score'] if s_res['label'] == 'irony' else 1 - s_res['score']
    print('Sarcasm Probability:', round(sarcasm_prob, 4))
    
    sent_res = sentiment_model(cleaned)[0]
    sent_probs = {x['label']: x['score'] for x in sent_res}
    
    print('Sentiment Probabilities:')
    print(f"  Positive: {round(sent_probs.get('positive', 0), 4)}")
    print(f"  Neutral:  {round(sent_probs.get('neutral', 0), 4)}")
    print(f"  Negative: {round(sent_probs.get('negative', 0), 4)}")
    
    # Fusion Engine
    pos = sent_probs.get('positive', 0)
    neg = sent_probs.get('negative', 0)
    neu = sent_probs.get('neutral', 0)
    
    pos_after = pos
    neg_after = neg
    
    print('Fusion Calculation:')
    if sarcasm_prob > 0.65:
        # Mathematical penalty
        penalty = pos * sarcasm_prob
        boost = pos * sarcasm_prob
        pos_after = max(0, pos - penalty)
        neg_after = min(1, neg + boost)
        
        # normalize
        total = pos_after + neg_after + neu
        pos_after /= total
        neg_after /= total
        neu /= total
        
        print(f'  Sarcasm > 0.65. Penalty to Positive: -{round(penalty, 4)}, Boost to Negative: +{round(boost, 4)}')
    else:
        print('  No sarcasm detected above threshold. No fusion applied.')
        
    final_probs = {'positive': pos_after, 'neutral': neu, 'negative': neg_after}
    final_pred = max(final_probs, key=final_probs.get)
    
    print('Final Probabilities:')
    print(f"  Positive: {round(pos_after, 4)}")
    print(f"  Neutral:  {round(neu, 4)}")
    print(f"  Negative: {round(neg_after, 4)}")
    print('Final Prediction:', final_pred.upper())
