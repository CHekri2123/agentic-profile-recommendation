# app/relevance_scorer.py
from typing import List, Dict
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

def calculate_relevance_scores(results: List[Dict], user_profile: Dict) -> List[Dict]:
    """Calculate relevance scores using TF-IDF."""
    if not results or not user_profile:
        return results
    
    # Extract key terms from user profile
    profile_terms = []
    
    # Add interests
    profile_terms.extend(user_profile.get("interests", []) or [])
    
    # Add skills
    profile_terms.extend(user_profile.get("demographics", {}).get("skills", []) or [])
    
    # Add industries
    profile_terms.extend(user_profile.get("demographics", {}).get("industries", []) or [])
    
    # Add role if specified
    if user_profile.get("preferences", {}).get("role"):
        profile_terms.append(user_profile["preferences"]["role"])
    
    # Create user profile query
    profile_query = " ".join(profile_terms)
    
    # Prepare documents from results
    documents = []
    for result in results:
        # Combine title and snippet
        doc = (result.get("title", "") + " " + result.get("snippet", "")).lower()
        documents.append(doc)
    
    # If no documents or empty profile, return results with zero scores
    if not documents or not profile_query:
        for result in results:
            result["relevance_score"] = 0
        return results
    
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(stop_words='english')
    
    try:
        # Add profile query to documents for vectorization
        all_docs = documents + [profile_query]
        tfidf_matrix = vectorizer.fit_transform(all_docs)
        
        # Get profile vector (last document)
        profile_vector = tfidf_matrix[-1]
        
        # Calculate cosine similarity between profile and each document
        # Manually calculate cosine similarity to avoid extra dependencies
        doc_vectors = tfidf_matrix[:-1]
        profile_norm = np.sqrt(profile_vector.multiply(profile_vector).sum())
        
        for i, result in enumerate(results):
            doc_vector = doc_vectors[i]
            doc_norm = np.sqrt(doc_vector.multiply(doc_vector).sum())
            
            # Dot product
            dot_product = doc_vector.multiply(profile_vector).sum()
            
            # Cosine similarity
            if doc_norm > 0 and profile_norm > 0:
                similarity = dot_product / (doc_norm * profile_norm)
            else:
                similarity = 0
                
            # Scale to 0-100 range
            score = float(similarity * 100)
            
            # Apply source-specific boosts
            if result.get("source") == "web_search":
                score *= 1.0  # Neutral weight
            elif result.get("source") == "books" and "books" in user_profile.get("interests", []):
                score *= 1.5  # Boost for matching interest
            elif result.get("source") == "movies" and "movies" in user_profile.get("interests", []):
                score *= 1.5  # Boost for matching interest
            
            # Add recency boost if available
            if result.get("published_date") or result.get("release_date"):
                # Implementation depends on your date format
                pass
            
            result["relevance_score"] = round(score, 2)
    
    except Exception as e:
        print(f"Error calculating TF-IDF scores: {str(e)}")
        # Fallback to original scoring method
        for result in results:
            result["relevance_score"] = 0
    
    # Sort by relevance score
    results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    return results
