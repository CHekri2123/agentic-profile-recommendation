from typing import List, Dict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from datetime import datetime
from dateutil import parser
import logging

logging.basicConfig(level=logging.INFO)

def calculate_relevance_scores(jobs: List[Dict], user_profile: Dict) -> List[Dict]:
    """
    Computes relevance scores using TF-IDF similarity between user profile and job listings.
    
    Args:
        jobs: List of job listings (each containing 'title', 'description', etc.).
        user_profile: Dictionary containing user skills, experience, and preferences.

    Returns:
        List of jobs sorted by computed relevance scores.
    """
    
    # ✅ Return empty list if no jobs or user profile is missing
    if not jobs or not user_profile:
        return jobs
    
    # ✅ Extract key terms from user profile
    profile_terms = []
    
    # Add user skills, industries, and role preferences
    profile_terms.extend(user_profile.get("demographics", {}).get("skills", []) or [])
    profile_terms.extend(user_profile.get("demographics", {}).get("industries", []) or [])
    
    # Add user role preference
    role = user_profile.get("preferences", {}).get("role")
    if role:
        profile_terms.append(role)

    # ✅ Create a single profile query string
    profile_query = " ".join(profile_terms).lower().strip()
    
    # 1️⃣ Ensure Profile Query Exists Before TF-IDF
    if not profile_query:
        for job in jobs:
            job["relevance_score"] = 0
        return jobs
    
    # ✅ Prepare documents from job listings
    documents = [
        (job.get("title", "") + " " + job.get("description", "") + " " + 
         job.get("company", "") + " " + job.get("location", "")).lower().strip()
        for job in jobs
    ]

    # ✅ Use TF-IDF Vectorizer (English stopwords removed for better relevance)
    vectorizer = TfidfVectorizer(stop_words="english")
    
    try:
        # ✅ Fit TF-IDF on combined documents (jobs + user profile)
        all_docs = documents + [profile_query]
        tfidf_matrix = vectorizer.fit_transform(all_docs)
        
        # ✅ Extract profile vector (last document in matrix)
        profile_vector = tfidf_matrix[-1]
        
        # ✅ Compute cosine similarity in a vectorized manner
        doc_vectors = tfidf_matrix[:-1]
        profile_norm = np.linalg.norm(profile_vector.toarray())  # Norm of profile vector
        doc_norms = np.linalg.norm(doc_vectors.toarray(), axis=1)  # Norms of document vectors
        
        # ✅ Compute cosine similarity
        similarities = (doc_vectors @ profile_vector.T).toarray().flatten()
        similarities = np.divide(
            similarities, (doc_norms * profile_norm), 
            out=np.zeros_like(similarities), where=(doc_norms * profile_norm) != 0
        )
        
        # ✅ Scale cosine similarity to a 0-100 range
        scaled_scores = (similarities * 100).astype(float)
        
        # ✅ Apply job-specific relevance boosts
        for i, job in enumerate(jobs):
            score = scaled_scores[i]
            original_score = score

            # ✅ Boost jobs that match user's preferred location
            user_location = user_profile.get("preferences", {}).get("location", "").lower()
            job_location = job.get("location", "").lower()
            if user_location and user_location in job_location:
                score += np.log1p(score * 0.3)
                
            # ✅ Boost jobs that match user's remote/hybrid preferences
            if user_profile.get("preferences", {}).get("remote") is True and "remote" in job_location:
                score += np.log1p(score * 0.4)
            elif user_profile.get("preferences", {}).get("hybrid") is True and "hybrid" in job_location:
                score += np.log1p(score * 0.3)
            
            # ✅ Boost jobs from preferred companies
            preferred_companies = user_profile.get("preferences", {}).get("companies", [])
            job_company = job.get("company", "").lower()
            if any(company.lower() in job_company for company in preferred_companies):
                score += np.log1p(score * 0.5)
            
            # ✅ Apply recency boost
            posted_date = job.get("posted_date")
            if posted_date:
                try:
                    # 3️⃣ Standardize Date Parsing
                    pub_date = parser.parse(posted_date)
                    days_old = (datetime.utcnow() - pub_date).days
                    if days_old < 7:  # Give higher score to very recent jobs
                        score += np.log1p(score * 0.3)
                    elif days_old < 30:  # Give higher score to recent jobs
                        score += np.log1p(score * 0.15)
                except Exception as e:
                    logging.warning(f"Error parsing date: {e}")
            
            # ✅ Apply source-specific boosts
            source = job.get("source", "").lower()
            if source == "indeed":
                score += np.log1p(score * 0.05)
            elif source == "linkedin":
                score += np.log1p(score * 0.1)
            
            # ✅ Assign final rounded score
            job["relevance_score"] = round(score, 2)
            
            # 4️⃣ Add Debug Logging for Scores
            logging.info(f"Job: {job['title']} | Base Score: {original_score:.2f} | Final Score: {job['relevance_score']}")

    except Exception as e:
        logging.error(f"⚠️ Error calculating TF-IDF relevance scores: {e}")
        # ✅ Fallback: Assign default zero scores
        for job in jobs:
            job["relevance_score"] = 0

    # ✅ Sort jobs by computed relevance scores (highest first)
    jobs.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    return jobs
