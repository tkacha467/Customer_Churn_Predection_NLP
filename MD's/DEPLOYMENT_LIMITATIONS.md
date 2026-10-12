# DEPLOYMENT_LIMITATIONS.md — Operational Constraints, Resource Limits & Hosting Risks

**Generated Date:** September 29, 2026  
**Product:** ChurnLens / Nasta Ghar AI Review Assistant (`v2.4.0`)  

---

## 1. Memory (RAM) Requirements & Measurement

### Measured Memory Footprint
- **Idle FastAPI Process:** ~120 MB RAM.
- **CardiffNLP RoBERTa Sentiment Model:** ~450 MB RAM in PyTorch memory.
- **CardiffNLP Irony/Sarcasm Model:** ~450 MB RAM in PyTorch memory.
- **Peak Memory During Concurrent Inference:** **~1.1 GB – 1.3 GB RAM**.

### Minimum Sizing Matrix
| Plan / Resource | RAM | Viability for Nasta Ghar | Outcome / Risk |
| :--- | :---: | :---: | :--- |
| **Free Tier (512 MB RAM)** | 512 MB | ❌ **UNSUITABLE** | Process will be killed immediately by Linux kernel with **OOM (Out Of Memory)** error during model loading. |
| **Starter (1.0 GB RAM)** | 1,024 MB | ⚠️ **MARGINAL / RISKY** | May start, but risk of OOM crash under 2+ concurrent customer review validation requests. |
| **Standard (1.5 GB – 2.0 GB RAM)** | 1,536–2,048 MB | ✅ **RECOMMENDED / STABLE** | Smooth concurrent inference, zero OOM risk, stable background garbage collection. |
| **Production Scale (4.0 GB+ RAM)** | 4,096 MB | ✅ **HIGH CAPACITY** | Supports 20+ concurrent dining table requests per second with multi-worker Uvicorn. |

*How Measured:* Measured locally during 24-test PyTorch pipeline initialization and inference benchmarking via Python `psutil` and process memory inspection.

---

## 2. Disk Storage Requirements

| Storage Component | Required Space | Type | Consequence of Missing Persistence |
| :--- | :---: | :---: | :--- |
| **Container Image / OS / PyTorch** | ~2.2 GB | Read-Only Image Layer | N/A (baked into container image). |
| **Pre-cached RoBERTa Model Weights** | ~996 MB | Read-Only Cache (`/root/.cache`) | If not pre-cached, downloaded on every restart. |
| **SQLite Database (`reviews.sqlite3`)** | < 15 MB | **PERSISTENT VOLUME** | **CRITICAL:** If stored on ephemeral container disk, all analytics events, table stats, and private feedback tickets are **wiped permanently on every redeploy or restart**. |
| **Business Links JSON (`business_links.json`)**| < 50 KB | **PERSISTENT VOLUME** | **CRITICAL:** Custom topics and Google Review URL overrides will reset to factory defaults on container restart if unmounted. |

---

## 3. Risks of Free-Tier / Serverless Hosting

Many free hosting providers (e.g., free Render Web Services, free Glitch, free Fly.io tiers, free Heroku-style dynos) impose operational behaviors that degrade or break the restaurant dining experience:

### A. Sleeping / Cold-Start Latency (15-Minute Inactivity Sleep)
- **The Problem:** Free-tier instances spin down ("sleep") after 15 minutes of zero web traffic.
- **Impact on Diners:** When a diner sits at Table 4 at 8:00 AM and scans the QR standee, the sleeping container must boot, load Python, import PyTorch, and prime NLP models. This takes **45 to 90 seconds**, causing diners to assume the QR code is broken and close the page.
- **Mitigation:** Use an always-on host (\$5–\$7/mo droplet or paid PaaS tier) or configure an uptime monitoring ping (`GET /healthz` every 5 minutes).

