from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.auth import get_user_model

from books.models import BookReview, BookRating, Book
from books.serializers.review_serializers import BookReviewSerializer, BookRatingSerializer


class BookReviewAPIView(generics.ListAPIView):
    """
    API endpoint that allows book reviews to be viewed.
    Returns all reviews.
    """
    serializer_class = BookReviewSerializer
    
    def get_queryset(self):
        return BookReview.objects.all().order_by('-created_at')


class BookReviewDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint that allows a specific book review to be viewed.
    """
    serializer_class = BookReviewSerializer
    lookup_field = 'review_id'
    
    def get_queryset(self):
        return BookReview.objects.all()


class BookReviewCreateAPIView(APIView):
    """
    API endpoint that allows book reviews to be created.
    Requires authentication.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        # Get book ID from request data
        book_id = request.data.get('book')
        if not book_id:
            return Response(
                {'error': 'Book ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if book exists
        try:
            book = Book.objects.get(isbn13=book_id)
        except Book.DoesNotExist:
            return Response(
                {'error': 'Book does not exist'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Check if user has already reviewed this book
        if BookReview.objects.filter(user=request.user, book=book).exists():
            return Response(
                {'error': 'You have already reviewed this book'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Validate and create review
        serializer = BookReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, book=book)
            return Response(
                serializer.data, 
                status=status.HTTP_201_CREATED
            )
            
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )


class BookReviewUpdateAPIView(generics.UpdateAPIView):
    """
    API endpoint that allows book reviews to be updated.
    Only allows users to update their own reviews.
    """
    serializer_class = BookReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'review_id'
    
    def get_queryset(self):
        return BookReview.objects.filter(user=self.request.user)


class BookReviewDeleteAPIView(generics.DestroyAPIView):
    """
    API endpoint that allows book reviews to be deleted.
    Only allows users to delete their own reviews.
    """
    serializer_class = BookReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'review_id'
    
    def get_queryset(self):
        return BookReview.objects.filter(user=self.request.user)


class BookReviewsByBookAPIView(generics.ListAPIView):
    """
    API endpoint that allows reviews for a specific book to be viewed.
    """
    serializer_class = BookReviewSerializer
    
    def get_queryset(self):
        book_id = self.kwargs.get('book_id')
        try:
            book = Book.objects.get(isbn13=book_id)
            return BookReview.objects.filter(book=book).order_by('-created_at')
        except Book.DoesNotExist:
            raise ValidationError({'book': 'Book does not exist'})


class BookRatingAPIView(generics.ListAPIView):
    """
    API endpoint that allows book ratings to be viewed.
    Returns all ratings.
    """
    serializer_class = BookRatingSerializer
    
    def get_queryset(self):
        return BookRating.objects.all().order_by('-created_at')


class BookRatingDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint that allows a specific book rating to be viewed.
    """
    serializer_class = BookRatingSerializer
    lookup_field = 'rate_id'
    
    def get_queryset(self):
        return BookRating.objects.all()


class BookRatingCreateAPIView(generics.CreateAPIView):
    """
    API endpoint that allows book ratings to be created.
    Requires authentication.
    """
    serializer_class = BookRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        book_id = self.request.data.get('book')
        try:
            book = Book.objects.get(isbn13=book_id)
            serializer.save(user=self.request.user, book=book)
        except Book.DoesNotExist:
            raise ValidationError({'book': 'Book does not exist'})


class BookRatingUpdateAPIView(generics.UpdateAPIView):
    """
    API endpoint that allows book ratings to be updated.
    Only allows users to update their own ratings.
    """
    serializer_class = BookRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'rate_id'
    
    def get_queryset(self):
        return BookRating.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save()
        
        # Recalculate average rating for the book
        book = serializer.instance.book
        book_ratings = BookRating.objects.filter(book=book)
        book.number_of_ratings = book_ratings.count()
        
        if book.number_of_ratings > 0:
            total_rating = sum(br.rate for br in book_ratings)
            book.average_rate = total_rating / book.number_of_ratings
        else:
            book.average_rate = None
        
        book.save()


class BookRatingDeleteAPIView(generics.DestroyAPIView):
    """
    API endpoint that allows book ratings to be deleted.
    Only allows users to delete their own ratings.
    """
    serializer_class = BookRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'rate_id'
    
    def get_queryset(self):
        return BookRating.objects.filter(user=self.request.user)
    
    def perform_destroy(self, instance):
        # Store book reference before deletion
        book = instance.book
        instance.delete()
        
        # Recalculate average rating
        book_ratings = BookRating.objects.filter(book=book)
        book.number_of_ratings = book_ratings.count()
        
        if book.number_of_ratings > 0:
            total_rating = sum(br.rate for br in book_ratings)
            book.average_rate = total_rating / book.number_of_ratings
        else:
            book.average_rate = None
        
        book.save()


class BookRatingsByBookAPIView(generics.ListAPIView):
    """
    API endpoint that allows ratings for a specific book to be viewed.
    """
    serializer_class = BookRatingSerializer
    
    def get_queryset(self):
        book_id = self.kwargs.get('book_id')
        try:
            book = Book.objects.get(isbn13=book_id)
            return BookRating.objects.filter(book=book).order_by('-created_at')
        except Book.DoesNotExist:
            raise ValidationError({'book': 'Book does not exist'})


class UserBookRatingAPIView(generics.RetrieveAPIView):
    """
    API endpoint that allows a user to view their own rating for a specific book.
    Requires authentication.
    """
    serializer_class = BookRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        book_id = self.kwargs.get('book_id')
        try:
            book = Book.objects.get(isbn13=book_id)
            rating = BookRating.objects.filter(book=book, user=self.request.user).first()
            if not rating:
                raise ValidationError({'rating': 'You have not rated this book yet'})
            return rating
        except Book.DoesNotExist:
            raise ValidationError({'book': 'Book does not exist'})
        

class UserRatingsAPIView(generics.ListAPIView):
    """
    API endpoint that allows retrieving all ratings submitted by a specific user.
    If requesting user is authenticated and looking at their own ratings,
    all their ratings are returned. Otherwise, only public ratings are returned.
    """
    serializer_class = BookRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        
        # Check if the requested user exists
        user = get_object_or_404(get_user_model(), id=user_id)
        
        # If user is looking at their own ratings, return all
        if self.request.user.id == int(user_id):
            return BookRating.objects.filter(user=user).order_by('-created_at')
        
        # Otherwise, only return public ratings (if you have a public flag) 
        # or all ratings if all are public by default
        return BookRating.objects.filter(user=user).order_by('-created_at')