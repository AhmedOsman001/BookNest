from typing import Dict, List, Any, Optional
import logging
import requests
from django.db import transaction
from books.models import Book, Author, BookAuthor, BookGenre
from books.utils.external_api_clients import search_external_apis
from books.utils.elasticsearch_client import ElasticsearchClient

# Configure logging
logger = logging.getLogger(__name__)


# def get_books_by_ids(book_ids: List[str]) -> List[Dict[str, Any]]:
#     """Retrieve full book details from database using Elasticsearch IDs"""
#     try:
#         books = Book.objects.filter(isbn13__in=book_ids)
#         return [{
#             'id': str(book.id),
#             'title': book.title,
#             'authors': [author.name for author in book.authors.all()],
#             'cover_img': book.cover_img,
#             'description': book.description
#         } for book in books]
#     except Exception as e:
#         logger.error(f"Error fetching books by IDs: {e}")
#         return []


def search_books(query: str, page: int = 1, page_size: int = 10, 
               filters: Optional[Dict[str, Any]] = None) -> tuple[List[Dict[str, Any]], int]:
    """
    Search for books in Elasticsearch first, then in the database, and finally in external APIs if needed.
    Supports pagination and filtering.
    
    Args:
        query: Search query string
        page: Page number (1-indexed)
        page_size: Number of results per page
        filters: Dictionary of filters to apply (e.g. {'genres': ['Fiction'], 'min_rating': 4})
        
    Returns:
        Tuple of (list of book dictionaries, total count)
    """
    # First, check if Elasticsearch is available
    if ElasticsearchClient.check_connection(max_retries=1):
        try:
            # Search in Elasticsearch with retry mechanism
            es_books, total_count = ElasticsearchClient.search_books(
                query, 
                page=page, 
                page_size=page_size, 
                filters=filters,
                max_retries=2
            )
            if es_books:
                logger.info(f"Found {len(es_books)} books in Elasticsearch for query: {query}")
                return es_books, total_count
            else:
                logger.info(f"No books found in Elasticsearch for query: {query}")
        except Exception as e:
            # Log the error but continue with other search methods
            logger.warning(f"Elasticsearch search error: {e}")
    else:
        logger.warning("Elasticsearch is not available, falling back to database search")
    
    # If no results from Elasticsearch, search in the local database
    try:
        # Build the base query
        db_query = Book.objects.filter(title__icontains=query)
        
        # Apply filters to database query if provided
        if filters:
            # Filter by genres
            if 'genres' in filters and filters['genres']:
                db_query = db_query.filter(genres__name__in=filters['genres'])
            
            # Filter by minimum rating
            if 'min_rating' in filters and filters['min_rating'] is not None:
                db_query = db_query.filter(average_rate__gte=filters['min_rating'])
            
            # Filter by publication date range
            if 'pub_date_from' in filters and filters['pub_date_from']:
                db_query = db_query.filter(publication_date__gte=filters['pub_date_from'])
            if 'pub_date_to' in filters and filters['pub_date_to']:
                db_query = db_query.filter(publication_date__lte=filters['pub_date_to'])
            
            # Filter by author
            if 'author' in filters and filters['author']:
                db_query = db_query.filter(authors__name__icontains=filters['author']).distinct()
        
        # Get total count for pagination
        total_count = db_query.count()
        
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        db_books = db_query.prefetch_related('authors', 'genres')[start:end]
        
        # If we found books in the database, return them
        if db_books.exists():
            # Convert to list of dictionaries
            books = [{
                'isbn13': book.isbn13,
                'isbn': book.isbn,
                'title': book.title,
                'authors': [author.name for author in book.authors.all()],
                'cover_img': book.cover_img,
                'publication_date': book.publication_date,
                'number_of_pages': book.number_of_pages,
                'description': book.description,
                'average_rate': book.average_rate,
                'source': 'database'
            } for book in db_books]
            return books, total_count
    except Exception as e:
        # Log the error but continue with external API search
        logger.warning(f"Database search error: {e}")
    
    # If no books found in database or an error occurred, search external APIs
    try:
        # First check network connectivity
        from books.utils.external_api_clients import check_network_connectivity
        if not check_network_connectivity():
            logger.error("Network connectivity issue detected. Cannot reach external APIs.")
            return [], 0
            
        # Use the improved search_external_apis with retry mechanism and increased timeout
        try:
            external_books = search_external_apis(query, max_retries=3, timeout=15)  # Increased timeout and retries
        except requests.Timeout:
            logger.error("Timeout while connecting to external APIs. Try again later.")
            return [], 0
        except requests.ConnectionError:
            logger.error("Connection error while accessing external APIs. Check network connectivity.")
            return [], 0
        
        # Save external books to database - only if we have results
        if external_books:
            successful_saves = 0
            for book_data in external_books:
                try:
                    result = save_external_book(book_data)
                    if result:
                        successful_saves += 1
                except Exception as e:
                    logger.error(f"Error saving external book: {e}")
            
            if successful_saves > 0:
                logger.info(f"Successfully saved {successful_saves} out of {len(external_books)} books")
        
        # Return the external books with their count
        return external_books, len(external_books)
    except Exception as e:
        logger.error(f"External API search error: {e}", exc_info=True)
        return [], 0


