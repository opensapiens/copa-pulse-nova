import boto3
import json
import os
from dotenv import load_dotenv
from .db import get_db_connection

load_dotenv()

PROMPT_TEMPLATE = """
Analyze the provided news article or post. Your goal is to identify the most specific possible location of the event described.
You must ONLY extract locations that are within North America (United States, Canada, Mexico). If the event takes place elsewhere (e.g., Europe, South America, Asia, etc.), return "Unknown" for the inferred_location.

Crucially, you should look for mentions of the 16 official 2026 World Cup host cities and gauge the overall event or emotion of the city:
- USA: Atlanta, Boston, Dallas, Houston, Kansas City, Los Angeles, Miami, New York/New Jersey, Philadelphia, San Francisco Bay Area, Seattle.
- Mexico: Guadalajara, Mexico City, Monterrey.
- Canada: Toronto, Vancouver.

Look for North American neighborhood or city names, or landmarks.
Use metadata (source city) to disambiguate.

Return a JSON:
{{
    "inferred_location": "Specific Landmark or City, Country",
    "confidence_score": 0.5,
    "reasoning": "Mentioned a local festival happening in downtown Toronto",
    "sentiment": "positive/neutral/negative",
    "nationalities": ["list"],
    "summary": "Short abstract about what's happening"
}}

Ensure the output is STRICTLY a valid JSON object. Do not include markdown formatting or backticks around the JSON.

Source: {source}
Title: {title}
Body: {body}
Author Location: {author_location}
Timestamp: {timestamp}
"""

CITY_SUMMARY_PROMPT = """
You are analyzing a batch of news articles and posts for the city of {location}. Your goal is to provide an overarching, combined view of the current vibe and key events happening in this city.

Read through the following news items carefully:
{news_items_text}

Return a single JSON block with the following info:
{{
    "sentiment": "positive", // Must be one of: "positive", "neutral", "negative", "mixed"
    "summary": "A concise overview (1-2 sentences) showing what people are talking about or feeling in this city.",
    "key_events": [
        "Event 1 brief description",
        "Event 2 brief description",
        "Event 3 brief description (Aim for 3-5 major distinct events)"
    ]
}}

Ensure the output is STRICTLY a valid JSON object. Do not include markdown formatting or backticks around the JSON.
"""

