import os
from dotenv import load_dotenv

# This line forces Python to read your local .env file
load_dotenv()

# Load the API key securely.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MEETUP_GRAPHQL_URL = "https://www.meetup.com/gql2"

# Default search parameters
DEFAULT_LATITUDE = 40.41999816894531
DEFAULT_LONGITUDE = -3.7100000381469727

# Supabase Configurations
SUPABASE_PROJECT_URL = os.getenv("SUPABASE_PROJECT_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_TABLE_NAME = os.getenv("SUPABASE_TABLE_NAME")