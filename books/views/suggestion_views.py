from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from books.utils.elasticsearch_client import ElasticsearchClient
import logging
from books.models import Book

# Configure logging
logger = logging.getLogger(__name__)


class BookSuggestionAPIView(APIView):
    """
    API endpoint for getting book title suggestions based on partial queries.
    
    This endpoint uses Elasticsearch's completion suggester to provide
    real-time search suggestions as the user types.
    """
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='q', description='Partial search query', required=True, type=str),
            OpenApiParameter(name='limit', description='Maximum number of suggestions', required=False, type=int),
        ],
        responses={200: {'type': 'array', 'items': {'type': 'object'}}},
        description=(
            "Get book title suggestions based on a partial query. "
            "Returns a list of suggested titles that match the query prefix."
        )
    )
    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', '')
        limit = request.query_params.get('limit', 5)
        
        try:
            limit = int(limit)
        except ValueError:
            limit = 5
        
        if not query:
            return Response(
                {"error": "Please provide a search query using the 'q' parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if Elasticsearch is available first
        if not ElasticsearchClient.check_connection(max_retries=1):
            logger.warning("Elasticsearch is not available for suggestions")
            return Response(
                {"warning": "Search suggestions are temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        try:
            # Get suggestions from Elasticsearch with retry mechanism
            suggestions = ElasticsearchClient.suggest_books(query, limit, max_retries=2)
            book_ids = [s['id'] for s in suggestions if 'id' in s]
            # Get full book details from database
            suggested_books = Book.objects.filter(isbn13__in=book_ids).values('isbn13','isbn', 'title', 'authors', 'publication_date', 'genres', 'number_of_pages', 'average_rate')

            # Return the suggestions with status code 200
            return Response(suggested_books)
        except Exception as e:
            # Log the error and return an empty list with appropriate status
            logger.error(f"Error getting suggestions: {e}")
            return Response(
                {"warning": "An error occurred while retrieving search suggestions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )            
            
def suggest_books_view(request):
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'suggestions': []})
    
    # Get title suggestions with IDs from Elasticsearch
    suggestions = ElasticsearchClient.suggest_books(query)
    
    # Extract IDs from suggestions
    book_ids = [s['id'] for s in suggestions if 'id' in s]
    
    # Get full book details from database
    books_data = get_books_by_ids(book_ids)
    
    # Merge score data from suggestions
    for book in books_data:
        suggestion = next((s for s in suggestions if s['id'] == book['id']), None)
        if suggestion:
            book['score'] = suggestion['score']
    
    return JsonResponse({'suggestions': books_data})
