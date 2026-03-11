from datetime import datetime
from typing import Dict, Any
from text_utils import clean_text, parse_datetime

def build_database_record(node: Dict, ai_data: Dict) -> Dict[str, Any]:
    """Combines raw API data and AI-extracted data into the final DB schema."""
    venue_raw = node.get('venue', {}) or {}
    group_raw = node.get('group', {}) or {}
    featured_photo = node.get('featuredEventPhoto') or {}
    
    event_date, event_time = parse_datetime(node.get('dateTime', ''))
    
    record = {
        "title": clean_text(node.get('title', 'No title')) or "No title",
        "description": clean_text(ai_data.get('description', '')),
        "date": event_date,
        "time": event_time,
        "city": ai_data.get('city'),
        "place": ai_data.get('place'),
        "street_name": ai_data.get('street_name'),
        "street_number": ai_data.get('street_number'),
        "organizer": group_raw.get('name', 'Unknown organizer'),
        "source": "Meetup",
        "source_url": node.get('eventUrl', ''),
        "image": featured_photo.get('highResUrl', ''),
        "min_age": ai_data.get('min_age'),
        "max_age": ai_data.get('max_age'),
        "sexual_orientation": ai_data.get('sexual_orientation'),
        "girls_price": ai_data.get('girls_price'),
        "boys_price": ai_data.get('boys_price'),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return record