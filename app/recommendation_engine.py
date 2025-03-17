# app/recommendation_engine.py
from typing import List, Dict
from functools import lru_cache
import time
from app.database import get_user_profile
from app.query_generator import generate_search_query
from app.data_sources.manager import fetch_from_all_sources
from app.relevance_scorer import calculate_relevance_scores
from app.recommendation_refiner import refine_recommendations

# In-memory cache for recommendations
recommendation_cache = {}
CACHE_EXPIRATION = 300  # 5 minutes in seconds

# Cache user profiles to reduce database queries
@lru_cache(maxsize=100)
def get_cached_user_profile(user_id: str):
    """Cache user profiles to reduce database queries"""
    return get_user_profile(user_id)

def generate_recommendations(user_id: str, limit: int = 10) -> List[Dict]:
    """
    Generate personalized recommendations for a user with caching.
    
    Args:
        user_id: Unique identifier for the user
        limit: Maximum number of recommendations to return
        
    Returns:
        List of recommendation dictionaries sorted by relevance
    """
    # Check cache first
    cache_key = f"{user_id}_{limit}"
    current_time = time.time()
    
    if cache_key in recommendation_cache:
        cached_result, timestamp = recommendation_cache[cache_key]
        # Return cached result if it's still fresh
        if current_time - timestamp < CACHE_EXPIRATION:
            return cached_result
    
    # Get user profile (using cached version)
    user_profile = get_cached_user_profile(user_id)
    
    if not user_profile:
        return []
    
    # Generate search query from user profile
    search_query = generate_search_query(user_profile)
    
    # Fetch data from multiple sources
    raw_results = fetch_from_all_sources(search_query, user_profile)
    
    # Calculate relevance scores
    scored_results = calculate_relevance_scores(raw_results, user_profile)
    
    # Refine recommendations using Gemini
    final_recommendations = refine_recommendations(scored_results, user_profile, limit)
    
    # Cache the result with timestamp
    recommendation_cache[cache_key] = (final_recommendations, current_time)
    
    return final_recommendations

def clear_user_cache(user_id: str):
    """
    Clear cached recommendations for a specific user.
    Useful after profile updates.
    
    Args:
        user_id: User ID to clear cache for
    """
    # Clear from recommendation cache
    keys_to_delete = [k for k in recommendation_cache.keys() if k.startswith(f"{user_id}_")]
    for key in keys_to_delete:
        del recommendation_cache[key]
    
    # Clear user profile cache
    get_cached_user_profile.cache_clear()
