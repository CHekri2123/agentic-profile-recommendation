from typing import List, Dict
import redis
import json
import streamlit as st
from app.database import get_user_profile
from app.query_generator import generate_search_query
from app.data_sources.manager import fetch_combined_jobs
from app.relevance_scorer import calculate_relevance_scores
from app.recommendation_refiner import refine_recommendations

# ✅ Load Redis credentials from Streamlit secrets
REDIS_HOST = st.secrets["REDIS_HOST"]
REDIS_PORT = int(st.secrets["REDIS_PORT"])
REDIS_PASSWORD = st.secrets.get("REDIS_PASSWORD", None)  # Handle empty password

# ✅ Connect to Redis
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD if REDIS_PASSWORD else None,
    decode_responses=True
)

# ✅ Check Redis connection
try:
    redis_client.ping()
    print("✅ Connected to Redis successfully!")
except redis.ConnectionError as e:
    raise RuntimeError("❌ Failed to connect to Redis! Check if Redis is running.") from e

CACHE_EXPIRATION = 300  # 5 minutes

def get_cached_user_profile(user_id: str):
    """
    Retrieve user profile from Redis cache or fetch from DB if not cached.
    
    Args:
        user_id: Unique identifier for the user
        
    Returns:
        User profile dictionary or None if not found
    """
    cache_key = f"user_profile:{user_id}"
    
    # ✅ Check Redis cache
    cached_profile = redis_client.get(cache_key)
    if cached_profile:
        return json.loads(cached_profile)  # Convert back to dictionary
    
    # ✅ Fetch from database if not cached
    user_profile = get_user_profile(user_id)
    if user_profile:
        redis_client.setex(cache_key, CACHE_EXPIRATION, json.dumps(user_profile))  # Cache for 5 mins
    
    return user_profile

def generate_job_recommendations(user_id: str, query: str = None, location: str = None, limit: int = 10) -> List[Dict]:
    """
    Generate personalized job recommendations for a user with Redis caching.
    
    Args:
        user_id: Unique identifier for the user
        query: Optional search query to override generated query
        location: Optional location filter
        limit: Maximum number of recommendations to return
        
    Returns:
        List of job recommendation dictionaries sorted by relevance
    """
    # ✅ Create a cache key that includes query and location if provided
    cache_params = f"{query or 'auto'}:{location or 'any'}"
    cache_key = f"job_recommendations:{user_id}:{cache_params}:{limit}"
    
    # ✅ Check Redis cache first
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)  # Return cached result
    
    # ✅ Get user profile (using Redis cache)
    user_profile = get_cached_user_profile(user_id)
    
    if not user_profile:
        return []
    
    # ✅ Use provided query or generate from user profile
    search_query = query if query else generate_search_query(user_profile)
    
    # ✅ Use provided location or get from user profile
    search_location = location if location else user_profile.get("preferences", {}).get("location", "USA")
    
    # ✅ Fetch jobs from multiple sources
    raw_jobs = fetch_combined_jobs(search_query, search_location, limit * 2)  # Fetch more than needed for better ranking
    
    # ✅ Calculate relevance scores
    scored_jobs = calculate_relevance_scores(raw_jobs, user_profile)
    
    # ✅ Refine recommendations using Gemini
    final_recommendations = refine_recommendations(scored_jobs, user_profile, limit)
    
    # ✅ Cache the result in Redis
    redis_client.setex(cache_key, CACHE_EXPIRATION, json.dumps(final_recommendations))
    
    return final_recommendations

def clear_user_job_cache(user_id: str):
    """
    Clear cached job recommendations for a specific user.
    Useful after profile updates.
    
    Args:
        user_id: User ID to clear cache for
    """
    # ✅ Delete job recommendation cache
    keys_to_delete = redis_client.keys(f"job_recommendations:{user_id}:*")
    for key in keys_to_delete:
        redis_client.delete(key)
    
    # ✅ Delete user profile cache
    redis_client.delete(f"user_profile:{user_id}")
