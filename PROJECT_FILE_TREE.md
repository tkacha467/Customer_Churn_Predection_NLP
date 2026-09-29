# PROJECT_FILE_TREE.md — Complete Repository & Directory Tree

**Generated Date:** September 29, 2026  
**Project:** ChurnLens / Nasta Ghar AI Review Assistant (`v2.4.0`)  
**Root Path:** `D:\churnlens`  
**Total Disk Footprint:** ~4.64 GB (4,979,883,439 bytes)  
**Total File Count:** 43,485 files  

---

## 1. Top-Level Directory Summary

| Directory / Item | Classification | File Count | Total Size (Bytes) | Size (MB) | Purpose & Description |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `data/` | Datasets (Offline) | 21 | 1,945,520,171 | 1,855.39 MB | Large CSV datasets (Amazon, Flipkart, Olist) used for offline ML training. |
| `models/` | ML Model Artifacts | 38 | 1,343,906,432 | 1,281.65 MB | DistilBERT weights, training checkpoints (`optimizer.pt`), pickle classifiers. |
| `.venv/` | Python VirtualEnv | 40,641 | 1,223,530,981 | 1,166.85 MB | Local Python 3.11 environment with PyTorch, Transformers, and scientific libraries. |
| `distilbert_churnlens_model.zip` | Archive | 1 | 246,990,683 | 235.55 MB | Standalone ZIP backup of fine-tuned DistilBERT model weights. |
| `frontend/` | React / Vite Frontend | 887 | 88,974,967 | 84.85 MB | Active React 19 SPA (Customer `/review` & Owner `/owner` interfaces) + node_modules. |
| `node_modules/` (root) | Stale Dependency | 1,767 | 29,577,996 | 28.21 MB | Stale root-level node_modules from legacy root build scripts. |
| `api/` | Backend Source Code | 68 | 253,257 | 0.24 MB | Active FastAPI backend, modular sentiment/sarcasm fusion pipeline, routes & auth. |
| `docs/` | Documentation | 17 | 223,484 | 0.21 MB | Deployment guides, architecture specs, integration notes, and presentations. |
| `tests/` | Automated Test Suite | 23 | 117,270 | 0.11 MB | Pytest automated test suites covering API, auth, storage, and NLP pipeline. |
| `chrome-extension/` | Companion Tool | 6 | 26,420 | 0.03 MB | Optional browser extension for automated Google Maps review auto-pasting. |
| `reports/` | Analysis Reports | 2 | 5,961 | 0.01 MB | Historical ML evaluation reports. |
| Root Files (`.gitignore`, etc.) | Configuration | 11 | 30,554 | 0.03 MB | Startup scripts, environment examples, pyproject.toml, and requirements. |

---

## 2. Largest Individual Files (> 15 MB)

