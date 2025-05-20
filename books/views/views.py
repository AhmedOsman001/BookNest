from books.models import Book , Author 
from books.serializers.book_serializers import BookSerializer, AuthorSerializer 
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from drf_spectacular.openapi import AutoSchema
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated, IsAdminUser 
from django.db import models


class BookListAPIView(generics.ListAPIView):
    schema = AutoSchema()
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'authors__name': ['icontains' , 'in'],
        'genres__genre': ['icontains', 'in', 'exact'],
        'average_rate': ['gte', 'lte'],
        'description': ['icontains'],
        'publication_date': ['exact', 'year', 'month', 'day', 'range'],
        'number_of_pages': ['gte', 'lte', 'exact'],
        'title': ['exact', 'icontains', 'istartswith'],
    }
    pagination_class = LimitOffsetPagination
    
    # def get_queryset(self):
    #     """
    #     Override get_queryset to implement search functionality that checks
    #     database first, then external APIs if needed.
    #     """
    #     queryset = super().get_queryset()
    #     search_query = self.request.query_params.get('search', None)
        
    #     if search_query:
    #         from books.utils.book_service import search_books
            
    #         # Search in database first, then external APIs if needed
    #         books_data = search_books(search_query)
            
    #         # If we got results from external APIs, they're already saved to DB
    #         # So we need to refresh our queryset to include them
    #         if any(book.get('source') != 'database' for book in books_data):
    #             queryset = Book.objects.all()
            
    #         # Filter queryset to only include books matching the search query
    #         # This will include both database books and newly saved external books
    #         queryset = queryset.filter(
    #             models.Q(title__icontains=search_query) |
    #             models.Q(authors__name__icontains=search_query) |
    #             models.Q(isbn13__icontains=search_query) |
    #             models.Q(isbn__icontains=search_query)
    #         ).distinct()
        
    #     return queryset
    


class BookDetailAPIView(generics.RetrieveAPIView):
    schema = AutoSchema()
    queryset = Book.objects.all()
    serializer_class = BookSerializer

#PRIV
class BookDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Book.objects.all()
    serializer_class = BookSerializer

#PRIV
class BookUpdateAPIView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Book.objects.all()
    serializer_class = BookSerializer

#PRIV
class BookCreateAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class AuthorListAPIView(generics.ListAPIView):
    schema = AutoSchema()
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'name': ['icontains'],
        'number_of_books': ['gte', 'lte'],
        'bio': ['icontains'],
        'date_of_birth': ['exact', 'year', 'month', 'day', 'range'],
    }
    pagination_class = LimitOffsetPagination


class AuthorDetailAPIView(generics.RetrieveAPIView):
    schema = AutoSchema()
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

#PRIV
class AuthorDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

#PRIV
class AuthorUpdateAPIView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

#PRIV
class AuthorCreateAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


# return all books by author name or id
class AuthorBookListAPIView(generics.ListAPIView):
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'authors__name': ['icontains' , 'in'],
        'genres__genre': ['icontains', 'in', 'exact'],
        'average_rate': ['gte', 'lte'],
        'description': ['icontains'],
        'publication_date': ['exact', 'year', 'month', 'day', 'range'],
        'number_of_pages': ['gte', 'lte', 'exact'],
        'title': ['exact', 'icontains', 'istartswith'],
    }
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        author_id = self.kwargs.get('pk')
        author_name = self.kwargs.get('name')        
        queryset = Book.objects.all().prefetch_related('authors')
        
        if author_id:
            queryset = queryset.filter(authors__author_id=author_id)
        elif author_name:            
            queryset = queryset.filter(authors__name__icontains=author_name)
        else:
            raise NotFound("Provide either author ID or name")
            
        queryset = queryset.distinct()
        
        return queryset
    


