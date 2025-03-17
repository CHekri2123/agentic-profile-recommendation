import requests
import streamlit as st
from typing import List, Dict, Optional

BOOKS_API_KEY = st.secrets["GOOGLE_BOOKS_API_KEY"]
MOVIES_API_KEY = st.secrets["TMDB_API_KEY"]

def fetch_books_data(query: str, limit: int = 5) -> List[Dict]:
    """Fetch book recommendations from Google Books API."""
    
    if not BOOKS_API_KEY:
        print("⚠️ Missing Google Books API Key. Skipping book fetch.")
        return []
    
    url = "https://www.googleapis.com/books/v1/volumes"
    
    params = {
        "q": query,
        "maxResults": limit,
        "key": BOOKS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()  # Raise error for failed responses (e.g., 404, 500)
        data = response.json()
        
        items = data.get("items", [])
        
        formatted_results = []
        for item in items:
            volume_info = item.get("volumeInfo", {})
            snippet = volume_info.get("description", "")

            formatted_results.append({
                "title": volume_info.get("title", "Unknown Title"),
                "link": volume_info.get("infoLink", ""),
                "snippet": (snippet[:200] + "...") if snippet else "No description available.",
                "source": "books",
                "source_name": "Google Books",
                "authors": volume_info.get("authors", ["Unknown Author"]),
                "published_date": volume_info.get("publishedDate", "Unknown Date")
            })
        
        return formatted_results
    
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error fetching books data: {str(e)}")
        return []

def fetch_movies_data(query: str, limit: int = 5) -> List[Dict]:
    """Fetch movie recommendations from TMDB API."""
    
    if not MOVIES_API_KEY:
        print("⚠️ Missing TMDB API Key. Skipping movie fetch.")
        return []
    
    url = "https://api.themoviedb.org/3/search/movie"
    
    params = {
        "api_key": MOVIES_API_KEY,
        "query": query,
        "page": 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])[:limit]
        
        formatted_results = []
        for result in results:
            snippet = result.get("overview", "")

            formatted_results.append({
                "title": result.get("title", "Unknown Title"),
                "link": f"https://www.themoviedb.org/movie/{result.get('id')}" if result.get("id") else "",
                "snippet": (snippet[:200] + "...") if snippet else "No overview available.",
                "source": "movies",
                "source_name": "TMDB",
                "release_date": result.get("release_date", "Unknown Date"),
                "vote_average": result.get("vote_average", 0)
            })
        
        return formatted_results
    
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error fetching movies data: {str(e)}")
        return []

# ✅ Placeholder for additional interest sources (e.g., tech news)
def fetch_tech_news(query: str, limit: int = 5) -> List[Dict]:
    """Fetch technology news articles."""
    # Implementation similar to above (e.g., using NewsAPI or web scraping)
    pass

# ✅ Test function for fetching books and movies
def test_interest_sources():
    """Test book and movie data fetching functions."""
    
    # ✅ Test Google Books API
    print("\n=== 📚 Testing Google Books API ===")
    books_query = "Artificial Intelligence"
    books_results = fetch_books_data(books_query, limit=3)
    
    print(f"✅ Found {len(books_results)} books for query: '{books_query}'")
    
    for i, result in enumerate(books_results, 1):
        print(f"\n--- 📖 Book {i} ---")
        print(f"Title: {result.get('title')}")
        print(f"Authors: {', '.join(result.get('authors', []))}")
        print(f"Published: {result.get('published_date')}")
        print(f"Link: {result.get('link')}")
        print(f"Snippet: {result.get('snippet')}")

    # ✅ Test TMDB API
    print("\n=== 🎬 Testing TMDB API ===")
    movies_query = "Science Fiction"
    movies_results = fetch_movies_data(movies_query, limit=3)
    
    print(f"✅ Found {len(movies_results)} movies for query: '{movies_query}'")
    
    for i, result in enumerate(movies_results, 1):
        print(f"\n--- 🎥 Movie {i} ---")
        print(f"Title: {result.get('title')}")
        print(f"Release Date: {result.get('release_date')}")
        print(f"Rating: {result.get('vote_average')}/10")
        print(f"Link: {result.get('link')}")
        print(f"Snippet: {result.get('snippet')}")

if __name__ == "__main__":
    test_interest_sources()
