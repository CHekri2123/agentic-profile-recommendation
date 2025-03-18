import logging
from typing import Dict

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_search_query(user_profile: Dict) -> str:
    """Generates a structured job search query based on the user profile."""

    # Extract relevant fields safely
    interests = user_profile.get("interests", []) or []
    preferences = user_profile.get("preferences", {}) or {}
    demographics = user_profile.get("demographics", {}) or {}

    skills = demographics.get("skills", []) or []
    industries = demographics.get("industries", []) or []
    
    # Build query components
    query_parts = []

    # 🔹 Prioritize Role
    role = preferences.get("role")
    if role:
        query_parts.append(f'"{role}"')

    # 🔹 Add Skills (Most Important for Job Search)
    if skills:
        query_parts.append(" ".join(f'"{skill}"' for skill in skills))

    # 🔹 Add Interests
    if interests:
        query_parts.append(", ".join(f'"{interest}"' for interest in interests))

    # 🔹 Add Location (if available)
    location = preferences.get("location")
    if location:
        query_parts.append(f'"{location}"')

    # 🔹 Add Work Preferences
    remote = preferences.get("remote")
    hybrid = preferences.get("hybrid")

    if remote is True:
        query_parts.append('"remote work"')
    elif hybrid is True:
        query_parts.append('"hybrid work"')

    # 🔹 Add Industries
    if industries:
        query_parts.append(" ".join(f'"{industry}"' for industry in industries))

    # 🔹 Combine all parts
    query = " ".join(query_parts).strip()

    # Log the generated query
    logger.info(f"Generated search query: {query}")

    return query if query else "default search query"
