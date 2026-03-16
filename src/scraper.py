import asyncio
import feedparser
import os
import hashlib
import ssl
import random
from datetime import datetime
from dotenv import load_dotenv
import praw
from prawcore import NotFound

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

async def fetch_reddit_posts():
    """Fetches Reddit posts about World Cup, soccer, and sports from relevant subreddits."""
    loop = asyncio.get_event_loop()
    
    def _fetch_reddit():
        try:
            # Initialize Reddit client (read-only mode, no authentication needed)
            reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID', 'your_client_id'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET', 'your_client_secret'),
                user_agent='CopaPulse:v1.0 (by /u/yourname)'
            )
            
            # Subreddits focused on soccer/World Cup
            subreddits = [
                'worldcup', 'soccer', 'football', 'MLS', 'LigaMX', 
                'ussoccer', 'CanadaSoccer', 'FutbolMX'
            ]
            
            results = []
            
            for subreddit_name in subreddits:
                try:
                    subreddit = reddit.subreddit(subreddit_name)
                    # Get hot posts from the last 24 hours
                    for post in subreddit.hot(limit=15):
                        # Skip stickied posts
                        if post.stickied:
                            continue
                            
                        results.append({
                            "id": generate_id(f"reddit_{subreddit_name}", post.id),
                            "source": f"Reddit: r/{subreddit_name}",
                            "title": post.title,
                            "body": post.selftext if post.selftext else post.title,
                            "author_location": "Unknown",  # Reddit doesn't expose user location
                            "url": f"https://reddit.com{post.permalink}",
                            "timestamp": datetime.fromtimestamp(post.created_utc).isoformat()
                        })
                except NotFound:
                    print(f"Subreddit r/{subreddit_name} not found, skipping...")
                except Exception as e:
                    print(f"Error fetching from r/{subreddit_name}: {e}")
                    
            return results
            
        except Exception as e:
            print(f"Reddit API error: {e}")
            print("Tip: Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env file")
            print("Get credentials at: https://www.reddit.com/prefs/apps")
            return []
    
    return await loop.run_in_executor(None, _fetch_reddit)

async def fetch_all_rss():
    """Fetches all RSS feeds concurrently."""
    tasks = [fetch_rss_feed(url) for url in RSS_FEEDS]
    results = await asyncio.gather(*tasks)
    return [item for sublist in results for item in sublist]

async def aggregate_feeds():
    """Entry point to aggregate all data sources."""
    rss_items, reddit_items = await asyncio.gather(
        fetch_all_rss(),
        fetch_reddit_posts()
    )
    mock_items = generate_mock_world_cup_data()
    
    all_items = rss_items + reddit_items + mock_items
    print(f"Fetched {len(rss_items)} RSS items, {len(reddit_items)} Reddit posts, {len(mock_items)} mock items")
    return all_items

if __name__ == "__main__":
    # Test script locally
    async def test():
        items = await aggregate_feeds()
        print(f"Fetched {len(items)} items.")
        if items:
            print("Sample item:", items[0])
            
    asyncio.run(test())
