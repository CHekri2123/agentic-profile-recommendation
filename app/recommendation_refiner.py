import requests
import json
import re
import streamlit as st
from typing import List, Dict

# ✅ Load Gemini API key securely from Streamlit secrets
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

def refine_recommendations(results: List[Dict], user_profile: Dict, limit: int = 10) -> List[Dict]:
    """
    Uses the Gemini API to refine and rank recommendations based on user profile.

    Args:
        results: List of initial recommendations with relevance scores.
        user_profile: The user's profile including interests, skills, and preferences.
        limit: The number of top recommendations to return.

    Returns:
        A refined list of recommendations ranked by Gemini.
    """

    # ✅ Return empty list if results are empty
    if not results:
        return []
    
    # ✅ Limit to processing top 20 results
    top_results = results[:20]

    # ✅ Format user profile details
    interests = ", ".join(user_profile.get("interests", []))
    skills = ", ".join(user_profile.get("demographics", {}).get("skills", []))
    industries = ", ".join(user_profile.get("demographics", {}).get("industries", []))
    
    profile_text = f"""
    User Interests: {interests or 'None'}
    Skills: {skills or 'None'}
    Industries: {industries or 'None'}
    """

    preferences = user_profile.get("preferences", {})
    if preferences.get("role"):
        profile_text += f"\nRole: {preferences['role']}"
    if preferences.get("location"):
        profile_text += f"\nLocation: {preferences['location']}"
    if preferences.get("remote") is True:
        profile_text += "\nPrefers remote work"
    elif preferences.get("hybrid") is True:
        profile_text += "\nPrefers hybrid work"

    # ✅ Format the results for the prompt
    results_text = "\n".join(
        f"""Result {i+1}:
        Title: {result.get('title', 'N/A')}
        Source: {result.get('source_name', 'Unknown')}
        Snippet: {result.get('snippet', 'No snippet available')}
        Relevance Score: {result.get('relevance_score', 0)}"""
        for i, result in enumerate(top_results)
    )

    # ✅ Construct the Gemini prompt
    prompt = f"""
    Given the following user profile and a list of potential recommendations, rank the top {limit} recommendations that best match the user's interests and preferences.

    **USER PROFILE:**
    {profile_text}

    **POTENTIAL RECOMMENDATIONS:**
    {results_text}

    **Instructions:**
    - Select and rank the **top {limit} recommendations**.
    - For each selected recommendation, provide:
      1. The **result number** from the original list.
      2. A **personalized explanation** (2-3 sentences) of why this recommendation is relevant.
      3. A **relevance score from 1-100**.

    **Format the response as a valid JSON array:**
    ```json
    [
        {{"result_index": 1, "explanation": "Reason why this is relevant", "relevance_score": 85}},
        {{"result_index": 2, "explanation": "Another reason", "relevance_score": 78}}
    ]
    ```
    """

    # ✅ Gemini API request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()  # Raises an error for HTTP 4xx/5xx

        # ✅ Extract the response text
        data = response.json()
        response_text = data["candidates"][0]["content"]["parts"][0].get("text", "")

        # ✅ Extract JSON from response using regex
        json_match = re.search(r'\[\s*\{.*\}\s*\]', response_text, re.DOTALL)
        if not json_match:
            raise ValueError("Failed to extract JSON from Gemini response")

        refined_results_data = json.loads(json_match.group())

        # ✅ Map the refined results to the original list
        final_recommendations = []
        for item in refined_results_data:
            result_index = item.get("result_index") - 1  # Convert from 1-based to 0-based
            if 0 <= result_index < len(top_results):
                recommendation = top_results[result_index].copy()
                recommendation["explanation"] = item.get("explanation", "No explanation provided.")
                recommendation["gemini_relevance_score"] = item.get("relevance_score", 0)
                final_recommendations.append(recommendation)
                
                # ✅ Stop once we reach the limit
                if len(final_recommendations) >= limit:
                    break

        return final_recommendations[:limit]  # Ensure limit is respected

    except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
        print(f"Error refining recommendations: {e}")
        # ✅ Fallback: Return top results sorted by original relevance score
        return top_results[:limit]
