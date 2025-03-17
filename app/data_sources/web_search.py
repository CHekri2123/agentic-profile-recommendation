# app/data_sources/web_search.py
import requests
import streamlit as st
from typing import List, Dict
import json
from bs4 import BeautifulSoup
import time
import concurrent.futures
from urllib.parse import urlparse
import re


SERP_API_KEY = st.secrets["SERPAPI_KEY"]

def fetch_search_results(query: str, limit: int = 10) -> List[Dict]:

    url = "https://serpapi.com/search"
    
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "engine": "google",
        "num": limit
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if "error" in data:
            print(f"Error in search API: {data['error']}")
            return []
        
        organic_results = data.get("organic_results", [])
        
        # Format the results
        formatted_results = []
        for result in organic_results:
            formatted_results.append({
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "snippet": result.get("snippet", ""),
                "source": "web_search",
                "source_name": "Google Search"
            })
        
        # Fetch content for each result
        results_with_content = fetch_content_for_results(formatted_results)
        
        return results_with_content
    
    except Exception as e:
        print(f"Error fetching search results: {str(e)}")
        return []

def fetch_content_for_results(results: List[Dict], max_workers: int = 5) -> List[Dict]:

    # Use ThreadPoolExecutor for parallel fetching
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all fetch tasks
        future_to_result = {
            executor.submit(fetch_and_extract_content, result): result 
            for result in results
        }
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_result):
            result = future_to_result[future]
            try:
                content = future.result()
                result["content"] = content
            except Exception as e:
                print(f"Error fetching content for {result.get('link')}: {str(e)}")
                result["content"] = ""
    
    return results

def fetch_and_extract_content(result: Dict) -> str:

    url = result.get("link", "")
    if not url:
        return ""
    
    # Skip certain file types and domains that are likely not to contain readable content
    if should_skip_url(url):
        return ""
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        # Add a small delay to avoid overwhelming servers
        time.sleep(0.5)
        
        # Fetch the webpage with a timeout
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check if the response is HTML
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type:
            return f"[Non-HTML content: {content_type}]"
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script, style, and other non-content elements
        for element in soup(['script', 'style', 'header', 'footer', 'nav', 'aside', 'noscript', 'iframe', 'svg']):
            element.decompose()
        
        # Extract text from main content areas
        main_content = extract_main_content(soup, url)
        
        # Clean up the text
        content = clean_text(main_content)
        
        # Limit content length to avoid extremely large texts
        if len(content) > 5000:
            content = content[:5000] + "..."
        
        return content
    
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        return ""

def extract_main_content(soup, url):

    # Try to find main content containers
    main_containers = soup.select('main, article, #content, .content, #main, .main, .post, .article, .post-content, .article-content')
    
    if main_containers:
        # Use the first main container found
        return main_containers[0].get_text(separator=' ', strip=True)
    
    # If no main containers, look for <p> tags with substantial content
    paragraphs = soup.find_all('p')
    if paragraphs:
        return ' '.join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20)
    
    # Fallback to body content
    body = soup.find('body')
    if body:
        return body.get_text(separator=' ', strip=True)
    
    return ""

def clean_text(text):
    """Clean up extracted text."""
    # Replace multiple whitespace with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove any remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove extra whitespace at the beginning and end
    text = text.strip()
    
    return text

def should_skip_url(url):
    """Check if URL should be skipped based on domain or file type."""
    # Parse URL
    parsed_url = urlparse(url)
    
    # Skip certain file types
    file_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.zip', '.rar', '.jpg', '.jpeg', '.png', '.gif']
    if any(parsed_url.path.endswith(ext) for ext in file_extensions):
        return True
    
    # Skip certain domains that are likely to block scraping or not contain useful content
    blocked_domains = ['facebook.com', 'twitter.com', 'instagram.com', 'youtube.com', 'linkedin.com']
    if any(domain in parsed_url.netloc for domain in blocked_domains):
        return True
    
    return False


