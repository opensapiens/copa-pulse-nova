import asyncio
import feedparser
import os
import hashlib
import ssl
import random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# General News Feeds for Host Country Vibes
RSS_FEEDS = [
    # US General News
    "http://rss.cnn.com/rss/cnn_us.rss",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    # Canada General News
    "https://rss.cbc.ca/lineup/canada.xml",
    # Mexico Local News (via Google News RSS for stability)
    "https://news.google.com/rss/search?q=Ciudad+de+Mexico+Noticias&hl=es-419&gl=MX&ceid=MX:es-419",
    "https://news.google.com/rss/search?q=Monterrey+Noticias&hl=es-419&gl=MX&ceid=MX:es-419",
    "https://news.google.com/rss/search?q=Guadalajara+Noticias&hl=es-419&gl=MX&ceid=MX:es-419",
    # Global coverage fallback
    "http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml"
]

def generate_id(source, item_id):
    """Generates a unique hash for a feed item to prevent duplicates."""
    return hashlib.md5(f"{source}_{item_id}".encode()).hexdigest()

def generate_mock_world_cup_data():
    """Generates mock data for 2026 host cities to supplement real news if feeds are slow."""
    cities = [
        ("Atlanta", "Piedmont Park"), 
        ("Boston", "Boston Common"), 
        ("Dallas", "Downtown"), 
        ("Houston", "Discovery Green"), 
        ("Kansas City", "Power & Light District"), 
        ("Los Angeles", "Santa Monica Pier"), 
        ("Miami", "South Beach"), 
        ("New York", "Times Square"), 
        ("Philadelphia", "Center City"), 
        ("San Francisco", "Fisherman's Wharf"), 
        ("Seattle", "Pike Place Market"),
        ("Guadalajara", "Centro Histórico"), 
        ("Mexico City", "Zócalo"), 
        ("Monterrey", "Macroplaza"),
        ("Toronto", "CN Tower"), 
        ("Vancouver", "Stanley Park")
    ]
    
    mocks = []
    for _ in range(10): # Add 10 dynamic hits
        city, landmark = random.choice(cities)
        sentiment = random.choice(["positive", "neutral"])
        events = ["Local festival", "Cultural exhibit", "Massive street fair", "Public concert", "Transit update"]
        mocks.append({
            "id": generate_id("mock_api", f"mock_{random.randint(1000,99999)}"),
            "source": f"Mock: City Vibes {city}",
            "title": f"{random.choice(events)} happening near {landmark}!",
            "body": f"The area around {landmark} in {city} is bustling with activity today. The mood amongst locals and tourists is generally {sentiment}.",
            "author_location": city,
            "url": "https://news.google.com",
            "timestamp": datetime.now().isoformat()
        })
    return mocks

async def fetch_rss_feed(url):
    """Fetches and parses a single RSS feed async using a thread pool since feedparser is sync."""
    loop = asyncio.get_event_loop()
    
    # Disable SSL verification which frequently blocks Python requests on macOS
    if hasattr(ssl, '_create_unverified_context'):
        ssl_context = ssl._create_unverified_context()
    else:
        ssl_context = None

    def _parse_with_ssl_bypass():
        import urllib.request
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, context=ssl_context) as response:
                return feedparser.parse(response.read())
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return feedparser.FeedParserDict(entries=[])
            
    feed = await loop.run_in_executor(None, _parse_with_ssl_bypass)
    results = []
    
    for entry in feed.entries[:30]: # Increased to top 30 to get wider city coverage
        results.append({
            "id": generate_id(url, entry.get("id", entry.link)),
            "source": f"RSS: {url.split('/')[2]}",
            "title": entry.get("title", ""),
            "body": entry.get("summary", ""),
            "author_location": "Unknown", # RSS rarely provides this reliably
            "url": entry.link,
            "timestamp": entry.get("published", datetime.now().isoformat())
        })
    return results

async def fetch_all_rss():
    """Fetches all RSS feeds concurrently."""
    tasks = [fetch_rss_feed(url) for url in RSS_FEEDS]
    results = await asyncio.gather(*tasks)
    return [item for sublist in results for item in sublist]

async def aggregate_feeds():
    """Entry point to aggregate all data sources."""
    rss_items = await fetch_all_rss()
    mock_items = generate_mock_world_cup_data()
    return rss_items + mock_items

if __name__ == "__main__":
    # Test script locally
    async def test():
        items = await aggregate_feeds()
        print(f"Fetched {len(items)} items.")
        if items:
            print("Sample item:", items[0])
            
    asyncio.run(test())
