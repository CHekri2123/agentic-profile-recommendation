import requests
import os
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY")  # Store API key in environment variable
JOOBLE_API_URL = "https://jooble.org/api/"

def fetch_jobs_from_jooble(query, location="USA", results=1):
    """Fetch job listings from Jooble API"""
    url = f"{JOOBLE_API_URL}{JOOBLE_API_KEY}"
    payload = {
        "keywords": query,
        "location": location,
        "page": 1,
        "searchMode": 1,
        "results": results
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json().get("jobs", [])
    else:
        print(f"Jooble API Error: {response.status_code} - {response.text}")
        return []

print(fetch_jobs_from_jooble("DATA SCIENCE","INDIA"))