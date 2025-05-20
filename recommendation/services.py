import logging
import pickle
import os
import pandas as pd
from datetime import datetime
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Count

from .models import RecommendationModel, UserRecommendation
from .recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)

class RecommendationService:
    """
    Service class for handling recommendation model training and generating recommendations
    """
    
    @staticmethod
    def get_ratings_dataframe():
        """
        Get ratings data from the database and convert to pandas DataFrame
        Assumes the existence of a Rating model with user, book, and rating fields
        """
        from books.models import BookRating  # Import here to avoid circular imports
        
        # Get all ratings
        ratings = BookRating.objects.select_related('user', 'book').all()
        
        # Convert to DataFrame format needed by RecommendationEngine
        data = {
            'user_id': [rating.user.id for rating in ratings],
            'isbn13': [rating.book.isbn13 for rating in ratings],
            'rate': [rating.rate for rating in ratings]
        }
        
        return pd.DataFrame(data)
    
    @staticmethod
    def train_recommendation_model(model_type='svd', min_ratings_per_user=5, n_factors=100, knn_k=40):
        """
        Train a new recommendation model and save it to the database
        """
        logger.info(f"Starting training of {model_type} recommendation model")
        
        # Get ratings data
        ratings_df = RecommendationService.get_ratings_dataframe()
        
        if ratings_df.empty:
            logger.error("No ratings data available for training")
            return None
            
        # Initialize recommendation engine with appropriate parameters
        engine = RecommendationEngine(
            model_type=model_type,
            min_ratings_per_user=min_ratings_per_user,
            rating_scale=(1, 5),  # Assuming 1-5 rating scale
            svd_n_factors=n_factors,
            knn_k=knn_k
        )
        
        # Train the model
        eval_metrics = engine.train(ratings_df, test_size=0.2)
        
        if not eval_metrics:
            logger.error("Model training failed")
            return None
            
        # Create model record
        with transaction.atomic():
            # Deactivate all existing models of the same type
            RecommendationModel.objects.filter(model_type=model_type, is_active=True).update(is_active=False)
            
            # Create new model record
            model_record = RecommendationModel.objects.create(
                model_type=model_type,
                min_ratings_per_user=min_ratings_per_user,
                n_factors=n_factors,
                knn_k=knn_k,
                rmse=eval_metrics.get('rmse'),
                mae=eval_metrics.get('mae'),
                is_active=True
            )
            
            # Serialize and save the model
            model_data = pickle.dumps(engine)
            model_filename = f"{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            model_record.model_file.save(model_filename, ContentFile(model_data))
            
        logger.info(f"Successfully trained and saved {model_type} model with id {model_record.id}")
        return model_record
    
    @staticmethod
    def load_recommendation_model(model_id=None):
        """
        Load a trained recommendation model from the database
        If model_id is not provided, load the latest active model
        """
        try:
            if model_id:
                model_record = RecommendationModel.objects.get(id=model_id)
            else:
                model_record = RecommendationModel.objects.filter(is_active=True).first()
                
            if not model_record or not model_record.model_file:
                logger.error("No valid recommendation model found")
                return None
                
            model_path = os.path.join(settings.MEDIA_ROOT, model_record.model_file.name)
            with open(model_path, 'rb') as f:
                engine = pickle.load(f)
                
            return engine, model_record
        except Exception as e:
            logger.error(f"Error loading recommendation model: {str(e)}")
            return None
    
    @staticmethod
    def generate_recommendations_for_user(user_id, n_recommendations=10, model_id=None):
        """
        Generate book recommendations for a specific user
        """
        # Load the recommendation model
        model_data = RecommendationService.load_recommendation_model(model_id)
        if not model_data:
            logger.error(f"Could not generate recommendations for user {user_id}: No model available")
            return []
            
        engine, model_record = model_data
        
        # Generate recommendations
        recommendations = engine.recommend_for_user(user_id=user_id, n_recommendations=n_recommendations)
        
        if not recommendations:
            logger.info(f"No recommendations generated for user {user_id}")
            return []
            
        # Save recommendations to database
        with transaction.atomic():
            # Clear existing recommendations for this user
            UserRecommendation.objects.filter(user_id=user_id).delete()
            
            # Create new recommendation records
            user_recs = []
            for book_isbn, score in recommendations:
                try:
                    from books.models import Book  # Import here to avoid circular imports
                    book = Book.objects.get(isbn13=book_isbn)
                    
                    user_rec = UserRecommendation(
                        user_id=user_id,
                        book=book,
                        score=score,
                        model=model_record
                    )
                    user_recs.append(user_rec)
                except Exception as e:
                    logger.error(f"Error creating recommendation for book {book_isbn}: {str(e)}")
            
            # Bulk create all recommendations
            UserRecommendation.objects.bulk_create(user_recs)
            
        logger.info(f"Generated {len(user_recs)} recommendations for user {user_id}")
        return user_recs
    
    @staticmethod
    def generate_recommendations_for_all_users(n_recommendations=10, model_id=None, min_ratings=3):
        """
        Generate recommendations for all users who have at least min_ratings
        """
        from books.models import BookRating  # Import here to avoid circular imports
        
        # Get users with sufficient ratings
        users_with_ratings = BookRating.objects.values('user').annotate(
            rating_count=Count('id')
        ).filter(rating_count__gte=min_ratings)
        
        user_ids = [user['user'] for user in users_with_ratings]
        
        recommendations_count = 0
        for user_id in user_ids:
            recs = RecommendationService.generate_recommendations_for_user(
                user_id, n_recommendations, model_id
            )
            recommendations_count += len(recs)
            
        logger.info(f"Generated recommendations for {len(user_ids)} users, total of {recommendations_count} recommendations")
        return recommendations_count