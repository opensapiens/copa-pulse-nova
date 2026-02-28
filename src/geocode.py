import time
import json
import ssl
import geopy.geocoders
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.extra.rate_limiter import RateLimiter
from .db import get_db_connection

# Disable SSL globally for geopy if certs are missing on macOS
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

class GeocoderCache:
    def __init__(self):
        # Initialize proper User-Agent for Nominatim per their usage policy
        self.geolocator = Nominatim(user_agent="copa-pulse-tracker/1.0", scheme='http')
        # Rate limit to 1 request per second to avoid getting blocked
        self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1.1)

    def get_coordinates(self, location_string):
        """
        Takes an LLM-inferred location string and returns (lat, lon).
        Uses DuckDB to cache results and enforce <2s load times on repetitive queries.
        """
        if not location_string or location_string.lower() == "unknown":
            return None, None
            
        # Check cache first
        try:
            conn = get_db_connection()
            cached = conn.execute(
                "SELECT lat, lon FROM geocode_cache WHERE location_string = ?", 
                [location_string]
            ).fetchone()
            if cached:
                return cached[0], cached[1]
        except Exception as e:
            print(f"Warning: Failed to read from geocode cache: {e}")

        # If not in cache, query Nominatim
        try:
            # We wrap with a simple retry loop for timeouts
            for _ in range(3):
                try:
                    location = self.geocode(location_string)
                    if location:
                        lat, lon = location.latitude, location.longitude
                        
                        # Save to cache
                        try:
                            # Re-establish connection just in case
                            conn = get_db_connection()
                            conn.execute(
                                "INSERT INTO geocode_cache (location_string, lat, lon) VALUES (?, ?, ?)",
                                [location_string, lat, lon]
                            )
                        except Exception as e:
                            print(f"Warning: Failed to write to geocode cache: {e}")
                            
                        return lat, lon
                    break # Break retry loop if location is suddenly None
                except (GeocoderTimedOut, GeocoderUnavailable):
                    time.sleep(2)
                    pass
        except Exception as e:
            print(f"Error geocoding {location_string}: {e}")
            
        return None, None

if __name__ == "__main__":
    # Test script locally
    g = GeocoderCache()
    lat, lon = g.get_coordinates("Zócalo, Mexico City")
    print(f"Zócalo -> Lat: {lat}, Lon: {lon}")
    # Second call should hit the cache and be instantaneous
    start_time = time.time()
    lat, lon = g.get_coordinates("Zócalo, Mexico City")
    print(f"Zócalo (cached) -> Lat: {lat}, Lon: {lon} - Took: {time.time() - start_time:.4f}s")
