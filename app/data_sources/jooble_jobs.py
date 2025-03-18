import requests
import streamlit as st

# ✅ Load Jooble API Key from Streamlit Secrets
JOOBLE_API_KEY = st.secrets["JOOBLE_API_KEY"]  # Store API key in Streamlit secrets
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
        jobs = response.json().get("jobs", [])
        return filter_valid_jobs(jobs)  # Filter results before returning
    else:
        print(f"❌ Jooble API Error: {response.status_code} - {response.text}")
        return []

def filter_valid_jobs(jobs):
    """Filters out jobs that do not contain essential fields."""
    required_fields = ["title", "location", "type", "snippet", "link"]
    
    filtered_jobs = [
        job for job in jobs
        if all(job.get(field) for field in required_fields) and job["type"] in {"Full-time", "Part-time", "Internship"}
    ]
    
    return filtered_jobs

# ✅ Example usage
if __name__ == "__main__":
    print(fetch_jobs_from_jooble("DATA SCIENCE", "INDIA"))
