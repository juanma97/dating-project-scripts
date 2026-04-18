import requests
import json
from datetime import datetime
from google import genai
from google.genai import types
from bs4 import BeautifulSoup
from config import SUPABASE_PROJECT_URL

LADOLCECITA_MAIN_URL = "https://www.ladolcecita.es/eventos/"

def fetch_and_parse_ladolcecita_events(client: genai.Client) -> list[dict]:
    print(f"Fetching HTML from {LADOLCECITA_MAIN_URL}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(LADOLCECITA_MAIN_URL, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch {LADOLCECITA_MAIN_URL}")
        return []
        
    soup = BeautifulSoup(response.text, 'html.parser')
    event_urls = set()
    for a in soup.select('a[href*="/evento/"]'):
        event_urls.add(a['href'])
        
    print(f"Found {len(event_urls)} unique event links.")
    
    combined_texts = []
    
    for url in event_urls:
        print(f"Fetching details from {url}...")
        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                s = BeautifulSoup(res.text, 'html.parser')
                text_content = s.get_text(separator=' | ', strip=True)
                combined_texts.append(f"EVENT URL: {url}\nCONTENT:\n{text_content}")
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            
    if not combined_texts:
        return []
        
    full_text = "\n\n---\n\n".join(combined_texts)
    
    print(f"Content parsed. Sending to Gemini...")
    
    current_date = datetime.now()
    
    prompt = f"""
    You are an expert data extraction algorithm. Read the following text extracted from multiple event pages of the 'LaDolceCita' speed dating website.
    Each event has its EVENT URL followed by its CONTENT.
    
    Today's date is: {current_date.strftime('%Y-%m-%d')}. Use this to determine the correct year for the events.
    
    IMPORTANT RULES FOR EXTRACTION:
    1. EXTRACT STRICTLY 'Speed Dating' or 'Citas rápidas' events.
    2. Be careful combining age groups. If multiple age groups are listed for the exact same date and venue within the same page, separate them. If only one age group is present per page, extract it directly.
    3. Check the "Genero" or available options in the event text to determine if it's for boys and girls, or just one.
    
    Return a STRICTLY FORMATTED JSON array of objects, where each object matches this schema exactly:
    - 'title': "Speed Dating en Madrid" (or a descriptive title based on the event)
    - 'description': Detailed summary of the event. Write in Spanish. Ensure it is PostgreSQL UTF-8 safe. No emojis.
    - 'date': The date in YYYY-MM-DD format (convert Spanish dates considering the current/next year).
    - 'time': The time in HH:MM format (e.g., '19:00').
    - 'city': City name (usually "Madrid").
    - 'place': Specific name of the venue (e.g. "Restaurante La Clave").
    - 'street_name': The street name of the venue (e.g. "Calle Velazquez").
    - 'street_number': The street number (e.g. "22").
    - 'organizer': "LaDolceCita"
    - 'source': "LaDolceCita"
    - 'source_url': The EVENT URL for the specific event you are parsing.
    - 'image': null
    - 'min_age': Integer. Minimum age for this specific event/group.
    - 'max_age': Integer. Maximum age for this specific event/group.
    - 'sexual_orientation': 'straight', 'gay', 'lesbian', or 'all'. If not explicitly specified, infer from the "Genero" options or prices: if it mentions options/prices for both girls and boys, it is 'straight'. If ONLY boys price/option is mentioned, it is 'gay'. If ONLY girls price/option is mentioned, it is 'lesbian'.
    - 'girls_price': float or null. Extract from the price listed (e.g., 22.00).
    - 'boys_price': float or null. Extract from the price listed.
    
    CRITICAL DATABASE CONSTRAINT: Ensure all text strings are strictly compatible with PostgreSQL UTF-8 encoding. 
    Do NOT include null bytes (\\x00). Absolutely NO emojis or emoticons should be included.
    
    Below is the combined web content:
    {full_text}
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
            
        print(f"Successfully extracted {len(events)} LaDolceCita events.")
        return events
        
    except Exception as e:
        print(f"Error during Gemini analysis: {e}")
        return []
