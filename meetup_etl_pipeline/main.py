import os
from config import DEFAULT_LATITUDE, DEFAULT_LONGITUDE
from meetup_client import fetch_meetup_events
from ai_analyzer import get_gemini_client, analyze_event_with_ai
from data_parser import build_database_record

def process_single_event_pipeline():
    """Main workflow orchestrator."""
    try:
        # 1. Initialize AI Client
        print("Initializing AI Client...")
        ai_client = get_gemini_client()
        
        # 2. Fetch Data from API
        print("Fetching data from Meetup...")
        api_data = fetch_meetup_events(
            query="speed dating", 
            city="Madrid", 
            lat=DEFAULT_LATITUDE, 
            lon=DEFAULT_LONGITUDE
        )
        
        # Validate API response
        if not api_data or not api_data.get('data', {}).get('results', {}).get('edges'):
            print("No events found.")
            return
            
        node = api_data['data']['results']['edges'][0]['node']
        
        # 3. Analyze with AI
        print("Analyzing event with Gemini AI...")
        ai_data = analyze_event_with_ai(
            client=ai_client,
            title=node.get('title', ''),
            description=node.get('description', ''),
            venue_data=node.get('venue', {}),
            url=node.get('eventUrl', '')
        )
        
        # 4. Parse & Combine
        print("Building database record...")
        db_record = build_database_record(node, ai_data)
        
        # 5. Output
        print("-" * 50)
        for column, value in db_record.items():
            print(f"{column}: {value}")
        print("-" * 50)
            
    except Exception as e:
        print(f"Pipeline failed: {e}")

if __name__ == "__main__":
    process_single_event_pipeline()