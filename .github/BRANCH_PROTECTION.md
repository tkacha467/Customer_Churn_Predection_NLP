# VRAJA AI — GitHub Security Controls & Branch Protection Specification
**Document Version:** 1.0 (Phase A6.5 Release Readiness)  
**Target Repository:** `tkacha467/Customer_Churn_Predection_NLP`

---

## 1. Protected Branch Configuration (`main`)

To ensure unverified code, unreviewed commits, or unisolated database operations never reach staging or production, the following branch protection settings must be configured on GitHub:

### 1.1 Pull Request Requirements
- **Require a pull request before merging**: Enforced.
- **Require approvals**: Minimum 1 approved review from authorized code owners.
- **Dismiss stale pull request approvals when new commits are pushed**: Enabled.
- **Require review from Code Owners**: Enabled (Security & Lead Architect).
- **Require approval of the most recent reviewable push**: Enabled.

### 1.2 Status Checks Requirements (Must pass before merging)
- `backend-security-and-tests` (Python 3.11 Pytest execution with database safety guards)
- `frontend-builds-and-audit` (Node 20 Product A and Product B `vite build` + npm audit)
- `release-integrity-manifest` (Release artifact cryptographic SHA-256 fingerprinting)
- `secret-scanning` (Gitleaks automated credential scan)

### 1.3 Branch Integrity & Hygiene
- **Require branches to be up to date before merging**: Enabled.
- **Require signed commits**: Enabled (GPG/SSH signature verification).
- **Require linear history**: Enabled (Squash & Merge or Rebase).
- **Do not allow bypassing the above settings**: Enabled (Enforce for Administrators).
- **Allow force pushes**: Strictly **DISABLED**.
- **Allow deletions**: Strictly **DISABLED**.

---

## 2. Release Artifact Integrity & Monitoring Design

### 2.1 File Integrity vs Live Database Separation
- **Code & Executable Artifacts**: `Backend/**/*.py`, `requirements.txt`, `Dockerfile`, `dist/**` are cryptographically fingerprinted in a release manifest linked to the Git commit SHA (`github.sha`).
- **Live SQLite Database**: Legitimate diner reviews and profile changes naturally modify the content and row checksum of `reviews.sqlite3`. Live databases are therefore monitored for:
  1. **Structural Health**: `PRAGMA quick_check(1)` ensuring zero B-tree or page corruption.
  2. **Schema Integrity**: SHA-256 fingerprint of `sqlite_master` DDL (tables, columns, indexes, triggers).
  3. **Data Integrity**: Foreign key constraints and transaction rollback guarantees.

---

## 3. Emergency Alerts Routing
All critical integrity breaches, schema tampering attempts, or container compromise events trigger alerts routed directly to:
**`vajra.techworks@gmail.com`** via VRAJA AI Security Shield.
