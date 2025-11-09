# app/sentiment.py
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_an = SentimentIntensityAnalyzer()

def sentiment_score(text: str) -> float:
    """
    Devuelve un score [-1..1]; >0 positivo, <0 negativo.
    """
    if not text:
        return 0.0
    s = _an.polarity_scores(text)
    return float(s.get("compound", 0.0))
