import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd

# Local imports
from src.scraper import aggregate_feeds
from src.inference import BedrockGuesser
from src.geocode import GeocoderCache
from src.db import get_db_connection

from cachetools import cached, TTLCache

app = FastAPI(title="CopaPulse API")

# Setup 5 minute TTL cache to mimic Streamlit's @st.cache_data behavior
data_cache = TTLCache(maxsize=1, ttl=300)

# Add CORS middleware to allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@cached(data_cache)
def fetch_and_process_data() -> List[Dict[str, Any]]:
    # We use the same business logic from app.py but adapt it to return JSON
    raw_items = asyncio.run(aggregate_feeds())
    if not raw_items:
        return []

    guesser = BedrockGuesser()
    geocoder = GeocoderCache()
    conn = get_db_connection()
    
    processed_data = []
    aws_available = False
    
    # Test if AWS credentials are configured
    try:
        import boto3
        import os
        if os.getenv('AWS_ACCESS_KEY_ID') and 'YOUR_' not in os.getenv('AWS_ACCESS_KEY_ID', '').upper():
            aws_available = True
    except:
        pass
    
    # 2. Pipeline processing for each item
    for item in raw_items:
        cached_item = conn.execute(
            "SELECT lat, lon, inferred_location, confidence_score, title, summary, sentiment FROM cached_items WHERE id = ?",
            [item['id']]
        ).fetchone()
        
        if cached_item:
            processed_data.append({
                "lat": cached_item[0],
                "lon": cached_item[1],
                "location": cached_item[2],
                "weight": cached_item[3],
                "title": cached_item[4],
                "summary": cached_item[5],
                "sentiment": cached_item[6],
                "id": item['id']
            })
            continue

        # If AWS is available, use AI inference
        if aws_available:
            llm_result = guesser.infer_location(item)
            if not llm_result:
                continue
                
            location_string = llm_result.get("inferred_location", "")
            weight = float(llm_result.get("confidence_score", 0.1))
            sentiment = llm_result.get("sentiment", "neutral")
            summary = llm_result.get("summary", item.get("title"))
            
            if not location_string or location_string.lower() == "unknown":
                continue

            lat, lon = geocoder.get_coordinates(location_string)
        else:
            # Fallback: Use mock data locations directly for demo purposes
            # Extract location from mock items (they already have author_location set)
            location_string = item.get('author_location', 'Unknown')
            if location_string == 'Unknown':
                continue
                
            lat, lon = geocoder.get_coordinates(location_string)
            weight = 0.7  # Default weight for mock data
            sentiment = "positive"
            summary = item.get('title', 'Mock event happening in the area.')
        
        if lat is not None and lon is not None:
            # We skip the DB insert error handling for brevity, assume cache is hit mostly in demo
            processed_data.append({
                "lat": lat,
                "lon": lon,
                "location": location_string,
                "weight": weight,
                "title": item['title'],
                "summary": summary,
                "sentiment": sentiment,
                "id": item['id']
            })

    # Group items by location for city-level summaries
    grouped_data = {}
    for pd_item in processed_data:
        loc = pd_item["location"]
        if loc not in grouped_data:
            grouped_data[loc] = []
        grouped_data[loc].append(pd_item)

    city_summaries = []
    for loc, items in grouped_data.items():
        # Try AI summarization if AWS is available, otherwise use fallback
        if aws_available:
            try:
                city_stats = guesser.summarize_city(loc, items)
            except:
                city_stats = {
                    "summary": f"Activity detected in {loc} with {len(items)} events.",
                    "sentiment": "neutral",
                    "key_events": [item['title'][:80] for item in items[:3]]
                }
        else:
            # Fallback summary without AI
            city_stats = {
                "summary": f"Activity detected in {loc} with {len(items)} events. Configure AWS credentials for AI-powered insights.",
                "sentiment": "positive",
                "key_events": [item['title'][:80] for item in items[:3]]
            }
        
        avg_lat = sum(i["lat"] for i in items) / len(items)
        avg_lon = sum(i["lon"] for i in items) / len(items)
        total_weight = sum(i["weight"] for i in items)
        
        # New: Gather reasoning strings from individual items to power the "Agent Reasoning" UI
        # We look up the original cache inference for each item ID
        reasoning_list = []
        try:
            for itm in items:
                res = conn.execute("SELECT reasoning FROM inference_cache WHERE id = ?", [itm['id']]).fetchone()
                if res and res[0]:
                    reasoning_list.append({"title": itm['title'], "reasoning": res[0]})
        except Exception as e:
            print(f"Error fetching reasoning: {e}")

        city_summaries.append({
            "lat": avg_lat,
            "lon": avg_lon,
            "location": loc,
            "weight": total_weight,
            "summary": city_stats.get("summary", "No summary available."),
            "sentiment": city_stats.get("sentiment", "neutral"),
            "key_events": city_stats.get("key_events", []),
            "reasoning": reasoning_list,
            "items_count": len(items)
        })

    return city_summaries

@app.get("/api/data")
def get_map_data():
    try:
        data = fetch_and_process_data()
        return {"status": "success", "data": data}
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
@app.get("/api")
def health_check():
    return {"status": "alive", "message": "CopaPulse API is running. Use /api/data for the map data."}
