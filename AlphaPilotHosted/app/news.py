# app/news.py
import os, time, feedparser
from datetime import datetime, timezone
from typing import List, Dict

DEFAULT_FEEDS = [
    # Fuentes rápidas y estables (añade o quita a tu gusto)
    "https://feeds.reuters.com/reuters/businessNews",
    "https://feeds.reuters.com/reuters/worldNews",
    "https://www.bloomberg.com/feeds/podcasts/report.xml",  # ejemplo
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
]
INFLUENCERS = [s.strip().lower() for s in os.getenv("INFLUENCERS", "trump, powell, elon musk").split(",") if s.strip()]

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def load_feeds() -> List[str]:
    urls = os.getenv("NEWS_RSS_URLS", "")
    feeds = [u.strip() for u in urls.split(",") if u.strip()] or DEFAULT_FEEDS
    return feeds

def fetch_latest(max_items=50) -> List[Dict]:
    """Lee últimos items de todos los feeds y devuelve lista normalizada."""
    items: List[Dict] = []
    for url in load_feeds():
        try:
            d = feedparser.parse(url)
            for e in d.entries[:max_items]:
                title = (e.get("title") or "").strip()
                summary = (e.get("summary") or "").strip()
                link = e.get("link") or ""
                # published_parsed puede faltar; toleramos
                ts = None
                if getattr(e, "published_parsed", None):
                    ts = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
                items.append({
                    "source": url,
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "ts": ts or _now_utc()
                })
        except Exception:
            continue
    return items

def contains_influencer(text: str) -> List[str]:
    t = (text or "").lower()
    hits = [inf for inf in INFLUENCERS if inf in t]
    return hits
