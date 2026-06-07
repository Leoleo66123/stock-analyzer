"""News sentiment via yfinance + VADER"""
import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = None

def _get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer

def fetch_news_sentiment(symbol: str) -> dict:
    """Fetch news and compute sentiment"""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        if not news:
            return {"error": "未找到相关新闻", "avg_sentiment": 0, "mood": "中性",
                    "mood_emoji": "😐", "article_count": 0, "articles": []}

        analyzer = _get_analyzer()
        articles = []
        scores = []

        for item in news[:20]:
            title = item.get("content", {}).get("title", "") or item.get("title", "")
            summary = item.get("content", {}).get("summary", "")
            publisher = item.get("content", {}).get("provider", {}).get("displayName", "")
            link = item.get("content", {}).get("canonicalUrl", {}).get("url", "")

            text = f"{title} {summary}"
            sentiment = analyzer.polarity_scores(text)["compound"]

            articles.append({
                "title": title[:100],
                "sentiment": round(sentiment, 3),
                "publisher": publisher,
                "link": link or "#",
            })
            scores.append(sentiment)

        avg_score = sum(scores) / len(scores) if scores else 0
        avg_score = round(avg_score, 3)

        if avg_score > 0.2:
            mood, emoji = "积极", "😊"
        elif avg_score < -0.2:
            mood, emoji = "消极", "😟"
        else:
            mood, emoji = "中性", "😐"

        return {
            "avg_sentiment": avg_score,
            "mood": mood,
            "mood_emoji": emoji,
            "article_count": len(articles),
            "articles": articles,
        }
    except Exception as e:
        return {"error": str(e), "avg_sentiment": 0, "mood": "N/A",
                "mood_emoji": "❓", "article_count": 0, "articles": []}
