import json
from typing import Dict, Any
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

def get_gemini_client() -> genai.Client:
    """Initializes and returns the Gemini client."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
    return genai.Client(api_key=GEMINI_API_KEY)

def analyze_event_with_ai(client: genai.Client, title: str, description: str, venue_data: Dict, url: str) -> Dict[str, Any]:
    """Sends event text to Gemini and forces a Postgres-safe JSON return."""
    raw_context = f"""
    EVENT TITLE: {title}
    EVENT URL: {url}
    RAW VENUE DATA: {venue_data}
    
    FULL DESCRIPTION BOX:
    {description}
    """
    
    prompt = f"""
    You are an expert data extraction algorithm. Read the following event information.
    
    CRITICAL DATABASE CONSTRAINT: Ensure all text strings are strictly compatible with PostgreSQL UTF-8 encoding. 
    Do NOT include null bytes (\\x00), invisible control characters, or unsupported symbols. Keep text clean.
    Absolutely NO emojis or emoticons should be included.
    
    Event Information:
    {raw_context}
    
    Extract the following data and return it STRICTLY as a JSON object:
    2. 'place': The specific name of the bar/venue.
    3. 'city': The city where the event takes place.
    4. 'description': A detailed SUMMARY of the event in Spanish, 2-3 paragraphs. SUMMARIZE in your own words. No emojis.
    5. 'min_age': Integer. Minimum age. Return null if not specified.
    6. 'max_age': Integer. Maximum age. Return null if not specified.
    7. 'sexual_orientation': Sexual orientation target. STRICTLY one of: 'straight', 'gay', 'lesbian', 'bisexual', 'all'. Default 'all'. If the event doesn't explicitly specify what type of relationships it is for, infer from prices: if both girls_price and boys_price are mentioned, it is 'straight'. If ONLY boys_price is mentioned, it is 'gay'. If ONLY girls_price is mentioned, it is 'lesbian'.
    8. 'girls_price': Float. Price for women. 0.0 if free. Return null if unknown.
    9. 'boys_price': Float. Price for men. 0.0 if free. Return null if unknown.
    10. 'street_name': The street name of the venue's address. Return null if not found.
    11. 'street_number': The street number of the venue's address. Return null if not found.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
        
    except Exception as e:
        print(f"Error during Gemini analysis: {e}")
        return {
            "place": "Unknown place", "city": "Unknown city",
            "description": "Description could not be generated.",
            "min_age": None, "max_age": None, "sexual_orientation": "all",
            "girls_price": None, "boys_price": None,
            "street_name": None, "street_number": None
        }