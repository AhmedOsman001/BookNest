from elasticsearch_dsl import Q
from elasticsearch.exceptions import ConnectionError, TransportError, NotFoundError
from books.search_indexes import BookDocument
from typing import List, Dict, Any, Optional, Tuple
import logging
import time
import socket

# Configure logging
logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Client for interacting with Elasticsearch"""
    
    @classmethod
    def check_connection(cls, max_retries=3, retry_interval=2):
        """Check if Elasticsearch is available and retry if necessary
        
        Args:
            max_retries: Maximum number of connection retries
            retry_interval: Seconds to wait between retries
            
        Returns:
            Boolean indicating if connection is available
        """
        retries = 0
        while retries < max_retries:
            try:
                # Try to create a search object and execute a simple query
                search = BookDocument.search()
                search.execute()
                return True
            except (ConnectionError, TransportError) as e:
                logger.warning(f"Elasticsearch connection error (attempt {retries+1}/{max_retries}): {str(e)}")
                retries += 1
                if retries < max_retries:
                    time.sleep(retry_interval)
            except Exception as e:
                logger.error(f"Unexpected error checking Elasticsearch connection: {str(e)}")
                return False
        
        return False
    
    @classmethod
    def search_books(cls, query: str, page: int = 1, page_size: int = 10, 
                     filters: Optional[Dict[str, Any]] = None, max_retries: int = 2) -> Tuple[List[Dict[str, Any]], int]:
        """Search for books in Elasticsearch with pagination and filtering
        
        Args:
            query: Search query string
            page: Page number (1-indexed)
            page_size: Number of results per page
            filters: Dictionary of filters to apply (e.g. {'genres': ['Fiction'], 'min_rating': 4})
            
        Returns:
            Tuple of (list of book dictionaries, total count)
        """
        # First check if Elasticsearch is available
        if not cls.check_connection():
            logger.error("Elasticsearch is not available")
            return [], 0
            
        # Create a multi-match query that searches across multiple fields
        search_query = Q(
            'multi_match',
            query=query,
            fields=[
                'title^3',  # Boost title matches
                'authors.name^2',  # Boost author matches
                'description',
                'isbn13',
                'isbn',
                'genres'
            ],
            fuzziness='AUTO'  # Allow for typos and fuzzy matching
        )
        
        # Start with the base search query
        search = BookDocument.search().query(search_query)
        
        # Apply filters if provided
        if filters:
            # Filter by genres
            if 'genres' in filters and filters['genres']:
                search = search.filter('terms', genres=filters['genres'])
            
            # Filter by minimum rating
            if 'min_rating' in filters and filters['min_rating'] is not None:
                search = search.filter('range', average_rate={'gte': filters['min_rating']})
            
            # Filter by publication date range
            if 'pub_date_from' in filters and filters['pub_date_from']:
                search = search.filter('range', publication_date={'gte': filters['pub_date_from']})
            if 'pub_date_to' in filters and filters['pub_date_to']:
                search = search.filter('range', publication_date={'lte': filters['pub_date_to']})
            
            # Filter by author
            if 'author' in filters and filters['author']:
                search = search.filter('nested', path='authors', query=Q('match', authors__name=filters['author']))
        
        # Calculate pagination parameters
        start = (page - 1) * page_size
        end = start + page_size
        
        # Apply pagination
        search = search[start:end]
        
        # Execute the search with retry mechanism
        retries = 0
        while True:
            try:
                response = search.execute()
                
                # Format the results
                books = []
                for hit in response:
                    book = {
                        'isbn13': hit.isbn13,
                        'isbn': hit.isbn,
                        'title': hit.title,
                        'authors': [author['name'] for author in hit.authors] if hasattr(hit, 'authors') else [],
                        'cover_img': hit.cover_img if hasattr(hit, 'cover_img') else None,
                        'publication_date': hit.publication_date if hasattr(hit, 'publication_date') else None,
                        'number_of_pages': hit.number_of_pages if hasattr(hit, 'number_of_pages') else None,
                        'description': hit.description if hasattr(hit, 'description') else '',
                        'average_rate': hit.average_rate if hasattr(hit, 'average_rate') else None,
                        'source': 'elasticsearch'
                    }
                    books.append(book)
                
                # Return both the books and the total count
                return books, response.hits.total.value
                
            except (ConnectionError, TransportError) as e:
                retries += 1
                logger.warning(f"Elasticsearch search error (attempt {retries}/{max_retries}): {str(e)}")
                if retries >= max_retries:
                    logger.error(f"Failed to search Elasticsearch after {max_retries} attempts")
                    return [], 0
                time.sleep(1)  # Wait before retrying
            except Exception as e:
                logger.error(f"Unexpected error during Elasticsearch search: {str(e)}")
                return [], 0
    
    @classmethod
    def suggest_books(cls, query: str, limit: int = 5, max_retries: int = 2) -> List[Dict[str, Any]]:
        """Get book title suggestions based on a partial query
        
        Args:
            query: Partial search query string
            limit: Maximum number of suggestions to return
            
        Returns:
            List of book title suggestions
        """
        # First check if Elasticsearch is available
        if not cls.check_connection():
            logger.error("Elasticsearch is not available for suggestions")
            return []
            
        # Create a completion suggester query
        suggest = {
            'title_suggest': {
                'prefix': query,
                'completion': {
                    'field': 'title.suggest',
                    'size': limit,
                    'fuzzy': {
                        'fuzziness': 1
                    }
                }
            }
        }
        
        # Execute the suggestion query with retry mechanism
        search = BookDocument.search()
        search = search.suggest('title_suggest', query, completion={
            'field': 'title.suggest',
            'size': limit,
            'fuzzy': {
                'fuzziness': 1
            }
        })
        
        retries = 0
        while True:
            try:
                response = search.execute()
                break
            except (ConnectionError, TransportError) as e:
                retries += 1
                logger.warning(f"Elasticsearch suggestion error (attempt {retries}/{max_retries}): {str(e)}")
                if retries >= max_retries:
                    logger.error(f"Failed to get suggestions from Elasticsearch after {max_retries} attempts")
                    return []
                time.sleep(1)  # Wait before retrying
            except Exception as e:
                logger.error(f"Unexpected error during Elasticsearch suggestion: {str(e)}")
                return []
        
        # Extract suggestions
        suggestions = []
        if hasattr(response, 'suggest') and 'title_suggest' in response.suggest:
            for option in response.suggest.title_suggest[0].options:
                suggestions.append({
                    'id': option._id,
                    'title': option.text,
                    'score': option._score,
                    # 'source':option._source
                    
                })
        
        return suggestions