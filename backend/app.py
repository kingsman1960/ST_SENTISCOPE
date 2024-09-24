# backend/app.py

from flask import Flask, render_template, request, jsonify
from news_fetcher import NewsFetcher
from entity_extractor import EntityExtractor
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from flair.models import TextClassifier
from flair.data import Sentence

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../frontend/templates'),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../frontend/static')
)

class SentimentAnalyzer:
    def __init__(self):
        self.load_models()

    def load_models(self):
        # Load FinBERT
        print("Loading FinBERT model...")
        self.finbert_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.finbert_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")

        # Load ESG-BERT
        print("Loading ESG-BERT model...")
        self.esgbert_tokenizer = AutoTokenizer.from_pretrained("nbroad/ESG-BERT")
        self.esgbert_model = AutoModelForSequenceClassification.from_pretrained("nbroad/ESG-BERT")

        # Load FinBERT-Tone
        print("Loading FinBERT-Tone model...")
        self.finbert_tone_tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
        self.finbert_tone_model = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")

        # Load Flair Sentiment Model
        print("Loading Flair Sentiment model...")
        self.flair_sentiment_model = TextClassifier.load('en-sentiment')

    def analyze_sentiments(self, text):
        """
        Performs multiple sentiment analyses on the given text and returns a dictionary with individual and average sentiment scores.
        """
        sentiments = {}

        # FinBERT Sentiment
        sentiments['FinBERT'] = self.analyze_sentiment_finbert(text)

        # ESG-BERT Sentiment
        sentiments['ESG-BERT'] = self.analyze_sentiment_esgbert(text)

        # FinBERT-Tone Sentiment
        sentiments['FinBERT-Tone'] = self.analyze_sentiment_finbert_tone(text)

        # Flair Sentiment
        sentiments['Flair'] = self.analyze_sentiment_flair(text)

        # Calculate average sentiments
        average_sentiments = self.calculate_average_sentiments(sentiments)

        return {
            'average_sentiments': average_sentiments,
            'detailed_sentiments': sentiments
        }

    def calculate_average_sentiments(self, sentiments):
        """
        Calculate the average of 'Negative', 'Neutral', 'Positive' sentiments from multiple models.
        """
        total_neg = 0
        total_neu = 0
        total_pos = 0
        count = 0

        for model, scores in sentiments.items():
            if model in ['FinBERT', 'ESG-BERT', 'FinBERT-Tone']:
                total_neg += scores.get('Negative', 0)
                total_neu += scores.get('Neutral', 0)
                total_pos += scores.get('Positive', 0)
                count += 1

        if count == 0:
            return {'Negative': 0, 'Neutral': 0, 'Positive': 0}

        average_neg = total_neg / count
        average_neu = total_neu / count
        average_pos = total_pos / count

        # The overall sentiment score is determined based on average_pos and average_neg
        overall_score = average_pos - average_neg  # Simple sentiment score

        if overall_score >= 0.6:
            overall_sentiment = "Very Positive"
        elif 0.2 <= overall_score < 0.6:
            overall_sentiment = "Slightly Positive"
        elif -0.2 < overall_score < 0.2:
            overall_sentiment = "Neutral"
        elif -0.6 < overall_score <= -0.2:
            overall_sentiment = "Slightly Negative"
        else:
            overall_sentiment = "Very Negative"

        return {
            'Negative': round(average_neg, 4),
            'Neutral': round(average_neu, 4),
            'Positive': round(average_pos, 4),
            'Overall_Sentiment': overall_sentiment
        }

    def analyze_sentiment_finbert(self, text):
        inputs = self.finbert_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.finbert_model(**inputs)
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=1)
            sentiment_scores = probabilities[0].tolist()
        labels = ['Negative', 'Neutral', 'Positive']
        return {label: round(score, 4) for label, score in zip(labels, sentiment_scores)}

    def analyze_sentiment_esgbert(self, text):
        inputs = self.esgbert_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.esgbert_model(**inputs)
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=1)
            sentiment_scores = probabilities[0].tolist()
        labels = ['Negative', 'Neutral', 'Positive']
        return {label: round(score, 4) for label, score in zip(labels, sentiment_scores)}

    def analyze_sentiment_finbert_tone(self, text):
        inputs = self.finbert_tone_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.finbert_tone_model(**inputs)
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=1)
            sentiment_scores = probabilities[0].tolist()
        labels = ['Negative', 'Neutral', 'Positive']
        return {label: round(score, 4) for label, score in zip(labels, sentiment_scores)}

    def analyze_sentiment_flair(self, text):
        sentence = Sentence(text)
        self.flair_sentiment_model.predict(sentence)
        sentiment = sentence.labels[0].value
        score = round(sentence.labels[0].score, 4)
        return {'sentiment': sentiment, 'score': score}

