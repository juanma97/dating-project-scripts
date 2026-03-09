import requests
from datetime import datetime
from typing import Dict, Optional
from config import MEETUP_GRAPHQL_URL

def fetch_meetup_events(query: str, city: str, lat: float, lon: float, limit: int = 1) -> Optional[Dict]:
    """Fetches raw event data from the Meetup GraphQL API."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
    }

    today = datetime.now()
    
    search_payload = {
        "operationName": "eventSearchWithSeries",
        "variables": {
            "first": limit, 
            "lat": lat,
            "lon": lon,
            "startDateRange": today.strftime("%Y-%m-%dT%H:%M:%S-04:00[US/Eastern]"),
            "numberOfEventsForSeries": 1,
            "seriesStartDate": today.strftime("%Y-%m-%d"),
            "query": query,
            "city": city,
            "country": "es",
            "sortField": "RELEVANCE",
            "doConsolidateEvents": True,
            "dataConfiguration": '{"isSimplifiedSearchEnabled": true}'
        },
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "846d1d8582288189f26c1a3bdc53922c51970cebd8976fb7284615ef0832d06e"
            }
        }
    }

    response = requests.post(MEETUP_GRAPHQL_URL, headers=headers, json=search_payload)
    response.raise_for_status()
    return response.json()