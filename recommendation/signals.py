# Fix 1: Update the signals.py file to ensure proper model training and recommendation

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Count
from books.models import BookRating
from recommendation.services import RecommendationService
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=BookRating)
def trigger_recommendations_on_rating_threshold(sender, instance, created, **kwargs):
    """
    Signal handler to automatically generate recommendations when a user
    reaches the threshold number of ratings (RATING_THRESHOLD).
    """
    if not created:
        # Only process newly created ratings
        return
        
    user = instance.user
    
    # Count how many ratings this user has
    user_rating_count = BookRating.objects.filter(user=user).count()
    
    # Define our threshold
    RATING_THRESHOLD = 22
    
    # Check if user just reached the threshold
    if user_rating_count == RATING_THRESHOLD:
        logger.info(f"User {user.username} (ID: {user.id}) has reached {RATING_THRESHOLD} ratings. Generating recommendations.")
        
        try:
            # First, ensure we have a trained model that includes this user's data
            # This is crucial - we need to train a new model that includes this user's ratings
            logger.info(f"Training new recommendation model to include user {user.id}'s ratings")
            
            # Train a new model synchronously to ensure it includes the current user's data
            try:
                model_record = RecommendationService.train_recommendation_model(
                    model_type='svd',  # Or your preferred model type
                    min_ratings_per_user=5  # Keep this lower than RATING_THRESHOLD
                )
                
                if model_record:
                    logger.info(f"Successfully trained new model (ID: {model_record.id}) including user {user.id}'s data")
                    model_id = model_record.id
                else:
                    logger.error(f"Failed to train new model for user {user.id}")
                    # Use the latest active model as fallback
                    model_id = None
            except Exception as train_e:
                logger.error(f"Error training model for user {user.id}: {str(train_e)}")
                model_id = None
            
            # Try async recommendation generation via celery
            try:
                from recommendation.tasks import generate_recommendations_for_user_task
                task = generate_recommendations_for_user_task.delay(
                    user_id=user.id,
                    model_id=model_id,  # Use our newly trained model
                    n_recommendations=10
                )
                logger.info(f"Recommendation generation task started for user {user.id}: Task ID {task.id}")
            except Exception as e:
                logger.error(f"Failed to trigger async recommendations for user {user.id}: {str(e)}")
                # Fallback to synchronous generation
                try:
                    recommendations = RecommendationService.generate_recommendations_for_user(
                        user_id=user.id, 
                        model_id=model_id,  # Use our newly trained model
                        n_recommendations=10
                    )
                    logger.info(f"Generated {len(recommendations)} recommendations for user {user.id} synchronously.")
                except Exception as inner_e:
                    logger.error(f"Synchronous recommendation generation also failed: {str(inner_e)}")
        except Exception as outer_e:
            logger.error(f"Complete failure in recommendation process: {str(outer_e)}")

# Fix 2: Update the recommendation_engine.py to better handle new users
# Add this method to the RecommendationEngine class

def recommend_for_new_user(self, user_id, n_recommendations=10):
    """
    Generate recommendations for a user who wasn't in the original training set.
    
    This method provides recommendations based on overall popularity when a user
    is not found in the training set.
    
    Args:
        user_id (object): The ID of the user for whom to generate recommendations.
        n_recommendations (int): The number of recommendations to return.
        
    Returns:
        list[tuple[object, float]]: A list of (item_id, score) tuples based on overall popularity.
    """
    if self.full_ratings_df is None:
        return []
    
    logger.info(f"Using fallback recommendations for new user {user_id}")
    
    # Get items the user has already rated
    user_ratings = self.full_ratings_df[self.full_ratings_df[self.user_id_col] == user_id]
    rated_items = set(user_ratings[self.item_id_col].unique())
    
    # Calculate item popularity (average rating)
    item_popularity = (
        self.full_ratings_df
        .groupby(self.item_id_col)[self.rating_col]
        .agg(['mean', 'count'])
        .reset_index()
    )
    
    # Filter out items the user has already rated
    recommendations = item_popularity[~item_popularity[self.item_id_col].isin(rated_items)]
    
    # Sort by popularity metrics (can adjust this formula as needed)
    # Combining average rating and count to balance quality and popularity
    recommendations['score'] = recommendations['mean'] * (1 + recommendations['count'] / recommendations['count'].max())
    recommendations = recommendations.sort_values('score', ascending=False)
    
    # Return top n recommendations
    top_n = [(row[self.item_id_col], row['score']) 
             for _, row in recommendations.head(n_recommendations).iterrows()]
    
    logger.info(f"Generated {len(top_n)} fallback recommendations for new user {user_id}")
    return top_n

# Fix 3: Update the recommend_for_user method in recommendation_engine.py
# to use the fallback method when a user isn't found

def recommend_for_user(self, user_id: object, n_recommendations: int = 10) -> list[tuple[object, float]]:
    """
    Generates top-N recommendations for a specific user for items they haven't rated.
    
    Args:
        user_id (object): The ID of the user for whom to generate recommendations.
                         This should be the raw user ID from your original data.
        n_recommendations (int): The number of recommendations to return.
    
    Returns:
        list[tuple[object, float]]: A list of (item_id, estimated_rating) tuples,
                                   sorted by estimated rating in descending order.
    """
    if not self.model or not self.trainset:
        logger.error("Model has not been trained yet. Please call the 'train' method first.")
        return []
        
    if self.full_ratings_df is None:
        logger.error("Full ratings data is not available. Call 'train' method first.")
        return []
    
    logger.info(f"Generating {n_recommendations} recommendations for user_id '{user_id}'.")
    
    try:
        # Convert the raw user_id to Surprise's inner id
        user_inner_id = self.trainset.to_inner_uid(user_id)
    except ValueError:
        logger.warning(f"User_id '{user_id}' not found in the training set. Using fallback recommendation method.")
        # Use our new fallback method for new users
        return self.recommend_for_new_user(user_id, n_recommendations)
    
