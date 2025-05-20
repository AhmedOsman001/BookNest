from rest_framework import serializers
from .models import RecommendationModel, UserRecommendation

class RecommendationModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationModel
        fields = ['id', 'model_type', 'created_at', 'is_active', 
                 'min_ratings_per_user', 'n_factors', 'knn_k', 'rmse', 'mae']
        read_only_fields = ['id', 'created_at', 'rmse', 'mae']


class UserRecommendationSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_author = serializers.CharField(source='book.author', read_only=True)
    book_cover = serializers.ImageField(source='book.cover', read_only=True)
    
    class Meta:
        model = UserRecommendation
        fields = ['id', 'book', 'book_title', 'book_author', 'book_cover', 'score', 'recommended_at']
        read_only_fields = ['id', 'score', 'recommended_at']