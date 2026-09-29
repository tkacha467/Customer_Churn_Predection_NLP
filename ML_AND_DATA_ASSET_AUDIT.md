# ML_AND_DATA_ASSET_AUDIT.md — Machine Learning Models & Datasets Inventory

**Generated Date:** September 29, 2026  
**Project:** ChurnLens / Nasta Ghar AI Review Assistant (`v2.4.0`)  

---

## 1. Executive Summary of AI / ML Assets

The application architecture has evolved from an offline customer churn tabular dataset experiment (Olist/Flipkart) into a specialized **Real-Time Hospitality Review Assistant & Integrity Engine (Nasta Ghar)**.

- **Active Runtime Models:** Two CardiffNLP RoBERTa transformer pipelines (`twitter-roberta-base-sentiment-latest` and `twitter-roberta-base-irony`) loaded into PyTorch CPU inference with an adaptive sentiment/sarcasm fusion layer.
- **Review Generation:** Primarily powered by `LocalLLMProvider` (zero-fabrication deterministic synthesis and 10 candidate perspectives) with optional, resilient fallback for cloud LLMs (Gemini / OpenAI).
- **Offline Datasets & Checkpoints:** ~3.2 GB of training data (`train.csv`, `test.csv`, `flipkart.csv`, `olist`) and training checkpoints (`optimizer.pt`, `distilbert_amazon`) remain on disk from previous ML development phases, but are **not loaded or required during production runtime**.

---

## 2. Machine Learning Model Inventory

