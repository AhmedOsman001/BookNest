from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from books.models import BookRating
from recommendation.services import RecommendationService
from recommendation.tasks import generate_recommendations_for_user_task

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_recommendations(request):
    """
    API endpoint to manually trigger recommendations generation
    if the user has enough ratings.
    """
    user = request.user
    
    # Count user ratings
    user_rating_count = BookRating.objects.filter(user=user).count()
    
    # Check if user has enough ratings
    if user_rating_count < 10:
        return Response({
            "status": "error",
            "message": f"You need at least 10 book ratings to get recommendations. You currently have {user_rating_count}.",
            "ratings_needed": 10 - user_rating_count
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Determine if async or sync based on request parameter
    use_async = request.data.get('async', True)
    n_recommendations = request.data.get('count', 15)
    
    if use_async:
        # Trigger async task
        task = generate_recommendations_for_user_task.delay(
            user_id=user.id,
            n_recommendations=n_recommendations
        )
        return Response({
            "status": "success",
            "message": "Recommendation generation started",
            "task_id": task.id
        })
    else:
        # Generate recommendations synchronously
        recommendations = RecommendationService.generate_recommendations_for_user(
            user_id=user.id,
            n_recommendations=n_recommendations
        )
        
        return Response({
            "status": "success",
            "message": f"Generated {len(recommendations)} recommendations",
            "recommendation_count": len(recommendations)
        })