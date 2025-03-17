# tests/test_recommendation_engine.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, MagicMock
from app.recommendation_engine import generate_recommendations

# Sample data for testing
@pytest.fixture
def sample_user_profile():
    return {
        "user_id": "test123",
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
def sample_raw_results():
    return [
        {
            "title": "Introduction to Machine Learning with Python",
            "snippet": "Learn the basics of machine learning using Python and TensorFlow.",
            "source": "web_search",
            "url": "https://example.com/ml-intro"
        },
        {
            "title": "Healthcare Data Science Jobs",
            "snippet": "Find Data Scientist roles in the Healthcare industry.",
            "source": "web_search",
            "url": "https://example.com/healthcare-jobs"
        }
    ]

@pytest.fixture
def sample_scored_results():
    return [
        {
            "title": "Introduction to Machine Learning with Python",
            "snippet": "Learn the basics of machine learning using Python and TensorFlow.",
            "source": "web_search",
            "url": "https://example.com/ml-intro",
            "relevance_score": 95.5
        },
        {
            "title": "Healthcare Data Science Jobs",
            "snippet": "Find Data Scientist roles in the Healthcare industry.",
            "source": "web_search",
            "url": "https://example.com/healthcare-jobs",
            "relevance_score": 85.2
        }
    ]

@pytest.fixture
def sample_final_recommendations():
    return [
        {
            "title": "Introduction to Machine Learning with Python",
            "snippet": "Learn the basics of machine learning using Python and TensorFlow.",
            "source": "web_search",
            "url": "https://example.com/ml-intro",
            "relevance_score": 95.5,
            "explanation": "This resource perfectly matches your interest in Machine Learning and skills in Python and TensorFlow.",
            "gemini_relevance_score": 95
        },
        {
            "title": "Healthcare Data Science Jobs",
            "snippet": "Find Data Scientist roles in the Healthcare industry.",
            "source": "web_search",
            "url": "https://example.com/healthcare-jobs",
            "relevance_score": 85.2,
            "explanation": "As someone interested in Data Science with experience in Healthcare industry, this job board listing is highly relevant to your career goals.",
            "gemini_relevance_score": 88
        }
    ]

@patch('app.recommendation_engine.get_user_profile')
@patch('app.recommendation_engine.generate_search_query')
@patch('app.recommendation_engine.fetch_from_all_sources')
@patch('app.recommendation_engine.calculate_relevance_scores')
@patch('app.recommendation_engine.refine_recommendations')
def test_generate_recommendations_success(
    mock_refine, mock_calculate, mock_fetch, mock_generate_query, mock_get_profile,
    sample_user_profile, sample_raw_results, sample_scored_results, sample_final_recommendations
):
    print("\n🧪 Testing generate_recommendations - success case")
    
    # Setup mocks
    mock_get_profile.return_value = sample_user_profile
    mock_generate_query.return_value = "AI OR Machine Learning Data Scientist San Francisco"
    mock_fetch.return_value = sample_raw_results
    mock_calculate.return_value = sample_scored_results
    mock_refine.return_value = sample_final_recommendations
    
    # Call function
    results = generate_recommendations("test123", limit=2)
    
    # Assertions
    assert results == sample_final_recommendations
    mock_get_profile.assert_called_once_with("test123")
    mock_generate_query.assert_called_once()
    mock_fetch.assert_called_once()
    mock_calculate.assert_called_once()
    mock_refine.assert_called_once()
    
    print("✅ Successful recommendation generation test passed!")

@patch('app.recommendation_engine.get_user_profile')
def test_generate_recommendations_user_not_found(mock_get_profile):
    print("\n🧪 Testing generate_recommendations - user not found")
    
    # Setup mock
    mock_get_profile.return_value = None
    
    # Call function
    results = generate_recommendations("nonexistent_user")
    
    # Assertions
    assert results == []
    mock_get_profile.assert_called_once_with("nonexistent_user")
    
    print("✅ User not found test passed!")

@patch('app.recommendation_engine.get_user_profile')
@patch('app.recommendation_engine.generate_search_query')
@patch('app.recommendation_engine.fetch_from_all_sources')
def test_generate_recommendations_empty_results(
    mock_fetch, mock_generate_query, mock_get_profile, sample_user_profile
):
    print("\n🧪 Testing generate_recommendations - empty results")
    
    # Setup mocks
    mock_get_profile.return_value = sample_user_profile
    mock_generate_query.return_value = "AI OR Machine Learning"
    mock_fetch.return_value = []  # Empty results
    
    # Call function
    results = generate_recommendations("test123")
    
    # Assertions
    assert results == []
    
    print("✅ Empty results test passed!")

@patch('app.recommendation_engine.get_user_profile')
@patch('app.recommendation_engine.generate_search_query')
@patch('app.recommendation_engine.fetch_from_all_sources')
@patch('app.recommendation_engine.calculate_relevance_scores')
@patch('app.recommendation_engine.refine_recommendations')
def test_generate_recommendations_limit(
    mock_refine, mock_calculate, mock_fetch, mock_generate_query, mock_get_profile,
    sample_user_profile, sample_raw_results, sample_scored_results, sample_final_recommendations
):
    print("\n🧪 Testing generate_recommendations - limit parameter")
    
    # Setup mocks
    mock_get_profile.return_value = sample_user_profile
    mock_generate_query.return_value = "AI OR Machine Learning"
    mock_fetch.return_value = sample_raw_results
    mock_calculate.return_value = sample_scored_results
    mock_refine.return_value = sample_final_recommendations[:1]  # Just one result
    
    # Call function with limit=1
    results = generate_recommendations("test123", limit=1)
    
    # Assertions
    assert len(results) == 1
    mock_refine.assert_called_once_with(sample_scored_results, sample_user_profile, 1)
    
    print("✅ Limit parameter test passed!")

@patch('app.recommendation_engine.get_user_profile')
@patch('app.recommendation_engine.generate_search_query')
@patch('app.recommendation_engine.fetch_from_all_sources')
@patch('app.recommendation_engine.calculate_relevance_scores')
def test_generate_recommendations_refiner_error(
    mock_calculate, mock_fetch, mock_generate_query, mock_get_profile,
    sample_user_profile, sample_raw_results, sample_scored_results
):
    print("\n🧪 Testing generate_recommendations - refiner error")
    
    # Setup mocks
    mock_get_profile.return_value = sample_user_profile
    mock_generate_query.return_value = "AI OR Machine Learning"
    mock_fetch.return_value = sample_raw_results
    mock_calculate.return_value = sample_scored_results
    
    # Simulate error in refine_recommendations by patching it to raise an exception
    with patch('app.recommendation_engine.refine_recommendations', side_effect=Exception("Refiner error")):
        # Call function
        results = generate_recommendations("test123")
        
        # Should return empty list on error
        assert results == []
    
    print("✅ Refiner error test passed!")

@patch('app.recommendation_engine.get_user_profile')
def test_generate_recommendations_with_none_values(mock_get_profile):
    print("\n🧪 Testing generate_recommendations - with None values in profile")
    
    # User profile with None values
    user_profile_with_none = {
        "user_id": "test123",
        "interests": None,
        "preferences": None,
        "demographics": None
    }
    
    # Setup mock
    mock_get_profile.return_value = user_profile_with_none
    
    # Patch the remaining functions to avoid actual API calls
    with patch('app.recommendation_engine.generate_search_query') as mock_generate_query:
        with patch('app.recommendation_engine.fetch_from_all_sources') as mock_fetch:
            with patch('app.recommendation_engine.calculate_relevance_scores') as mock_calculate:
                with patch('app.recommendation_engine.refine_recommendations') as mock_refine:
                    # Set up return values
                    mock_generate_query.return_value = ""
                    mock_fetch.return_value = []
                    mock_calculate.return_value = []
                    mock_refine.return_value = []
                    
                    # Call function - should not raise exceptions
                    results = generate_recommendations("test123")
                    
                    # Should return empty list
                    assert results == []
    
    print("✅ None values in profile test passed!")