@transaction.atomic
def save_external_book(book_data: Dict[str, Any]) -> Optional[Book]:
    """
    Save a book from external API to the database.
    
    Args:
        book_data: Book data from external API
        
    Returns:
        Created Book instance or None if failed
    """
    # Validate required fields before attempting to save
    if not book_data.get('isbn13') or not book_data.get('title'):
        logger.warning("Cannot save book: missing required fields (isbn13 or title)")
        return None
    
    # Check for network connectivity issues with cover image URL
    if book_data.get('cover_img'):
        from books.utils.external_api_clients import check_network_connectivity
        if not check_network_connectivity():
            # If network is down, set cover_img to None to avoid connection errors
            logger.warning(f"Network connectivity issue detected. Setting cover_img to None for book {book_data['title']}")
            book_data['cover_img'] = None
        
    try:
        # Check if book already exists - use get_or_none pattern to avoid exceptions
        existing_book = Book.objects.filter(isbn13=book_data['isbn13']).first()
        if existing_book:
            logger.info(f"Book with ISBN13 {book_data['isbn13']} already exists")
            return None
        
        # Create book
        book = Book(
            isbn13=book_data['isbn13'],
            isbn=book_data.get('isbn'),
            title=book_data['title'],
            cover_img=book_data.get('cover_img'),
            description=book_data.get('description', ''),
            number_of_pages=book_data.get('number_of_pages'),
            average_rate=None  # No ratings yet
        )
        
        # Handle publication date (might be just a year from some APIs)
        try:
            pub_date = book_data.get('publication_date')
            if pub_date and isinstance(pub_date, int):
                from datetime import date
                book.publication_date = date(pub_date, 1, 1)  # Default to January 1st
            elif pub_date and isinstance(pub_date, str):
                # Try to parse string date in various formats
                from dateutil.parser import parse
                try:
                    book.publication_date = parse(pub_date).date()
                except (ValueError, TypeError):
                    # If parsing fails, try to extract just the year
                    import re
                    year_match = re.search(r'\d{4}', pub_date)
                    if year_match:
                        from datetime import date
                        book.publication_date = date(int(year_match.group()), 1, 1)
                    else:
                        book.publication_date = None
            else:
                book.publication_date = pub_date
        except Exception as e:
            logger.warning(f"Error processing publication date: {e}")
            book.publication_date = None
        
        book.save()
        
        # Create authors
        if book_data.get('authors'):
            for author_data in book_data.get('authors', []):
                try:
                    # Handle both string author names and author dictionaries
                    if isinstance(author_data, str):
                        author_name = author_data
                        author_bio = None
                        author_birth_date = None
                        author_num_books = 1
                    else:
                        # Extract author details from dictionary
                        author_name = author_data.get('name', '')
                        author_bio = author_data.get('bio', None)
                        author_birth_date = author_data.get('birth_date')
                        # Validate number_of_books to ensure it's within SmallIntegerField range (-32768 to 32767)
                        author_num_books = author_data.get('number_of_books', 1)
                        if author_num_books is not None:
                            try:
                                author_num_books = int(author_num_books)
                                # Ensure value is within PostgreSQL smallint range
                                if author_num_books < -32768 or author_num_books > 32767:
                                    logger.warning(f"Number of books value {author_num_books} out of range for smallint, setting to default value")
                                    author_num_books = 1
                            except (ValueError, TypeError):
                                logger.warning(f"Invalid number_of_books value: {author_num_books}, setting to default value")
                                author_num_books = 1
                    
                    if not author_name:
                        continue  # Skip authors without names
                    
                    # Check if author already exists
                    author, created = Author.objects.get_or_create(
                        name=author_name,
                        defaults={
                            'bio': author_bio,
                            'date_of_birth': author_birth_date,
                            'number_of_books': author_num_books
                        }
                    )
                    
                    # Update author info if we have more details and author already existed
                    if not created and isinstance(author_data, dict):
                        update_fields = []
                        
                        # Only update fields if they're empty in the database but we have data
                        if (author.bio is None or author.bio == '') and author_bio:
                            author.bio = author_bio
                            update_fields.append('bio')
                            
                        if author.date_of_birth is None and author_birth_date:
                            author.date_of_birth = author_birth_date
                            update_fields.append('date_of_birth')
                            
                        if author.number_of_books is None and author_num_books:
                            author.number_of_books = author_num_books
                            update_fields.append('number_of_books')
                        elif author.number_of_books is not None:
                            # Increment book count for existing author, with validation
                            try:
                                new_count = author.number_of_books + 1
                                # Ensure value is within PostgreSQL smallint range
                                if new_count <= 32767:
                                    author.number_of_books = new_count
                                    update_fields.append('number_of_books')
                                else:
                                    logger.warning(f"Incrementing number_of_books would exceed smallint range for author {author_name}, keeping current value")
                            except Exception as e:
                                logger.warning(f"Error updating number_of_books: {e}")
                            
                        if update_fields:
                            author.save(update_fields=update_fields)
                    
                    # Create book-author relationship
                    BookAuthor.objects.create(book=book, author=author)
                except Exception as e:
                    logger.warning(f"Error adding author '{author_name if isinstance(author_data, str) else author_data.get('name', '')}' to book: {e}")
                    # Continue with other authors even if one fails
        
        # Add genres if available
        if book_data.get('genres'):
            for genre_name in book_data.get('genres', []):
                try:
                    if genre_name and isinstance(genre_name, str):
                        # Normalize genre name (trim whitespace, capitalize first letter)
                        genre_name = genre_name.strip()
                        if genre_name:
                            BookGenre.objects.create(book=book, genre=genre_name)
                except Exception as e:
                    logger.warning(f"Error adding genre '{genre_name}' to book: {e}")
                    # Continue with other genres even if one fails
        
        return book
    
    except Exception as e:
        logger.error(f"Error saving external book: {e}", exc_info=True)
        # Check for specific error types and provide more context
        if 'connection' in str(e).lower():
            logger.error("Network connection error while saving book - check internet connectivity")
        return None