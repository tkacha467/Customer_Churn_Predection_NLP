import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Review Integrity NLP", layout="wide", page_icon="🤖")

st.sidebar.title("NLP Integrity Platform")
st.sidebar.markdown("Analyzing Flipkart reviews using a DistilBERT model trained on 3.6M Amazon reviews.")

page = st.sidebar.radio("Navigate", ["Dataset Overview", "Amazon Data Explorer", "Flipkart Integrity Analysis", "Model Architecture"])

@st.cache_data
def load_flipkart_results():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(project_root, 'data', 'processed', 'flipkart_integrity_results.csv')
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return None

@st.cache_data
def load_amazon_sample(sample_size=1000):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    train_path = os.path.join(project_root, 'data', 'train.csv')
    if os.path.exists(train_path):
        # Read a chunk instead of the whole 1.5GB file
        df = pd.read_csv(train_path, header=None, names=['Class_Index', 'Review_Title', 'Review_Text'], nrows=sample_size)
        df['Sentiment'] = df['Class_Index'].map({1: 'NEGATIVE', 2: 'POSITIVE'})
        return df
    return None

if page == "Dataset Overview":
    st.title("Dataset Overview")
    st.write("This project utilizes a pure NLP pipeline relying on two massive datasets.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Amazon Polarity Dataset")
        st.metric("Total Reviews (Train)", "3,600,000")
        st.metric("Total Reviews (Test)", "400,000")
        st.write("Used exclusively for training and validating the DistilBERT sequence classification model. Labels are purely binary (1=Negative, 2=Positive).")
        
    with col2:
        st.subheader("2. Flipkart Dataset")
        st.metric("Total Reviews", "363,261")
        st.write("Used exclusively for Inference. The trained Amazon DistilBERT model analyzes the sentiment of the textual review and compares it against the user's provided Star Rating to flag fake or sarcastic mismatches.")

elif page == "Amazon Data Explorer":
    st.title("Amazon Reviews Dataset (Training Data)")
    st.write("Because the Amazon training file is **1.5 GB** (3.6 Million rows), we are loading a random sample of 1,000 reviews here for exploration and visualization.")
    
    amazon_df = load_amazon_sample(1000)
    
    if amazon_df is not None:
        col1, col2 = st.columns(2)
        col1.metric("Sample Size Loaded", len(amazon_df))
        col2.metric("Total Size on Disk", "3.6 Million")
        
        st.subheader("Raw Data Sample")
        st.dataframe(amazon_df[['Sentiment', 'Review_Title', 'Review_Text']], use_container_width=True)
        
        st.subheader("Sentiment Distribution (Training Set)")
        # In the full dataset it's perfectly balanced (1.8M pos / 1.8M neg).
        fig = px.pie(amazon_df, names='Sentiment', title='Balance of Positive vs Negative Reviews', color='Sentiment', color_discrete_map={'POSITIVE':'green', 'NEGATIVE':'red'})
        st.plotly_chart(fig)
    else:
        st.error("Amazon train.csv not found in data/ folder!")

elif page == "Flipkart Integrity Analysis":
    st.title("Flipkart Review Integrity Analysis")
    st.write("Detecting mismatches where the sentiment of the review text contradicts the star rating.")
    
    df = load_flipkart_results()
    
    if df is not None:
        mismatches = df[df['Mismatch_Flag'] == 1]
        
        col1, col2 = st.columns(2)
        col1.metric("Total Reviews Analyzed (Sample)", len(df))
        col2.metric("Total Mismatches Detected", len(mismatches))
        
        st.subheader("Flagged Review Examples")
        if len(mismatches) > 0:
            st.dataframe(mismatches[['Product_name', 'Rate', 'Sentiment', 'Review_Text', 'Confidence']], use_container_width=True)
        else:
            st.success("No mismatches found in this sample!")
            
        st.subheader("Sentiment Distribution")
        fig = px.pie(df, names='Sentiment', title='Predicted Sentiment Breakdown')
        st.plotly_chart(fig)
        
    else:
        st.warning("No analysis results found. Please run `python src/flipkart_integrity.py` first.")

elif page == "Model Architecture":
    st.title("Model Architecture: DistilBERT")
    
    st.markdown("""
    ### Why DistilBERT?
    DistilBERT is a smaller, faster, cheaper, and lighter version of BERT. It retains 97% of BERT's language understanding capabilities while being 60% faster.
    
    ### Training Pipeline
    1. **Data**: 3.6 Million Amazon Reviews
    2. **Preprocessing**: Tokenized with `AutoTokenizer`, truncated to 512 tokens.
    3. **Mapping**: 
       - Class 1 → 0 (Negative)
       - Class 2 → 1 (Positive)
    4. **Fine-tuning**: `AutoModelForSequenceClassification` with 2 output labels.
    
    ### Integrity Logic
    The model runs on Flipkart reviews and compares its prediction against the Star Rating (`Rate`):
    - **Fake Negative**: User gave 4 or 5 stars, but text is predicted NEGATIVE.
    - **Fake Positive**: User gave 1 or 2 stars, but text is predicted POSITIVE.
    """)
