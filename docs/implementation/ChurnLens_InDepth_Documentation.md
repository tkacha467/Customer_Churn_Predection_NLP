# ChurnLens: Customer Risk Intelligence Platform
## Comprehensive Project Documentation

---

## 1. Executive Summary
**ChurnLens** is an end-to-end Machine Learning pipeline and interactive React dashboard designed to predict customer churn and evaluate review integrity for e-commerce platforms. By combining transactional data (RFM metrics) with Natural Language Processing (NLP) on customer reviews, ChurnLens provides a holistic 360-degree risk profile for every customer.

## 2. The Real Problem We Are Solving
In the highly competitive e-commerce sector, acquiring a new customer is 5 to 25 times more expensive than retaining an existing one. 
The core problems businesses face are:
1. **Unpredictable Customer Attrition (Churn)**: Companies often only realize a customer has left *after* they stop buying. There is no proactive intervention.
2. **Review Fraud and Mismatches**: Customers sometimes leave 5-star ratings but write scathing negative reviews (or vice-versa), polluting product metrics and hiding real sentiment.
3. **Siloed Data**: Transactional data (purchases) and behavioral data (reviews) are usually kept separate, preventing a unified view of customer risk.

**The Solution:** ChurnLens solves this by identifying *at-risk* customers before they leave using XGBoost, while simultaneously using NLP to detect sentiment anomalies in reviews, aggregating this into a single, actionable "Risk Score".

---

## 3. Technology Stack
This project is built using a modern, scalable, serverless-frontend architecture.

### Data Engineering & Machine Learning (Python)
- **Pandas & NumPy**: For heavy data manipulation, merging 100k+ rows across 9 tables.
- **Scikit-Learn**: For data preprocessing, TF-IDF vectorization, and Logistic Regression.
- **Imbalanced-Learn (SMOTE)**: To handle the massive class imbalance between retained and churned customers.
- **XGBoost**: The primary Gradient Boosting classifier used for predicting churn probability.
- **VADER Sentiment**: For lexicon and rule-based sentiment analysis on customer reviews.

### Frontend Application (JavaScript / React)
- **React 18 & Vite**: Lightning-fast frontend framework and bundler.
- **Tailwind CSS v4**: Utility-first styling for a clinical, professional B2B SaaS aesthetic (Vercel/Datadog inspired).
- **Framer Motion**: For buttery-smooth, physics-based page transitions and animations.
- **Recharts**: For rendering dynamic, animated SVG charts.
- **PapaParse**: For in-browser CSV parsing, eliminating the need for a backend server.

---

## 4. Step-by-Step Implementation Guide
How this project was built from scratch:

### Phase 1: Data Engineering & Cleaning
1. Loaded 9 relational tables from the Olist E-commerce dataset.
2. Merged tables (Orders, Customers, Payments, Reviews, Products) using `customer_id` and `order_id`.
3. Handled missing values (imputed medians for prices, filled missing text with placeholders).
4. Converted timestamp strings to proper `datetime` objects.

### Phase 2: Feature Engineering (RFM)
1. **Recency**: Calculated the days since the customer's last purchase.
2. **Frequency**: Counted the total number of unique orders per customer.
3. **Monetary**: Summed the total payment value per customer.
4. **Extra Features**: Extracted average delivery delays, average installments, and average review scores.

### Phase 3: Churn Label Creation
1. Defined a "Churned" customer as someone who has only ordered once AND hasn't ordered in the last 180 days.
2. Created a binary target variable `churn` (1 = Churned, 0 = Retained).

### Phase 4: XGBoost Predictive Modeling
1. Split the engineered dataset into 80% Training and 20% Testing.
2. Applied **SMOTE** (Synthetic Minority Over-sampling Technique) to the training data so the model doesn't just predict "Retained" every time.
3. Trained an **XGBClassifier** to predict the churn probability.
4. Evaluated using Precision, Recall, F1-Score, and AUC-ROC, exporting the `feature_importance.png`.

### Phase 5: NLP Review Integrity Detection
1. Vectorized customer review text using `TfidfVectorizer`.
2. Calculated expected sentiment vs actual star rating.
3. Trained a Logistic Regression model to classify whether a review's text matches its rating.
4. Exported the `nlp_confusion_matrix.png`.

### Phase 6: Frontend Dashboard Construction
1. Built a React SPA using Vite.
2. Designed a pure dark-mode, high-contrast UI using Tailwind CSS.
3. Created an interactive `dataLoader.js` to parse the processed CSVs directly in the browser.
4. Built 5 distinct pages: Overview, Churn Analysis, Review Integrity, Customer Lookup, and Model Performance.

---

## 5. SWOT Analysis

### Strengths
- **Proactive rather than Reactive**: Identifies risk before the customer actually leaves.
- **Multi-modal Analysis**: Combines tabular numerical data with unstructured text data for better accuracy.
- **Serverless Architecture**: The React frontend parses CSVs directly, meaning zero hosting costs for a backend database.

### Weaknesses
- **Static Data Dependency**: Currently, the dashboard reads from static CSV files. In a real-world enterprise scenario, it would need to be connected to a live SQL database via an API.
- **Language Limitations**: The current NLP model is primarily optimized for English text; localized e-commerce platforms would require multilingual embeddings.

### Opportunities
- **Automated Marketing Hooks**: The system can be extended to automatically trigger discount emails via a CRM (like HubSpot or Salesforce) when a customer's Risk Score crosses 80%.
- **Deep Learning Upgrade**: Transitioning from XGBoost to neural networks (e.g., TabNet) if the dataset grows into the tens of millions of rows.

### Threats
- **Data Privacy (GDPR/CCPA)**: Handling granular customer data requires strict compliance. The system must ensure PII (Personally Identifiable Information) is anonymized.
- **Concept Drift**: E-commerce behavior changes rapidly. A model trained on 2018 data will eventually degrade in accuracy in 2026 without continuous retraining.

---

## 6. Conclusion
ChurnLens transforms raw, messy e-commerce logs into a refined, predictive intelligence tool. By giving business stakeholders a sleek, Datadog-style interface to search for specific users and visualize global churn trends, ChurnLens bridges the gap between complex data science and actionable business strategy.
