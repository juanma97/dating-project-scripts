import os
import time
from config import DEFAULT_LATITUDE, DEFAULT_LONGITUDE, SUPABASE_PROJECT_URL, SUPABASE_ANON_KEY, SUPABASE_TABLE_NAME
from meetup_client import fetch_meetup_events
from ai_analyzer import get_gemini_client, analyze_event_with_ai
from data_parser import build_database_record
from supabase import create_client, Client

def process_events_pipeline():
    """Main workflow orchestrator."""
    try:
        # 0. Initialize Supabase Client
        print("Initializing Supabase Client...")
        supabase: Client = create_client(SUPABASE_PROJECT_URL, SUPABASE_ANON_KEY)
        
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
            
        edges = api_data['data']['results']['edges']
        limit = min(20, len(edges))
        
        for i, edge in enumerate(edges[:limit]):
            node = edge['node']
            print(f"\n--- Processing Event {i + 1} of {limit} ---")
            
            # 3. Analyze with AI
            ai_data = analyze_event_with_ai(
                client=ai_client,
                title=node.get('title', ''),
                description=node.get('description', ''),
                venue_data=node.get('venue', {}),
                url=node.get('eventUrl', '')
            )
            
            # 4. Parse & Combine
            db_record = build_database_record(node, ai_data)
            
            # 5. Insert into Supabase
            print(f"Inserting into Supabase table '{SUPABASE_TABLE_NAME}'...")
            try:
                response = supabase.table(SUPABASE_TABLE_NAME).insert(db_record).execute()
                print(f"Successfully inserted: {db_record.get('title', 'Unknown')}")
            except Exception as insert_error:
                print(f"Failed to insert '{db_record.get('title', 'Unknown')}': {insert_error}")
            
            if i < limit - 1:
                print("Pausing for 3 seconds...")
                time.sleep(3)
            
    except Exception as e:
        print(f"Pipeline failed: {e}")

if __name__ == "__main__":
    process_events_pipeline()