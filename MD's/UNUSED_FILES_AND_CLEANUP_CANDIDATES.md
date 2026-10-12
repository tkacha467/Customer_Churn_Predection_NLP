# UNUSED_FILES_AND_CLEANUP_CANDIDATES.md — File Categorization & Candidate Audit

**Generated Date:** September 29, 2026  
**Project:** ChurnLens / Nasta Ghar AI Review Assistant (`v2.4.0`)  

---

## 1. Classification Categories

Every file and directory in the project has been categorized into one of seven distinct functional classes:

| Category | Definition | Deployment Treatment |
| :--- | :--- | :--- |
| **A. Production Runtime** | Necessary for the running FastAPI server, models, and React UI. | **Include in production container/host** |
| **B. Production Build** | Tooling needed during the build step (e.g., Vite bundler, requirements). | **Use during CI/CD build; omit build cache** |
| **C. Dev & Testing** | Test fixtures, pytest suites, mock files, dev configs. | **Retain in Git; exclude from prod container** |
| **D. Training & Research** | Datasets, training notebooks, evaluation scripts. | **Store in data warehouse/archive; omit from prod** |
| **E. Generated / Reproducible** | Vite build output (`dist/`), `.pytest_cache/`, `__pycache__/`. | **Exclude via `.gitignore`** |
| **F. Obsolete / Legacy** | Early prototype code, deprecated UI versions, unused starter assets. | **Candidate for repository deletion** |
| **G. Uncertain / Companion** | Auxiliary tools requiring business intent confirmation (e.g. extension). | **Retain until business confirmation** |

---

## 2. Category A: Required for Production Runtime

These files form the minimum runtime core of the Nasta Ghar application:

| Path | Size | Description & Runtime Role |
| :--- | :---: | :--- |
| `api/main.py` | 8.08 KB | FastAPI application instance, CORS middleware, startup model priming, routes mount. |
| `api/config/settings.py` | 1.04 KB | Model names, inference device, fusion thresholds. |
| `api/preprocessing/text_cleaner.py` | 1.95 KB | Regex-based input normalizer, emoji handler, contractions expander. |
| `api/models/model_loader.py` | 3.01 KB | Thread-safe singleton model pipeline loader. |
| `api/models/sentiment.py` | 1.45 KB | 3-class sentiment score extractor. |
| `api/models/sarcasm.py` | 0.86 KB | Irony/sarcasm probability estimator. |
| `api/fusion/engine.py` | 2.38 KB | Context-aware Sentiment/Sarcasm fusion engine. |
| `api/fusion/explainer.py` | 1.20 KB | Rule-based decision explainer. |
| `api/review_assistant/routes.py` | 9.80 KB | 11 FastAPI route endpoints under `/api`. |
| `api/review_assistant/schemas.py` | 6.03 KB | Pydantic request/response validation schemas and event allowlists. |
| `api/review_assistant/service.py` | 12.00 KB | Business orchestrator, sliding-window rate limiters, session management. |
| `api/review_assistant/auth.py` | 2.69 KB | Signed HTTP-only cookie authentication for owner portal. |
| `api/review_assistant/generator.py` | 3.60 KB | Review generation dispatcher. |
| `api/review_assistant/validator.py` | 3.68 KB | Review tone & star rating consistency validator. |
| `api/review_assistant/storage.py` | 3.34 KB | SQLite database repository for analytics events and private tickets. |
| `api/review_assistant/google_reviews.py` | 5.12 KB | Restaurant configuration and Google review deep-link generator. |
| `api/review_assistant/llm_provider.py` | 7.88 KB | LocalLLMProvider and optional CloudLLMProvider abstraction. |
| `api/review_assistant/prompts.py` | 19.35 KB | 10 candidate review options, humanized review synthesis rules. |
| `api/review_assistant/business_links.json` | 2.16 KB | Seed restaurant metadata (Nasta Ghar, Rajkot). |
| `frontend/dist/` (built assets) | ~360 KB | Pre-compiled static single-page application (`index.html`, `index-*.js`, `index-*.css`). |
| `frontend/public/restaurant/*` | 916.29 KB | Darshanbhai host graphic (`darshan-host.png`), backdrop webp images. |

---

## 3. Category B & C: Production Build, Development & Testing

