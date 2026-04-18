import requests
import json
from datetime import datetime
from google import genai
from google.genai import types
from bs4 import BeautifulSoup
from config import SUPABASE_PROJECT_URL

CITA2_URL = "https://www.cita2.net/eventos.html"

def fetch_and_parse_cita2_events(client: genai.Client) -> list[dict]:
    print(f"Fetching HTML from {CITA2_URL}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(CITA2_URL, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    text_content = soup.get_text(separator=' | ', strip=True)
    
    print(f"Content parsed. Text length: {len(text_content)} characters. Sending to Gemini...")
    
    current_date = datetime.now()
    
    prompt = f"""
    You are an expert data extraction algorithm. Read the following text extracted from the 'Cita2' speed dating website.
    
    Today's date is: {current_date.strftime('%Y-%m-%d')}. Use this to determine the correct year for the events.
    
    IMPORTANT RULES FOR EXTRACTION:
    1. EXTRACT STRICTLY 'Speed Dating' or 'Citas rápidas' events.
    2. COMPLETELY EXCLUDE any events that are purely "Cena desconocidos" or "Cenas" unless they explicitly state it involves Speed Dating. Do not include them in the output.
    3. If multiple age groups are listed for the exact same date, time, and venue, DO NOT combine them. Treat each specific age range as a completely SEPARATE event record in the JSON array.
    
    Return a STRICTLY FORMATTED JSON array of objects, where each object matches this schema exactly:
    - 'title': "Speed Dating en Madrid" (or a descriptive title based on the event)
    - 'description': Detailed summary of the event. Write in Spanish. Ensure it is PostgreSQL UTF-8 safe. No emojis.
    - 'date': The date in YYYY-MM-DD format (convert the Spanish dates like 'Viernes 24 abril' to the correct upcoming date using the current year/next year context).
    - 'time': The time in HH:MM format (e.g., '20:15', '20:00').
    - 'city': "Madrid"
    - 'place': Specific name of the venue (e.g. "Triada Malasaña").
    - 'street_name': The street name of the venue (e.g. "Corredera Baja de San Pablo").
    - 'street_number': The street number (e.g. "17").
    - 'organizer': "Cita2"
    - 'source': "Cita2"
    - 'source_url': "{CITA2_URL}"
    - 'image': null
    - 'min_age': Integer. Minimum age for this specific event/group.
    - 'max_age': Integer. Maximum age for this specific event/group.
    - 'sexual_orientation': 'straight', 'gay', 'lesbian', or 'all' based on text (e.g. 'Speed Dating Gay Chicos'). If not explicitly specified, infer from prices: if both girls and boys prices are mentioned, it is 'straight'. If ONLY boys price is mentioned, it is 'gay'. If ONLY girls price is mentioned, it is 'lesbian'.
    - 'girls_price': float or null.
    - 'boys_price': float or null.
    
    CRITICAL DATABASE CONSTRAINT: Ensure all text strings are strictly compatible with PostgreSQL UTF-8 encoding. 
    Do NOT include null bytes (\\x00). Absolutely NO emojis or emoticons should be included.
    
    Below is the web content:
    {text_content}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        events = json.loads(response.text)
        
        # Ensure we add created_at and set default image
        for event in events:
            event['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if not event.get('image'):
                event['image'] = f"{SUPABASE_PROJECT_URL}/storage/v1/object/public/images/default.png"
            
        print(f"Successfully extracted {len(events)} grouped events.")
        return events
        
    except Exception as e:
        print(f"Error during Gemini analysis: {e}")
        return []
