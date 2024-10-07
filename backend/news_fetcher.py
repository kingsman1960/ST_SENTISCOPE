# backend/news_fetcher.py

import requests
from datetime import datetime, timedelta
import time

class News_Fetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://newsapi.org/v2/everything'
        self.trusted_sources = [
            'reuters.com', 'bloomberg.com', 'cnbc.com', 'wsj.com', 'ft.com',
            'marketwatch.com', 'seekingalpha.com',
            'apnews.com', 'bbc.com', 'npr.org', 'nytimes.com', 'washingtonpost.com',
            'economist.com', 'forbes.com', 'barrons.com',
            'morningstar.com', 'businessinsider.com', 'thestreet.com', 'zacks.com',  'nasdaq.com', 'foxbusiness.com', 'money.cnn.com',
            'financial-times.com', 'theguardian.com'
        ]
        self.last_request_time = 0
        self.request_interval = 1  # Minimum time between requests in seconds

    def fetch_news_by_ticker(self, ticker):
        """
        Fetch news articles for a given ticker using NewsAPI.
        Returns a list of articles with relevant information.
        """
        financial_keywords = (
            "finance OR market OR stock OR economy OR investment OR "
            "financials OR earnings OR revenue OR profit OR loss OR "
            "dividends OR trading OR portfolio OR hedge OR risk OR "
            "inflation OR interest rates OR monetary policy OR fiscal policy OR "
            "economic growth OR GDP OR recession OR bull market OR bear market"
        )
        query = f"{ticker} AND ({financial_keywords})"
        domains = ','.join(self.trusted_sources)
        
        params = {
            'q': query,
            'domains': domains,
            'apiKey': self.api_key,
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': 14,
            'from': (datetime.now() - timedelta(days=30)).isoformat()  # Last 30 days
        }
        
        max_retries = 3
        retry_delay = 5  # seconds

        for attempt in range(max_retries):
            try:
                self._wait_for_rate_limit()
                response = requests.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                articles = []
                for article in data.get('articles', []):
                    articles.append({
                        'title': article.get('title'),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'description': article.get('description'),
                        'urlToImage': article.get('urlToImage'),
                        'link': article.get('url'),
                        'publishedAt': article.get('publishedAt')
                    })
                return articles
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    if attempt < max_retries - 1:
                        print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        print("Max retries reached. Unable to fetch news.")
                        return []
                else:
                    print(f"HTTP error occurred: {e}")
                    return []
            except requests.RequestException as e:
                print(f"Error fetching news for ticker '{ticker}': {e}")
                return []

    def _wait_for_rate_limit(self):
        """Ensure that requests are not sent too frequently"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.request_interval:
            time.sleep(self.request_interval - time_since_last_request)
        self.last_request_time = time.time()

# Usage example:
# news_fetcher = News_Fetcher('your_newsapi_key_here')
# news = news_fetcher.fetch_news_by_ticker('AAPL')