| Rank | File Path | Size (Bytes) | Size (MB) | Category | Required at Runtime? |
| :---: | :--- | :---: | :---: | :--- | :---: |
| 1 | `data/train.csv` | 1,585,200,224 | 1,511.76 MB | Training Dataset | **No** (Offline training only) |
| 2 | `models/checkpoints/checkpoint-5/optimizer.pt` | 535,729,227 | 510.91 MB | PyTorch Optimizer | **No** (Training checkpoint only) |
| 3 | `.venv/Lib/site-packages/torch/lib/torch_cpu.dll` | 305,887,744 | 291.72 MB | Python Library | **Yes** (Local PyTorch runtime) |
| 4 | `models/distilbert_amazon/model.safetensors` | 267,832,560 | 255.43 MB | DistilBERT Weights | **No** (Legacy fine-tuned model) |
| 5 | `models/distilbert/model.safetensors` | 267,832,560 | 255.43 MB | DistilBERT Weights | **Optional** (Local offline fallback) |
| 6 | `models/checkpoints/checkpoint-5/model.safetensors` | 267,832,560 | 255.43 MB | Model Checkpoint | **No** (Training checkpoint) |
| 7 | `distilbert_churnlens_model.zip` | 246,990,683 | 235.55 MB | ZIP Archive | **No** (Archive backup) |
| 8 | `data/test.csv` | 176,046,679 | 167.89 MB | Evaluation Dataset | **No** (Offline evaluation only) |
| 9 | `data/raw/olist/olist_geolocation_dataset.csv` | 61,273,883 | 58.44 MB | Tabular Dataset | **No** (Legacy Olist dataset) |
| 10 | `data/flipkart.csv` | 57,988,503 | 55.30 MB | Benchmark Dataset | **No** (Offline benchmark only) |
| 11 | `.venv/Lib/site-packages/torch/lib/torch_cpu.lib` | 29,325,638 | 27.97 MB | Python Library | **Yes** (Local PyTorch dependency) |
| 12 | `.venv/Lib/site-packages/pyarrow/arrow.dll` | 21,993,984 | 20.98 MB | Python Library | **No** (Unused pyarrow runtime) |
| 13 | `frontend/node_modules/.../rolldown-binding.node` | 20,510,208 | 19.56 MB | Build Tooling | **Yes** (Vite build bundler) |
| 14 | `.venv/Lib/site-packages/numpy.libs/libscipy_openblas64_...dll` | 20,415,488 | 19.47 MB | Python Library | **Yes** (NumPy BLAS library) |
| 15 | `.venv/Lib/site-packages/torch/lib/torch_python.dll` | 20,099,584 | 19.17 MB | Python Library | **Yes** (PyTorch Python binding) |
| 16 | `data/raw/olist/olist_orders_dataset.csv` | 17,654,914 | 16.84 MB | Tabular Dataset | **No** (Legacy Olist dataset) |
| 17 | `data/raw/olist/olist_order_items_dataset.csv` | 15,438,671 | 14.72 MB | Tabular Dataset | **No** (Legacy Olist dataset) |

---

## 3. Structural Directory Tree

