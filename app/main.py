import uvicorn
import json
import logging
import streamlit as st
from fastapi import FastAPI, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from functools import lru_cache
import redis

from app.query_parser import parse_query_with_gemini
from app.database import save_user_profile, get_user_profile
from app.recommendation_engine import generate_recommendations

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration from Streamlit secrets
try:
    REDIS_URL = st.secrets["REDIS_URL"]
    CACHE_EXPIRATION = int(st.secrets["CACHE_EXPIRATION"])
    logger.info("✅ Loaded configuration from Streamlit secrets.")
except Exception as e:
    logger.error(f"⚠️ Failed to load secrets: {e}")
    REDIS_URL = "redis://localhost:6379"
    CACHE_EXPIRATION = 300  # Default to 5 minutes

# Initialize Redis client (if available)
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=5)
    redis_client.ping()  # Test connection
    redis_available = True
    logger.info("✅ Connected to Redis successfully!")
except Exception as e:
    redis_available = False
    logger.warning(f"⚠️ Redis not available, using in-memory cache: {e}")
    recommendation_cache = {}  # Fallback in-memory cache

# FastAPI App
app = FastAPI(title="AI Recommendation Service")

# Add Gzip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Pydantic Model for input validation
class UserQuery(BaseModel):
    query: str

@app.post("/parse-query/")
def parse_query(user_input: UserQuery):
    """Parses user query, saves structured data, and returns the profile."""
    parsed_data = parse_query_with_gemini(user_input.query)

    if "error" in parsed_data:
        raise HTTPException(status_code=400, detail=parsed_data["error"])

    # Save user profile to MongoDB
    if not save_user_profile(parsed_data):
        raise HTTPException(status_code=500, detail="Failed to save user profile.")

    # Clear cache after updating the profile
    clear_user_cache(parsed_data["user_id"])

    return {"message": "✅ User profile saved/updated successfully!", "profile": parsed_data}

@lru_cache(maxsize=100)
def get_cached_user_profile(user_id: str):
    """Cache user profiles to reduce database queries."""
    return get_user_profile(user_id)

@app.get("/get-user/{user_id}")
def get_user(user_id: str):
    """Fetches user profile from MongoDB with caching."""
    user_profile = get_cached_user_profile(user_id)
    
    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found")

    return user_profile

@app.get("/recommendations/{user_id}")
def get_recommendations(user_id: str, limit: int = 10):
    """Generates personalized recommendations for a user with caching."""
    cache_key = f"recommendations:{user_id}:{limit}"
    
    # Try to get from cache
    if redis_available:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
    elif cache_key in recommendation_cache:
        return recommendation_cache[cache_key]
    
    # Generate recommendations if not in cache
    recommendations = generate_recommendations(user_id, limit)
    
    if not recommendations:
        raise HTTPException(status_code=404, detail="No recommendations found or user not found")
    
    # Cache the result
    result = {"user_id": user_id, "recommendations": recommendations}
    
    if redis_available:
        redis_client.setex(cache_key, CACHE_EXPIRATION, json.dumps(result))
    else:
        recommendation_cache[cache_key] = result
    
    return result

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "caching": "redis" if redis_available else "in-memory"
    }

@app.post("/clear-cache/{user_id}")
def clear_user_cache(user_id: str):
    """Clears cached recommendations for a user."""
    if redis_available:
        pattern = f"recommendations:{user_id}:*"
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    else:
        keys_to_delete = [k for k in recommendation_cache.keys() if k.startswith(f"recommendations:{user_id}:")]
        for key in keys_to_delete:
            del recommendation_cache[key]
    
    # Clear user profile cache
    get_cached_user_profile.cache_clear()
    
    return {"message": f"✅ Cache cleared for user {user_id}"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
