from typing import List, Dict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from datetime import datetime

def calculate_relevance_scores(results: List[Dict], user_profile: Dict) -> List[Dict]:
    """
    Computes relevance scores using TF-IDF similarity between user profile and recommendation data.
    
    Args:
        results: List of recommendation results (each containing 'title' and 'snippet').
        user_profile: Dictionary containing user interests, skills, and preferences.

    Returns:
        List of results sorted by computed relevance scores.
    """
    
    # ✅ Return empty list if no results or user profile is missing
    if not results or not user_profile:
        return results
    
    # ✅ Extract key terms from user profile
    profile_terms = []
    
    # Add user interests, skills, and industries
    profile_terms.extend(user_profile.get("interests", []) or [])
    profile_terms.extend(user_profile.get("demographics", {}).get("skills", []) or [])
    profile_terms.extend(user_profile.get("demographics", {}).get("industries", []) or [])
    
    # Add user role preference
    role = user_profile.get("preferences", {}).get("role")
    if role:
        profile_terms.append(role)

    # ✅ Create a single profile query string
    profile_query = " ".join(profile_terms).lower().strip()
    
    # ✅ Prepare documents from recommendation results
    documents = [
        (result.get("title", "") + " " + result.get("snippet", "")).lower().strip()
        for result in results
    ]
    
    # ✅ Return results with zero scores if there's no meaningful user profile or documents
    if not documents or not profile_query:
        for result in results:
            result["relevance_score"] = 0
        return results

    # ✅ Use TF-IDF Vectorizer (English stopwords removed for better relevance)
    vectorizer = TfidfVectorizer(stop_words="english")
    
    try:
        # ✅ Fit TF-IDF on combined documents (results + user profile)
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
        
        # ✅ Apply source-specific relevance boosts
        for i, result in enumerate(results):
            score = scaled_scores[i]

            if result.get("source") == "books" and "books" in user_profile.get("interests", []):
                score *= 1.5  # Boost book-related results
            elif result.get("source") == "movies" and "movies" in user_profile.get("interests", []):
                score *= 1.5  # Boost movie-related results
            
            # ✅ Apply recency boost (if applicable)
            published_date = result.get("published_date") or result.get("release_date")
            if published_date:
                try:
                    pub_date = datetime.strptime(published_date, "%Y-%m-%d")  # Ensure date format is YYYY-MM-DD
                    days_old = (datetime.utcnow() - pub_date).days
                    if days_old < 30:  # Give higher score to recent content
                        score *= 1.2
                except Exception:
                    pass  # Ignore errors if date format is incorrect
            
            # ✅ Assign final rounded score
            result["relevance_score"] = round(score, 2)

    except Exception as e:
        print(f"⚠️ Error calculating TF-IDF relevance scores: {e}")
        # ✅ Fallback: Assign default zero scores
        for result in results:
            result["relevance_score"] = 0

    # ✅ Sort results by computed relevance scores (highest first)
    results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    return results
