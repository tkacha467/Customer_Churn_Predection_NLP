# AUDIT_SUMMARY.md — Comprehensive Repository, Dependency & Asset Audit Summary

**Audit Date:** September 29, 2026  
**Project:** ChurnLens / Nasta Ghar AI Review Assistant (`v2.4.0`)  
**Workspace Path:** `D:\churnlens`  
**Current Git Commit:** `253e6dd` on branch `main`  
**Total Workspace Size:** 4.64 GB (4,979,883,439 bytes) across 43,485 files  

---

## 1. Executive Summary

A comprehensive, evidence-based audit of the entire `D:\churnlens` repository was conducted to establish exact runtime requirements, map code and data dependencies, identify disk bloat, and verify production deployment readiness.

### Key Audit Findings
1. **Product Focus:** The repository houses the active **Nasta Ghar AI Review Assistant** (FastAPI backend + React 19 frontend). The customer journey operates at `/review` and the owner dashboard operates at `/owner`.
2. **Disk Breakdown:** Of the 4.64 GB on disk, **over 3.14 GB (68%)** consists of offline training CSV datasets (`data/` = 1.85 GB) and PyTorch training checkpoints (`models/checkpoints/` = 766 MB, `distilbert_churnlens_model.zip` = 235 MB) that are **completely unused during production runtime**.
3. **Active AI Models:** The live application loads two lightweight CardiffNLP RoBERTa models from Hugging Face for sentiment (`cardiffnlp/twitter-roberta-base-sentiment-latest`) and sarcasm analysis (`cardiffnlp/twitter-roberta-base-irony`), with review generation handled locally by `LocalLLMProvider` (10 candidate ideas, zero-fabrication rules).
4. **Automated Verification:** All 24 automated backend tests pass (`24 passed, 0 failed`), the React frontend builds in 295ms (producing a 290 kB JS / 88 kB gzip bundle), and the linter passes with 0 errors.

---

## 2. Active Application Entry Points & Execution Flow

```
+-----------------------------------------------------------------------------------+
| 1. Customer Scans QR Code (?table=T1&type=dine_in)                                |
|    -> React SPA loads /review in mobile browser                                   |
| 2. Customer selects Star Rating (1-5) & Aspects (Breakfast, Chai, Staff, etc.)    |
|    -> POST /api/reviews/ideas returns 10 distinct, natural review candidate ideas |
| 3. Customer selects idea card & taps "Draft Review"                               |
|    -> POST /api/reviews/generate generates 15-45 word draft with 0-2 emojis       |
|    -> Real-time CardiffNLP RoBERTa + Sarcasm validation ensures rating matches    |
| 4. Customer taps "Copy & Open Google Review"                                      |
|    -> Draft copied to clipboard, browser opens official Google review page        |
|    -> SQLite logs analytics event (total generations, copies, clicks)             |
+-----------------------------------------------------------------------------------+
```

