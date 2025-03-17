# app/recommendation_refiner.py
import requests
import json
import os
import re
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def refine_recommendations(results: List[Dict], user_profile: Dict, limit: int = 10) -> List[Dict]:

    # Return empty list if results is empty
    if not results:
        return []
    
    # Limit the number of results to process
    top_results = results[:min(20, len(results))]  # Process top 20 results
    
    # Format the results for the prompt
    results_text = ""
    for i, result in enumerate(top_results, 1):
        results_text += f"Result {i}:\n"
        results_text += f"Title: {result.get('title', '')}\n"
        results_text += f"Source: {result.get('source_name', '')}\n"
        results_text += f"Snippet: {result.get('snippet', '')}\n"
        results_text += f"Relevance Score: {result.get('relevance_score', 0)}\n\n"
    
    # Format user profile for the prompt with None handling
    interests = user_profile.get('interests', []) or []
    skills = user_profile.get('demographics', {}) or {}.get('skills', []) or []
    industries = user_profile.get('demographics', {}) or {}.get('industries', []) or []
    
    profile_text = f"User Interests: {', '.join(interests)}\n"
    profile_text += f"Skills: {', '.join(skills)}\n"
    profile_text += f"Industries: {', '.join(industries)}\n"
    
    preferences = user_profile.get("preferences", {}) or {}
    if preferences.get("role"):
        profile_text += f"Role: {preferences['role']}\n"
    if preferences.get("location"):
        profile_text += f"Location: {preferences['location']}\n"
    if preferences.get("remote") is True:
        profile_text += "Prefers remote work\n"
    elif preferences.get("hybrid") is True:
        profile_text += "Prefers hybrid work\n"
    
    # Create the prompt for Gemini
    prompt = f"""
    Given a user profile and a list of potential recommendations, select and rank the top {limit} recommendations that would be most valuable and relevant to this user.
    
    USER PROFILE:
    {profile_text}
    
    POTENTIAL RECOMMENDATIONS:
    {results_text}
    
    For each selected recommendation, provide:
    1. The result number from the original list
    2. A personalized explanation of why this is relevant to the user (2-3 sentences)
    3. A relevance score from 1-100
    
    Format your response as a valid JSON array with objects containing fields: "result_index", "explanation", "relevance_score"
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        
        # Extract the response text
        response_text = data["candidates"][0]["content"]["parts"][0].get("text", "")
        
        # Extract JSON from the response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            refined_results_data = json.loads(json_match.group())
            
            # Map the refined results back to the original results
            final_recommendations = []
            for item in refined_results_data:
                result_index = item.get("result_index") - 1  # Convert from 1-based to 0-based indexing
                if 0 <= result_index < len(top_results):
                    recommendation = top_results[result_index].copy()
                    recommendation["explanation"] = item.get("explanation", "")
                    recommendation["gemini_relevance_score"] = item.get("relevance_score", 0)
                    final_recommendations.append(recommendation)
                    
                    # Stop once we reach the limit
                    if len(final_recommendations) >= limit:
                        break
            
            return final_recommendations[:limit]  # Ensure we respect the limit
        else:
            # If JSON parsing fails, return top results by original relevance score
            return top_results[:limit]
    
    except Exception as e:
        print(f"Error refining recommendations: {str(e)}")
        # Fallback to original relevance scoring
        return top_results[:limit]