# Initialize backend modules
news_fetcher = NewsFetcher()
sentiment_analyzer = SentimentAnalyzer()
entity_extractor = EntityExtractor(sentiment_analyzer.flair_sentiment_model)

# sector tickers
SECTOR_TICKERS = {
    'Banking': ['JPM', 'BAC', 'WFC', 'C', 'GS'],
    'Technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'], 
    'Healthcare': ['JNJ', 'PFE', 'MRK', 'ABT', 'TMO'],
    'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'TOT'],
    'Retail': ['WMT', 'TGT', 'AMZN', 'COST', 'LOW']
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_sectors', methods=['GET'])
def get_sectors():
    # List of sectors 
    sectors = list(SECTOR_TICKERS.keys())
    return jsonify(sectors)

@app.route('/analyze_sector', methods=['POST'])
def analyze_sector():
    sector = request.form.get('sector')
    if not sector:
        return jsonify({"error": "No sector provided."}), 400

    if sector == 'Manually Paste Article':
        return jsonify({"error": "Please select a valid sector."}), 400

    # Getting the tickers for the selected sector
    tickers = SECTOR_TICKERS.get(sector, [])
    if not tickers:
        return jsonify({"error": "No tickers found for the selected sector."}), 404

    # Fetching news articles for each ticker
    all_articles = []
    for ticker in tickers:
        articles = news_fetcher.fetch_news_by_ticker(ticker)
        all_articles.extend(articles)

    if not all_articles:
        return jsonify({"error": "No articles found for the selected sector's tickers."}), 404

    # 5 most relevant articles per sector
    analyzed_articles = []
    for article in all_articles[:5]:
        description = article.get('description', '')
        if not description:
            description = article.get('content', '')  

        # Performing sentiment analysis
        sentiments = sentiment_analyzer.analyze_sentiments(description)

        # Extracting named entities
        entities = entity_extractor.extract_entities(description)

        analyzed_article = {
            'title': article.get('title', 'No Title'),
            'source': article.get('source', 'Unknown'),
            'description': description,
            'urlToImage': article.get('urlToImage', ''),
            'link': article.get('link', ''),
            'average_sentiments': sentiments['average_sentiments'],
            'detailed_sentiments': sentiments['detailed_sentiments'],
            'entities': entities
        }
        analyzed_articles.append(analyzed_article)

    # Calculate overall sentiment based on all articles
    overall_sentiment = calculate_overall_sentiment(analyzed_articles)

    return jsonify({
        'overall_sentiment': overall_sentiment,
        'articles': analyzed_articles
    })

@app.route('/analyze_article', methods=['POST'])
def analyze_article():
    article_text = request.form.get('article')
    if not article_text:
        return jsonify({"error": "No article text provided."}), 400

    # Perform sentiment analysis
    sentiments = sentiment_analyzer.analyze_sentiments(article_text)

    # Extract named entities
    entities = entity_extractor.extract_entities(article_text)

    analysis = {
        'average_sentiments': sentiments['average_sentiments'],
        'detailed_sentiments': sentiments['detailed_sentiments'],
        'entities': entities
    }

    # Determine overall sentiment for the single article
    overall_sentiment = sentiments['average_sentiments']['Overall_Sentiment']

    return jsonify({
        'overall_sentiment': overall_sentiment,
        'analysis': analysis
    })

def calculate_overall_sentiment(articles):
    """
    Calculate the overall sentiment across all analyzed articles.
    """
    total_neg = 0
    total_neu = 0
    total_pos = 0
    count = 0

    for article in articles:
        avg_sent = article['average_sentiments']
        total_neg += avg_sent.get('Negative', 0)
        total_neu += avg_sent.get('Neutral', 0)
        total_pos += avg_sent.get('Positive', 0)
        count += 1

    if count == 0:
        return "Neutral"

    average_neg = total_neg / count
    average_neu = total_neu / count
    average_pos = total_pos / count

    # Determine overall sentiment based on average_pos and average_neg
    overall_score = average_pos - average_neg  # Simple sentiment score

    if overall_score >= 0.6:
        overall_sentiment = "Very Positive"
    elif 0.2 <= overall_score < 0.6:
        overall_sentiment = "Slightly Positive"
    elif -0.2 < overall_score < 0.2:
        overall_sentiment = "Neutral"
    elif -0.6 < overall_score <= -0.2:
        overall_sentiment = "Slightly Negative"
    else:
        overall_sentiment = "Very Negative"

    return overall_sentiment

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True)
