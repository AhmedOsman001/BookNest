import logging
from celery import shared_task
from .services import RecommendationService

logger = logging.getLogger(__name__)

@shared_task
def train_recommendation_model_task(model_type='svd', min_ratings_per_user=5, n_factors=100, knn_k=40):
    """
    Background task for training a recommendation model
    """
    logger.info(f"Starting background task for training {model_type} model")
    try:
        model_record = RecommendationService.train_recommendation_model(
            model_type=model_type,
            min_ratings_per_user=min_ratings_per_user,
            n_factors=n_factors,
            knn_k=knn_k
        )
        return f"Successfully trained model ID: {model_record.id}" if model_record else "Model training failed"
    except Exception as e:
        logger.error(f"Error in train_recommendation_model_task: {str(e)}")
        return f"Error training model: {str(e)}"

@shared_task
def generate_recommendations_for_user_task(user_id, n_recommendations=10, model_id=None):
    """
    Background task for generating recommendations for a single user
    """
    logger.info(f"Starting background task for generating recommendations for user {user_id}")
    try:
        recs = RecommendationService.generate_recommendations_for_user(
            user_id=user_id,
            n_recommendations=n_recommendations,
            model_id=model_id
        )
        return f"Generated {len(recs)} recommendations for user {user_id}"
    except Exception as e:
        logger.error(f"Error in generate_recommendations_for_user_task: {str(e)}")
        return f"Error generating recommendations: {str(e)}"

@shared_task
def generate_recommendations_for_all_users_task(n_recommendations=10, model_id=None, min_ratings=3):
    """
    Background task for generating recommendations for all eligible users
    """
    logger.info("Starting background task for generating recommendations for all users")
    try:
        count = RecommendationService.generate_recommendations_for_all_users(
            n_recommendations=n_recommendations,
            model_id=model_id,
            min_ratings=min_ratings
        )
        return f"Generated recommendations for multiple users, total count: {count}"
    except Exception as e:
        logger.error(f"Error in generate_recommendations_for_all_users_task: {str(e)}")
        return f"Error generating recommendations for all users: {str(e)}"