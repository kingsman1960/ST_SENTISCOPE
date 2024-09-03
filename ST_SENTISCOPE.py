import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import requests
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

# Set page configuration
st.set_page_config(
    page_title="Financial Sector News Sentiment Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Download NLTK data
nltk.download('vader_lexicon', quiet=True)

# Load models
def load_models():
    finbert_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
    finbert_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
    
    esgbert_tokenizer = AutoTokenizer.from_pretrained("nbroad/ESG-BERT")
    esgbert_model = AutoModelForSequenceClassification.from_pretrained("nbroad/ESG-BERT")
    
    finbert_tone_tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
    finbert_tone_model = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")
    
    return finbert_tokenizer, finbert_model, esgbert_tokenizer, esgbert_model, finbert_tone_tokenizer, finbert_tone_model

finbert_tokenizer, finbert_model, esgbert_tokenizer, esgbert_model, finbert_tone_tokenizer, finbert_tone_model = load_models()

# List of trusted sources
trusted_sources = [
    'reuters.com', 'apnews.com', 'bbc.com', 'npr.org', 'wsj.com', 
    'nytimes.com', 'washingtonpost.com', 'economist.com', 'ft.com',
    'bloomberg.com', 'cnbc.com', 'forbes.com',
    'finance.yahoo.com'
]

# Function to fetch financial news from NewsAPI for a specific sector
def fetch_financial_news(api_key, sector):
    # Add financial keywords to make the search more specific
    financial_keywords = "finance OR market OR stock OR economy OR investment"
    
    # Construct the query with sector, financial keywords, and trusted sources
    query = f"{sector} AND ({financial_keywords})"
    domains = ','.join(trusted_sources)
    
    url = f"https://newsapi.org/v2/everything?q={query}&domains={domains}&apiKey={api_key}&language=en&sortBy=relevancy&pageSize=10"
    response = requests.get(url)
    data = response.json()
    articles = data.get('articles', [])
    return articles

# Sentiment analysis functions
def analyze_sentiment_finbert(text):
    inputs = finbert_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = finbert_model(**inputs)
    probabilities = torch.nn.functional.softmax(outputs.logits, dim=1)
    sentiment_scores = probabilities[0].tolist()
    labels = ['Negative', 'Neutral', 'Positive']
    return {label: score for label, score in zip(labels, sentiment_scores)}

def analyze_sentiment_vader(text):
    sia = SentimentIntensityAnalyzer()
    return sia.polarity_scores(text)

def analyze_sentiment_esgbert(text):
    inputs = esgbert_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = esgbert_model(**inputs)
    probabilities = torch.nn.functional.softmax(outputs.logits, dim=1)
    sentiment_scores = probabilities[0].tolist()
    labels = ['Negative', 'Neutral', 'Positive']
    return {label: score for label, score in zip(labels, sentiment_scores)}

def analyze_sentiment_finbert_tone(text):
    inputs = finbert_tone_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = finbert_tone_model(**inputs)
    probabilities = torch.nn.functional.softmax(outputs.logits, dim=1)
    sentiment_scores = probabilities[0].tolist()
    labels = ['Negative', 'Neutral', 'Positive']
    return {label: score for label, score in zip(labels, sentiment_scores)}

# Streamlit app
st.title("Financial Sector News Sentiment Analysis")

# Get API key from Streamlit secrets
api_key = st.secrets["newsapi"]["api_key"]

# Define sectors
sectors = ['Banking', 'Technology', 'Healthcare', 'Energy', 'Retail']

# Sector selection
selected_sector = st.selectbox("Select a business sector to analyze:", sectors)

if st.button("Analyze"):
    # Fetch financial news for the selected sector
    news_data = fetch_financial_news(api_key, selected_sector)

    if news_data:
        # Display results
        st.subheader(f"Financial News and Sentiment Analysis for {selected_sector} Sector")
        for i, article in enumerate(news_data, 1):
            st.write(f"**{i}. {article['title']}**")
            st.write(f"Source: {article['source']['name']}")
            
            # Display image if available
            if article['urlToImage']:
                st.image(article['urlToImage'], caption=article['title'], use_column_width=True)
            
            st.write(article['description'])
            
            # Perform sentiment analysis on the description
            finbert_sentiment = analyze_sentiment_finbert(article['description'])
            vader_sentiment = analyze_sentiment_vader(article['description'])
            esgbert_sentiment = analyze_sentiment_esgbert(article['description'])
            finbert_tone_sentiment = analyze_sentiment_finbert_tone(article['description'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("FinBERT Sentiment:")
                st.write(finbert_sentiment)
                st.write("ESG-BERT Sentiment:")
                st.write(esgbert_sentiment)
            with col2:
                st.write("VADER Sentiment:")
                st.write(vader_sentiment)
                st.write("FinBERT-Tone Sentiment:")
                st.write(finbert_tone_sentiment)
            
            st.markdown("---")

        # Visualize sentiment distribution for the selected sector
        st.subheader(f"Sentiment Distribution for {selected_sector} Sector")

        finbert_sentiments = [analyze_sentiment_finbert(article['description']) for article in news_data]
        vader_sentiments = [analyze_sentiment_vader(article['description'])['compound'] for article in news_data]
        esgbert_sentiments = [analyze_sentiment_esgbert(article['description']) for article in news_data]
        finbert_tone_sentiments = [analyze_sentiment_finbert_tone(article['description']) for article in news_data]

        col1, col2 = st.columns(2)
        
        with col1:
            fig, ax = plt.subplots()
            df = pd.DataFrame(finbert_sentiments)
            df_melted = df.melt(var_name='Sentiment', value_name='Score')
            sns.boxplot(x='Sentiment', y='Score', data=df_melted, ax=ax)
            ax.set_title("FinBERT Sentiment Distribution")
            st.pyplot(fig)

            fig, ax = plt.subplots()
            df = pd.DataFrame(esgbert_sentiments)
            df_melted = df.melt(var_name='Sentiment', value_name='Score')
            sns.boxplot(x='Sentiment', y='Score', data=df_melted, ax=ax)
            ax.set_title("ESG-BERT Sentiment Distribution")
            st.pyplot(fig)

        with col2:
            fig, ax = plt.subplots()
            sns.histplot(vader_sentiments, kde=True, ax=ax)
            ax.set_title("VADER Sentiment Distribution")
            ax.set_xlabel("Compound Score")
            st.pyplot(fig)

            fig, ax = plt.subplots()
            df = pd.DataFrame(finbert_tone_sentiments)
            df_melted = df.melt(var_name='Sentiment', value_name='Score')
            sns.boxplot(x='Sentiment', y='Score', data=df_melted, ax=ax)
            ax.set_title("FinBERT-Tone Sentiment Distribution")
            st.pyplot(fig)

        st.markdown("---")
        st.write("Note: This analysis is based on a sample of recent financial news articles from trusted sources for the selected sector. "
                 "The sentiment may not reflect the overall market sentiment.")
    else:
        st.error("Unable to fetch news data. Please check your API key and try again.")