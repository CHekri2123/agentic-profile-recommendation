# app/database.py
import os
import pymongo
from dotenv import load_dotenv
from functools import lru_cache

# Load environment variables
load_dotenv()

# MongoDB connection string from environment variables
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI is not set in the environment variables!")

# Connect to MongoDB with connection pooling
try:
    client = pymongo.MongoClient(
        MONGO_URI,
        maxPoolSize=50,  # Maximum connections in the pool
        minPoolSize=10,  # Minimum connections to maintain
        retryWrites=True,
        serverSelectionTimeoutMS=5000  # Timeout for server selection
    )
    # Validate the connection
    client.admin.command('ping')
    print("✅ Connected to MongoDB successfully!")
except pymongo.errors.ConnectionFailure as e:
    print(f"❌ Could not connect to MongoDB: {e}")
    raise e

# Define database and collection
db = client["recommendation_db"]
users_collection = db["users"]

# In-memory cache for user profiles
user_profile_cache = {}
CACHE_EXPIRATION = 300  # 5 minutes in seconds

def save_user_profile(user_profile: dict):
    """
    Save or update a user profile in MongoDB.
    
    Args:
        user_profile: User profile dictionary to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Use upsert=True to insert if the document doesn't exist, or update if it does
        result = users_collection.update_one(
            {"user_id": user_profile["user_id"]},
            {"$set": user_profile},
            upsert=True
        )
        
        if result.upserted_id:
            print(f"✅ Inserted new user: {user_profile['user_id']}")
        else:
            print(f"✅ Updated user: {user_profile['user_id']}")
        
        # Clear cache for this user
        clear_user_cache(user_profile["user_id"])
        
        return True
    except pymongo.errors.PyMongoError as e:
        print(f"❌ Error saving/updating user profile: {e}")
        return False

def get_user_profile(user_id: str):
    """
    Fetch a user profile from MongoDB.
    
    Args:
        user_id: User ID to fetch
        
    Returns:
        dict: User profile or None if not found
    """
    try:
        user_profile = users_collection.find_one({"user_id": user_id}, {"_id": 0})
        
        if not user_profile:
            print(f"⚠️ User with ID {user_id} not found.")
            return None
        
        print(f"✅ Retrieved user profile for ID: {user_id}")
        return user_profile
    except pymongo.errors.PyMongoError as e:
        print(f"❌ Error retrieving user profile: {e}")
        return None

def delete_user_profile(user_id: str):
    """
    Delete a user profile from MongoDB.
    
    Args:
        user_id: User ID to delete
        
    Returns:
        bool: True if deleted, False otherwise
    """
    try:
        result = users_collection.delete_one({"user_id": user_id})
        
        if result.deleted_count > 0:
            print(f"✅ Deleted user profile for ID: {user_id}")
            # Clear cache for this user
            clear_user_cache(user_id)
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
        list: List of user profiles
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

def clear_user_cache(user_id: str):
    """Clear cached data for a specific user"""
    # This function will be called when a user profile is updated or deleted
    # It helps maintain cache consistency
    pass

def get_db_client():
    """
    Returns the MongoDB client for dependency injection.
    
    Returns:
        pymongo.MongoClient: The MongoDB client instance
    """
    try:
        # Validate connection is still alive
        client.admin.command('ping')
        return client
    except pymongo.errors.ConnectionFailure:
        # Reconnect if connection is lost
        return pymongo.MongoClient(MONGO_URI)
