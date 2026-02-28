import streamlit as st
import pydeck as pdk
import pandas as pd
import asyncio
import time
from datetime import datetime

# Local imports
from src.scraper import aggregate_feeds
from src.inference import BedrockGuesser
from src.geocode import GeocoderCache
from src.db import get_db_connection

# Page config must be the first Streamlit command
st.set_page_config(
    page_title="CopaPulse",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Full Screen and Bottom Sheet Mobile Layout
st.markdown("""
    <style>
    /* Remove padding to make map truly full-screen */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }
    
    /* Fix bottom sheet container */
    div[data-testid="stExpander"] {
        position: fixed !important;
        bottom: 0;
        left: 0;
        right: 0;
        margin-bottom: 0px;
        z-index: 999;
        background-color: rgba(17, 17, 17, 0.95);
        border-top-left-radius: 20px;
        border-top-right-radius: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0px -5px 15px rgba(0,0,0,0.5);
    }
    
    /* Adjust expander header style */
    .streamlit-expanderHeader {
        font-size: 1.2rem;
        font-weight: bold;
        padding: 15px 20px;
        color: white;
    }
    
    /* Hide specific Streamlit elements for mobile feel */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Title Layer over the map */
    .title-layer {
        position: absolute;
        top: 20px;
        left: 20px;
        z-index: 999;
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        background: rgba(0,0,0,0.3);
        padding: 10px 20px;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATA PIPELINE (Cached to prevent excessive API calls)
# ---------------------------------------------------------
@st.cache_data(ttl=300) # 5 minutes TTL
def fetch_and_process_data():
    """Builds the map data using our ingestion, inference, and geocoding pipeline."""
    # 1. Scrape RSS and Reddit
    raw_items = asyncio.run(aggregate_feeds())
    if not raw_items:
        return pd.DataFrame()

    # Initialize modules
    guesser = BedrockGuesser()
    geocoder = GeocoderCache()
    conn = get_db_connection()
    
    processed_data = []
    
    # 2. Pipeline processing for each item
    for item in raw_items:
        # Check cache explicitly first (even though modules check it, we can save time here)
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
                "sentiment": cached_item[6]
            })
            continue

        # Inference Step
        llm_result = guesser.infer_location(item)
        if not llm_result:
            continue
            
        location_string = llm_result.get("inferred_location", "")
        weight = float(llm_result.get("confidence_score", 0.1))
        sentiment = llm_result.get("sentiment", "neutral")
        summary = llm_result.get("summary", item.get("title"))
        
        if not location_string or location_string.lower() == "unknown":
            continue

        # Geocoding Step
        lat, lon = geocoder.get_coordinates(location_string)
        
        if lat is not None and lon is not None:
            # Save total pipeline output to `cached_items`
            try:
                conn.execute("""
                    INSERT INTO cached_items 
                    (id, source, title, url, published_at, lat, lon, inferred_location, confidence_score, summary, sentiment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    item['id'], item['source'], item['title'], item['url'], 
                    # Handle datetime conversion safely
                    datetime.now(), 
                    lat, lon, location_string, weight, summary, sentiment
                ])
            except Exception as e:
                print(f"Error inserting to cached_items: {e}")
                
            processed_data.append({
                "lat": lat,
                "lon": lon,
                "location": location_string,
                "weight": weight,
                "title": item['title'],
                "summary": summary,
                "sentiment": sentiment
            })

    return pd.DataFrame(processed_data)

# ---------------------------------------------------------
# UI RENDERING
# ---------------------------------------------------------

# Title overlay
st.markdown('<div class="title-layer"><h1>🏆 CopaPulse Live</h1><p>2026 World Cup Crowd Tracker</p></div>', unsafe_allow_html=True)

# Fetch data
with st.spinner("Syncing Pulse Data (RSS + Reddit + Nova-Lite)..."):
    df = fetch_and_process_data()

if df.empty:
    st.warning("No location data found in the current feeds cycle. Check the terminal logs for Bedrock or scraper issues.")
    st.stop()

# PyDeck Map
# Calculate bounds or center (default to North America for 2026 World Cup)
view_state = pdk.ViewState(
    latitude=39.8283, 
    longitude=-98.5795,
    zoom=3,
    pitch=50
)

# Heatmap Layer
heatmap_layer = pdk.Layer(
    "HeatmapLayer",
    data=df,
    opacity=0.8,
    get_position=["lon", "lat"],
    get_weight="weight",
    aggregation="SUM", 
    radiusPixels=50,
)

# Scatterplot Layer for exact tooltips
scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df,
    get_position=["lon", "lat"],
    get_color=[255, 50, 50, 200],
    get_radius=20000,
    pickable=True
)

tooltip = {
    "html": "<b>📍 {location}</b><br/>"
            "<i>{title}</i><br/>"
            "<hr style='margin: 4px; border-color: rgba(255,255,255,0.2);'>"
            "<b>Sentiment:</b> {sentiment}<br/>"
            "<b>Summary:</b> {summary}<br/>"
            "<b>Confidence:</b> {weight}",
    "style": {
        "backgroundColor": "rgba(30, 41, 59, 0.9)", 
        "color": "white",
        "fontSize": "14px",
        "padding": "12px",
        "borderRadius": "8px",
        "boxShadow": "0 4px 6px rgba(0,0,0,0.3)"
    }
}

r = pdk.Deck(
    layers=[heatmap_layer, scatter_layer],
    initial_view_state=view_state,
    map_style=pdk.map_styles.DARK,
    tooltip=tooltip
)

# Render full screen map
st.pydeck_chart(r, use_container_width=True)

# ---------------------------------------------------------
# MOBILE BOTTOM SHEET: LIVE SUMMARY
# ---------------------------------------------------------
st.markdown("<br><br><br><br><br>", unsafe_allow_html=True) # padding spacer 

hottest_spot_row = df.loc[df['weight'].idxmax()] if not df.empty else None

with st.expander("🔥 Live Summary (Swipe Up)", expanded=True):
    if hottest_spot_row is not None:
        st.subheader(f"📍 Hottest Spot: {hottest_spot_row['location']}")
        st.write(f"📝 **Event:** {hottest_spot_row['title']}")
        st.write(f"ℹ️ **Summary:** {hottest_spot_row['summary']}")
        
        sentiment = hottest_spot_row['sentiment']
        emoji = "🤩" if sentiment == "positive" else "😐" if sentiment == "neutral" else "😡"
        st.write(f"Vibe Check: {sentiment.capitalize()} {emoji}")
        
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')} - Auto-refreshes every 5 mins.")

# ---------------------------------------------------------
# AUTO REFRESH LOOP (Every 5 mins)
# ---------------------------------------------------------
# Using classic Streamlit time.sleep to force a rerun if needed
time.sleep(300)
st.rerun()
