# app/data_sources/interest_sources.py
import requests
import os
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()
BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
MOVIES_API_KEY = os.getenv("TMDB_API_KEY")

def fetch_books_data(query: str, limit: int = 5) -> List[Dict]:
    """Fetch book recommendations from Google Books API."""
    url = "https://www.googleapis.com/books/v1/volumes"
    
    params = {
        "q": query,
        "maxResults": limit,
        "key": BOOKS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        items = data.get("items", [])
        
        formatted_results = []
        for item in items:
            volume_info = item.get("volumeInfo", {})
            formatted_results.append({
                "title": volume_info.get("title", ""),
                "link": volume_info.get("infoLink", ""),
                "snippet": volume_info.get("description", "")[:200] + "..." if volume_info.get("description") else "",
                "source": "books",
                "source_name": "Google Books",
                "authors": volume_info.get("authors", []),
                "published_date": volume_info.get("publishedDate", "")
            })
        
        return formatted_results
    
    except Exception as e:
        print(f"Error fetching books data: {str(e)}")
        return []

def fetch_movies_data(query: str, limit: int = 5) -> List[Dict]:
    """Fetch movie recommendations from TMDB API."""
    url = "https://api.themoviedb.org/3/search/movie"
    
    params = {
        "api_key": MOVIES_API_KEY,
        "query": query,
        "page": 1
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        results = data.get("results", [])[:limit]
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                "title": result.get("title", ""),
                "link": f"https://www.themoviedb.org/movie/{result.get('id')}" if result.get("id") else "",
                "snippet": result.get("overview", "")[:200] + "..." if result.get("overview") else "",
                "source": "movies",
                "source_name": "TMDB",
                "release_date": result.get("release_date", ""),
                "vote_average": result.get("vote_average", 0)
            })
        
        return formatted_results
    
    except Exception as e:
        print(f"Error fetching movies data: {str(e)}")
        return []

# Add more interest-based data sources as needed
def fetch_tech_news(query: str, limit: int = 5) -> List[Dict]:
    """Fetch technology news articles."""
    # Implementation similar to above
    pass

def test_interest_sources():
    # Test Google Books API
    print("=== Testing Google Books API ===")
    books_query = "Artificial Intelligence"
    
    print(f"Fetching book data for query: '{books_query}'")
    books_results = fetch_books_data(books_query, limit=3)
    
    print(f"Found {len(books_results)} books")
    
    # Print book results
    for i, result in enumerate(books_results, 1):
        print(f"\n--- Book {i} ---")
        print(f"Title: {result.get('title')}")
        print(f"Authors: {', '.join(result.get('authors', []))}")
        print(f"Published: {result.get('published_date')}")
        print(f"Link: {result.get('link')}")
        print(f"Snippet: {result.get('snippet')}")
    
    # Test TMDB API
    print("\n\n=== Testing TMDB API ===")
    movies_query = "Science Fiction"
    
    print(f"Fetching movie data for query: '{movies_query}'")
    movies_results = fetch_movies_data(movies_query, limit=3)
    
    print(f"Found {len(movies_results)} movies")
    
    # Print movie results
    for i, result in enumerate(movies_results, 1):
        print(f"\n--- Movie {i} ---")
        print(f"Title: {result.get('title')}")
        print(f"Release Date: {result.get('release_date')}")
        print(f"Rating: {result.get('vote_average')}/10")
        print(f"Link: {result.get('link')}")
        print(f"Snippet: {result.get('snippet')}")

if __name__ == "__main__":
    test_interest_sources()
