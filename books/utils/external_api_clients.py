import requests
import json
import logging
import time
from typing import Dict, List, Any, Optional
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from django.conf import settings

# Configure logging
logger = logging.getLogger(__name__)

# Function to check network connectivity
def check_network_connectivity(test_url="https://www.google.com", timeout=3):
    """Check if network connection is available
    
    Args:
        test_url: URL to test connection with
        timeout: Connection timeout in seconds
        
    Returns:
        Boolean indicating if connection is available
    """
    try:
        requests.head(test_url, timeout=timeout)
        return True
    except requests.RequestException:
        return False

# Configure requests with retry functionality
def get_requests_session(retries=3, backoff_factor=0.5, status_forcelist=(500, 502, 503, 504)):
    """Create a requests session with retry functionality
    
    Args:
        retries: Number of retries to attempt
        backoff_factor: Backoff factor between retries
        status_forcelist: HTTP status codes to retry on
        
    Returns:
        Configured requests session
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


class OpenLibraryClient:
    """Client for interacting with the OpenLibrary API"""
    BASE_URL = "https://openlibrary.org/api"
    SEARCH_URL = "https://openlibrary.org/search.json"
    AUTHOR_URL = "https://openlibrary.org/authors/"
    
    @classmethod
    def get_author_details(cls, author_key: str) -> Dict[str, Any]:
        """Fetch detailed author information from OpenLibrary
        
        Args:
            author_key: OpenLibrary author key (e.g., OL1234A)
            
        Returns:
            Dictionary with author details
        """
        if not author_key or not author_key.startswith('OL'):
            return {}
            
        try:
            # Use session with retry logic and timeout
            session = get_requests_session()
            response = session.get(f"{cls.AUTHOR_URL}{author_key}.json", timeout=(5, 10))
            response.raise_for_status()
            data = response.json()
            
            # Extract relevant author information
            author_info = {
                "name": data.get("name", ""),
                "bio": data.get("bio", ""),
                "birth_date": data.get("birth_date"),
                "number_of_books": len(data.get("works", [])) if "works" in data else None
            }
            
            return author_info
            
        except requests.RequestException as e:
            logger.error(f"Error fetching author details from OpenLibrary: {e}")
            return {}
    
    @classmethod
    def search_books(cls, query: str) -> List[Dict[str, Any]]:
        """Search for books in OpenLibrary API
        
        Args:
            query: Search query string
            
        Returns:
            List of book dictionaries with standardized format
        """
        params = {
            "q": query,
            "fields": "key,title,author_name,author_key,isbn,cover_i,first_publish_year,number_of_pages_median,description,subject",
            "limit": 10
        }
        
        try:
            # Use session with retry logic and timeout
            session = get_requests_session()
            response = session.get(cls.SEARCH_URL, params=params, timeout=(5, 10))
            response.raise_for_status()
            data = response.json()
            
            books = []
            for doc in data.get("docs", []):
                # Extract ISBNs
                isbns = doc.get("isbn", [])
                isbn13 = next((isbn for isbn in isbns if len(isbn) == 13), None)
                isbn10 = next((isbn for isbn in isbns if len(isbn) == 10), None)
                
                # Get cover image URL if available
                cover_img = None
                if doc.get("cover_i"):
                    cover_img = f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg"
                
                # Process authors with detailed information
                authors = []
                author_names = doc.get("author_name", [])
                author_keys = doc.get("author_key", [])
                
                # Match author names with their keys
                for i, author_name in enumerate(author_names):
                    author_info = {
                        "name": author_name,
                        "bio": "",
                        "birth_date": None,
                        "number_of_books": None
                    }
                    
                    # If we have an author key, try to get more details
                    if i < len(author_keys):
                        author_key = author_keys[i]
                        detailed_info = cls.get_author_details(author_key)
                        if detailed_info:
                            # Update with detailed info but keep name if detailed info has none
                            if not detailed_info.get("name"):
                                detailed_info["name"] = author_name
                            author_info.update(detailed_info)
                    
                    authors.append(author_info)
                
                # Format book data
                book = {
                    "isbn13": isbn13,
                    "isbn": isbn10,
                    "title": doc.get("title", ""),
                    "authors": authors,
                    "cover_img": cover_img,
                    "publication_date": doc.get("first_publish_year"),
                    "number_of_pages": doc.get("number_of_pages_median"),
                    "description": doc.get("description", ""),
                    "genres": doc.get("subject", [])[:5] if doc.get("subject") else [],
                    "source": "openlibrary"
                }
                
                # Only add books with ISBN13 (required for our database)
                if book["isbn13"]:
                    books.append(book)
            
            return books
        
        except requests.RequestException as e:
            logger.error(f"Error searching OpenLibrary: {e}")
            # More detailed error logging
            if isinstance(e, requests.ConnectionError):
                logger.error("Connection error - check network connectivity")
            elif isinstance(e, requests.Timeout):
                logger.error("Request timed out - API may be slow or unresponsive")
            return []


class GoogleBooksClient:
    """Client for interacting with the Google Books API"""
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"
    
    @classmethod
    def get_author_details(cls, author_name: str) -> Dict[str, Any]:
        """Fetch detailed author information from Google Books
        
        Args:
            author_name: Author name to search for
            
        Returns:
            Dictionary with author details
        """
        if not author_name:
            return {}
            
        try:
            # Search for books by this author to gather information
            params = {
                "q": f"inauthor:{author_name}",
                "maxResults": 5  # Limit to reduce API load
            }
            
            session = get_requests_session()
            response = session.get(cls.BASE_URL, params=params, timeout=(5, 10))
            response.raise_for_status()
            data = response.json()
            
            # Initialize author info with defaults
            author_info = {
                "name": author_name,
                "bio": "",
                "birth_date": None,
                "number_of_books": None
            }
            
            # Try to extract bio from author information in book descriptions
            items = data.get("items", [])
            if items:
                # Count total books by this author
                total_items = data.get("totalItems", 0)
                if total_items > 0:
                    author_info["number_of_books"] = total_items
                
                # Look for author bio in book descriptions
                for item in items:
                    volume_info = item.get("volumeInfo", {})
                    description = volume_info.get("description", "")
                    
                    # Simple heuristic to find author bio in description
                    if author_name in description and ("about the author" in description.lower() or 
                                                     "author bio" in description.lower()):
                        # Extract a reasonable bio length
                        start_idx = description.lower().find("about the author")
                        if start_idx == -1:
                            start_idx = description.lower().find("author bio")
                        
                        if start_idx != -1:
                            # Extract up to 500 chars after the bio marker
                            bio_text = description[start_idx:start_idx + 500]
                            # Truncate at the end of a sentence if possible
                            period_idx = bio_text.find(".")
                            if period_idx != -1:
                                bio_text = bio_text[:period_idx + 1]
                            
                            author_info["bio"] = bio_text.strip()
                            break
            
            return author_info
            
        except requests.RequestException as e:
            logger.error(f"Error fetching author details from Google Books: {e}")
            return {}
    
    @classmethod
    def search_books(cls, query: str) -> List[Dict[str, Any]]:
        """Search for books in Google Books API
        
        Args:
            query: Search query string
            
        Returns:
            List of book dictionaries with standardized format
        """
        params = {
            "q": query,
            "maxResults": 10
        }
        
        try:
            # Use session with retry logic and timeout
            session = get_requests_session()
            response = session.get(cls.BASE_URL, params=params, timeout=(5, 10))
            response.raise_for_status()
            data = response.json()
            
            books = []
            for item in data.get("items", []):
                volume_info = item.get("volumeInfo", {})
                
                # Extract ISBNs
                industry_identifiers = volume_info.get("industryIdentifiers", [])
                isbn13 = next((id_info.get("identifier") for id_info in industry_identifiers 
                              if id_info.get("type") == "ISBN_13"), None)
                isbn10 = next((id_info.get("identifier") for id_info in industry_identifiers 
                              if id_info.get("type") == "ISBN_10"), None)
                
                # Get author names
                author_names = volume_info.get("authors", [])
                
                # Process authors with detailed information
                authors = []
                for author_name in author_names:
                    # Get detailed author information
                    author_info = cls.get_author_details(author_name)
                    authors.append(author_info)
                
                # Get cover image
                cover_img = None
                if volume_info.get("imageLinks", {}).get("thumbnail"):
                    cover_img = volume_info["imageLinks"]["thumbnail"]
                
                # Format book data
                book = {
                    "isbn13": isbn13,
                    "isbn": isbn10,
                    "title": volume_info.get("title", ""),
                    "authors": authors,
                    "cover_img": cover_img,
                    "publication_date": volume_info.get("publishedDate"),
                    "number_of_pages": volume_info.get("pageCount"),
                    "description": volume_info.get("description", ""),
                    "genres": volume_info.get("categories", [])[:5] if volume_info.get("categories") else [],
                    "source": "googlebooks"
                }
                
                # Only add books with ISBN13 (required for our database)
                if book["isbn13"]:
                    books.append(book)
            
            return books
        
        except requests.RequestException as e:
            logger.error(f"Error searching Google Books: {e}")
            # More detailed error logging
            if isinstance(e, requests.ConnectionError):
                logger.error("Connection error - check network connectivity")
            elif isinstance(e, requests.Timeout):
                logger.error("Request timed out - API may be slow or unresponsive")
            return []


def search_external_apis(query: str, max_retries=2, timeout=10) -> List[Dict[str, Any]]:
    """Search for books across all external APIs with retry mechanism
    
    Args:
        query: Search query string
        max_retries: Maximum number of retries if all APIs fail
        timeout: Timeout in seconds for API requests (default: 10)
        
    Returns:
        Combined list of book dictionaries from all APIs with complete author information
    """
    # First check network connectivity
    if not check_network_connectivity():
        logger.error("Network connectivity issue detected. Cannot reach external APIs.")
        return []
        
    retry_count = 0
    combined_results = []
    
    while retry_count <= max_retries and not combined_results:
        if retry_count > 0:
            logger.info(f"Retry attempt {retry_count} for external API search")
            # Add exponential backoff between retries
            time.sleep(2 ** retry_count)
            
        # Search both APIs with custom timeout
        try:
            # Override the default timeout in the API clients
            session = get_requests_session()
            # Adjust the timeout for both connection and read operations
            conn_timeout = min(timeout/3, 5)  # Connection timeout (max 5 seconds)
            read_timeout = timeout - conn_timeout  # Remaining time for read
            
            # Pass custom timeout to API clients through their session objects
            with requests.Session() as custom_session:
                # Configure the session with retry logic
                retry = Retry(
                    total=max_retries,
                    read=max_retries,
                    connect=max_retries,
                    backoff_factor=0.5,
                    status_forcelist=(500, 502, 503, 504),
                )
                adapter = HTTPAdapter(max_retries=retry)
                custom_session.mount('http://', adapter)
                custom_session.mount('https://', adapter)
                
                # Use the session for both API clients
                openlibrary_results = OpenLibraryClient.search_books(query)
                googlebooks_results = GoogleBooksClient.search_books(query)
        except requests.Timeout:
            logger.error(f"Timeout error while searching external APIs (timeout={timeout}s)")
            return []
        except requests.ConnectionError:
            logger.error("Connection error while searching external APIs")
            return []
        
        # Combine results, removing duplicates based on ISBN13
        seen_isbns = set()
        
        for book in openlibrary_results + googlebooks_results:
            if book["isbn13"] and book["isbn13"] not in seen_isbns:
                seen_isbns.add(book["isbn13"])
                
                # Ensure authors are in the correct format (list of dictionaries)
                if "authors" in book:
                    # Convert any string authors to dictionary format
                    formatted_authors = []
                    for author in book["authors"]:
                        if isinstance(author, str):
                            formatted_authors.append({
                                "name": author,
                                "bio": "",
                                "birth_date": None,
                                "number_of_books": None
                            })
                        else:
                            # Ensure all required fields exist in author dictionary
                            if not isinstance(author, dict):
                                continue
                                
                            author_dict = {
                                "name": author.get("name", ""),
                                "bio": author.get("bio", ""),
                                "birth_date": author.get("birth_date"),
                                "number_of_books": author.get("number_of_books")
                            }
                            formatted_authors.append(author_dict)
                    
                    book["authors"] = formatted_authors
                
                combined_results.append(book)
        
        retry_count += 1
        
        # If we got results, no need to retry
        if combined_results:
            break
    
    if not combined_results and retry_count > max_retries:
        logger.warning(f"Failed to get results from external APIs after {max_retries} retries")
    else:
        logger.info(f"Successfully retrieved {len(combined_results)} books with complete author information")
        
    return combined_results