import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="ChurnLens Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Load Data ---
@st.cache_data
def load_data():
    try:
        features = pd.read_csv('../data/processed/rfm_features.csv')
        risk_scores = pd.read_csv('../data/processed/final_risk_scores.csv')
        nlp_scores = pd.read_csv('../data/processed/nlp_integrity_scores.csv')
        return features, risk_scores, nlp_scores
    except Exception as e:
        st.error(f"Error loading data: {e}. Please ensure you have run the full pipeline in src/.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

features, risk_scores, nlp_scores = load_data()

# --- Sidebar Navigation ---
st.sidebar.title("ChurnLens")
st.sidebar.markdown("Customer Risk Intelligence Platform")
page = st.sidebar.radio("Navigate", ["Overview", "Churn Analysis", "Review Integrity", "Customer Lookup", "Model Performance"])

if not risk_scores.empty:
    if page == "Overview":
        st.title("Project Overview")
        st.write("Welcome to the ChurnLens dashboard. This platform combines XGBoost churn predictions with DistilBERT NLP review integrity to provide a unified Customer Risk Score.")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Customers", len(risk_scores))
        churn_rate = (risk_scores['churn'].mean() * 100) if 'churn' in risk_scores else 0
        col2.metric("Overall Churn Rate", f"{churn_rate:.1f}%")
        
        high_risk = len(risk_scores[risk_scores['risk_category'] == 'HIGH RISK'])
        col3.metric("High Risk Customers", high_risk)

        st.subheader("Risk Distribution")
        fig = px.pie(risk_scores, names='risk_category', title='Customer Risk Categories',
                     color='risk_category', color_discrete_map={'HIGH RISK':'#ff4b4b', 'MEDIUM RISK':'#ffa421', 'LOW RISK':'#00cc96'})
        st.plotly_chart(fig, use_container_width=True)

    elif page == "Churn Analysis":
        st.title("Churn Analysis (XGBoost)")
        
        st.subheader("RFM Distribution by Churn Status")
        col1, col2 = st.columns(2)
        
        fig_recency = px.box(features, x='churn', y='recency', color='churn', title="Recency vs Churn")
        col1.plotly_chart(fig_recency, use_container_width=True)
        
        fig_monetary = px.box(features, x='churn', y='monetary', color='churn', title="Monetary Value vs Churn")
        col2.plotly_chart(fig_monetary, use_container_width=True)

    elif page == "Review Integrity":
        st.title("Review Integrity (DistilBERT)")
        st.write("Detecting mismatches where the sentiment of the review text contradicts the star rating.")
        
        if not nlp_scores.empty:
            mismatches = nlp_scores[nlp_scores['integrity_mismatch'] == 1]
            st.metric("Total Mismatches Detected", len(mismatches))
            
            st.subheader("Flagged Review Examples")
            st.dataframe(mismatches[['star_rating', 'bert_sentiment', 'english_text', 'bert_confidence']].head(10))
        else:
            st.warning("NLP data not found.")

    elif page == "Customer Lookup":
        st.title("Customer Risk Lookup")
        customer_id = st.text_input("Enter customer_unique_id")
        
        if customer_id:
            customer_data = risk_scores[risk_scores['customer_unique_id'] == customer_id]
            if not customer_data.empty:
                st.subheader("Customer Risk Profile")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Risk Score", f"{customer_data['risk_score'].values[0]:.2f}")
                c2.metric("Risk Category", customer_data['risk_category'].values[0])
                c3.metric("Churn Probability", f"{customer_data['churn_probability'].values[0]:.2f}")
                
                st.write("Feature Details")
                st.json(customer_data.to_dict(orient='records')[0])
            else:
                st.error("Customer not found.")

    elif page == "Model Performance":
        st.title("Model Performance")
        st.write("Evaluate the XGBoost and DistilBERT model metrics here.")
        
        # Load pre-saved confusion matrix images if they exist
        if os.path.exists('../models/confusion_matrix.png'):
            st.image('../models/confusion_matrix.png', caption='XGBoost Confusion Matrix')
        else:
            st.info("Confusion matrix image not found. Run model training to generate it.")
            
        if os.path.exists('../models/feature_importance.png'):
            st.image('../models/feature_importance.png', caption='XGBoost Feature Importance')
else:
    st.warning("Please run the data pipeline to generate processed datasets.")
