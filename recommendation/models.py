from django.db import models
from django.conf import settings
from django.utils import timezone
from books.models import Book
class RecommendationModel(models.Model):
    """
    Model to store trained recommendation models and their metadata
    """
    MODEL_TYPES = (
        ('svd', 'Singular Value Decomposition'),
        ('knn', 'K-Nearest Neighbors'),
    )
    
    model_type = models.CharField(max_length=10, choices=MODEL_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)
    
    # Model parameters
    min_ratings_per_user = models.IntegerField(default=5)
    n_factors = models.IntegerField(default=100, help_text="Number of factors for SVD model")
    knn_k = models.IntegerField(default=40, help_text="Number of neighbors for KNN model")
    
    # Model performance metrics
    rmse = models.FloatField(null=True, blank=True)
    mae = models.FloatField(null=True, blank=True)
    
    # Serialized model data will be stored in a file referenced by this field
    model_file = models.FileField(upload_to='recommendation_models/', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_model_type_display()} model created on {self.created_at.strftime('%Y-%m-%d')}"


class UserRecommendation(models.Model):
    """
    Model to store precomputed book recommendations for users
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='book_recommendation')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)  # Assuming Book model exists in 'books' app
    score = models.FloatField(help_text="Predicted rating or recommendation score")
    recommended_at = models.DateTimeField(default=timezone.now)
    model = models.ForeignKey(RecommendationModel, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-score']
        unique_together = ['user', 'book']
    
    def __str__(self):
        return f"Recommendation for {self.user} - {self.book} (Score: {self.score:.2f})"