| Path | Category | Size | Reason & Purpose |
| :--- | :---: | :---: | :--- |
| `frontend/package.json` | B | 507 B | Frontend npm dependencies (`react`, `react-dom`, `qrcode`, `vite`, `oxlint`). |
| `frontend/package-lock.json` | B | 57.16 KB | NPM dependency lockfile. |
| `frontend/vite.config.js` | B | 293 B | Vite build and local proxy configuration. |
| `frontend/src/*` (React source) | B | ~150 KB | React source code compiled by `npm run build`. |
| `requirements.txt` | B | 192 B | Python pip dependencies. |
| `pyproject.toml` | B | 365 B | Python project configuration. |
| `start_app.bat` | C | 2.48 KB | Windows developer launcher for starting frontend + backend concurrently. |
| `tests/conftest.py` | C | 537 B | Pytest test configuration and isolated temp database fixtures. |
| `tests/api/test_neutral_sentiment.py` | C | 2.57 KB | Sentiment threshold test suite. |
| `tests/test_product_transformation.py` | C | 6.15 KB | Review generation, 10 ideas, and emoji rules test suite. |
| `tests/test_review_assistant.py` | C | 7.10 KB | Auth, rate-limiting, SQLite persistence, and API integration test suite. |

---

## 4. Category D, E, F & G: Candidates for Exclusion & Future Cleanup

| Item / Path | Category | Disk Size | Git Status | Reason for Removal / Exclusion | Confidence | Recommended Action |
| :--- | :---: | :---: | :---: | :--- | :---: | :--- |
| `data/train.csv` | D | 1,511.76 MB | Ignored | 3.6M Amazon reviews dataset. Not read by active API. | **High** | **Exclude from prod deployment.** (Archive offline if needed for retraining). |
| `data/test.csv` | D | 167.89 MB | Ignored | 400k Amazon test reviews dataset. Not read by active API. | **High** | **Exclude from prod deployment.** |
| `data/flipkart.csv` | D | 55.30 MB | Ignored | 363k Flipkart reviews dataset. Not read by active API. | **High** | **Exclude from prod deployment.** |
| `data/raw/olist/*` | D | 119.34 MB | Ignored | Brazilian e-commerce churn tabular dataset (8 CSV files). | **High** | **Exclude from prod deployment.** |
| `models/checkpoints/checkpoint-5/` | D | 766.35 MB | Ignored | Intermediate PyTorch optimizer checkpoint (`optimizer.pt` = 510MB). | **High** | **Exclude from prod deployment.** |
| `models/distilbert_amazon/` | D | 255.43 MB | Ignored | Fine-tuned Amazon DistilBERT model. Not loaded by `model_loader.py`. | **High** | **Exclude from prod deployment.** |
| `distilbert_churnlens_model.zip` | D | 235.55 MB | Ignored | Standalone ZIP archive backup of DistilBERT model. | **High** | **Exclude from prod deployment.** |
| `models/*.pkl` | F | 2.97 MB | Ignored | XGBoost, Logistic Regression, TF-IDF vectorizer from ChurnLens v1. | **High** | **Exclude from prod deployment.** |
| `models/distilbert/` | A / D | 255.43 MB | Ignored | Local DistilBERT model weights (optional fallback in `model_loader.py`). | **Medium** | **Retain if offline fallback is required**; otherwise omit if Hugging Face cache is used. |
| `node_modules/` (root level) | F | 28.21 MB | Ignored | Stale root-level node_modules (Vite and React live in `frontend/node_modules`). | **High** | **Safe to delete from local disk.** |
| `chrome-extension/` | G | 26.42 KB | Tracked | Companion browser extension for auto-pasting reviews into Google Maps. | **Low** | **Retain in repository** as optional product companion. |
| `docs/` | C | 223.48 KB | Tracked | Documentation, specs, and architecture reference guides. | **High** | **Retain in Git; exclude from prod container image.** |
| `reports/` | C | 5.96 KB | Tracked | Historical ML benchmark reports. | **High** | **Retain in Git; exclude from prod container image.** |

---

## 5. Summary of Disk Savings for Deployment

| Scope | Total Disk Footprint |
| :--- | :---: |
| **Current Local Workspace (All Files, Datasets, Checkpoints, VirtualEnv)** | **4,640 MB (4.64 GB)** |
| **Offline Datasets & Checkpoints Excluded (`data/`, `checkpoints/`, etc.)** | **-3,142 MB (-3.14 GB)** |
| **VirtualEnv & Dev Tooling Excluded (Installed fresh in minimal container)** | **-1,250 MB (-1.25 GB)** |
| **Target Production Deployment Package Size (Source + Pre-cached RoBERTa Models)** | **~250 MB – 350 MB** |
