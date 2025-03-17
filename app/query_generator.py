# app/query_generator.py
from typing import List, Dict

def generate_search_query(user_profile: Dict) -> str:

    # Extract relevant information
    interests = user_profile.get("interests", []) or []
    preferences = user_profile.get("preferences", {}) or {}
    demographics = user_profile.get("demographics", {}) or {}
    skills = demographics.get("skills", [])
    industries = demographics.get("industries", [])
    
    # Build query components
    query_parts = []
    
    # Add interests
    if interests:
        query_parts.append(" OR ".join(interests))
    
    # Add role if specified
    if preferences.get("role"):
        query_parts.append(preferences["role"])
    
    # Add location if specified
    if preferences.get("location"):
        query_parts.append(preferences["location"])
    
    # Add remote/hybrid preference
    if preferences.get("remote") is True:
        query_parts.append("remote work")
    elif preferences.get("hybrid") is True:
        query_parts.append("hybrid work")
    
    # Add skills
    if skills:
        query_parts.append(" ".join(skills))  # No limit on skills
    
    # Add industries
    if industries:
        query_parts.append(" ".join(industries))  # No limit on industries
    
    # Combine all parts
    query = " ".join(query_parts)
    
    return query
