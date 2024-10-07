# sentiment_analyzer.py

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, DistilBertTokenizer, DistilBertForSequenceClassification
from flair.models import TextClassifier
from flair.data import Sentence

class SentimentAnalyzer:
    def __init__(self):
        self.load_models()

    def load_models(self):
        # Load FinBERT
        print("Loading FinBERT model...")
        self.finbert_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.finbert_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")

        # Load DistilBERT trained on Financial PhraseBank
        print("Loading DistilBERT Financial PhraseBank model...")
        self.distilbert_financial_tokenizer = DistilBertTokenizer.from_pretrained("./distilbert-financial-sentiment")
        self.distilbert_financial_model = DistilBertForSequenceClassification.from_pretrained("./distilbert-financial-sentiment")

        # Load FinBERT-Tone
        print("Loading FinBERT-Tone model...")
        self.finbert_tone_tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
        self.finbert_tone_model = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")

        # Load Flair Sentiment Model
        print("Loading Flair Sentiment model...")
        self.flair_sentiment_model = TextClassifier.load('en-sentiment')

    def analyze_sentiment_finbert(self, text):
        inputs = self.finbert_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.finbert_model(**inputs)
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=1)
            sentiment_scores = probabilities[0].tolist()
        labels = ['Negative', 'Neutral', 'Positive']
        return {label: round(score, 4) for label, score in zip(labels, sentiment_scores)}

    def analyze_sentiment_distilbert_financial(self, text):
        inputs = self.distilbert_financial_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.distilbert_financial_model(**inputs)
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
    
    def analyze_sentiments(self, text):
        sentiments = {}
        sentiments['FinBERT'] = self.analyze_sentiment_finbert(text)
        sentiments['DistilBERT-Financial'] = self.analyze_sentiment_distilbert_financial(text)
        sentiments['FinBERT-Tone'] = self.analyze_sentiment_finbert_tone(text)
        sentiments['Flair'] = self.analyze_sentiment_flair(text)
        
        average_sentiments = self.calculate_average_sentiments(sentiments)
        return {
            'average_sentiments': average_sentiments,
            'detailed_sentiments': sentiments
        }
    
    def calculate_average_sentiments(self, sentiments):
        total_neg = 0
        total_neu = 0
        total_pos = 0
        count = 0

        for model, scores in sentiments.items():
            if model in ['FinBERT', 'FinBERT-Tone', 'DistilBERT-Financial']:
                total_neg += scores.get('Negative', 0)
                total_neu += scores.get('Neutral', 0)
                total_pos += scores.get('Positive', 0)
                count += 1

        if count == 0:
            return {'Negative': 0, 'Neutral': 0, 'Positive': 0}

        average_neg = total_neg / count
        average_neu = total_neu / count
        average_pos = total_pos / count

        overall_score = average_pos - average_neg

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