### B. Ephemeral Disk Reset on Redeploy
- **The Problem:** Serverless functions (AWS Lambda, Vercel Serverless, Google Cloud Functions) and stateless containers have an immutable, ephemeral file system.
- **Impact on Business:** Restaurant owners will lose custom Google review link updates, table analytics, and private escalation tickets whenever a new deploy occurs.
- **Mitigation:** Mount a dedicated persistent volume at `/data` or connect to an external managed database (PostgreSQL) if scaling across multiple server instances.

### C. Cross-Domain Cookie Blocking
- **The Problem:** The Owner Portal relies on `HttpOnly; SameSite=Strict; Secure` session cookies.
- **Impact:** If the frontend is deployed to `nasta-ghar.vercel.app` and the API backend is deployed to `nasta-api.onrender.com`, modern browsers (Chrome/Safari) treat this as a third-party cross-site request and **block the authentication cookie**, preventing the owner from logging in.
- **Mitigation:** Host both under the same parent domain (e.g., `app.yourdomain.com` and `api.yourdomain.com`) or configure an Nginx / Cloudflare reverse proxy on a single origin.

---

## 4. External API Dependencies & Cost Exposure

```
+-----------------------------------------------------------------------------------------+
| Default Configuration (`LLM_PROVIDER=local`):                                          |
| - Google Maps API: ZERO API calls (uses standard HTTPS URL deep-links)                   |
| - LLM Costs: $0.00 / month (100% deterministic local template & synthesis rules)        |
| - CardiffNLP Models: Free & open-source (no subscription or token billing)              |
| - Total External API Cost: $0.00 / month                                                |
+-----------------------------------------------------------------------------------------+
| Optional Cloud Mode (`LLM_PROVIDER=gemini` or `LLM_PROVIDER=openai`):                   |
| - Gemini 1.5 Flash: ~$0.0001 per review (Free tier provides 15 RPM at zero cost)       |
| - OpenAI GPT-4o-mini: ~$0.00015 per review                                              |
| - Unexpected Bill Risk: LOW (Sliding-window rate limiter caps requests at 30/min/IP)    |
| - Fallback: Automatic silent fallback to local engine if key quota is exhausted         |
+-----------------------------------------------------------------------------------------+
```

---

## 5. Features Affected by Hosting Constraints

| Feature | Condition / Constraint | Impact if Constraint Unmet |
| :--- | :--- | :--- |
| **Real-Time Sentiment Validation** | Host has < 1.0 GB RAM | Endpoint crashes with 500 error due to Out-Of-Memory. |
| **Instant Review Ideas (Carousel)**| Instant Local Engine | Operates smoothly even on minimal CPU (latency < 5ms). |
| **One-Tap Clipboard Copy** | Non-HTTPS hosting (`http://`) | Modern mobile browsers **block `navigator.clipboard`** on insecure origins. HTTPS is mandatory for clipboard copy. |
| **Google Maps App Opening** | User browser on mobile | Direct URL `https://maps.google.com/...` opens native Google Maps app if installed, or mobile browser if not. |
| **Table Analytics Feed** | Missing persistent disk | Analytics reset to 0 after server restart. |
| **Owner Password Reset** | No database-stored passwords | Password is controlled strictly by `OWNER_PASSWORD` environment variable in cloud secret manager. |

---

## 6. Summary of Hosting Recommendations

1. **Best Low-Cost Solution (\$4–\$6 / month):**
   - **Provider:** DigitalOcean, Linode, Hetzner, or Hetzner Cloud VPS.
   - **Configuration:** 2 GB RAM, 1 vCPU, 20 GB SSD.
   - **Setup:** Docker + Docker Compose + Caddy/Nginx (handles free SSL automatically and serves frontend + backend on one domain).
2. **Best Managed Container PaaS (\$7–\$12 / month):**
   - **Provider:** Railway, Render (Standard plan), or Fly.io.
   - **Configuration:** 2 GB RAM plan + 1 GB persistent volume mounted at `/data`.
