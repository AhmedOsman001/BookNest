from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.views.profile import IsOwnerOrReadOnly
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q

from books.models import ReadingList, Book
from books.serializers.book_serializers import ReadingListSerializer, ReadingListDetailSerializer


class ReadingListAPIView(generics.ListAPIView):
    """
    API endpoint that allows reading lists to be viewed.
    Returns public lists and user's own lists if authenticated.
    """
    serializer_class = ReadingListSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return ReadingList.objects.filter(
                Q(privacy='public') | Q(profile__user=self.request.user)
            ).order_by('-created_at')
        return ReadingList.objects.filter(privacy='public').order_by('-created_at')


class ReadingListDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint that allows a specific reading list to be viewed.
    Returns public lists and user's own lists if authenticated.
    """
    serializer_class = ReadingListDetailSerializer
    lookup_field = 'list_id'
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return ReadingList.objects.filter(
                Q(privacy='public') | Q(profile__user=self.request.user)
            )
        return ReadingList.objects.filter(privacy='public')


class ReadingListCreateAPIView(generics.CreateAPIView):
    """
    API endpoint that allows reading lists to be created.
    Requires authentication.
    """
    serializer_class = ReadingListSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


class ReadingListUpdateAPIView(generics.UpdateAPIView):
    """
    API endpoint that allows reading lists to be updated.
    Only allows users to update their own lists.
    """
    serializer_class = ReadingListSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'list_id'
    
    def get_queryset(self):
        return ReadingList.objects.filter(profile__user=self.request.user)


class ReadingListDeleteAPIView(generics.DestroyAPIView):
    """
    API endpoint that allows reading lists to be deleted.
    Only allows users to delete their own lists.
    """
    serializer_class = ReadingListSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'list_id'
    
    def get_queryset(self):
        return ReadingList.objects.filter(profile__user=self.request.user)


class ReadingListBookOperationsAPIView(APIView):
    """
    API endpoint that allows books to be added to or removed from reading lists.
    Only allows users to modify their own lists.
    """
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def post(self, request, *args, **kwargs):
        """
        Add a book to a reading list
        """
        book_id = request.data.get('book_id')
        list_id = request.data.get('list_id')
        
        if not book_id or not list_id:
            return Response(
                {"error": "Both book_id and list_id are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        book = get_object_or_404(Book, isbn13=book_id)
        reading_list = get_object_or_404(
            ReadingList, 
            list_id=list_id, 
            profile__user=request.user
        )
        
        # Add book to reading list if not already there
        if not reading_list.books.filter(isbn13=book_id).exists():
            reading_list.books.add(book)
            return Response(
                {"message": f'Added "{book.title}" to "{reading_list.name}"'}, 
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"message": f'This book is already in "{reading_list.name}"'}, 
            status=status.HTTP_200_OK
        )
    
    def delete(self, request, *args, **kwargs):
        """
        Remove a book from a reading list
        """
        book_id = request.data.get('book_id')
        list_id = request.data.get('list_id')
        
        if not book_id or not list_id:
            return Response(
                {"error": "Both book_id and list_id are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        book = get_object_or_404(Book, isbn13=book_id)
        reading_list = get_object_or_404(
            ReadingList, 
            list_id=list_id, 
            profile__user=request.user
        )
        
        # Remove book from reading list
        if reading_list.books.filter(isbn13=book_id).exists():
            reading_list.books.remove(book)
            return Response(
                {"message": f'Removed "{book.title}" from "{reading_list.name}"'}, 
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"message": f'This book is not in "{reading_list.name}"'}, 
            status=status.HTTP_404_NOT_FOUND
        )