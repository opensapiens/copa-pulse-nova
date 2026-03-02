import duckdb
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "copapulse.db")

def get_db_connection():
    """Initializes and returns a DuckDB connection with required tables."""
    conn = duckdb.connect(database=DB_PATH, read_only=False)
    
    # Create table for cached LLM inference
    conn.execute("""
        CREATE TABLE IF NOT EXISTS inference_cache (
            id VARCHAR PRIMARY KEY,
            title VARCHAR,
            body VARCHAR,
            inferred_location VARCHAR,
            confidence_score DOUBLE,
            reasoning VARCHAR,
            sentiment VARCHAR,
            nationalities VARCHAR,
            summary VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create table for cached geocoding
    conn.execute("""
        CREATE TABLE IF NOT EXISTS geocode_cache (
            location_string VARCHAR PRIMARY KEY,
            lat DOUBLE,
            lon DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create table for raw processed items to power the real-time feed
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cached_items (
            id VARCHAR PRIMARY KEY,
            source VARCHAR,
            title VARCHAR,
            url VARCHAR,
            published_at TIMESTAMP,
            lat DOUBLE,
            lon DOUBLE,
            inferred_location VARCHAR,
            confidence_score DOUBLE,
            summary VARCHAR,
            sentiment VARCHAR
        )
    """)
    
    # Create table for cached city summaries
    conn.execute("""
        CREATE TABLE IF NOT EXISTS city_summary_cache (
            id VARCHAR PRIMARY KEY,
            location VARCHAR,
            item_ids_hash VARCHAR,
            summary VARCHAR,
            sentiment VARCHAR,
            key_events VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    return conn
