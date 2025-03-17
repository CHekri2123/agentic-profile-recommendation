# app/data_sources/manager.py
from typing import List, Dict
from .web_search import fetch_search_results
from .interest_sources import fetch_books_data, fetch_movies_data


def get_data_sources_for_interests(interests: List[str]) -> List[str]:
    """Map user interests to appropriate data sources."""
    source_mapping = {
        "books": ["books", "reading", "literature"],
        "movies": ["movies", "films", "cinema"],
        "tech": ["technology", "programming", "coding", "software", "AI", "artificial intelligence"]
        # Add more mappings as needed
    }
    
    active_sources = []
    for source, related_interests in source_mapping.items():
        if any(interest.lower() in [ri.lower() for ri in related_interests] for interest in interests):
            active_sources.append(source)
    
    return active_sources

def fetch_from_all_sources(query: str, user_profile: Dict) -> List[Dict]:
    """
    Fetch data from all relevant sources based on user profile.
    
    Args:
        query: Search query string
        user_profile: User profile dictionary
        
    Returns:
        Combined list of results from all sources
    """
    all_results = []
    
    # Always fetch web search results
    web_results = fetch_search_results(query, limit=10)
    all_results.extend(web_results)
    
    # Fetch from interest-specific sources
    interests = user_profile.get("interests", [])
    active_sources = get_data_sources_for_interests(interests)
    
    if "books" in active_sources:
        book_results = fetch_books_data(query, limit=5)
        all_results.extend(book_results)
    
    if "movies" in active_sources:
        movie_results = fetch_movies_data(query, limit=5)
        all_results.extend(movie_results)
    
    # Add more interest-specific sources as needed
    
    return all_results


def test_manager_functionality():
    """
    Test function to check if the manager is correctly combining results from all sources.
    
    Returns:
        A summary of results from different sources
    """
    # Dummy user profile with interests in movies and books
    user_profile = {
        "interests": ["AI", "movies", "books"],
        "preferences": {
            "role": "Data Scientist",
            "location": "San Francisco",
            "remote": True
        },
        "demographics": {
            "skills": ["Python", "Machine Learning"],
            "industries": ["Technology"]
        }
    }
    
    # Dummy query
    query = "Generative AI"
    print(f"Testing with query: '{query}'")
    
    # Get active sources based on interests
    interests = user_profile.get("interests", [])
    active_sources = get_data_sources_for_interests(interests)
    print(f"Active sources based on interests: {active_sources}")
    
    # Fetch results from all sources
    results = fetch_from_all_sources(query, user_profile)
    
    # Group results by source
    sources = {}
    for result in results:
        source = result.get('source')
        if source not in sources:
            sources[source] = 0
        sources[source] += 1
    
    # Print summary
    print(f"\nTotal results fetched: {len(results)}")
    print("\nResults by source:")
    for source, count in sources.items():
        print(f"- {source}: {count} results")
    
    return {
        "total_results": len(results),
        "sources_breakdown": sources,
        "results": results
    }

# You can call this function if the file is run directly
if __name__ == "__main__":
    test_manager_functionality()
