import pymongo
import redis
import json
import ssl
import logging
import streamlit as st
from functools import lru_cache

# ✅ Load MongoDB & Redis Config from Streamlit Secrets
MONGO_URI = st.secrets["MONGO_URI"]
DATABASE_NAME = st.secrets["DATABASE_NAME"]
REDIS_URL = st.secrets["REDIS_URL"]

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI is missing from Streamlit secrets!")

if not REDIS_URL:
    raise ValueError("❌ REDIS_URL is missing from Streamlit secrets!")

# ✅ Initialize MongoDB Client with TLS 1.2 Fix
try:
    client = pymongo.MongoClient(
        MONGO_URI,
        maxPoolSize=50,
        minPoolSize=10,
        retryWrites=True,
        serverSelectionTimeoutMS=5000,
        tlsAllowInvalidCertificates=True  # 👈 Add this line
    )

    client.admin.command("ping")
    print("✅ Connected to MongoDB successfully!")
except pymongo.errors.ServerSelectionTimeoutError as e:
    print(f"❌ MongoDB Server Selection Timeout: {e}")
    raise e
except pymongo.errors.ConnectionFailure as e:
    print(f"❌ Could not connect to MongoDB: {e}")
    raise e

# ✅ Initialize Redis Client
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    print("✅ Connected to Redis successfully!")
except Exception as e:
    print(f"❌ Could not connect to Redis: {e}")
    redis_client = None  # Fallback if Redis is unavailable

# ✅ Define database and collections
db = client[DATABASE_NAME]
users_collection = db["users"]

# ✅ Cache expiration time in seconds
CACHE_EXPIRATION = 300  # 5 minutes


def save_user_profile(user_profile: dict):
    """
    Save or update a user profile in MongoDB and cache in Redis.

    Args:
        user_profile: User profile dictionary to save.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        result = users_collection.update_one(
            {"user_id": user_profile["user_id"]},
            {"$set": user_profile},
            upsert=True
        )

        if result.upserted_id:
            print(f"✅ Inserted new user: {user_profile['user_id']}")
        else:
            print(f"✅ Updated user: {user_profile['user_id']}")

        # ✅ Update Redis cache
        if redis_client:
            redis_client.setex(
                f"user_profile:{user_profile['user_id']}",
                CACHE_EXPIRATION,
                json.dumps(user_profile),
            )

        return True
    except pymongo.errors.PyMongoError as e:
        print(f"❌ Error saving/updating user profile: {e}")
        return False


def get_user_profile(user_id: str):
    """
    Fetch a user profile from Redis cache first, then MongoDB if not found.

    Args:
        user_id: User ID to fetch.

    Returns:
        dict: User profile or None if not found.
    """
    try:
        if redis_client:
            cached_profile = redis_client.get(f"user_profile:{user_id}")
            if cached_profile:
                print(f"✅ Cache hit: Retrieved user {user_id} from Redis.")
                return json.loads(cached_profile)

        # ✅ If not found in Redis, fetch from MongoDB
        user_profile = users_collection.find_one({"user_id": user_id}, {"_id": 0})

        if user_profile:
            print(f"✅ Retrieved user profile from MongoDB for ID: {user_id}")

            # ✅ Store in Redis for future requests
            if redis_client:
                redis_client.setex(
                    f"user_profile:{user_id}",
                    CACHE_EXPIRATION,
                    json.dumps(user_profile),
                )

            return user_profile

        print(f"⚠️ User with ID {user_id} not found.")
        return None
    except pymongo.errors.PyMongoError as e:
        print(f"❌ Error retrieving user profile: {e}")
        return None


def delete_user_profile(user_id: str):
    """
    Delete a user profile from MongoDB and Redis.

    Args:
        user_id: User ID to delete.

    Returns:
        bool: True if deleted, False otherwise.
    """
    try:
        result = users_collection.delete_one({"user_id": user_id})

        if result.deleted_count > 0:
            print(f"✅ Deleted user profile for ID: {user_id}")

            # ✅ Remove from Redis cache
            if redis_client:
                redis_client.delete(f"user_profile:{user_id}")

            return True
        else:
            print(f"⚠️ No user found with ID {user_id} to delete.")
            return False
    except pymongo.errors.PyMongoError as e:
        print(f"❌ Error deleting user profile: {e}")
        return False


def list_all_users():
    """
    List all users in the database.

    Returns:
        list: List of user profiles.
    """
    try:
        users = list(users_collection.find({}, {"_id": 0}))

        if not users:
            print("⚠️ No users found in the database.")
            return []

        print(f"✅ Found {len(users)} users in the database.")
        return users
    except pymongo.errors.PyMongoError as e:
        print(f"❌ Error listing all users: {e}")
        return []


def get_db_client():
    """
    Returns the MongoDB client for dependency injection.

    Returns:
        pymongo.MongoClient: The MongoDB client instance.
    """
    try:
        client.admin.command("ping")
        return client
    except pymongo.errors.ConnectionFailure:
        return pymongo.MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
