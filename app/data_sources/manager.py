import itertools
from .adzuna_jobs import fetch_jobs_from_adzuna
from .jooble_jobs import fetch_jobs_from_jooble

def fetch_combined_jobs(query, location="USA", results=10):
    """Fetch job listings from multiple sources and combine them."""
    
    # Fetch from both sources
    adzuna_jobs = fetch_jobs_from_adzuna(query, location, results)
    jooble_jobs = fetch_jobs_from_jooble(query, location, results)

    # Merge results
    combined_jobs = list(itertools.chain(adzuna_jobs, jooble_jobs))
    
    # Remove duplicates based on job title and link
    unique_jobs = {job["link"]: job for job in combined_jobs}.values()

    return list(unique_jobs)

# Example usage
if __name__ == "__main__":
    jobs = fetch_combined_jobs("Software Engineer", "USA", 1)
    print(jobs[0])
