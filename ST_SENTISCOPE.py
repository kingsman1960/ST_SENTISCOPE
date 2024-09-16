import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import requests
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
from flair.models import TextClassifier
from flair.data import Sentence


# Download required NLTK data
nltk.download('vader_lexicon')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')

# Set page configuration
st.set_page_config(
    page_title="Financial Sector News Sentiment Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load models
# Load models
def load_models():
    finbert_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
    finbert_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
    esgbert_tokenizer = AutoTokenizer.from_pretrained("nbroad/ESG-BERT")
    esgbert_model = AutoModelForSequenceClassification.from_pretrained("nbroad/ESG-BERT")
    finbert_tone_tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
    finbert_tone_model = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")
    flair_sentiment_model = TextClassifier.load('en-sentiment')
    flair_ner_model = TextClassifier.load('ner')
    return finbert_tokenizer, finbert_model, esgbert_tokenizer, esgbert_model, finbert_tone_tokenizer, finbert_tone_model, flair_sentiment_model, flair_ner_model

finbert_tokenizer, finbert_model, esgbert_tokenizer, esgbert_model, finbert_tone_tokenizer, finbert_tone_model, flair_sentiment_model, flair_ner_model = load_models()

# List of trusted sources
trusted_sources = [
    'reuters.com', 'apnews.com', 'bbc.com', 'npr.org', 'wsj.com',
    'nytimes.com', 'washingtonpost.com', 'economist.com', 'ft.com',
    'bloomberg.com', 'cnbc.com', 'forbes.com', 'finance.yahoo.com'
]

# Function to fetch financial news from NewsAPI for a specific sector
def fetch_financial_news(api_key, sector):
    financial_keywords = "finance OR market OR stock OR economy OR investment"
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

# Add Flair sentiment analysis function
def analyze_sentiment_flair(text):
    sentence = Sentence(text)
    flair_sentiment_model.predict(sentence)
    return {'sentiment': sentence.labels[0].value, 'score': sentence.labels[0].score}

# Add Flair named entity recognition function
def extract_entities_flair(text):
    sentence = Sentence(text)
    flair_ner_model.predict(sentence)
    return [(entity.text, entity.tag) for entity in sentence.get_spans('ner')]

def extract_entities_nltk(text):
    tokens = nltk.word_tokenize(text)
    pos_tags = nltk.pos_tag(tokens)
    tree = nltk.ne_chunk(pos_tags)
    entities = []
    for subtree in tree:
        if isinstance(subtree, nltk.Tree):
            entity_text = ' '.join([word for word, tag in subtree.leaves()])
            entity_label = subtree.label()
            entities.append((entity_text, entity_label))
    return entities

# Streamlit app
st.title("Financial Sector News Sentiment Analysis")

# Get API key from Streamlit secrets
api_key = st.secrets["newsapi"]["api_key"]

# Define sectors
sectors = ['Banking', 'Technology', 'Healthcare', 'Energy', 'Retail', 'Manually Paste Article']

# Sector selection
selected_sector = st.selectbox("Select a business sector to analyze or choose to paste an article manually:", sectors)

if selected_sector == 'Manually Paste Article':
    # Text area for manual article input
    article_text = st.text_area("Paste your article here:", height=300)
    if st.button("Analyze Pasted Article"):
        if article_text:
            st.subheader("Analysis of Manually Pasted Article")
            
            # Perform sentiment analysis on the pasted article
            finbert_sentiment = analyze_sentiment_finbert(article_text)
            vader_sentiment = analyze_sentiment_vader(article_text)
            esgbert_sentiment = analyze_sentiment_esgbert(article_text)
            finbert_tone_sentiment = analyze_sentiment_finbert_tone(article_text)

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

            # Add entity visualization for pasted article
            st.subheader("Named Entities in Pasted Article")
            entities = extract_entities_nltk(article_text)
            if entities:
                entity_df = pd.DataFrame(entities, columns=['Entity', 'Label'])
                st.dataframe(entity_df)
            else:
                st.write("No named entities found in this article.")
        else:
            st.error("Please paste an article before analyzing.")

else:
    if st.button("Analyze"):
        # Fetch financial news for the selected sector
        news_data = fetch_financial_news(api_key, selected_sector)

        if news_data:
            # Display results
            st.subheader(f"Financial News and Sentiment Analysis for {selected_sector} Sector")

            for i, article in enumerate(news_data, 1):
                st.write(f"**{i}. {article['title']}**")
                st.write(f"Source: {article['source']['name']}")

                if article['urlToImage']:
                    st.image(article['urlToImage'], caption=article['title'], use_column_width=True)

                st.write(article['description'])

                # Perform sentiment analysis on the description
                finbert_sentiment = analyze_sentiment_finbert(article['description'])
                vader_sentiment = analyze_sentiment_vader(article['description'])
                esgbert_sentiment = analyze_sentiment_esgbert(article['description'])
                finbert_tone_sentiment = analyze_sentiment_finbert_tone(article['description'])

               # Add Flair sentiment analysis
                flair_sentiment = analyze_sentiment_flair(article['description'])
    
                col1, col2, col3 = st.columns(3)
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
                with col3:
                    st.write("Flair Sentiment:")
                    st.write(flair_sentiment)

                # Add entity visualization for each article
                st.subheader("Named Entities")
                entities_nltk = extract_entities_nltk(article['description'])
                entities_flair = extract_entities_flair(article['description'])
    
                if entities_nltk or entities_flair:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("NLTK Named Entities:")
                if entities_nltk:
                    entity_df_nltk = pd.DataFrame(entities_nltk, columns=['Entity', 'Label'])
                    st.dataframe(entity_df_nltk)
                else:
                    st.write("No named entities found by NLTK.")
                with col2:
                    st.write("Flair Named Entities:")
                if entities_flair:
                    entity_df_flair = pd.DataFrame(entities_flair, columns=['Entity', 'Label'])
                    st.dataframe(entity_df_flair)
                else:
                    st.write("No named entities found by Flair.")
            else:
                st.write("No named entities found in this article.")

            # Update the "Top Named Entities Across All Articles" section to include Flair entities
            st.subheader("Top Named Entities Across All Articles")
            all_text = " ".join([article['description'] for article in news_data])
            all_entities_nltk = extract_entities_nltk(all_text)
            all_entities_flair = extract_entities_flair(all_text)

            if all_entities_nltk or all_entities_flair:
                col1, col2 = st.columns(2)
            with col1:
                st.write("NLTK Named Entities:")
            if all_entities_nltk:
                entity_counts_nltk = pd.DataFrame(all_entities_nltk, columns=['Entity', 'Label']).groupby(['Entity', 'Label']).size().reset_index(name='Count')
                entity_counts_nltk = entity_counts_nltk.sort_values('Count', ascending=False).head(10)
                st.dataframe(entity_counts_nltk)
            
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.barplot(x='Count', y='Entity', hue='Label', data=entity_counts_nltk, ax=ax)
                ax.set_title("Top 10 NLTK Named Entities Across All Articles")
                st.pyplot(fig)
            else:
                st.write("No named entities found by NLTK across all articles.")
    
            with col2:
                st.write("Flair Named Entities:")
                if all_entities_flair:
                    entity_counts_flair = pd.DataFrame(all_entities_flair, columns=['Entity', 'Label']).groupby(['Entity', 'Label']).size().reset_index(name='Count')
                    entity_counts_flair = entity_counts_flair.sort_values('Count', ascending=False).head(10)
                    st.dataframe(entity_counts_flair)
            
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.barplot(x='Count', y='Entity', hue='Label', data=entity_counts_flair, ax=ax)
                    ax.set_title("Top 10 Flair Named Entities Across All Articles")
                    st.pyplot(fig)
                else:
                    st.write("No named entities found by Flair across all articles.")
            else:
            st.write("No named entities found across all articles.")

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