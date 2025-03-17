import logging
from typing import List, Dict

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_search_query(user_profile: Dict) -> str:
    """Generates a structured search query based on the user profile."""

    # Extract relevant information safely
    interests = user_profile.get("interests", []) or []
    preferences = user_profile.get("preferences", {}) or {}
    demographics = user_profile.get("demographics", {}) or {}

    skills = demographics.get("skills", []) or []
    industries = demographics.get("industries", []) or []
    
    # Build query components
    query_parts = []
    
    # Add interests
    if interests:
        query_parts.append(" OR ".join(interests))
    
    # Add role if specified
    role = preferences.get("role")
    if role:
        query_parts.append(role)
    
    # Add location if specified
    location = preferences.get("location")
    if location:
        query_parts.append(location)
    
    # Add remote/hybrid preference
    if preferences.get("remote") is True:
        query_parts.append("remote work")
    elif preferences.get("hybrid") is True:
        query_parts.append("hybrid work")
    
    # Add skills
    if skills:
        query_parts.append(" ".join(skills))
    
    # Add industries
    if industries:
        query_parts.append(" ".join(industries))

    # Combine all parts
    query = " ".join(query_parts).strip()

    # Log the generated query
    logger.info(f"Generated search query: {query}")

    return query if query else "default search query"
