# tests/test_query_generator.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.query_generator import generate_search_query

# Sample user profiles for testing
@pytest.fixture
def complete_user_profile():
    return {
        "interests": ["AI", "machine learning", "data science", "robotics", "automation"],
        "preferences": {
            "role": "Data Scientist",
            "location": "San Francisco",
            "remote": True,
            "hybrid": False
        },
        "demographics": {
            "skills": ["Python", "TensorFlow", "PyTorch", "SQL", "Data Visualization"],
            "industries": ["Technology", "Healthcare", "Finance"]
        }
    }

@pytest.fixture
def minimal_user_profile():
    return {
        "interests": ["Software Engineering"],
        "preferences": {},
        "demographics": {}
    }

@pytest.fixture
def empty_user_profile():
    return {}

@pytest.fixture
def remote_user_profile():
    return {
        "interests": ["Web Development"],
        "preferences": {
            "remote": True
        },
        "demographics": {}
    }

@pytest.fixture
def hybrid_user_profile():
    return {
        "interests": ["Web Development"],
        "preferences": {
            "hybrid": True
        },
        "demographics": {}
    }

# Test with complete user profile
def test_generate_search_query_complete(complete_user_profile):
    print("\n🧪 Testing generate_search_query with complete user profile")
    
    query = generate_search_query(complete_user_profile)
    
    # Check that all components are included
    assert "AI OR machine learning OR data science OR robotics OR automation" in query
    assert "Data Scientist" in query
    assert "San Francisco" in query
    assert "remote work" in query
    assert "Python TensorFlow PyTorch SQL Data Visualization" in query
    assert "Technology Healthcare Finance" in query
    
    print("✅ Complete user profile test passed!")

# Test with minimal user profile
def test_generate_search_query_minimal(minimal_user_profile):
    print("\n🧪 Testing generate_search_query with minimal user profile")
    
    query = generate_search_query(minimal_user_profile)
    
    # Check that only interests are included
    assert query == "Software Engineering"
    assert "remote" not in query.lower()
    assert "hybrid" not in query.lower()
    
    print("✅ Minimal user profile test passed!")

# Test with empty user profile
def test_generate_search_query_empty(empty_user_profile):
    print("\n🧪 Testing generate_search_query with empty user profile")
    
    query = generate_search_query(empty_user_profile)
    
    # Check that an empty string is returned
    assert query == ""
    
    print("✅ Empty user profile test passed!")

# Test remote preference
def test_generate_search_query_remote(remote_user_profile):
    print("\n🧪 Testing generate_search_query with remote preference")
    
    query = generate_search_query(remote_user_profile)
    
    # Check that remote work is included
    assert "Web Development" in query
    assert "remote work" in query
    assert "hybrid work" not in query
    
    print("✅ Remote preference test passed!")

# Test hybrid preference
def test_generate_search_query_hybrid(hybrid_user_profile):
    print("\n🧪 Testing generate_search_query with hybrid preference")
    
    query = generate_search_query(hybrid_user_profile)
    
    # Check that hybrid work is included
    assert "Web Development" in query
    assert "hybrid work" in query
    assert "remote work" not in query
    
    print("✅ Hybrid preference test passed!")

# Test with missing fields
def test_generate_search_query_missing_fields():
    print("\n🧪 Testing generate_search_query with missing fields")
    
    # User profile with some missing fields
    user_profile = {
        "interests": ["Marketing"],
        # Missing preferences
        "demographics": {
            "skills": ["Social Media", "Content Creation"]
            # Missing industries
        }
    }
    
    query = generate_search_query(user_profile)
    
    # Check that only available fields are included
    assert "Marketing" in query
    assert "Social Media Content Creation" in query
    assert "remote" not in query.lower()
    assert "hybrid" not in query.lower()
    
    print("✅ Missing fields test passed!")

# Test with None values
def test_generate_search_query_none_values():
    print("\n🧪 Testing generate_search_query with None values")
    
    # User profile with None values
    user_profile = {
        "interests": None,
        "preferences": {
            "role": None,
            "location": "New York"
        },
        "demographics": None
    }
    
    query = generate_search_query(user_profile)
    
    # Check that only non-None values are included
    assert query == "New York"
    
    print("✅ None values test passed!")

# Test with empty strings in lists
def test_generate_search_query_empty_strings():
    print("\n🧪 Testing generate_search_query with empty strings in lists")
    
    user_profile = {
        "interests": ["AI", "", "Data Science"],
        "demographics": {
            "skills": ["Python", "", "SQL"],
            "industries": ["", "Technology", ""]
        }
    }
    
    query = generate_search_query(user_profile)
    
    # Empty strings should be included in the query
    assert "AI OR  OR Data Science" in query
    assert "Python  SQL" in query
    assert "  Technology " in query
    
    print("✅ Empty strings test passed!")
