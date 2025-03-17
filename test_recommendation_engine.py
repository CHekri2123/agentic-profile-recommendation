# test_recommendation_engine.py
from app.recommendation_engine import generate_recommendations
import json

def test_recommendation_engine():

    # Test with a user ID that exists in your database
    user_id = "283d5f163bf94b07b30177c617576984"  # Replace with an actual user ID from your database
    
    print(f"Generating recommendations for user: {user_id}")
    recommendations = generate_recommendations(user_id, limit=5)
    
    if not recommendations:
        print("No recommendations found or user not found.")
        return
    
    print(f"\nFound {len(recommendations)} recommendations:")
    
    # Print recommendations in a readable format
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec.get('title')}")
        print(f"   Source: {rec.get('source_name', rec.get('source', 'Unknown'))}")
        print(f"   Relevance: {rec.get('gemini_relevance_score', rec.get('relevance_score', 0))}")
        print(f"   Explanation: {rec.get('explanation', 'No explanation provided')}")
        print(f"   Link: {rec.get('link')}")

if __name__ == "__main__":
    test_recommendation_engine()
