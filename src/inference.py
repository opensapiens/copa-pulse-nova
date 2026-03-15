import boto3
import json
import os
from dotenv import load_dotenv
from .db import get_db_connection

load_dotenv()

PROMPT_TEMPLATE = """
You are a sports event intelligence system for the 2026 FIFA World Cup.
Your ONLY job is to process articles and posts that are about SPORTS — specifically football/soccer matches, fan reactions, stadium atmosphere, goal celebrations, player performances, team news, fan zones, World Cup fixtures, upsets, red cards, chants, or crowd energy.

STRICT FILTER RULE: If this article or post is NOT primarily about a sports event or sports-related fan activity, you MUST return "Unknown" for inferred_location and set confidence_score to 0.0. Ignore politics, general news, weather, business, entertainment, or any non-sports content entirely.

If the article IS sports-related:
- Identify the most specific location of the sports event or fan activity described.
- You must ONLY extract locations within North America (United States, Canada, Mexico). If the sports event is physically located elsewhere, return "Unknown".
- Map to one of the 16 official 2026 World Cup host cities if possible:
  USA: Atlanta, Boston, Dallas, Houston, Kansas City, Los Angeles, Miami, New York/New Jersey, Philadelphia, San Francisco Bay Area, Seattle.
  Mexico: Guadalajara, Mexico City, Monterrey.
  Canada: Toronto, Vancouver.
- Use stadium names, fan zones, or local landmarks to pinpoint location.
- Gauge the crowd/fan energy: are fans celebrating, anxious, devastated, or electric?

Return a JSON:
{{
    "inferred_location": "Specific Stadium, Fan Zone, or Host City, Country",
    "confidence_score": 0.5,
    "reasoning": "Article describes fans storming the streets near SoFi Stadium after a last-minute goal",
    "sentiment": "positive/neutral/negative",
    "nationalities": ["list of nationalities of fans or teams mentioned"],
    "summary": "One sentence sports-focused summary of the crowd energy or match event"
}}

Ensure the output is STRICTLY a valid JSON object. Do not include markdown formatting or backticks around the JSON.

Source: {source}
Title: {title}
Body: {body}
Author Location: {author_location}
Timestamp: {timestamp}
"""

CITY_SUMMARY_PROMPT = """
You are a 2026 FIFA World Cup stadium atmosphere analyst.
You are analyzing a batch of SPORTS-ONLY news articles and fan posts for the host city of {location}.
Your goal is to capture the current match atmosphere, crowd energy, and key sporting moments happening in this city.

Focus EXCLUSIVELY on:
- Match results, goals, upsets, red cards, penalties
- Fan crowd energy, chants, stadium atmosphere, fan zone reactions
- Player standout performances or controversies
- Team news (injuries, lineups, surprises)
- Any incidents or highlights inside or around the stadium

Ignore any non-sports content entirely.

Read through the following sports items:
{news_items_text}

Return a single JSON block:
{{
    "sentiment": "positive",
    "summary": "A 1-2 sentence punchy sports-focused description of the current atmosphere and fan energy in this city.",
    "key_events": [
        "Goal: Mbappe scores in the 89th minute — crowd erupts at SoFi",
        "Red card controversy sparks heated debate among fans outside the stadium",
        "Fan zones at downtown LA packed to capacity — massive celebrations"
    ]
}}

sentiment must be one of: "positive", "neutral", "negative", "mixed".
key_events should be 3-5 specific, punchy sports moments — not generic statements.
Ensure the output is STRICTLY a valid JSON object. Do not include markdown formatting or backticks around the JSON.
"""

class BedrockGuesser:
    def __init__(self):
        # Configure the boto3 client for Bedrock Runtime
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        )
        # Amazon Nova Lite model ID (use environment variable for flexibility)
        self.model_id = os.getenv('BEDROCK_MODEL_ID', 'us.amazon.nova-lite-v1:0')
        
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
                    "text": "You are a sports intelligence AI specializing in the 2026 FIFA World Cup. You extract geolocation and crowd energy data exclusively from sports-related content. You must ignore all non-sports content and return Unknown for anything unrelated to football matches, fan activity, or stadium events."
                }
            ],
            "inferenceConfig": {
                "maxTokens": 512,
                "temperature": 0.1,
                "topP": 0.9,
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

            # Hard filter: drop non-sports content (confidence 0 or Unknown location)
            if float(result.get("confidence_score", 0.0)) == 0.0:
                return None
            if result.get("inferred_location", "").strip().lower() in ("", "unknown"):
                return None
            
            # Write to cache
            try:
                conn.execute("""
                    INSERT INTO inference_cache 
                    (id, title, body, inferred_location, confidence_score, reasoning, sentiment, nationalities, summary) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (id) DO NOTHING
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
                    "text": "You are a 2026 FIFA World Cup match atmosphere analyst. You synthesize fan posts and sports news into punchy, stadium-grade summaries of crowd energy, match highlights, and key sporting moments. You never discuss non-sports topics."
                }
            ],
            "inferenceConfig": {
                "maxTokens": 512,
                "temperature": 0.2,
                "topP": 0.9,
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
                    ON CONFLICT (id) DO NOTHING
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
