import os
import requests
import json
import re
import time
import streamlit as st
from typing import List, Dict

# ✅ Load Gemini API key from environment variables
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
if not GEMINI_API_KEY:
    raise ValueError("⚠️ Missing Gemini API key! Set GEMINI_API_KEY in environment variables.")

def call_gemini_api(payload, retries=3, backoff=2):
    """ Calls the Gemini API with retry logic for transient failures. """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(backoff ** attempt)  # Exponential backoff
            else:
                raise RuntimeError(f"🚨 Gemini API request failed after {retries} attempts: {e}")

def refine_recommendations(jobs: List[Dict], user_profile: Dict, limit: int = 10) -> List[Dict]:
    """
    Uses the Gemini API to refine and rank job recommendations based on user profile.

    Args:
        jobs: List of initial job recommendations with relevance scores.
        user_profile: The user's profile including skills, experience, and preferences.
        limit: The number of top recommendations to return.

    Returns:
        A refined list of job recommendations ranked by Gemini.
    """

    # ✅ Return empty list if jobs are empty
    if not jobs:
        return []
    
    # ✅ Limit to processing top 20 jobs
    top_jobs = jobs[:20]

    # ✅ Format user profile details
    skills = ", ".join(user_profile.get("demographics", {}).get("skills", []))
    industries = ", ".join(user_profile.get("demographics", {}).get("industries", []))
    experience = user_profile.get("demographics", {}).get("experience", "Not specified")
    
    profile_text = f"""
    User Skills: {skills or 'None'}
    Industries: {industries or 'None'}
    Experience Level: {experience or 'Not specified'}
    """

    preferences = user_profile.get("preferences", {})
    if preferences.get("role"):
        profile_text += f"\nDesired Role: {preferences['role']}"
    if preferences.get("location"):
        profile_text += f"\nPreferred Location: {preferences['location']}"
    if preferences.get("remote") is True:
        profile_text += "\nPrefers remote work"
    elif preferences.get("hybrid") is True:
        profile_text += "\nPrefers hybrid work"
    if preferences.get("salary_min"):
        profile_text += f"\nMinimum Salary: ${preferences['salary_min']}"

    # ✅ Format the jobs for the prompt
    jobs_text = "\n".join(
        f"""Job {i+1}:
        Title: {job.get('title', 'N/A')}
        Company: {job.get('company', 'Unknown')}
        Location: {job.get('location', 'Not specified')}
        Description: {job.get('description', 'No description available')[:300]}...
        Salary: {job.get('salary', 'Not specified')}
        Source: {job.get('source', 'Unknown')}
        Relevance Score: {job.get('relevance_score', 0)}"""
        for i, job in enumerate(top_jobs)
    )

    # ✅ Construct the Gemini prompt
    prompt = f"""
    Given the following user profile and a list of potential job recommendations, rank the top {limit} jobs that best match the user's skills, experience, and preferences.

    **USER PROFILE:**
    {profile_text}

    **POTENTIAL JOB RECOMMENDATIONS:**
    {jobs_text}

    **Instructions:**
    - Select and rank the **top {limit} job recommendations**.
    - For each selected job, provide:
      1. The **job number** from the original list.
      2. A **personalized explanation** (2-3 sentences) of why this job is relevant to the user's profile.
      3. A **relevance score from 1-100** based on how well the job matches the user's skills and preferences.

    **Format the response as a valid JSON array:**
    ```
    [
        {{"job_index": 1, "explanation": "This job matches your skills in data science and preference for remote work", "relevance_score": 85}},
        {{"job_index": 2, "explanation": "This role aligns with your experience in the healthcare industry", "relevance_score": 78}}
    ]
    ```
    """

    # ✅ Gemini API request with retry logic
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        data = call_gemini_api(payload)

        # ✅ Extract the response text safely
        response_text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        # ✅ Extract JSON from response using regex
        json_match = re.search(r'\[\s*\{.*\}\s*\]', response_text, re.DOTALL)
        if not json_match:
            raise ValueError("Failed to extract JSON from Gemini response")

        refined_results_data = json.loads(json_match.group())

        # ✅ Map the refined results to the original list
        final_recommendations = []
        for item in refined_results_data:
            job_index = item.get("job_index") - 1  # Convert from 1-based to 0-based
            if 0 <= job_index < len(top_jobs):
                recommendation = top_jobs[job_index].copy()
                recommendation["explanation"] = item.get("explanation", "No explanation provided.")
                recommendation["gemini_relevance_score"] = item.get("relevance_score", 0)
                final_recommendations.append(recommendation)
                
                # ✅ Stop once we reach the limit
                if len(final_recommendations) >= limit:
                    break

        return final_recommendations[:limit]  # Ensure limit is respected

    except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
        print(f"Error refining job recommendations: {e}")
        # ✅ Fallback: Return top jobs sorted by original relevance score
        return top_jobs[:limit]
