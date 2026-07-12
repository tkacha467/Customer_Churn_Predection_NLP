# E-Commerce Customer Churn Prediction & Review Integrity Analysis using XGBoost + DistilBERT

**Course / Project Report**

---

## 1. Abstract
Customer retention and genuine product feedback are critical pillars of e-commerce sustainability. Traditional churn models rely solely on historical transactional data (Recency, Frequency, Monetary) but often overlook unstructured behavioral data. In this project, we propose a fused intelligence architecture. First, an XGBoost classifier with SMOTE oversampling predicts customer churn probability based on historical RFM metrics. Second, a fine-tuned DistilBERT Natural Language Processing (NLP) model evaluates the integrity of customer reviews, flagging cases where textual sentiment directly contradicts numerical star ratings (e.g., negative text with a 5-star rating). These two components are mathematically fused into a final "Customer Risk Score" (0.6 Churn + 0.4 Integrity Mismatch). Results validate that this multi-modal approach yields a highly accurate and actionable risk metric for e-commerce platforms.

## 2. Introduction & Problem Statement
Acquiring a new customer costs 5 to 25 times more than retaining an existing one. E-commerce platforms struggle with two interconnected issues:
1. **Unpredictable Churn**: Customers abandon platforms silently. By the time a business notices the lack of purchases, the customer is already lost.
2. **Review Fraud and Mismatch**: Platforms suffer from "review bombing" or fake reviews where the rating does not reflect the text, confusing recommendation algorithms and human buyers alike.

**Objective**: To build an end-to-end intelligent system that detects churning customers, evaluates review integrity using NLP, calculates a fused Risk Score, and visualizes the results on a Streamlit dashboard.

## 3. Literature Review
1. **Chen, T., & Guestrin, C. (2016)**. *XGBoost: A Scalable Tree Boosting System*. This foundational paper demonstrated that gradient boosting can highly effectively model tabular e-commerce data with missing values.
2. **Sanh, V. et al. (2019)**. *DistilBERT, a distilled version of BERT*. The authors demonstrated that a smaller, faster NLP transformer could retain 97% of BERT's language understanding capabilities, making it ideal for large-scale review analysis.
3. **Chawla, N. V. et al. (2002)**. *SMOTE: Synthetic Minority Over-sampling Technique*. Used in this project to resolve the massive class imbalance inherent in e-commerce churn datasets (where retained customers vastly outnumber churned ones).
4. **Burez, J., & Van den Poel, D. (2009)**. *Handling class imbalance in customer churn prediction*. This paper reinforces the necessity of using techniques like SMOTE to prevent the model from predicting the majority class.
5. **Pang, B., & Lee, L. (2008)**. *Opinion mining and sentiment analysis*. A seminal review confirming that cross-referencing user-provided ratings with extracted textual sentiment is a valid heuristic for anomaly detection.

## 4. Dataset Description
- **Olist Brazilian E-Commerce Dataset**: 100k+ orders across 9 relational tables (customers, orders, reviews, payments, products, etc.). Used for RFM features and churn labeling.
- **Amazon Reviews Dataset**: 3.4M+ real English reviews used for fine-tuning the DistilBERT sentiment classification task.
- **Flipkart Reviews Dataset**: 363k reviews used as a validation/test set for the NLP module.

## 5. Methodology

### 5.1 Data Engineering
Nine relational tables were joined sequentially. Missing product categories were imputed with "unknown" and translated from Portuguese to English.

### 5.2 Churn Prediction Module (XGBoost)
- **Labeling**: A customer was labeled as "Churned" (1) if they bought only once and their last order was >180 days before the dataset end date.
- **Features**: Recency, Frequency, Monetary (RFM), plus extra features like average delivery delay and preferred payment method.
- **Model**: An XGBoost Classifier was trained after balancing the dataset using SMOTE.

### 5.3 NLP Integrity Module (DistilBERT)
- **Architecture**: A binary sentiment classifier built on `distilbert-base-uncased`.
- **Integrity Logic**: A mismatch is flagged (1) if the rating is >= 4 but the text is negative, or if the rating is <= 2 but the text is positive.
- **Translation**: Portuguese reviews from the Olist dataset were translated to English using `deep-translator` before being passed through the BERT pipeline.

### 5.4 Risk Score Fusion
The final customer risk score was calculated using a weighted formula:
`Risk Score = (0.6 * Churn Probability) + (0.4 * Integrity Risk)`
- **High Risk**: > 0.7
- **Medium Risk**: 0.4 to 0.7
- **Low Risk**: < 0.4

## 6. Results
The XGBoost model significantly outperformed the dummy baseline across AUC-ROC and F1-Score metrics, proving that delivery delays and RFM profiles are strong indicators of churn. The DistilBERT model accurately flagged sarcastic and contradictory reviews, exposing hidden reputation damage.

## 7. Conclusion
The integration of tabular machine learning and unstructured NLP provides a far more robust view of a customer's true risk profile than traditional RFM models alone. The accompanying Streamlit dashboard allows non-technical stakeholders to effortlessly query the risk of any `customer_unique_id`.

## 8. Future Scope
- **Graph Neural Networks (GraphSAGE)**: Implementing GNNs to predict relationship-based churn (e.g., if a group of customers from the same zip code churn together).
- **Real-time API Alerts**: Hooking the Streamlit dashboard into a CRM to send automated email/SMS discount codes when a user crosses the 0.7 Risk Threshold.
- **Multilingual BERT**: Removing the translation bottleneck by fine-tuning an `xlm-roberta` model natively on Portuguese text.
- **Cloud Deployment**: Wrapping the ML models in Docker containers and deploying them as a scalable API on AWS (SageMaker) or GCP.
