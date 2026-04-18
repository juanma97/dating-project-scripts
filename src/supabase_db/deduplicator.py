from typing import List, Dict, Any
from supabase import Client

def remove_duplicates(supabase: Client, table_name: str):
    """
    Fetches all records from the specified table and removes duplicates
    based on city, street_name, street_number, date, and time.
    """
    print(f"\n--- Removing duplicates from table '{table_name}' ---")
    try:
        # 1. Fetch all records
        response = supabase.table(table_name).select("*").execute()
        all_records = response.data
        
        if not all_records:
            print("No records found in database.")
            return

        seen = {}
        duplicates_ids = []
        
        # 2. Identify duplicates
        for record in all_records:
            # Combination of fields that defines a duplicate
            key = (
                record.get('city'), 
                record.get('street_name'), 
                record.get('street_number'), 
                record.get('date'), 
                record.get('time'),
                record.get('min_age'),
                record.get('max_age')
            )
            
            if key in seen:
                duplicates_ids.append(record.get('id'))
            else:
                seen[key] = record.get('id')
        
        # 3. Delete duplicates
        if duplicates_ids:
            print(f"Found {len(duplicates_ids)} duplicates. Deleting...")
            for dup_id in duplicates_ids:
                supabase.table(table_name).delete().eq("id", dup_id).execute()
            print("Duplicates removed successfully.")
        else:
            print("No duplicates found.")
            
    except Exception as e:
        print(f"Error during deduplication: {e}")
        raise e
