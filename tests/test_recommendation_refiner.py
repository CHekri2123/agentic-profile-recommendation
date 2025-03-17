# tests/test_recommendation_refiner.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, MagicMock
import json
from app.recommendation_refiner import refine_recommendations

# Sample data for testing
@pytest.fixture
def sample_user_profile():
    return {
        "interests": ["AI", "Machine Learning", "Data Science"],
        "preferences": {
            "role": "Data Scientist",
            "location": "San Francisco",
            "remote": True
        },
        "demographics": {
            "skills": ["Python", "TensorFlow", "SQL"],
            "industries": ["Technology", "Healthcare"]
        }
    }

@pytest.fixture
def sample_scored_results():
    return [
        {
            "title": "Introduction to Machine Learning with Python",
            "snippet": "Learn the basics of machine learning using Python and TensorFlow.",
            "source_name": "Web Search",
            "url": "https://example.com/ml-intro",
            "relevance_score": 95.5
        },
        {
            "title": "Healthcare Data Science Jobs",
            "snippet": "Find Data Scientist roles in the Healthcare industry.",
            "source_name": "Job Board",
            "url": "https://example.com/healthcare-jobs",
            "relevance_score": 85.2
        },
        {
            "title": "Remote Work Opportunities",
            "snippet": "List of remote job opportunities for developers.",
            "source_name": "Job Board",
            "url": "https://example.com/remote-jobs",
            "relevance_score": 75.8
        }
    ]

@pytest.fixture
def mock_gemini_response():
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": """
                            Here are the refined recommendations:
                            
                            ```
                            [
                                {
                                    "result_index": 1,
                                    "explanation": "This resource perfectly matches your interest in Machine Learning and skills in Python and TensorFlow. It provides foundational knowledge that's essential for your Data Scientist role.",
                                    "relevance_score": 95
                                },
                                {
                                    "result_index": 2,
                                    "explanation": "As someone interested in Data Science with experience in Healthcare industry, this job board listing is highly relevant to your career goals.",
                                    "relevance_score": 88
                                }
                            ]
                            ```
                            """
                        }
                    ]
                }
            }
        ]
    }

@patch('app.recommendation_refiner.requests.post')
def test_refine_recommendations_success(mock_post, sample_user_profile, sample_scored_results, mock_gemini_response):
    print("\n🧪 Testing refine_recommendations - success case")
    
    # Setup mock
    mock_response = MagicMock()
    mock_response.json.return_value = mock_gemini_response
    mock_post.return_value = mock_response
    
    # Call function
    results = refine_recommendations(sample_scored_results, sample_user_profile, limit=2)
    
    # Assertions
    assert len(results) == 2
    assert "explanation" in results[0]
    assert "gemini_relevance_score" in results[0]
    assert results[0]["title"] == "Introduction to Machine Learning with Python"
    
    # Check that the post request was made
    mock_post.assert_called_once()
    
    print("✅ Successful refinement test passed!")

@patch('app.recommendation_refiner.requests.post')
def test_refine_recommendations_api_error(mock_post, sample_user_profile, sample_scored_results):
    print("\n🧪 Testing refine_recommendations - API error")
    
    # Setup mock to raise exception
    mock_post.side_effect = Exception("API Error")
    
    # Call function
    results = refine_recommendations(sample_scored_results, sample_user_profile, limit=2)
    
    # Assertions - should fall back to original scoring
    assert len(results) == 2
    assert "explanation" not in results[0]
    assert results[0]["title"] == "Introduction to Machine Learning with Python"
    assert results[1]["title"] == "Healthcare Data Science Jobs"
    
    print("✅ API error fallback test passed!")

@patch('app.recommendation_refiner.requests.post')
def test_refine_recommendations_json_parsing_error(mock_post, sample_user_profile, sample_scored_results):
    print("\n🧪 Testing refine_recommendations - JSON parsing error")
    
    # Setup mock with invalid JSON
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "This is not valid JSON"
                        }
                    ]
                }
            }
        ]
    }
    mock_post.return_value = mock_response
    
    # Call function
    results = refine_recommendations(sample_scored_results, sample_user_profile, limit=2)
    
    # Assertions - should fall back to original scoring
    assert len(results) == 2
    assert "explanation" not in results[0]
    assert results[0]["title"] == "Introduction to Machine Learning with Python"
    
    print("✅ JSON parsing error fallback test passed!")

@patch('app.recommendation_refiner.requests.post')
def test_refine_recommendations_empty_results(mock_post, sample_user_profile):
    print("\n🧪 Testing refine_recommendations - empty results")
    
    # Call function with empty results
    results = refine_recommendations([], sample_user_profile, limit=2)
    
    # Assertions
    assert results == []
    
    # The API should not be called
    mock_post.assert_not_called()
    
    print("✅ Empty results test passed!")

@patch('app.recommendation_refiner.requests.post')
def test_refine_recommendations_limit_handling(mock_post, sample_user_profile, sample_scored_results, mock_gemini_response):
    print("\n🧪 Testing refine_recommendations - limit handling")
    
    # Setup mock
    mock_response = MagicMock()
    mock_response.json.return_value = mock_gemini_response
    mock_post.return_value = mock_response
    
    # Call function with different limits
    results_limit_1 = refine_recommendations(sample_scored_results, sample_user_profile, limit=1)
    
    # Assertions
    assert len(results_limit_1) == 1
    
    print("✅ Limit handling test passed!")

@patch('app.recommendation_refiner.requests.post')
def test_refine_recommendations_none_values(mock_post, sample_scored_results):
    print("\n🧪 Testing refine_recommendations - None values in user profile")
    
    # User profile with None values
    user_profile = {
        "interests": None,
        "preferences": None,
        "demographics": None
    }
    
    # Call function
    results = refine_recommendations(sample_scored_results, user_profile, limit=2)
    
    # Should not raise an exception and fall back to original scoring
    assert len(results) == 2
    
    print("✅ None values handling test passed!")
