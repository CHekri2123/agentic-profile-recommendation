# app/main.py
import uvicorn
import json
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from functools import lru_cache
import redis
import os
from dotenv import load_dotenv

from app.query_parser import parse_query_with_gemini
from app.database import save_user_profile, get_user_profile
from app.recommendation_engine import generate_recommendations

# Load environment variables
load_dotenv()

# Initialize Redis client (if available)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_EXPIRATION = int(os.getenv("CACHE_EXPIRATION", "300"))  # 5 minutes in seconds

# Initialize Redis client with connection pooling
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_available = True
    print("✅ Connected to Redis successfully!")
except Exception as e:
    redis_available = False
    print(f"⚠️ Redis not available, using in-memory cache: {str(e)}")
    # Fallback to in-memory cache
    recommendation_cache = {}

app = FastAPI(title="AI Recommendation Service")

# Add Gzip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 📌 Pydantic Model for input validation
class UserQuery(BaseModel):
    query: str

@app.post("/parse-query/")
def parse_query(user_input: UserQuery):
    """Parses user query, saves structured data, and returns the profile."""
    parsed_data = parse_query_with_gemini(user_input.query)

    if "error" in parsed_data:
        raise HTTPException(status_code=400, detail=parsed_data["error"])

    # Save user profile to MongoDB
    save_user_profile(parsed_data)

    return {"message": "User profile saved/updated successfully", "profile": parsed_data}

@lru_cache(maxsize=100)
def get_cached_user_profile(user_id: str):
    """Cache user profiles to reduce database queries"""
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
    # Create cache key
    cache_key = f"recommendations:{user_id}:{limit}"
    
    # Try to get from cache
    if redis_available:
        # Redis cache
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
    elif cache_key in recommendation_cache:
        # In-memory cache
        return recommendation_cache[cache_key]
    
    # Generate recommendations if not in cache
    recommendations = generate_recommendations(user_id, limit)
    
    if not recommendations:
        raise HTTPException(status_code=404, detail="No recommendations found or user not found")
    
    # Cache the result
    result = {"user_id": user_id, "recommendations": recommendations}
    
    if redis_available:
        # Redis cache with expiration
        redis_client.setex(cache_key, CACHE_EXPIRATION, json.dumps(result))
    else:
        # In-memory cache
        recommendation_cache[cache_key] = result
    
    return result

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "caching": "redis" if redis_available else "in-memory"
    }

# Clear cache for a user (useful after profile updates)
@app.post("/clear-cache/{user_id}")
def clear_user_cache(user_id: str):
    """Clears cached recommendations for a user."""
    if redis_available:
        # Get all keys matching the pattern
        pattern = f"recommendations:{user_id}:*"
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    else:
        # Clear from in-memory cache
        keys_to_delete = [k for k in recommendation_cache.keys() if k.startswith(f"recommendations:{user_id}:")]
        for key in keys_to_delete:
            del recommendation_cache[key]
    
    # Clear user profile cache
    get_cached_user_profile.cache_clear()
    
    return {"message": f"Cache cleared for user {user_id}"}

# Run the FastAPI server
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
