from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from books.models import Book
from books.serializers.book_serializers import BookSerializer
from books.utils.book_service import search_books
from books.utils.elasticsearch_client import ElasticsearchClient
import logging

# Configure logging
logger = logging.getLogger(__name__)


class BookSearchAPIView(APIView):
    """
    API endpoint for searching books across local database and external APIs.
    
    This endpoint first searches the local database for books matching the query.
    If no results are found, it searches external APIs (OpenLibrary and Google Books),
    saves the results to the database, and returns them.
    """
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='q', description='Search query', required=True, type=str),
            OpenApiParameter(name='page', description='Page number', required=False, type=int),
            OpenApiParameter(name='page_size', description='Number of results per page', required=False, type=int),
            OpenApiParameter(name='genre', description='Filter by genre', required=False, type=str),
            OpenApiParameter(name='author', description='Filter by author', required=False, type=str),
            OpenApiParameter(name='min_rating', description='Filter by minimum rating', required=False, type=float),
            OpenApiParameter(name='pub_date_from', description='Filter by publication date (from)', required=False, type=str),
            OpenApiParameter(name='pub_date_to', description='Filter by publication date (to)', required=False, type=str),
            OpenApiParameter(name='num_pages', description='Filter by number of pages', required=False, type=int),
            
        ],
        responses={200: BookSerializer(many=True)},
        description=(
            "Search for books by title, author, or ISBN. "
            "First searches the local database, then external APIs if no results are found. "
            "Supports pagination and filtering by genre, author, rating, and publication date."
        )
    )
    def get(self, request, *args, **kwargs):
        # Get query parameters
        query = request.query_params.get('q', '')
        # Validate search query
        # if not query:
        #     return Response(
        #         {"error": "Please provide a search query using the 'q' parameter"},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        
        # Get pagination parameters
        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 10))
            
            # Validate pagination parameters
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 50:
                page_size = 10
        except ValueError:
            page = 1
            page_size = 10
        
        # Build filters dictionary
        filters = {}
        
        # Add genre filter if provided
        genre = request.query_params.get('genre')
        if genre:
            filters['genres'] = [genre]
        
        # Add author filter if provided
        author = request.query_params.get('author')
        if author:
            filters['author'] = author
        
        # Add rating filter if provided
        min_rating = request.query_params.get('min_rating')
        if min_rating:
            try:
                filters['min_rating'] = float(min_rating)
            except ValueError:
                pass
        
        # Add publication date filters if provided
        pub_date_from = request.query_params.get('pub_date_from')
        if pub_date_from:
            filters['pub_date_from'] = pub_date_from
        
        pub_date_to = request.query_params.get('pub_date_to')
        if pub_date_to:
            filters['pub_date_to'] = pub_date_to

        num_pages = request.query_params.get('num_pages')
        if num_pages:
            try:
                filters['num_pages'] = int(num_pages)
            except ValueError:
                pass
        
        # Check Elasticsearch availability for search status info
        es_available = ElasticsearchClient.check_connection(max_retries=1)
        if not es_available:
            logger.warning("Elasticsearch is not available for search, falling back to database only")
        
        # Search books using our service that checks DB first, then external APIs
        try:
            books_data, total_count = search_books(query, page=page, page_size=page_size, filters=filters)
            
            # If we found books, they're already saved to the database
            if books_data:
                # Get the ISBNs of all books found
                isbns = [book['isbn13'] for book in books_data if isinstance(book, dict) and 'isbn13' in book]
                
                # Fetch the books from the database
                books = Book.objects.filter(isbn13__in=isbns).prefetch_related('authors', 'genres')
                serializer = BookSerializer(books, many=True)
                
                # Calculate total pages
                total_pages = (total_count + page_size - 1) // page_size
                
                response_data = {
                    'results': serializer.data,
                    'count': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages
                }
                
                # Add search engine info if Elasticsearch is not available
                if not es_available:
                    response_data['search_info'] = "Using database search only. Full-text search is temporarily unavailable."
                    
                return Response(response_data)
            
            # If no books found, return empty paginated response
            response_data = {
                'results': [],
                'count': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }
            
            # Add search engine info if Elasticsearch is not available
            if not es_available:
                response_data['search_info'] = "Using database search only. Full-text search is temporarily unavailable."
                
            return Response(response_data)
            
        except Exception as e:
            # Log the error and return an error response
            logger.error(f"Error searching books: {e}")
            return Response(
                {"error": "An error occurred while searching for books"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        