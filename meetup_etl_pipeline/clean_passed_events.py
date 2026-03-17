import os
from datetime import datetime
from supabase import create_client, Client
from config import SUPABASE_PROJECT_URL, SUPABASE_ANON_KEY, SUPABASE_TABLE_NAME

def clean_passed_events():
    """Removes events from Supabase that have already passed based on current date and time."""
    print("Initializing Supabase Client for cleaning...")
    
    if not SUPABASE_PROJECT_URL or not SUPABASE_ANON_KEY or not SUPABASE_TABLE_NAME:
        print("Missing Supabase configuration. Please check your environment variables.")
        return

    supabase: Client = create_client(SUPABASE_PROJECT_URL, SUPABASE_ANON_KEY)
    
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    
    print(f"Current Date: {current_date}, Current Time: {current_time}")

    # 1. Delete events where the date is older than today
    print(f"Deleting events from before {current_date}...")
    try:
        response_date = supabase.table(SUPABASE_TABLE_NAME).delete().lt('date', current_date).execute()
        deleted_count_date = len(response_date.data) if hasattr(response_date, 'data') and response_date.data else 0
        print(f"Deleted {deleted_count_date} events from previous days.")
    except Exception as e:
        print(f"Failed to delete older events: {e}")

    # 2. Delete events from today where the time is older than the current time
    print(f"Deleting passed events from today (before {current_time})...")
    try:
        response_time = supabase.table(SUPABASE_TABLE_NAME).delete().eq('date', current_date).lt('time', current_time).execute()
        deleted_count_time = len(response_time.data) if hasattr(response_time, 'data') and response_time.data else 0
        print(f"Deleted {deleted_count_time} passed events from today.")
    except Exception as e:
        print(f"Failed to delete today's passed events: {e}")
        
    print("Cleanup completed.")

if __name__ == "__main__":
    clean_passed_events()
