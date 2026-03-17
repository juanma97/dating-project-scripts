import re
from typing import Optional, Tuple

def clean_text(text: Optional[str]) -> str:
    """Removes emojis, symbols, and null bytes to leave clean text."""
    if not text: 
        return ""
    
    text = re.sub(r'[\U0001f300-\U0001f650\U0001f680-\U0001f6ff\U0001f900-\U0001f9ff\U0001fa70-\U0001faff\u2600-\u26ff\u2700-\u27bf]', '', text)
    text = re.sub(r'[\x00]', '', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def parse_datetime(raw_datetime: str) -> Tuple[Optional[str], Optional[str]]:
    """Splits an ISO datetime string into separate date and time strings."""
    if not raw_datetime:
        return None, None
    parts = raw_datetime.split('T')
    if len(parts) == 2:
        return parts[0], parts[1][:8]
    return None, None