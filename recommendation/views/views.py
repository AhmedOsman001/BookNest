from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..models import RecommendationModel, UserRecommendation
from ..serializers import RecommendationModelSerializer, UserRecommendationSerializer
from ..services import RecommendationService
from ..tasks import (
    train_recommendation_model_task,
    generate_recommendations_for_user_task,
    generate_recommendations_for_all_users_task
)


class RecommendationModelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for recommendation models
    """
    queryset = RecommendationModel.objects.all()
    serializer_class = RecommendationModelSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admins can access model endpoints
    
    @action(detail=False, methods=['post'])
    def train(self, request):
        """
        Train a new recommendation model
        """
        model_type = request.data.get('model_type', 'svd')
        min_ratings = int(request.data.get('min_ratings_per_user', 5))
        n_factors = int(request.data.get('n_factors', 100))
        knn_k = int(request.data.get('knn_k', 40))
        async_training = request.data.get('async', True)
        
        if model_type not in ['svd', 'knn']:
            return Response(
                {"error": "Invalid model_type. Choose 'svd' or 'knn'"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if async_training:
            # Train model asynchronously
            task = train_recommendation_model_task.delay(
                model_type=model_type,
                min_ratings_per_user=min_ratings,
                n_factors=n_factors,
                knn_k=knn_k
            )
            return Response({"message": "Model training started", "task_id": task.id})
        else:
            # Train model synchronously
            model_record = RecommendationService.train_recommendation_model(
                model_type=model_type,
                min_ratings_per_user=min_ratings,
                n_factors=n_factors,
                knn_k=knn_k
            )
            
            if model_record:
                serializer = self.get_serializer(model_record)
                return Response(serializer.data)
            else:
                return Response(
                    {"error": "Model training failed"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a specific model and deactivate all others
        """
        model = self.get_object()
        
        # Deactivate all models of the same type
        RecommendationModel.objects.filter(model_type=model.model_type).update(is_active=False)
        
        # Activate the selected model
        model.is_active = True
        model.save()
        
        serializer = self.get_serializer(model)
        return Response(serializer.data)
        

class UserRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for user recommendations
    """
    serializer_class = UserRecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return recommendations for the current user only
        """
        return UserRecommendation.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate new recommendations for the current user
        """
        n_recommendations = int(request.data.get('n_recommendations', 10))
        model_id = request.data.get('model_id')
        async_generation = request.data.get('async', False)
        
        if async_generation:
            # Generate recommendations asynchronously
            task = generate_recommendations_for_user_task.delay(
                user_id=request.user.id,
                n_recommendations=n_recommendations,
                model_id=model_id
            )
            return Response({"message": "Recommendation generation started", "task_id": task.id})
        else:
            # Generate recommendations synchronously
            recommendations = RecommendationService.generate_recommendations_for_user(
                user_id=request.user.id,
                n_recommendations=n_recommendations,
                model_id=model_id
            )
            
            if recommendations:
                serializer = self.get_serializer(recommendations, many=True)
                return Response(serializer.data)
            else:
                return Response(
                    {"message": "No recommendations generated. You may need more ratings or the model needs training."},
                    status=status.HTTP_200_OK
                )
    
    @action(detail=False, methods=['get'])
    def refresh(self, request):
        """
        Shortcut to regenerate recommendations with default parameters
        """
        recommendations = RecommendationService.generate_recommendations_for_user(
            user_id=request.user.id
        )
        
        if recommendations:
            serializer = self.get_serializer(recommendations, many=True)
            return Response(serializer.data)
        else:
            return Response(
                {"message": "No recommendations available. Try rating more books."},
                status=status.HTTP_200_OK
            )


class AdminRecommendationViewSet(viewsets.ViewSet):
    """
    Admin-only API endpoints for managing the recommendation system
    """
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=False, methods=['post'])
    def generate_all(self, request):
        """
        Generate recommendations for all eligible users
        """
        n_recommendations = int(request.data.get('n_recommendations', 10))
        model_id = request.data.get('model_id')
        min_ratings = int(request.data.get('min_ratings', 3))
        async_generation = request.data.get('async', True)
        
        if async_generation:
            # Generate recommendations asynchronously
            task = generate_recommendations_for_all_users_task.delay(
                n_recommendations=n_recommendations,
                model_id=model_id,
                min_ratings=min_ratings
            )
            return Response({"message": "Recommendation generation for all users started", "task_id": task.id})
        else:
            # Generate recommendations synchronously
            count = RecommendationService.generate_recommendations_for_all_users(
                n_recommendations=n_recommendations,
                model_id=model_id,
                min_ratings=min_ratings
            )
            
            return Response({"message": f"Generated recommendations for multiple users, total count: {count}"})