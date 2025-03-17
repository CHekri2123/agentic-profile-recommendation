# tests/test_relevance_scorer.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.relevance_scorer import calculate_relevance_scores

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
def sample_results():
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
        },
        {
            "title": "Remote Work Opportunities",
            "snippet": "List of remote job opportunities for developers.",
            "source": "web_search",
            "url": "https://example.com/remote-jobs"
        },
        {
            "title": "SQL for Data Analysis",
            "snippet": "Advanced SQL techniques for data analysis and reporting.",
            "source": "books",
            "url": "https://example.com/sql-book"
        }
    ]

def test_calculate_relevance_scores(sample_user_profile, sample_results):
    print("\n🧪 Testing calculate_relevance_scores with sample data")
    
    # Calculate scores
    scored_results = calculate_relevance_scores(sample_results, sample_user_profile)
    
    # Check that scores were calculated
    assert all("relevance_score" in result for result in scored_results)
    
    # Check that results are sorted by score (descending)
    scores = [result["relevance_score"] for result in scored_results]
    assert scores == sorted(scores, reverse=True)
    
    # Check that items with more matching terms have higher scores
    # The first result should have higher score than the third (more matches)
    assert scored_results[0]["relevance_score"] > scored_results[-1]["relevance_score"]
    
    print("✅ Basic scoring and sorting test passed!")

def test_calculate_relevance_scores_empty_results(sample_user_profile):
    print("\n🧪 Testing calculate_relevance_scores with empty results")
    
    # Calculate scores with empty results
    scored_results = calculate_relevance_scores([], sample_user_profile)
    
    # Check that an empty list is returned
    assert scored_results == []
    
    print("✅ Empty results test passed!")

def test_calculate_relevance_scores_empty_profile():
    print("\n🧪 Testing calculate_relevance_scores with empty profile")
    
    # Sample results
    results = [
        {
            "title": "Some Article",
            "snippet": "Some content",
            "source": "web_search"
        }
    ]
    
    # Calculate scores with empty profile
    scored_results = calculate_relevance_scores(results, {})
    
    # Check that scores are calculated (should be low or zero)
    assert all("relevance_score" in result for result in scored_results)
    
    print("✅ Empty profile test passed!")

def test_source_specific_boosts(sample_user_profile, sample_results):
    print("\n🧪 Testing source-specific boosts")
    
    # Add "books" to interests to test boost
    sample_user_profile["interests"].append("books")
    
    # Calculate scores
    scored_results = calculate_relevance_scores(sample_results, sample_user_profile)
    
    # Find the books result
    books_result = next((r for r in scored_results if r["source"] == "books"), None)
    
    # Check that it exists and has a score
    assert books_result is not None
    assert "relevance_score" in books_result
    
    # Calculate what the score would be without the boost
    # We can't directly test the boost factor, but we can check it's not zero
    assert books_result["relevance_score"] > 0
    
    print("✅ Source-specific boost test passed!")

def test_exact_vs_partial_matches():
    print("\n🧪 Testing exact vs partial matches")
    
    # Create a user profile with specific terms
    user_profile = {
        "interests": ["Python programming"]
    }
    
    # Create results with exact and partial matches
    results = [
        {
            "title": "Python programming tutorial",  # Exact match
            "snippet": "Learn Python programming basics",
            "source": "web_search"
        },
        {
            "title": "Programming languages",  # Partial match
            "snippet": "Overview of different programming languages including Python",
            "source": "web_search"
        }
    ]
    
    # Calculate scores
    scored_results = calculate_relevance_scores(results, user_profile)
    
    # The exact match should have a higher score
    assert scored_results[0]["relevance_score"] > scored_results[1]["relevance_score"]
    
    print("✅ Exact vs partial match test passed!")

def test_none_values_handling():
    print("\n🧪 Testing None values handling")
    
    # Create a user profile with None values
    user_profile = {
        "interests": None,
        "preferences": {
            "role": None
        },
        "demographics": None
    }
    
    # Create results
    results = [
        {
            "title": "Some article",
            "snippet": "Some content",
            "source": "web_search"
        }
    ]
    
    # This should not raise an exception
    scored_results = calculate_relevance_scores(results, user_profile)
    
    # Check that scores were calculated
    assert all("relevance_score" in result for result in scored_results)
    
    print("✅ None values handling test passed!")
