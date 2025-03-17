import requests
import json
import uuid
import re
import streamlit as st
from typing import Optional, List, Dict
from pydantic import BaseModel, ValidationError
from app.database import save_user_profile  # ✅ Removed the dot for consistency

# ✅ Use Streamlit's secret management
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

class UserProfile(BaseModel):
    user_id: str
    name: str
    interests: List[str]
    preferences: Dict
    demographics: Dict

def extract_json(text: str) -> Optional[dict]:
    """Extract JSON from Gemini's response (handles Markdown code blocks)."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None

def parse_query_with_gemini(user_input: str) -> dict:
    """Parses a user query into a structured profile using Gemini API."""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}

    prompt = f"""
    Extract structured information from this query: '{user_input}'.

    Return a **valid JSON** that exactly follows this schema:

    {{
    "user_id": "{uuid.uuid4().hex}",
    "name": "if mentioned, use the name, else generate a default username like user_<UUID>",
    "interests": ["list of job-relevant interests such as AI, finance, gaming, healthcare, programming. Ignore food, travel, and personal hobbies."],
    "preferences": {{
        "location": "if mentioned, else null",
        "remote": true/false/null,
        "hybrid": true/false/null,
        "sponsorship": true/false/null,
        "role": "if mentioned, else null",
        "posted_days_ago": "if mentioned, else null"
    }},
    "demographics": {{
        "skills": ["list of technical skills if mentioned, else empty list"],
        "industries": ["list of industries if mentioned, else empty list"]
    }}
    }}

    **Strictly adhere to this format. Do not include any extra text, explanations, or other formatting. Ensure that "remote", "hybrid", and "sponsorship" fields are boolean values (True/False) or null. Return ONLY valid JSON.**
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()

        try:
            parsed_text = data["candidates"][0]["content"]["parts"][0].get("text", "")
            structured_data = extract_json(parsed_text)

            if structured_data:
                # ✅ Ensure all required fields are present
                structured_data["user_id"] = structured_data.get("user_id", uuid.uuid4().hex)
                
                # ✅ Generate a shorter default username
                if not structured_data.get("name") or structured_data["name"].startswith("user_"):
                    structured_data["name"] = f"user_{structured_data['user_id'][:8]}"

                structured_data.setdefault("interests", [])
                structured_data.setdefault("preferences", {})
                structured_data.setdefault("demographics", {})

                # ✅ Enforce correct data types (Booleans for remote, hybrid, sponsorship)
                structured_data["preferences"]["remote"] = structured_data["preferences"].get("remote")
                structured_data["preferences"]["hybrid"] = structured_data["preferences"].get("hybrid")
                structured_data["preferences"]["sponsorship"] = structured_data["preferences"].get("sponsorship")

                # ✅ Ensure `remote` & `hybrid` are mutually exclusive
                if structured_data["preferences"].get("remote") is True:
                    structured_data["preferences"]["hybrid"] = False

                # ✅ Auto-set `posted_days_ago = 0` if urgency is detected
                if any(word in user_input.lower() for word in ["immediately", "right now", "urgent", "asap"]):
                    structured_data["preferences"]["posted_days_ago"] = 0

                try:
                    # Validate using Pydantic
                    user_profile = UserProfile(**structured_data)

                    # ✅ Store in MongoDB
                    save_user_profile(user_profile.model_dump())

                    return user_profile.model_dump()  # Return validated dictionary
                except ValidationError as validation_error:
                    return {"error": f"Pydantic validation error: {validation_error}"}
            else:
                return {"error": "Parsing failed: API response does not contain valid JSON"}

        except Exception as e:
            return {"error": f"Parsing failed: {str(e)}"}
    
    else:
        return {"error": f"API Error: {response.status_code}, Response: {response.text}"}