- **Frontend Entry:** [`frontend/src/main.jsx`](file:///d:/churnlens/frontend/src/main.jsx) $\rightarrow$ [`frontend/src/App.jsx`](file:///d:/churnlens/frontend/src/App.jsx)
- **Backend Entry:** [`api/main.py`](file:///d:/churnlens/api/main.py)
- **Review Service Router:** [`api/review_assistant/routes.py`](file:///d:/churnlens/api/review_assistant/routes.py)

---

## 3. Top 10 Largest Sources of Disk Usage

| Rank | Path | Size | Category | Runtime Need |
| :---: | :--- | :---: | :--- | :---: |
| 1 | `data/train.csv` | 1.51 GB | Offline Dataset | **No** |
| 2 | `.venv/` | 1.17 GB | Python Virtual Environment | **Yes (Local dev only)** |
| 3 | `models/checkpoints/checkpoint-5/` | 766.35 MB | Training Checkpoint | **No** |
| 4 | `models/distilbert/` | 255.43 MB | DistilBERT Local Fallback | **Optional fallback** |
| 5 | `models/distilbert_amazon/` | 255.43 MB | Historical DistilBERT Model | **No** |
| 6 | `distilbert_churnlens_model.zip` | 235.55 MB | Backup ZIP Archive | **No** |
| 7 | `data/test.csv` | 167.89 MB | Offline Dataset | **No** |
| 8 | `data/raw/olist/` | 119.34 MB | Tabular Churn Dataset | **No** |
| 9 | `frontend/node_modules/` | 84.85 MB | Node.js Dependencies | **Build time only** |
| 10 | `data/flipkart.csv` | 55.30 MB | Benchmark Dataset | **No** |

---

## 4. Confirmed Unused / Obsolete Files

The following items have zero references in the active runtime path, test suite, or build pipeline:

1. **Large Training Datasets (`data/`):** `train.csv` (1.51 GB), `test.csv` (167.89 MB), `flipkart.csv` (55.3 MB), and `data/raw/olist/*` (119 MB).
2. **Intermediate Checkpoints:** `models/checkpoints/checkpoint-5/optimizer.pt` (510.9 MB) and `safetensors` (255.4 MB).
3. **Backup Archive:** `distilbert_churnlens_model.zip` (235.55 MB).
4. **Historical Models:** `models/distilbert_amazon/` (255.4 MB), `models/xgboost_churn_v1.pkl` (0.73 MB), `models/lr_mismatch_v1.pkl` (0.38 MB), `models/tfidf_vectorizer.pkl` (1.86 MB).
5. **Root Node Modules:** `node_modules/` at root (28.21 MB). (Vite and React reside cleanly in `frontend/node_modules/`).

---

## 5. Files to Exclude from Production Deployment

When building Docker containers or deploying to cloud hosts (Railway, Render, Fly.io, VPS), exclude the following to keep the deployment image under **850 MB download / 2.2 GB uncompressed**:
- `data/` (Excludes 1.85 GB of CSVs)
- `models/checkpoints/` and `models/distilbert_amazon/` (Excludes 1.02 GB)
- `distilbert_churnlens_model.zip` (Excludes 235 MB)
- `node_modules/` at project root (Excludes 28 MB)
- `tests/` and `docs/` (Retained in Git, omitted from production container)

---

## 6. Uncertain Files Requiring Product Review

- **`chrome-extension/` (26.42 KB):** A Chrome MV3 extension designed to automate pasting copied reviews into Google Maps review modals. Retained in repository as an optional companion tool.

---

## 7. Discrepancies Between Code and Historical Documentation

1. **Brand Identity:** Some early template docstrings and schemas referenced a placeholder ("Cuore Cafe"). This was audited and corrected to **Nasta Ghar (Breakfast & Snacks, Rajkot)** across all schemas and route fallbacks.
2. **LLM Provider:** Older docs mentioned Ollama/GGUF requirements. The codebase has transitioned to an in-memory `LocalLLMProvider` that enforces strict zero-fabrication rules and 15–45 word constraints without external background processes.
3. **Storage Strategy:** The database has transitioned to SQLite WAL mode with hard retention limits (2,000 analytics events, 5,000 feedback tickets) to ensure permanent sub-15MB storage without disk unbounded growth.

---

## 8. Audit Reports Created in this Task

All detailed audit findings have been compiled into dedicated markdown reports:

1. [**`PROJECT_FILE_TREE.md`**](file:///d:/churnlens/PROJECT_FILE_TREE.md) — Complete recursive directory tree, top file rankings, and size breakdowns.
2. [**`FILE_DEPENDENCY_GRAPH.md`**](file:///d:/churnlens/FILE_DEPENDENCY_GRAPH.md) — Mermaid architecture diagrams, import tracing, and file-by-file dependency table.
3. [**`ML_AND_DATA_ASSET_AUDIT.md`**](file:///d:/churnlens/ML_AND_DATA_ASSET_AUDIT.md) — In-depth analysis of CardiffNLP RoBERTa, DistilBERT, datasets, and LLM providers.
4. [**`UNUSED_FILES_AND_CLEANUP_CANDIDATES.md`**](file:///d:/churnlens/UNUSED_FILES_AND_CLEANUP_CANDIDATES.md) — 7-category classification of all files, removal candidates, and risk assessment.
5. [**`PRODUCTION_DEPLOYMENT_INVENTORY.md`**](file:///d:/churnlens/PRODUCTION_DEPLOYMENT_INVENTORY.md) — Minimal production manifest, Dockerfile, environment variables, and persistence rules.
6. [**`AUDIT_SUMMARY.md`**](file:///d:/churnlens/AUDIT_SUMMARY.md) — This high-level executive summary.

---

## 9. Recommended Next Steps

1. **Commit Working Tree Changes:** Commit the verified production-readiness improvements and audit reports to Git.
2. **Exclude Offline Data in `.dockerignore`:** Ensure `.dockerignore` explicitly ignores `data/`, `models/checkpoints/`, `models/distilbert_amazon/`, and `*.zip`.
3. **Host on 2 GB RAM Instance:** Deploy backend container to a cloud host (e.g. Railway, Render, DigitalOcean) with at least 1.5–2 GB RAM and an attached persistent volume mounted to `/data`.
