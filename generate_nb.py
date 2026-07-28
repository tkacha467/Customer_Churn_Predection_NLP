import json
import os

code_cells = [
    {'cell_type': 'markdown', 'metadata': {}, 'source': ['# Phase 5: NLP Review Integrity with DistilBERT\n', 'This notebook is designed to be run in **Google Colab** on a T4 GPU.']},
    {'cell_type': 'code', 'metadata': {}, 'source': ['!pip install -q transformers datasets evaluate accelerate']},
    {'cell_type': 'code', 'metadata': {}, 'source': [
        'import torch\n',
        'from datasets import load_dataset\n',
        'from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments\n',
        'import evaluate\n',
        'import numpy as np\n',
        '\n',
        'print("GPU Available:", torch.cuda.is_available())'
    ]},
    {'cell_type': 'code', 'metadata': {}, 'source': [
        '# Load a subset of the massive Amazon Polarity dataset (3.6M reviews)\n',
        '# We use a smaller subset (e.g., 50k) to keep training time manageable in Colab\n',
        'print("Loading dataset...")\n',
        'dataset = load_dataset("amazon_polarity")\n',
        '\n',
        '# We will use 50,000 for training and 5,000 for validation to save time\n',
        'small_train = dataset["train"].shuffle(seed=42).select(range(50000))\n',
        'small_test = dataset["test"].shuffle(seed=42).select(range(5000))\n'
    ]},
    {'cell_type': 'code', 'metadata': {}, 'source': [
        '# Initialize Tokenizer\n',
        'model_name = "distilbert-base-uncased"\n',
        'tokenizer = AutoTokenizer.from_pretrained(model_name)\n',
        '\n',
        'def tokenize_function(examples):\n',
        '    return tokenizer(examples["content"], padding="max_length", truncation=True, max_length=128)\n',
        '\n',
        'print("Tokenizing dataset...")\n',
        'tokenized_train = small_train.map(tokenize_function, batched=True)\n',
        'tokenized_test = small_test.map(tokenize_function, batched=True)\n'
    ]},
    {'cell_type': 'code', 'metadata': {}, 'source': [
        '# Initialize Model\n',
        'model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)\n',
        '\n',
        '# Define Metrics\n',
        'metric = evaluate.load("accuracy")\n',
        '\n',
        'def compute_metrics(eval_pred):\n',
        '    logits, labels = eval_pred\n',
        '    predictions = np.argmax(logits, axis=-1)\n',
        '    return metric.compute(predictions=predictions, references=labels)\n'
    ]},
    {'cell_type': 'code', 'metadata': {}, 'source': [
        '# Training Arguments\n',
        'training_args = TrainingArguments(\n',
        '    output_dir="./results",\n',
        '    eval_strategy="epoch",\n',
        '    save_strategy="epoch",\n',
        '    learning_rate=2e-5,\n',
        '    per_device_train_batch_size=32,\n',
        '    per_device_eval_batch_size=32,\n',
        '    num_train_epochs=2,\n',
        '    weight_decay=0.01,\n',
        ')\n',
        '\n',
        'trainer = Trainer(\n',
        '    model=model,\n',
        '    args=training_args,\n',
        '    train_dataset=tokenized_train,\n',
        '    eval_dataset=tokenized_test,\n',
        '    compute_metrics=compute_metrics,\n',
        ')\n'
    ]},
    {'cell_type': 'code', 'metadata': {}, 'source': [
        '# Train the Model\n',
        'print("Starting Training...")\n',
        'trainer.train()\n'
    ]},
    {'cell_type': 'code', 'metadata': {}, 'source': [
        '# Save Model and Tokenizer for Download\n',
        'save_path = "./distilbert_churnlens_model"\n',
        'trainer.save_model(save_path)\n',
        'tokenizer.save_pretrained(save_path)\n',
        '\n',
        '!zip -r distilbert_churnlens_model.zip distilbert_churnlens_model\n',
        'print("Model zipped! You can now download distilbert_churnlens_model.zip from the Colab file explorer.")\n'
    ]}
]

nb = {'cells': code_cells, 'metadata': {}, 'nbformat': 4, 'nbformat_minor': 4}

with open('notebooks/04_nlp_bert.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Notebook generated.")