```
d:\churnlens\
├── .env.example                     # Environment template for local/production configuration
├── .gitignore                       # Git exclusions (data, models, .venv, dist, sqlite)
├── .editorconfig                    # Editor indentation and formatting standards
├── .pre-commit-config.yaml          # Pre-commit hook configurations
├── pyproject.toml                   # Python build system & backend dependencies
├── requirements.txt                 # Production Python requirements (FastAPI, PyTorch, Transformers)
├── start_app.bat                    # One-click Windows launcher for API and Frontend
├── README.md                        # Project landing readme
├── PRODUCT_PROGRESS.md              # Historical development roadmap
├── PRODUCTION_READINESS_REPORT.md   # Comprehensive QA and Security Audit report
│
├── api/                             # BACKEND APPLICATION
│   ├── main.py                      # FastAPI entry point, startup guards, CORS, model priming
│   ├── config/
│   │   └── settings.py              # Pydantic ModelConfig, FusionConfig, AppSettings
│   ├── preprocessing/
│   │   └── text_cleaner.py          # Regex cleaner, contractions expander, emoji normalizer
│   ├── models/
│   │   ├── model_loader.py          # Thread-safe lazy loader for HuggingFace/Local models
│   │   ├── sentiment.py             # 3-class sentiment analyzer (Positive, Neutral, Negative)
│   │   └── sarcasm.py               # Irony/sarcasm probability estimator
│   ├── fusion/
│   │   ├── engine.py                # Context-aware Sentiment & Sarcasm fusion engine
│   │   └── explainer.py             # Rule-based decision explainer for integrity debug
│   └── review_assistant/            # NASTA GHAR HOSPITALITY SERVICE MODULE
│       ├── __init__.py              # Router exporter
│       ├── routes.py                # 11 HTTP route handlers (ideas, generate, validate, tickets, analytics)
│       ├── schemas.py               # Pydantic request/response validation schemas & allowlists
│       ├── service.py               # Core orchestrator service, sliding-window rate limiters
│       ├── auth.py                  # HMAC-SHA256 signed owner cookie auth & origin protection
│       ├── generator.py             # Zero-fabrication review synthesis orchestrator
│       ├── validator.py             # Star-rating consistency validator
│       ├── storage.py               # SQLite WAL-mode persistence (2k events, 5k tickets)
│       ├── google_reviews.py        # Business config manager & Google review deep-link generator
│       ├── llm_provider.py          # LLM provider abstraction (Local deterministic vs Cloud)
│       ├── prompts.py               # 10 candidate review ideas & humanized prompt templates
│       └── business_links.json      # Default restaurant metadata (Nasta Ghar)
│
├── frontend/                        # REACT 19 + VITE CLIENT SPA
│   ├── index.html                   # HTML shell with responsive mobile meta viewport
│   ├── package.json                 # Frontend dependencies (React 19, QRCode, Vite, Oxlint)
│   ├── vite.config.js               # Vite bundler configuration & local development proxy
│   ├── public/                      # Static assets served at root
│   │   ├── favicon.svg              # Brand icon
│   │   ├── icons.svg                # SVG sprites
│   │   ├── nasta_ghar_review_qr.png # Table standee QR graphic
│   │   ├── nasta_ghar_standee.png   # Printable tabletop standee
│   │   └── restaurant/              # Scene background & Darshanbhai character assets
│   │       ├── darshan-host.png     # Host avatar graphic
│   │       ├── scene-phone.webp     # Mobile optimized restaurant backdrop
│   │       └── scene-wide.webp      # Tablet/Desktop restaurant backdrop
│   └── src/                         # React source code
│       ├── main.jsx                 # React root renderer
│       ├── App.jsx                  # Main routing container (/review vs /owner views)
│       ├── index.css                # Application styles (Glassmorphism, animations, responsive rules)
│       ├── lib/
│       │   └── api.js               # Centralized apiFetch client with credentials: include
│       └── components/
│           ├── CustomerReview.jsx   # Guest review creation journey, carousel, Google Maps redirect
│           ├── OwnerPortal.jsx      # Owner analytics dashboard, private tickets, QR generator
│           ├── RestaurantWorld.jsx  # Interactive restaurant atmosphere animation widget
│           ├── RestaurantWorld.css  # Scene-specific animation styling
│           └── NastaGharRestaurantScene.jsx # Interactive 3D/Isometric restaurant preview
│
├── tests/                           # AUTOMATED TEST SUITE (24 PASSING TESTS)
│   ├── conftest.py                  # Isolated test environment fixtures & temporary DB paths
│   ├── api/
│   │   └── test_neutral_sentiment.py # CardiffNLP sentiment threshold tests
│   ├── test_product_transformation.py # 10 candidate ideas, zero-fabrication & emoji rules
│   └── test_review_assistant.py     # Auth cookies, rate limits, SQLite storage, business config
│
├── chrome-extension/                # COMPANION EXTENSION
│   ├── manifest.json                # Chrome MV3 manifest
│   ├── content_app.js               # Auto-paste bridge on localhost review page
│   └── content_google.js            # Auto-paste bridge on Google Maps review page
│
├── docs/                            # SPECIFICATIONS & GUIDES
│   ├── DEPLOYMENT.md                # Production container deployment guide
│   ├── GOOGLE_INTEGRATION.md        # Google Place ID & Maps deep-linking documentation
│   ├── PRODUCT_SPECIFICATION.md     # Complete Nasta Ghar functional specifications
│   ├── PRODUCT_ARCHITECTURE.md      # Backend/Frontend architecture design
│   └── MODEL_AUDIT.md               # CardiffNLP & DistilBERT performance benchmarks
│
├── data/ (OFFLINE ONLY)             # Large CSV datasets for model training & evaluation
├── models/ (OFFLINE / BACKUP)       # PyTorch checkpoints and DistilBERT safetensors
└── .venv/ (LOCAL RUNTIME)           # Python 3.11 virtual environment
```
