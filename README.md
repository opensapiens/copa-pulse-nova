# CopaPulse Nova - 2026 FIFA World Cup Heatmap

A real-time heatmap visualization of crowd energy and match atmosphere across 2026 FIFA World Cup host cities in North America. Powered by Amazon Nova Lite and real-time data from Reddit and news sources.

## Features

- **Real-time Data Scraping**: Pulls posts from Reddit (r/worldcup, r/soccer, r/MLS, etc.) and RSS news feeds
- **AI-Powered Location Inference**: Uses Amazon Bedrock Nova Lite to extract location and sentiment from unstructured text
- **Geocoding**: Maps locations to 16 official 2026 World Cup host cities
- **Interactive Heatmap**: Visualizes crowd energy and match atmosphere on an interactive map
- **City Summaries**: AI-generated summaries of key sporting events per city

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Reddit    │────▶│   Scraper    │────▶│  Bedrock    │
│  r/soccer   │     │  (RSS/PRAW)  │     │ Nova Lite   │
└─────────────┘     └──────────────┘     └─────────────┘
                            │                    │
┌─────────────┐            │                    ▼
│  RSS Feeds  │────────────┘           ┌─────────────────┐
│  (CNN, NYT) │                        │   Inference     │
└─────────────┘                        │  (Location,     │
                                       │  Sentiment)     │
                                       └─────────────────┘
                                                │
                                                ▼
                                       ┌─────────────────┐
                                       │   Geocoder      │
                                       │  (Nominatim)    │
                                       └─────────────────┘
                                                │
                                                ▼
                                       ┌─────────────────┐
                                       │  DuckDB Cache   │
                                       │  + Map View     │
                                       └─────────────────┘
```

## Setup

### 1. Prerequisites

- Python 3.9+
- AWS Account with Bedrock access
- Reddit API credentials (optional but recommended)

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.\.venv\Scripts\activate.bat
# macOS/Linux:
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:

- **AWS Credentials**: Get from AWS IAM Console
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_DEFAULT_REGION` (e.g., `us-east-1`)

- **Bedrock Model** (optional, defaults to Nova Lite):
  - `BEDROCK_MODEL_ID=us.amazon.nova-lite-v1:0`

- **Reddit API** (optional, but needed for Reddit scraping):
  - Go to https://www.reddit.com/prefs/apps
  - Create a "script" app
  - Copy `client_id` and `client_secret` to `.env`

### 4. Enable Amazon Bedrock Nova Lite

1. Log into AWS Console
2. Navigate to Amazon Bedrock
3. Go to "Model access"
4. Request access to "Amazon Nova Lite"
5. Wait for approval (usually instant)

### 5. Run the Application

#### Option A: Streamlit Web App (app.py)

```bash
streamlit run app.py
```

Opens at http://localhost:8501

#### Option B: FastAPI Backend (api.py)

```bash
uvicorn api:app --reload
```

API docs at http://localhost:8000/docs

#### Option C: React Frontend + API

```bash
# Terminal 1: Start API
uvicorn api:app --reload

# Terminal 2: Start React frontend
cd frontend
npm install
npm run dev
```

Frontend at http://localhost:5173

## Testing the Data Pipeline

### Test Scraper

```bash
python -m src.scraper
```

Should output:

```
Fetched X RSS items, Y Reddit posts, Z mock items
Sample item: {...}
```

### Test Inference

```bash
python -m src.inference
```

Should output:

```
Inference Result: {
  "inferred_location": "...",
  "confidence_score": 0.8,
  "sentiment": "positive",
  ...
}
```

### Test Full Pipeline

```bash
# Run the Streamlit app and check the console for logs
streamlit run app.py
```

Watch the terminal for:

- "Fetched X RSS items, Y Reddit posts..."
- Any errors from Bedrock API
- Geocoding lookups

## Troubleshooting

### "Error inferring location: ..."

- Verify AWS credentials are correct
- Check that Bedrock Nova Lite access is enabled
- Ensure `AWS_DEFAULT_REGION` matches where you have Bedrock access

### "Reddit API error: ..."

- Verify `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` in `.env`
- Make sure you created a "script" app (not "web app") on Reddit
- Reddit integration is optional - the app works with RSS feeds alone

### No heatpoints showing on map

- Check if scraper is finding news items (check console logs)
- Verify that items mention North American cities
- The AI model filters out non-sports content - make sure your sources discuss sports
- Try the mock data generator as a fallback (already included)

### Geocoding errors

- The app uses free Nominatim geocoding (no API key needed)
- Rate limits may apply - caching is enabled to minimize requests

## 2026 World Cup Host Cities

The app focuses on these 16 official host cities:

**USA**: Atlanta, Boston, Dallas, Houston, Kansas City, Los Angeles, Miami, New York/New Jersey, Philadelphia, San Francisco Bay Area, Seattle

**Mexico**: Guadalajara, Mexico City, Monterrey

**Canada**: Toronto, Vancouver

## Project Structure

```
copa-pulse-nova/
├── app.py                 # Streamlit web interface
├── api.py                 # FastAPI backend
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variable template
├── src/
│   ├── scraper.py        # Reddit + RSS feed aggregator
│   ├── inference.py      # Bedrock Nova Lite integration
│   ├── geocode.py        # Location to lat/lon conversion
│   └── db.py             # DuckDB caching layer
└── frontend/             # React TypeScript frontend
    ├── src/
    │   ├── App.tsx
    │   └── MapComponent.tsx
    └── package.json
```

## License

MIT
