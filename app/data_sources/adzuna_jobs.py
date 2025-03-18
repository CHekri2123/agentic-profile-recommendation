import requests
import streamlit as st

# ✅ Load Adzuna API Credentials from Streamlit Secrets
ADZUNA_API_ID = st.secrets["ADZUNA_API_ID"]  # Store API ID in Streamlit secrets
ADZUNA_API_KEY = st.secrets["ADZUNA_API_KEY"]  # Store API Key in Streamlit secrets
ADZUNA_API_URL = "https://api.adzuna.com/v1/api/jobs"

def fetch_jobs_from_adzuna(query, location="USA", results=10):
    """Fetch job listings from Adzuna API"""
    url = f"{ADZUNA_API_URL}/us/search/1"
    params = {
        "app_id": ADZUNA_API_ID,
        "app_key": ADZUNA_API_KEY,
        "results_per_page": results,
        "what": query,
        "where": location
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        jobs = response.json().get("results", [])
        return filter_valid_jobs(jobs)  # Filter results before returning
    else:
        print(f"❌ Adzuna API Error: {response.status_code} - {response.text}")
        return []

def filter_valid_jobs(jobs):
    """Filters out jobs that do not contain essential fields."""
    required_fields = ["title", "location", "contract_time", "description", "redirect_url"]

    filtered_jobs = [
        {
            "title": job["title"],
            "location": job["location"]["display_name"] if "location" in job and "display_name" in job["location"] else "Unknown",
            "type": convert_job_type(job.get("contract_time")),
            "snippet": job["description"],
            "link": job["redirect_url"]
        }
        for job in jobs
        if all(job.get(field) for field in required_fields)
    ]
    
    return filtered_jobs

def convert_job_type(contract_time):
    """Converts Adzuna contract time to standardized job types."""
    mapping = {
        "full_time": "Full-time",
        "part_time": "Part-time",
        "intern": "Internship"
    }
    return mapping.get(contract_time, "Other")

# ✅ Example usage
if __name__ == "__main__":
    print(fetch_jobs_from_adzuna("Software Engineer", "USA"))
