import os
import time
from config import DEFAULT_LATITUDE, DEFAULT_LONGITUDE, SUPABASE_PROJECT_URL, SUPABASE_ANON_KEY, SUPABASE_TABLE_NAME
from meetup.client import fetch_meetup_events
from gemini.analyzer import get_gemini_client, analyze_event_with_ai
from meetup.parser import build_database_record
from bedazzling.client import fetch_and_parse_bedazzling_events
from cita2.client import fetch_and_parse_cita2_events
from ladolcecita.client import fetch_and_parse_ladolcecita_events
from supabase_db.deduplicator import remove_duplicates
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
        
        target_city = "Madrid"
        
        # 2. Fetch Data from API
        print("Fetching data from Meetup...")
        api_data = fetch_meetup_events(
            query="speed dating", 
            city=target_city, 
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
            
            # 5. Filter by city and Check for missing fields
            if (db_record.get('city') or '').lower() != target_city.lower():
                print(f"Skipping event '{db_record.get('title', 'Unknown')}' because it is not in {target_city} (Found: {db_record.get('city', 'Unknown')})")
                continue
                
            mandatory_fields = ["date", "time", "city", "street_name", "street_number", "source_url"]
            missing_mandatory = [k for k in mandatory_fields if db_record.get(k) in [None, ""]]
            
            if missing_mandatory:
                print(f"Skipping event '{db_record.get('title', 'Unknown')}' due to missing mandatory fields: {', '.join(missing_mandatory)}")
            else:
                print(f"Inserting into Supabase table '{SUPABASE_TABLE_NAME}'...")
                try:
                    response = supabase.table(SUPABASE_TABLE_NAME).insert(db_record).execute()
                    print(f"Successfully inserted: {db_record.get('title', 'Unknown')}")
                except Exception as insert_error:
                    print(f"Failed to insert '{db_record.get('title', 'Unknown')}': {insert_error}")
            
            if i < limit - 1:
                print("Pausing for 3 seconds...")
                time.sleep(3)
        
        # 6. Fetch and Process Bedazzling Events
        print("\n--- Starting Bedazzling Events Processing ---")
        bedazzling_events = fetch_and_parse_bedazzling_events(ai_client)
        if bedazzling_events:
            for i, db_record in enumerate(bedazzling_events):
                print(f"\n--- Processing Bedazzling Event {i + 1} of {len(bedazzling_events)} ---")
                
                if (db_record.get('city') or '').lower() != target_city.lower():
                    print(f"Skipping event '{db_record.get('title', 'Unknown')}' because it is not in {target_city}")
                    continue
                    
                mandatory_fields = ["date", "time", "city", "street_name", "street_number", "source_url"]
                missing_mandatory = [k for k in mandatory_fields if db_record.get(k) in [None, ""]]
                
                if missing_mandatory:
                    print(f"Skipping event '{db_record.get('title', 'Unknown')}' due to missing mandatory fields: {', '.join(missing_mandatory)}")
                else:
                    print(f"Inserting into Supabase table '{SUPABASE_TABLE_NAME}'...")
                    try:
                        response = supabase.table(SUPABASE_TABLE_NAME).insert(db_record).execute()
                        print(f"Successfully inserted: {db_record.get('title', 'Unknown')} at {db_record.get('date')} {db_record.get('time')}")
                    except Exception as insert_error:
                        print(f"Failed to insert '{db_record.get('title', 'Unknown')}': {insert_error}")
        else:
            print("No Bedazzling events found or error occurred.")

        # 7. Fetch and Process Cita2 Events
        print("\n--- Starting Cita2 Events Processing ---")
        cita2_events = fetch_and_parse_cita2_events(ai_client)
        if cita2_events:
            for i, db_record in enumerate(cita2_events):
                print(f"\n--- Processing Cita2 Event {i + 1} of {len(cita2_events)} ---")
                
                if (db_record.get('city') or '').lower() != target_city.lower():
                    print(f"Skipping event '{db_record.get('title', 'Unknown')}' because it is not in {target_city}")
                    continue
                    
                mandatory_fields = ["date", "time", "city", "street_name", "street_number", "source_url"]
                missing_mandatory = [k for k in mandatory_fields if db_record.get(k) in [None, ""]]
                
                if missing_mandatory:
                    print(f"Skipping event '{db_record.get('title', 'Unknown')}' due to missing mandatory fields: {', '.join(missing_mandatory)}")
                else:
                    print(f"Inserting into Supabase table '{SUPABASE_TABLE_NAME}'...")
                    try:
                        response = supabase.table(SUPABASE_TABLE_NAME).insert(db_record).execute()
                        print(f"Successfully inserted: {db_record.get('title', 'Unknown')} at {db_record.get('date')} {db_record.get('time')}")
                    except Exception as insert_error:
                        print(f"Failed to insert '{db_record.get('title', 'Unknown')}': {insert_error}")
        else:
            print("No Cita2 events found or error occurred.")

        # 8. Fetch and Process LaDolceCita Events
        print("\n--- Starting LaDolceCita Events Processing ---")
        ladolcecita_events = fetch_and_parse_ladolcecita_events(ai_client)
        if ladolcecita_events:
            for i, db_record in enumerate(ladolcecita_events):
                print(f"\n--- Processing LaDolceCita Event {i + 1} of {len(ladolcecita_events)} ---")
                
                if (db_record.get('city') or '').lower() != target_city.lower():
                    print(f"Skipping event '{db_record.get('title', 'Unknown')}' because it is not in {target_city}")
                    continue
                    
                mandatory_fields = ["date", "time", "city", "street_name", "street_number", "source_url"]
                missing_mandatory = [k for k in mandatory_fields if db_record.get(k) in [None, ""]]
                
                if missing_mandatory:
                    print(f"Skipping event '{db_record.get('title', 'Unknown')}' due to missing mandatory fields: {', '.join(missing_mandatory)}")
                else:
                    print(f"Inserting into Supabase table '{SUPABASE_TABLE_NAME}'...")
                    try:
                        response = supabase.table(SUPABASE_TABLE_NAME).insert(db_record).execute()
                        print(f"Successfully inserted: {db_record.get('title', 'Unknown')} at {db_record.get('date')} {db_record.get('time')}")
                    except Exception as insert_error:
                        print(f"Failed to insert '{db_record.get('title', 'Unknown')}': {insert_error}")
        else:
            print("No LaDolceCita events found or error occurred.")

        # 9. deduplicate records
        remove_duplicates(supabase, SUPABASE_TABLE_NAME)
            
    except Exception as e:
        print(f"Pipeline failed: {e}")

if __name__ == "__main__":
    process_events_pipeline()