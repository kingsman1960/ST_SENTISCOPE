# backend/news_fetcher.py

import requests
import feedparser

class NewsFetcher:
    def __init__(self):
        # Define base Google News RSS feed URL
        self.base_rss_url = 'https://news.google.com/rss/search?q={}'
    
    def fetch_news_by_ticker(self, ticker):
        """
        Fetch news articles for a given ticker using Google News RSS feeds.
        Returns a list of articles with relevant information.
        """
        rss_url = self.base_rss_url.format(ticker)
        try:
            response = requests.get(rss_url)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            articles = []
            for entry in feed.entries[:5]:  # Fetch latest 5 articles per ticker
                article = {
                    'title': entry.title,
                    'source': entry.source.title if 'source' in entry else 'Google News',
                    'description': entry.summary,
                    'urlToImage': self.extract_image_url(entry),
                    'link': entry.link
                }
                articles.append(article)
            return articles
        except requests.RequestException as e:
            print(f"Error fetching news for ticker '{ticker}': {e}")
            return []
    
    def extract_image_url(self, entry):
        """
        Extract image URL from the RSS entry if available.
        Google News RSS may not always provide images; this is a placeholder.
        """
        # Google News RSS feeds typically do not include images.
        # You might need to scrape the article page or use another source to get images.
        return ''
