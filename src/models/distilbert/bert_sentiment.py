import pandas as pd
import numpy as np
import os
import torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
import warnings
warnings.filterwarnings('ignore')

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    f1 = f1_score(labels, preds, average="weighted")
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc, "f1": f1}

def train_amazon_sentiment(data_path='/content/drive/MyDrive/Churnlens_predection/', models_path='/content/drive/MyDrive/Churnlens_predection/models/', sample_size=50000):
    print("Starting Amazon DistilBERT Training Pipeline...")
    
    train_file = os.path.join(data_path, 'train.csv')
    
    if not os.path.exists(train_file):
        print(f"File not found: {train_file}")
        return
        
    print(f"Loading data from {train_file}...")
    # Amazon dataset has no headers
    df = pd.read_csv(train_file, header=None, names=['class_index', 'review_title', 'review_text'])
    
    # Class 1 is Negative, Class 2 is Positive
    # Map to 0 and 1
    df['label'] = df['class_index'].map({1: 0, 2: 1})
    
    # Combine title and text
    df['text'] = df['review_title'].fillna('') + " " + df['review_text'].fillna('')
    
    # Sample the dataset
    if sample_size and sample_size < len(df):
        print(f"Sampling {sample_size} rows out of {len(df)}...")
        df = df.sample(sample_size, random_state=42)
        
    # Split into train and validation sets
    train_df, val_df = train_test_split(df[['text', 'label']], test_size=0.2, random_state=42)
    
    print("Tokenizing data...")
    model_name = "distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    train_dataset = Dataset.from_pandas(train_df)
    val_dataset = Dataset.from_pandas(val_df)
    
    def tokenize_function(examples):
        return tokenizer(examples['text'], padding="max_length", truncation=True, max_length=128)
        
    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_val = val_dataset.map(tokenize_function, batched=True)
    
    print("Initializing Model...")
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
    
    # Map config labels for clarity during inference
    model.config.id2label = {0: 'NEGATIVE', 1: 'POSITIVE'}
    model.config.label2id = {'NEGATIVE': 0, 'POSITIVE': 1}
    
    # Check if GPU is available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Training on device: {device}")
    
    # Adjust parameters for small local runs
    epochs = 2 if sample_size > 1000 else 1
    
    training_args = TrainingArguments(
        output_dir=os.path.join(models_path, 'checkpoints'),
        num_train_epochs=epochs,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=64,
        warmup_steps=500 if sample_size > 5000 else 0,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=100 if sample_size > 1000 else 10,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        compute_metrics=compute_metrics,
    )
    
    print("Starting Training...")
    trainer.train()
    
    save_dir = os.path.join(models_path, 'distilbert_amazon')
    os.makedirs(save_dir, exist_ok=True)
    print(f"Saving fine-tuned model to {save_dir}...")
    trainer.save_model(save_dir)
    tokenizer.save_pretrained(save_dir)
    
    print("Training Complete!")

if __name__ == "__main__":
    # We use a tiny sample size of 100 for local testing so it doesn't freeze laptops.
    # The user can change this to 50000 or None when running in Colab with GPU.
    train_amazon_sentiment(sample_size=100)
