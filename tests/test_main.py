# tests/test_main.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest
import json

from app.main import app

# Create test client
client = TestClient(app)

# Sample user profile for testing
@pytest.fixture
def sample_user_profile():
    return {
        "user_id": "test123",
        "name": "Test User",
        "interests": ["AI", "Technology", "Books"],
        "preferences": {
            "language": "English",
            "categories": ["Science", "Technology"]
        },
        "demographics": {
            "age": 30,
            "location": "New York"
        }
    }

# Sample recommendations for testing
@pytest.fixture
def sample_recommendations():
    return [
        {
            "id": "rec1",
            "title": "Introduction to AI",
            "source": "article",
            "relevance_score": 0.95,
            "url": "https://example.com/ai-intro"
        },
        {
            "id": "rec2",
            "title": "Machine Learning Basics",
            "source": "video",
            "relevance_score": 0.87,
            "url": "https://example.com/ml-basics"
        }
    ]

# Test parse_query endpoint
@patch('app.main.parse_query_with_gemini')
@patch('app.main.save_user_profile')
def test_parse_query_success(mock_save_profile, mock_parse_query, sample_user_profile):
    print("\n🧪 Testing parse_query endpoint - success case")
    # Setup mocks
    mock_parse_query.return_value = sample_user_profile
    mock_save_profile.return_value = True
    
    # Make request
    response = client.post(
        "/parse-query/",
        json={"query": "I like technology and books"}
    )
    
    # Assertions
    assert response.status_code == 200
    assert response.json() == {
        "message": "User profile saved/updated successfully",
        "profile": sample_user_profile
    }
    mock_parse_query.assert_called_once_with("I like technology and books")
    mock_save_profile.assert_called_once_with(sample_user_profile)
    print("✅ parse_query success test passed!")

@patch('app.main.parse_query_with_gemini')
def test_parse_query_error(mock_parse_query):
    print("\n🧪 Testing parse_query endpoint - error case")
    # Setup mock to return error
    mock_parse_query.return_value = {"error": "Failed to parse query"}
    
    # Make request
    response = client.post(
        "/parse-query/",
        json={"query": "Invalid query"}
    )
    
    # Assertions
    assert response.status_code == 400
    assert response.json() == {"detail": "Failed to parse query"}
    print("✅ parse_query error test passed!")

# Test get_user endpoint
@patch('app.main.get_user_profile')
def test_get_user_success(mock_get_profile, sample_user_profile):
    print("\n🧪 Testing get_user endpoint - success case")
    # Setup mock
    mock_get_profile.return_value = sample_user_profile
    
    # Make request
    response = client.get("/get-user/test123")
    
    # Assertions
    assert response.status_code == 200
    assert response.json() == sample_user_profile
    mock_get_profile.assert_called_once_with("test123")
    print("✅ get_user success test passed!")

@patch('app.main.get_user_profile')
def test_get_user_not_found(mock_get_profile):
    print("\n🧪 Testing get_user endpoint - not found case")
    # Setup mock
    mock_get_profile.return_value = None
    
    # Make request
    response = client.get("/get-user/nonexistent")
    
    # Assertions
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}
    print("✅ get_user not found test passed!")

# Test recommendations endpoint
@patch('app.main.generate_recommendations')
def test_get_recommendations_success(mock_generate_recommendations, sample_recommendations):
    print("\n🧪 Testing recommendations endpoint - success case")
    # Setup mock
    mock_generate_recommendations.return_value = sample_recommendations
    
    # Make request
    response = client.get("/recommendations/test123")
    
    # Assertions
    assert response.status_code == 200
    assert response.json() == {
        "user_id": "test123",
        "recommendations": sample_recommendations
    }
    mock_generate_recommendations.assert_called_once_with("test123", 10)
    print("✅ recommendations success test passed!")

@patch('app.main.generate_recommendations')
def test_get_recommendations_with_limit(mock_generate_recommendations, sample_recommendations):
    print("\n🧪 Testing recommendations endpoint - with limit parameter")
    # Setup mock
    mock_generate_recommendations.return_value = sample_recommendations[:1]
    
    # Make request
    response = client.get("/recommendations/test123?limit=1")
    
    # Assertions
    assert response.status_code == 200
    assert response.json() == {
        "user_id": "test123",
        "recommendations": sample_recommendations[:1]
    }
    mock_generate_recommendations.assert_called_once_with("test123", 1)
    print("✅ recommendations with limit test passed!")

@patch('app.main.generate_recommendations')
def test_get_recommendations_not_found(mock_generate_recommendations):
    print("\n🧪 Testing recommendations endpoint - not found case")
    # Setup mock
    mock_generate_recommendations.return_value = None
    
    # Make request
    response = client.get("/recommendations/nonexistent")
    
    # Assertions
    assert response.status_code == 404
    assert response.json() == {"detail": "No recommendations found or user not found"}
    print("✅ recommendations not found test passed!")

# Test validation errors
def test_parse_query_validation_error():
    print("\n🧪 Testing parse_query endpoint - validation error")
    # Make request with missing required field
    response = client.post("/parse-query/", json={})
    
    # Assertions
    assert response.status_code == 422  # Unprocessable Entity
    print("✅ parse_query validation error test passed!")
