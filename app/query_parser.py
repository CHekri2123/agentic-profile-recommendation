import requests
import json
import uuid
import re
import streamlit as st
from typing import Optional, List, Dict
from pydantic import BaseModel, ValidationError
from app.database import save_user_profile as save_candidate_profile

# ✅ Use Streamlit's secret management
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# ✅ Updated Candidate Profile Schema
class CandidateProfile(BaseModel):
    user_id: str
    name: str
    experience: int  # Years of experience
    skills: List[str]
    past_jobs: List[str]
    education: Optional[str]
    resume_link: Optional[str]
    preferences: Dict

# ✅ Extract JSON from Gemini's Response (Handles Markdown Blocks)
def extract_json(text: str) -> Optional[dict]:
    """Extract JSON from Gemini's response."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None

# ✅ Parse Query into Structured Candidate Profile
def parse_query_with_gemini(user_input: str) -> dict:
    """Parses a user job query into a structured candidate profile using Gemini API."""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}

    prompt = f"""
    Extract structured job-seeking information from this query: '{user_input}'.

    Return a **valid JSON** that exactly follows this schema:

    {{
        "user_id": "{uuid.uuid4().hex}",
        "name": "if mentioned, else 'user_<UUID>'",
        "experience": "if mentioned in years, else 0",
        "skills": ["list of technical and job-relevant skills"],
        "past_jobs": ["list of past job titles if mentioned, else empty"],
        "education": "highest degree if mentioned, else null",
        "resume_link": "if user mentioned a resume or LinkedIn, extract URL, else null",
        "preferences": {{
            "job_roles": ["desired job roles"],
            "location": "preferred location or 'remote'",
            "employment_type": "full-time, part-time, contract, internship",
            "salary_expectation": "if mentioned, else null",
            "industry": "desired industry if specified, else null"
        }}
    }}

    **Strictly return only valid JSON.**
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()

        try:
            parsed_text = data["candidates"][0]["content"]["parts"][0].get("text", "")
            structured_data = extract_json(parsed_text)

            if structured_data:
                # ✅ Ensure `user_id` is generated if missing
                structured_data["user_id"] = structured_data.get("user_id", uuid.uuid4().hex)

                # ✅ Generate a shorter default username
                if not structured_data.get("name") or structured_data["name"].startswith("user_"):
                    structured_data["name"] = f"user_{structured_data['user_id'][:8]}"

                # ✅ Ensure required fields exist
                structured_data.setdefault("experience", 0)
                structured_data.setdefault("skills", [])
                structured_data.setdefault("past_jobs", [])
                structured_data.setdefault("education", None)
                structured_data.setdefault("resume_link", None)
                structured_data.setdefault("preferences", {})

                # ✅ Ensure proper data types for job preferences
                structured_data["preferences"]["job_roles"] = structured_data["preferences"].get("job_roles", [])
                structured_data["preferences"]["location"] = structured_data["preferences"].get("location", "remote")
                structured_data["preferences"]["employment_type"] = structured_data["preferences"].get("employment_type", "full-time")
                structured_data["preferences"]["salary_expectation"] = structured_data["preferences"].get("salary_expectation")
                structured_data["preferences"]["industry"] = structured_data["preferences"].get("industry")

                # ✅ Auto-set `job_roles = []` if not specified
                if not structured_data["preferences"]["job_roles"]:
                    structured_data["preferences"]["job_roles"] = ["Software Engineer"]  # Default role

                try:
                    # ✅ Validate using Pydantic
                    candidate_profile = CandidateProfile(**structured_data)

                    # ✅ Store in MongoDB
                    save_candidate_profile(candidate_profile.model_dump())

                    return candidate_profile.model_dump()  # Return validated dictionary
                except ValidationError as validation_error:
                    return {"error": f"Pydantic validation error: {validation_error}"}
            else:
                return {"error": "Parsing failed: API response does not contain valid JSON"}

        except Exception as e:
            return {"error": f"Parsing failed: {str(e)}"}
    
    else:
        return {"error": f"API Error: {response.status_code}, Response: {response.text}"}
