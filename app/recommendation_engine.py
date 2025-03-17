from typing import List, Dict
import time
import redis
import json
import streamlit as st
from app.database import get_user_profile
from app.query_generator import generate_search_query
from app.data_sources.manager import fetch_from_all_sources
from app.relevance_scorer import calculate_relevance_scores
from app.recommendation_refiner import refine_recommendations

# ✅ Connect to Redis using Streamlit secrets
redis_client = redis.Redis(
    host=st.secrets["REDIS_HOST"],
    port=st.secrets["REDIS_PORT"],
    password=st.secrets["REDIS_PASSWORD"],
    decode_responses=True  # Ensures we get strings, not bytes
)

CACHE_EXPIRATION = 300  # 5 minutes in seconds

def get_cached_user_profile(user_id: str):
    """
    Retrieve user profile from Redis cache or fetch from DB if not cached.
    
    Args:
        user_id: Unique identifier for the user
        
    Returns:
        User profile dictionary or None if not found
    """
    cache_key = f"user_profile:{user_id}"
    
    # Check Redis cache
    cached_profile = redis_client.get(cache_key)
    if cached_profile:
        return json.loads(cached_profile)  # Convert back to dictionary
    
    # Fetch from database if not cached
    user_profile = get_user_profile(user_id)
    if user_profile:
        redis_client.setex(cache_key, CACHE_EXPIRATION, json.dumps(user_profile))  # Cache for 5 mins
    
    return user_profile

def generate_recommendations(user_id: str, limit: int = 10) -> List[Dict]:
    """
    Generate personalized recommendations for a user with Redis caching.
    
    Args:
        user_id: Unique identifier for the user
        limit: Maximum number of recommendations to return
        
    Returns:
        List of recommendation dictionaries sorted by relevance
    """
    cache_key = f"recommendations:{user_id}:{limit}"
    
    # Check Redis cache first
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)  # Return cached result
    
    # Get user profile (using Redis cache)
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
    
    # Cache the result in Redis
    redis_client.setex(cache_key, CACHE_EXPIRATION, json.dumps(final_recommendations))
    
    return final_recommendations

def clear_user_cache(user_id: str):
    """
    Clear cached recommendations for a specific user.
    Useful after profile updates.
    
    Args:
        user_id: User ID to clear cache for
    """
    # Delete recommendation cache
    keys_to_delete = redis_client.keys(f"recommendations:{user_id}:*")
    for key in keys_to_delete:
        redis_client.delete(key)
    
    # Delete user profile cache
    redis_client.delete(f"user_profile:{user_id}")
