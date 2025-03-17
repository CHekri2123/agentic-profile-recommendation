# tests/test_query_parser.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json
import uuid
import re
from unittest.mock import patch, MagicMock

from app.query_parser import (
    extract_json,
    parse_query_with_gemini,
    UserProfile
)

# Test extract_json function
def test_extract_json_valid():
    print("\n🧪 Testing extract_json with valid JSON")
    # Test with valid JSON in a markdown code block
    text = """
    Here's the JSON:
    ```
    {"name": "John", "age": 30}
    ```
    """
    result = extract_json(text)
    assert result == {"name": "John", "age": 30}
    print("✅ extract_json with valid JSON test passed!")

def test_extract_json_invalid():
    print("\n🧪 Testing extract_json with invalid JSON")
    # Test with invalid JSON
    text = """
    Here's the JSON:
    ```
    {"name": "John", "age": 30,}
    ```
    """
    result = extract_json(text)
    assert result is None
    print("✅ extract_json with invalid JSON test passed!")

def test_extract_json_no_json():
    print("\n🧪 Testing extract_json with no JSON")
    # Test with no JSON
    text = "This is just plain text with no JSON."
    result = extract_json(text)
    assert result is None
    print("✅ extract_json with no JSON test passed!")

# Mock response for successful API call
@pytest.fixture
def mock_successful_response():
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": """
                            ```
                            {
                                "user_id": "abc123",
                                "name": "John Doe",
                                "interests": ["AI", "Machine Learning", "Data Science"],
                                "preferences": {
                                    "location": "San Francisco",
                                    "remote": true,
                                    "hybrid": false,
                                    "sponsorship": null,
                                    "role": "Data Scientist",
                                    "posted_days_ago": null
                                },
                                "demographics": {
                                    "skills": ["Python", "TensorFlow", "SQL"],
                                    "industries": ["Technology", "Healthcare"]
                                }
                            }
                            ```
                            """
                        }
                    ]
                }
            }
        ]
    }

# Mock response for failed API call
@pytest.fixture
def mock_failed_response():
    return {
        "error": {
            "code": 400,
            "message": "Invalid request"
        }
    }

# Test parse_query_with_gemini function
@patch('app.query_parser.requests.post')
@patch('app.query_parser.save_user_profile')
def test_parse_query_success(mock_save_profile, mock_post, mock_successful_response):
    print("\n🧪 Testing parse_query_with_gemini - success case")
    # Setup mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_successful_response
    mock_post.return_value = mock_response
    mock_save_profile.return_value = True
    
    # Call function
    result = parse_query_with_gemini("I'm John Doe, looking for a Data Scientist role in San Francisco, remote work")
    
    # Assertions
    assert result["name"] == "John Doe"
    assert "AI" in result["interests"]
    assert result["preferences"]["location"] == "San Francisco"
    assert result["preferences"]["remote"] is True
    assert result["preferences"]["hybrid"] is False
    assert "Python" in result["demographics"]["skills"]
    
    # Verify API call
    mock_post.assert_called_once()
    # Verify save_user_profile call
    mock_save_profile.assert_called_once()
    print("✅ parse_query_with_gemini success test passed!")

@patch('app.query_parser.requests.post')
def test_parse_query_api_error(mock_post):
    print("\n🧪 Testing parse_query_with_gemini - API error")
    # Setup mock
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_post.return_value = mock_response
    
    # Call function
    result = parse_query_with_gemini("Some query")
    
    # Assertions
    assert "error" in result
    assert "API Error: 400" in result["error"]
    print("✅ parse_query_with_gemini API error test passed!")

@patch('app.query_parser.requests.post')
def test_parse_query_invalid_json(mock_post):
    print("\n🧪 Testing parse_query_with_gemini - invalid JSON in response")
    # Setup mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "This is not JSON"
                        }
                    ]
                }
            }
        ]
    }
    mock_post.return_value = mock_response
    
    # Call function
    result = parse_query_with_gemini("Some query")
    
    # Assertions
    assert "error" in result
    assert "does not contain valid JSON" in result["error"]
    print("✅ parse_query_with_gemini invalid JSON test passed!")

@patch('app.query_parser.requests.post')
def test_parse_query_validation_error(mock_post):
    print("\n🧪 Testing parse_query_with_gemini - validation error")
    # Setup mock to return a response that will cause a validation error
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    # Create a response with incomplete JSON that will fail validation
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": """
                            ```
                            {
                                "user_id": "abc123",
                                "name": "John Doe"
                                # Missing required fields
                            }
                            ```
                            """
                        }
                    ]
                }
            }
        ]
    }
    mock_post.return_value = mock_response
    
    # Call function
    result = parse_query_with_gemini("Some query")
    
    # Debug print
    print(f"Result: {result}")
    
    # Assertions
    assert "error" in result
    # The error message might vary, so we'll check for a partial match
    assert any(["validation" in result["error"].lower(),
               "invalid" in result["error"].lower(),
               "missing" in result["error"].lower(),
               "failed" in result["error"].lower()])
    print("✅ parse_query_with_gemini validation error test passed!")

@patch('app.query_parser.requests.post')
@patch('app.query_parser.save_user_profile')
def test_parse_query_urgency_detection(mock_save_profile, mock_post, mock_successful_response):
    print("\n🧪 Testing parse_query_with_gemini - urgency detection")
    # Setup mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_successful_response
    mock_post.return_value = mock_response
    mock_save_profile.return_value = True
    
    # Call function with urgent query
    result = parse_query_with_gemini("I need a job ASAP! I'm John Doe, looking for a Data Scientist role")
    
    # Assertions
    assert result["preferences"]["posted_days_ago"] == 0
    print("✅ parse_query_with_gemini urgency detection test passed!")

# Test UserProfile Pydantic model
def test_user_profile_model_valid():
    print("\n🧪 Testing UserProfile Pydantic model - valid data")
    # Valid data
    data = {
        "user_id": "abc123",
        "name": "John Doe",
        "interests": ["AI", "Machine Learning"],
        "preferences": {
            "location": "San Francisco"
        },
        "demographics": {
            "skills": ["Python"]
        }
    }
    
    # Create model
    user_profile = UserProfile(**data)
    
    # Assertions
    assert user_profile.user_id == "abc123"
    assert user_profile.name == "John Doe"
    assert "AI" in user_profile.interests
    assert user_profile.preferences["location"] == "San Francisco"
    assert "Python" in user_profile.demographics["skills"]
    print("✅ UserProfile model valid data test passed!")

def test_user_profile_model_invalid():
    print("\n🧪 Testing UserProfile Pydantic model - invalid data")
    # Invalid data (missing required fields)
    data = {
        "user_id": "abc123",
        # Missing name
        # Missing interests
        "preferences": {},
        "demographics": {}
    }
    
    # Try to create model
    with pytest.raises(Exception):
        user_profile = UserProfile(**data)
    
    print("✅ UserProfile model invalid data test passed!")
