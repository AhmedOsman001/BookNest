from rest_framework import serializers
from books.models import BookReview, BookRating
from django.contrib.auth import get_user_model

User = get_user_model()

class BookReviewSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    book_title = serializers.SerializerMethodField()
    
    class Meta:
        model = BookReview
        fields = ['review_id', 'review_text', 'created_at', 'user', 'book', 'username', 'book_title']
        read_only_fields = ['review_id', 'created_at', 'username', 'book_title']
    
    def get_book_title(self, obj):
        return obj.book.title if obj.book else None
    
    def get_username(self, obj):
        return obj.user.username
    
    def get_book_average_rate(self, obj):
        return obj.book.average_rate if obj.book else None
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Remove user ID from the representation if not needed in response
        if 'user' in representation:
            representation.pop('user')
        return representation

class BookRatingSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    book_title = serializers.SerializerMethodField()
    book_average_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = BookRating
        fields = ['rate_id', 'rate', 'created_at', 'user', 'book', 'username', 'book_title', 'book_average_rate']
        read_only_fields = ['rate_id', 'created_at', 'username', 'book_title', 'book_average_rate']
    
    def get_book_title(self, obj):
        return obj.book.title if obj.book else None
    
    def get_username(self, obj):
        return obj.user.username
    
    def get_book_average_rate(self, obj):
        return obj.book.average_rate if obj.book else None
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Remove user ID from the representation if not needed in response
        if 'user' in representation:
            representation.pop('user')
        return representation
    
    def create(self, validated_data):
        # Get the book instance
        book = validated_data.get('book')
        user = validated_data.get('user')
        
        # Check if the user has already rated this book
        existing_rating = BookRating.objects.filter(user=user, book=book).first()
        
        if existing_rating:
            # Update existing rating
            existing_rating.rate = validated_data.get('rate')
            existing_rating.save()
            return existing_rating
        
        # Create new rating
        rating = BookRating.objects.create(**validated_data)
        
        # Update book's average rating and number of ratings
        book_ratings = BookRating.objects.filter(book=book)
        book.number_of_ratings = book_ratings.count()
        
        if book.number_of_ratings > 0:
            total_rating = sum(br.rate for br in book_ratings)
            book.average_rate = total_rating / book.number_of_ratings
        
        book.save()
        
        return rating
    
    def update(self, instance, validated_data):
        # Update the rating
        instance.rate = validated_data.get('rate', instance.rate)
        instance.save()
        
        # Update book's average rating
        book = instance.book
        book_ratings = BookRating.objects.filter(book=book)
        
        if book_ratings.exists():
            total_rating = sum(br.rate for br in book_ratings)
            book.average_rate = total_rating / book_ratings.count()
            book.save()
        
        return instance