class BedrockGuesser:
    def __init__(self):
        # Configure the boto3 client for Bedrock Runtime
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        )
        self.model_id = 'amazon.nova-lite-v1:0'
        
    def _create_payload(self, context_text):
        """Creates the payload structure expected by Nova-Lite."""
        return {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": context_text}]
                }
            ],
            "system": [
                {
                    "text": "You are a precise geospatial reasoning AI designed to extract the most specific physical location from a text snippet."
                }
            ],
            "inferenceConfig": {
                "max_new_tokens": 512,
                "temperature": 0.1,  # Keep it deterministic
                "top_p": 0.9,
            }
        }

    def infer_location(self, item):
        """Runs the payload through Bedrock and parses the JSON result."""
        item_id = item.get("id")
        
        # Check cache first
        try:
            conn = get_db_connection()
            cached = conn.execute(
                "SELECT * FROM inference_cache WHERE id = ?", [item_id]
            ).fetchone()
            if cached:
                cols = [desc[0] for desc in conn.description]
                return dict(zip(cols, cached))
        except Exception as e:
            print(f"Warning: Failed to read from inference cache: {e}")

        prompt = PROMPT_TEMPLATE.format(
            source=item.get("source", ""),
            title=item.get("title", ""),
            body=item.get("body", ""),
            author_location=item.get("author_location", ""),
            timestamp=item.get("timestamp", "")
        )
        
        body = json.dumps(self._create_payload(prompt))
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body,
                accept='application/json',
                contentType='application/json'
            )
            response_body = json.loads(response.get('body').read())
            
            # Nova response structures
            output_message = response_body.get('output', {}).get('message', {})
            content = output_message.get('content', [{}])[0].get('text', '')
            
            # Defensive parsing since LLMs might include markdown backticks
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            
            # Write to cache
            try:
                conn.execute("""
                    INSERT INTO inference_cache 
                    (id, title, body, inferred_location, confidence_score, reasoning, sentiment, nationalities, summary) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    item_id, item.get("title", ""), item.get("body", ""),
                    result.get("inferred_location", ""), 
                    float(result.get("confidence_score", 0.0)),
                    result.get("reasoning", ""), 
                    result.get("sentiment", ""),
                    json.dumps(result.get("nationalities", [])), 
                    result.get("summary", "")
                ])
                result['id'] = item_id
            except Exception as e:
                print(f"Warning: Failed to write to inference cache: {e}")
                
            return result
            
        except Exception as e:
            print(f"Error inferring location for {item_id}: {e}")
            return None

    def summarize_city(self, location, items):
        """
        Takes a location string and a list of feed items for that location, 
        and uses the LLM to generate an overall summary, sentiment, and 3-5 key events.
        """
        import hashlib
        
        # Sort items by id for deterministic hash
        sorted_items = sorted(items, key=lambda x: x.get('id', ''))
        item_ids = [str(x.get('id')) for x in sorted_items]
        item_ids_str = ",".join(item_ids)
        item_ids_hash = hashlib.md5(item_ids_str.encode('utf-8')).hexdigest()
        cache_id = f"{location}_{item_ids_hash}"
        
        # Check cache
        try:
            conn = get_db_connection()
            cached = conn.execute(
                "SELECT summary, sentiment, key_events FROM city_summary_cache WHERE id = ?", 
                [cache_id]
            ).fetchone()
            if cached:
                return {
                    "summary": cached[0],
                    "sentiment": cached[1],
                    "key_events": json.loads(cached[2]) if cached[2] else []
                }
        except Exception as e:
            print(f"Warning: Failed to read from city_summary_cache: {e}")

        # Build prompt
        news_items_text = ""
        for i, item in enumerate(sorted_items):
            news_items_text += f"---\nItem {i+1}:\nTitle: {item.get('title', '')}\nSummary: {item.get('summary', '')}\nSentiment: {item.get('sentiment', 'neutral')}\n\n"

        prompt = CITY_SUMMARY_PROMPT.format(
            location=location,
            news_items_text=news_items_text
        )
        
        body = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "system": [
                {
                    "text": "You are a highly capable news aggregator and data analyst."
                }
            ],
            "inferenceConfig": {
                "max_new_tokens": 512,
                "temperature": 0.2,
                "top_p": 0.9,
            }
        })
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body,
                accept='application/json',
                contentType='application/json'
            )
            response_body = json.loads(response.get('body').read())
            
            output_message = response_body.get('output', {}).get('message', {})
            content = output_message.get('content', [{}])[0].get('text', '')
            
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            
            # Write to cache
            try:
                conn.execute("""
                    INSERT INTO city_summary_cache 
                    (id, location, item_ids_hash, summary, sentiment, key_events) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [
                    cache_id, location, item_ids_hash, 
                    result.get("summary", ""), 
                    result.get("sentiment", "neutral"), 
                    json.dumps(result.get("key_events", []))
                ])
            except Exception as e:
                print(f"Warning: Failed to write to city_summary_cache: {e}")
                
            return result
            
        except Exception as e:
            print(f"Error summarizing city {location}: {e}")
            return {
                "summary": "Could not generate summary.",
                "sentiment": "neutral",
                "key_events": []
            }

if __name__ == "__main__":
    # Test script locally
    guesser = BedrockGuesser()
    mock_item = {
        "id": "mock_id_123",
        "source": "Reddit: r/worldcup",
        "title": "Insane celebrations right now!",
        "body": "People are climbing the Obelisk in Buenos Aires, absolutely massive crowd forming.",
        "author_location": "B.A.",
        "timestamp": "2026-06-15T10:00:00Z"
    }
    result = guesser.infer_location(mock_item)
    print("Inference Result:", json.dumps(result, indent=2))