| Model Identifier | Architecture / Source | Loaded By | When Loaded | Disk Footprint | Memory (RAM) | Production Role | Failure & Fallback Behavior |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **`cardiffnlp/twitter-roberta-base-sentiment-latest`** | RoBERTa-base (125M params) via Hugging Face Hub | [`api/models/model_loader.py`](file:///d:/churnlens/api/models/model_loader.py#L27) | Background startup thread + on-demand singleton | ~498 MB (in HF cache) | ~450 MB RAM | **Primary Sentiment Validator:** 3-class classification (Positive, Neutral, Negative) for review drafts. | Falls back to local `models/distilbert/` if Hugging Face pipeline throws an exception. |
| **`cardiffnlp/twitter-roberta-base-irony`** | RoBERTa-base (125M params) via Hugging Face Hub | [`api/models/model_loader.py`](file:///d:/churnlens/api/models/model_loader.py#L55) | Background startup thread + on-demand singleton | ~498 MB (in HF cache) | ~450 MB RAM | **Sarcasm / Irony Estimator:** Computes irony probability to penalize false positive ratings. | Logs warning and sets `_sarcasm_model = None`; fusion engine operates on sentiment alone without failing. |
| **`models/distilbert/`** | DistilBERT (66M params, PyTorch Safetensors) | [`api/models/model_loader.py`](file:///d:/churnlens/api/models/model_loader.py#L38) | Only if CardiffNLP download fails | 255.43 MB | ~300 MB RAM | **Local Offline Fallback:** Binary sentiment model fine-tuned for offline use. | Used automatically if internet connection is down during first boot. |
| **`models/distilbert_amazon/`** | DistilBERT fine-tuned on Amazon customer reviews | None (Historical artifact) | Never loaded by active code | 255.43 MB | N/A | **Offline Research Asset:** Evaluated during initial benchmark. | Not referenced by `api/` or `frontend/`. |
| **`models/checkpoints/checkpoint-5/`** | PyTorch training checkpoint (`optimizer.pt` + `safetensors`) | None (Historical artifact) | Never loaded by active code | 766.35 MB | N/A | **Training Checkpoint:** Intermediate optimizer state from epoch 5. | Not referenced at runtime. Safe to exclude from deployment. |
| **`distilbert_churnlens_model.zip`** | Compressed model archive | None | Never loaded | 235.55 MB | N/A | **Backup Archive:** Standalone ZIP file of fine-tuned model. | Safe to exclude from deployment. |
| **`models/xgboost_churn_v1.pkl`** | XGBoost Classifier (Tabular Churn) | None | Never loaded | 0.73 MB | N/A | **Legacy Model:** Original telecom/e-commerce churn tabular model. | Not referenced by Nasta Ghar review assistant. |
| **`models/lr_mismatch_v1.pkl`** | Logistic Regression Classifier | None | Never loaded | 0.38 MB | N/A | **Legacy Model:** Early baseline mismatch detector. | Not referenced by Nasta Ghar review assistant. |
| **`models/tfidf_vectorizer.pkl`** | Scikit-Learn TF-IDF Matrix | None | Never loaded | 1.86 MB | N/A | **Legacy Feature Extractor:** Word unigram/bigram vectorizer. | Not referenced by Nasta Ghar review assistant. |

---

## 3. Dataset Inventory

| Dataset Name | File Path | File Size | Format | Read By | Runtime Necessity | Training / Research Purpose |
| :--- | :--- | :---: | :---: | :--- | :---: | :--- |
| **Amazon Reviews (Train)** | `data/train.csv` | 1,511.76 MB | CSV (Text + Label) | None (Legacy scripts) | **NOT NEEDED** | 3.6M Amazon reviews used for initial DistilBERT fine-tuning. |
| **Amazon Reviews (Test)** | `data/test.csv` | 167.89 MB | CSV (Text + Label) | None (Legacy scripts) | **NOT NEEDED** | 400k Amazon reviews test partition for evaluation. |
| **Flipkart Reviews** | `data/flipkart.csv` | 55.30 MB | CSV (Rating + Review) | None (Legacy scripts) | **NOT NEEDED** | 363k Flipkart customer reviews used for rating consistency validation tests. |
| **Olist Geolocation** | `data/raw/olist/olist_geolocation_dataset.csv` | 58.44 MB | CSV | None | **NOT NEEDED** | Brazilian ZIP code latitude/longitude coordinates (ChurnLens v1). |
| **Olist Orders** | `data/raw/olist/olist_orders_dataset.csv` | 16.84 MB | CSV | None | **NOT NEEDED** | Order status, timestamps, and delivery dates (ChurnLens v1). |
| **Olist Order Items** | `data/raw/olist/olist_order_items_dataset.csv` | 14.72 MB | CSV | None | **NOT NEEDED** | Line items, seller IDs, shipping limits, and item prices. |
| **Olist Order Reviews** | `data/raw/olist/olist_order_reviews_dataset.csv` | 13.78 MB | CSV | None | **NOT NEEDED** | Star ratings and Portuguese review survey responses. |
| **Olist Customers** | `data/raw/olist/olist_customers_dataset.csv` | 8.62 MB | CSV | None | **NOT NEEDED** | Customer IDs, customer unique IDs, city, and state. |
| **Olist Order Payments** | `data/raw/olist/olist_order_payments_dataset.csv` | 5.51 MB | CSV | None | **NOT NEEDED** | Payment types, installments, and transaction values. |
| **Olist Products** | `data/raw/olist/olist_products_dataset.csv` | 2.27 MB | CSV | None | **NOT NEEDED** | Category names, photos quantity, weight, and dimensions. |
| **Olist Sellers** | `data/raw/olist/olist_sellers_dataset.csv` | 0.17 MB | CSV | None | **NOT NEEDED** | Seller city, state, and location. |
| **Olist Category Translation** | `data/raw/olist/product_category_name_translation.csv` | 2.61 KB | CSV | None | **NOT NEEDED** | Portuguese to English category name translation lookup. |
| **Flipkart Integrity Output** | `data/processed/flipkart_integrity_results.csv` | 0.09 MB | CSV | None | **NOT NEEDED** | Output artifact from offline consistency batch evaluation script. |

---

## 4. LLM & Inference Provider Verification

### 1. Local Hospitality Synthesis Engine (`LocalLLMProvider`)
- **Location:** [`api/review_assistant/llm_provider.py#L43`](file:///d:/churnlens/api/review_assistant/llm_provider.py#L43) and [`api/review_assistant/prompts.py`](file:///d:/churnlens/api/review_assistant/prompts.py).
- **Execution Mode:** In-memory, deterministic template & synthesis engine.
- **Dependency:** Pure Python runtime; zero external API keys, zero network requests, zero monthly cost.
- **Constraints Enforced:**
  - 15 to 45 words maximum.
  - 0 to 2 contextual emojis (tasteful calibration, 0 emojis for 1-2 star ratings).
  - Strict zero fabrication (never invents unmentioned dishes, staff names, or events).
  - 10 candidate perspectives across all 1–5 star ratings (e.g. Breakfast, Chai, Staff Hospitality, Cleanliness, Value, Family).

### 2. Cloud LLM Provider (`CloudLLMProvider`)
- **Location:** [`api/review_assistant/llm_provider.py#L90`](file:///d:/churnlens/api/review_assistant/llm_provider.py#L90).
- **Supported Integrations:** Google Gemini (`gemini-1.5-flash`) via `GEMINI_API_KEY` and OpenAI (`gpt-4o-mini`) via `OPENAI_API_KEY`.
- **Fault-Tolerance:** Built-in try-catch with a 5-second socket timeout. If the API key is missing, expired, rate-limited, or network fails, it **automatically and silently falls back to `LocalLLMProvider`** without throwing an error to the diner.

### 3. Ollama / Local GGUF
- **Status:** Not present in active runtime path. The local CardiffNLP RoBERTa model handles validation, while `LocalLLMProvider` handles generation without requiring an Ollama background process.

---

## 5. Memory and Sizing Profile for Deployment

- **PyTorch + Hugging Face Cache:**
  - Disk storage for CardiffNLP RoBERTa weights: **~1.0 GB** in standard Hugging Face cache (`~/.cache/huggingface/hub`).
  - RAM consumption during inference: **~1.0 GB – 1.2 GB RAM**.
  - Minimum Recommended Server Instance: **1.5 GB to 2.0 GB RAM** (e.g. DigitalOcean $6/mo droplet, Render Standard 2GB, or AWS t4g.small).
- **Offline Assets Safe for Exclusion:**
  - Excluding `data/` (1.85 GB), `models/checkpoints/` (766 MB), `models/distilbert_amazon/` (255 MB), and `distilbert_churnlens_model.zip` (235 MB) reduces the repository/container build payload by **over 3.1 GB**.
