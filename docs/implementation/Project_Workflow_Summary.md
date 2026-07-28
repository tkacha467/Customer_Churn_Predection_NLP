# ChurnLens: Comprehensive Project Workflow & Technical Architecture

This document outlines the end-to-end workflow of the ChurnLens project, detailing every step taken, the algorithms and models applied, the technologies utilized, and the specific factors (features) involved.

---

## Phase 1: Data Engineering & Cleaning

**Objective:** Consolidate raw data into a clean, unified format for analysis.

*   **Actions Taken:**
    *   Ingested 9 relational tables from the Olist E-commerce dataset.
    *   Merged core tables (Orders, Customers, Payments, Reviews, Products) to create a single comprehensive dataset.
    *   Cleaned missing values by imputing medians for numerical data (like prices) and using placeholders for missing text.
    *   Standardized timestamp formats into proper datetime objects.
*   **Technologies Used:** Python, Pandas, NumPy.
*   **Factors/Features Handled:** `customer_id`, `order_id`, raw price, raw text, raw timestamps.

---

## Phase 2: Feature Engineering (RFM Analysis)

**Objective:** Transform raw transactional data into meaningful behavioral metrics that indicate customer engagement.

*   **Actions Taken:**
    *   Calculated standard RFM (Recency, Frequency, Monetary) metrics for each customer.
    *   Extracted additional operational and feedback metrics.
*   **Technologies Used:** Python, Pandas.
*   **Factors/Features Engineered:**
    *   **Recency:** Number of days since the customer's most recent purchase.
    *   **Frequency:** Total count of unique orders per customer.
    *   **Monetary:** Total monetary value spent by the customer.
    *   **Auxiliary Features:** Average delivery delays, average payment installments, and average review scores.

---

## Phase 3: Target Definition (Churn Labeling)

**Objective:** Define what constitutes a "churned" customer for the machine learning model to learn from.

*   **Actions Taken:**
    *   Established a business rule to identify churn.
    *   Created the binary target variable based on historical behavior.
*   **Technologies Used:** Python, Pandas.
*   **Factors/Features Created:**
    *   **`churn` (Target Variable):** Labeled as `1` (Churned) if the customer ordered exactly once AND their last order was more than 180 days ago. Labeled as `0` (Retained) otherwise.

---

## Phase 4: Predictive Modeling (Machine Learning for Churn)

**Objective:** Predict the probability of a customer churning based on their behavioral features.

*   **Actions Taken:**
    *   Split the dataset into Training (80%) and Testing (20%) sets.
    *   Applied synthetic oversampling to balance the dataset, preventing the model from being biased toward the majority class (retained customers).
    *   Trained a gradient boosting classifier to predict the churn probability.
    *   Evaluated model performance using Precision, Recall, F1-Score, and AUC-ROC metrics.
*   **Algorithms / Models Used:**
    *   **SMOTE (Synthetic Minority Over-sampling Technique):** To handle extreme class imbalance.
    *   **XGBoost (XGBClassifier):** The primary machine learning algorithm used for tabular churn prediction.
*   **Technologies Used:** Python, Scikit-Learn, Imbalanced-Learn, XGBoost.
*   **Factors/Features Used:** Recency, Frequency, Monetary, average delivery delays, average installments, average review scores.

---

## Phase 5: Natural Language Processing (Review Integrity)

**Objective:** Analyze the text of customer reviews to determine true sentiment and identify anomalies (e.g., sarcastic 5-star reviews or overly critical 5-star ratings).

*   **Actions Taken:**
    *   Scored the raw text sentiment of customer reviews.
    *   Vectorized the text data to convert words into numerical features.
    *   Compared expected textual sentiment against the actual numerical star rating given.
    *   Trained a classification model to detect if the text genuinely matches the rating.
*   **Algorithms / Models Used:**
    *   **VADER Sentiment:** A lexicon and rule-based sentiment analysis tool used to extract baseline sentiment scores.
    *   **TF-IDF (Term Frequency-Inverse Document Frequency):** Used (`TfidfVectorizer`) to translate raw text into a sparse matrix of numerical weights.
    *   **Logistic Regression:** A supervised classification model trained to predict whether a review is genuine or anomalous based on the TF-IDF vectors and sentiment scores.
*   **Technologies Used:** Python, Scikit-Learn, NLTK/VADER.
*   **Factors/Features Used:** Raw review text, numerical review scores (1-5 stars), TF-IDF word vectors, calculated sentiment polarity.

---

## Phase 6: Frontend Dashboard Development

**Objective:** Build an interactive, user-friendly interface for business stakeholders to explore the data, view risk profiles, and analyze model performance.

*   **Actions Taken:**
    *   Designed a high-contrast, dark-mode B2B SaaS dashboard.
    *   Implemented client-side CSV parsing to ingest model outputs directly without a backend server.
    *   Created data visualizations (charts, graphs) to display churn analysis and NLP insights.
*   **Technologies Used:** JavaScript, React 18, Vite, Tailwind CSS v4, Framer Motion (for animations), Recharts (for data visualization), PapaParse (for client-side CSV processing).
*   **Data Consumed:** Output CSV files from the Data Engineering and ML/NLP pipelines (containing Risk Scores, Churn Probabilities, and NLP integrity flags).
