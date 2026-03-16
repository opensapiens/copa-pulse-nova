"""
Test script to verify CopaPulse Nova pipeline components.
Run this to check if Reddit scraping, Bedrock inference, and geocoding work.
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

def check_environment():
    """Verify environment variables are configured."""
    print("\n" + "="*60)
    print("🔍 CHECKING ENVIRONMENT CONFIGURATION")
    print("="*60 + "\n")
    
    required = {
        'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
        'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'AWS_DEFAULT_REGION': os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
    }
    
    optional = {
        'REDDIT_CLIENT_ID': os.getenv('REDDIT_CLIENT_ID'),
        'REDDIT_CLIENT_SECRET': os.getenv('REDDIT_CLIENT_SECRET'),
        'BEDROCK_MODEL_ID': os.getenv('BEDROCK_MODEL_ID', 'us.amazon.nova-lite-v1:0'),
    }
    
    all_good = True
    
    for key, value in required.items():
        if value and value != f'your_{key.lower()}':
            print(f"✅ {key}: Configured")
        else:
            print(f"❌ {key}: MISSING or not configured!")
            all_good = False
    
    print()
    for key, value in optional.items():
        if value and 'your_' not in value.lower():
            print(f"✅ {key}: Configured")
        else:
            print(f"⚠️  {key}: Not configured (optional)")
    
    print()
    return all_good

async def test_scraper():
    """Test the Reddit and RSS scraper."""
    print("\n" + "="*60)
    print("🌐 TESTING DATA SCRAPER (Reddit + RSS)")
    print("="*60 + "\n")
    
    try:
        from src.scraper import aggregate_feeds
        
        items = await aggregate_feeds()
        
        if not items:
            print("❌ No items fetched! Check your internet connection or Reddit API credentials.")
            return False
        
        print(f"✅ Successfully fetched {len(items)} items")
        
        # Count by source type
        reddit_count = sum(1 for item in items if 'Reddit' in item.get('source', ''))
        rss_count = sum(1 for item in items if 'RSS' in item.get('source', ''))
        mock_count = sum(1 for item in items if 'Mock' in item.get('source', ''))
        
        print(f"   - {reddit_count} from Reddit")
        print(f"   - {rss_count} from RSS feeds")
        print(f"   - {mock_count} from mock data")
        
        if items:
            print("\n📄 Sample item:")
            sample = items[0]
            print(f"   Source: {sample.get('source', 'N/A')}")
            print(f"   Title: {sample.get('title', 'N/A')[:80]}...")
            print(f"   ID: {sample.get('id', 'N/A')}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Scraper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_inference():
    """Test Bedrock Nova Lite inference."""
    print("\n" + "="*60)
    print("🤖 TESTING BEDROCK NOVA LITE INFERENCE")
    print("="*60 + "\n")
    
    try:
        from src.inference import BedrockGuesser
        
        guesser = BedrockGuesser()
        print(f"✅ Bedrock client initialized")
        print(f"   Model: {guesser.model_id}")
        print(f"   Region: {os.getenv('AWS_DEFAULT_REGION', 'us-east-1')}")
        
        # Test with a mock item about a World Cup match
        test_item = {
            "id": "test_inference_123",
            "source": "Test",
            "title": "Massive celebrations at SoFi Stadium after last-minute goal!",
            "body": "Fans are going wild at SoFi Stadium in Los Angeles after a dramatic 89th minute goal. The atmosphere is electric!",
            "author_location": "Los Angeles",
            "timestamp": "2026-06-15T10:00:00Z"
        }
        
        print("\n🧪 Testing with sample sports article:")
        print(f"   Title: {test_item['title']}")
        print()
        
        result = guesser.infer_location(test_item)
        
        if result:
            print("✅ Inference successful!")
            print(f"   Location: {result.get('inferred_location', 'N/A')}")
            print(f"   Confidence: {result.get('confidence_score', 0):.2f}")
            print(f"   Sentiment: {result.get('sentiment', 'N/A')}")
            print(f"   Summary: {result.get('summary', 'N/A')}")
            print()
            return True
        else:
            print("❌ Inference returned None (item may have been filtered out)")
            print("   This could be normal if the AI doesn't recognize it as sports content")
            print()
            return False
            
    except Exception as e:
        print(f"❌ Inference test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        
        if "UnrecognizedClientException" in str(e):
            print("💡 TIP: Check your AWS credentials in .env file")
        elif "ValidationException" in str(e):
            print("💡 TIP: You may need to enable Bedrock model access in AWS Console")
            print("   Go to: AWS Console → Bedrock → Model access → Request access to Nova Lite")
        elif "ResourceNotFoundException" in str(e):
            print("💡 TIP: Model ID may be incorrect. Check BEDROCK_MODEL_ID in .env")
            print("   Current model: " + os.getenv('BEDROCK_MODEL_ID', 'us.amazon.nova-lite-v1:0'))
        
        print()
        return False

def test_geocoding():
    """Test geocoding functionality."""
    print("\n" + "="*60)
    print("📍 TESTING GEOCODING")
    print("="*60 + "\n")
    
    try:
        from src.geocode import GeocoderCache
        
        geocoder = GeocoderCache()
        
        test_locations = [
            "Los Angeles, California, USA",
            "Mexico City, Mexico",
            "Toronto, Canada"
        ]
        
        for location in test_locations:
            lat, lon = geocoder.get_coordinates(location)
            if lat and lon:
                print(f"✅ {location}: ({lat:.4f}, {lon:.4f})")
            else:
                print(f"❌ {location}: Failed to geocode")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Geocoding test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False

async def run_full_test():
    """Run all tests in sequence."""
    print("\n" + "🔬 " + "="*56 + " 🔬")
    print("   COPAPULSE NOVA - SYSTEM TEST")
    print("🔬 " + "="*56 + " 🔬")
    
    # Step 1: Environment
    env_ok = check_environment()
    
    if not env_ok:
        print("\n⚠️  CRITICAL: AWS credentials not configured!")
        print("Please configure .env file before continuing.\n")
        return
    
    # Step 2: Scraper
    scraper_ok = await test_scraper()
    
    # Step 3: Inference (only if AWS is configured)
    inference_ok = False
    if env_ok:
        inference_ok = test_inference()
    
    # Step 4: Geocoding
    geocoding_ok = test_geocoding()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60 + "\n")
    print(f"Environment:     {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Data Scraping:   {'✅ PASS' if scraper_ok else '❌ FAIL'}")
    print(f"AI Inference:    {'✅ PASS' if inference_ok else '❌ FAIL'}")
    print(f"Geocoding:       {'✅ PASS' if geocoding_ok else '❌ FAIL'}")
    
    print()
    
    if all([env_ok, scraper_ok, inference_ok, geocoding_ok]):
        print("🎉 ALL TESTS PASSED! Your CopaPulse Nova is ready to run!")
        print()
        print("Next steps:")
        print("  1. Run the app: streamlit run app.py")
        print("  2. Or use the API: uvicorn api:app --reload")
        print("  3. Or start both: .\\run.ps1")
    else:
        print("⚠️  Some tests failed. Please fix the issues above before running the app.")
    
    print()

if __name__ == "__main__":
    asyncio.run(run_full_test())
