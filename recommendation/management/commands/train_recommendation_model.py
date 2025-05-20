import logging
from django.core.management.base import BaseCommand
from recommendation.services import RecommendationService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Train a new recommendation model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model-type',
            type=str,
            default='svd',
            choices=['svd', 'knn'],
            help='Type of recommendation model to train (svd, knn)'
        )
        parser.add_argument(
            '--min-ratings',
            type=int,
            default=5,
            help='Minimum number of ratings a user must have to be included'
        )
        parser.add_argument(
            '--n-factors',
            type=int,
            default=100,
            help='Number of factors for SVD model'
        )
        parser.add_argument(
            '--knn-k',
            type=int,
            default=40,
            help='Number of neighbors for KNN model'
        )

    def handle(self, *args, **options):
        model_type = options['model_type']
        min_ratings = options['min_ratings']
        n_factors = options['n_factors']
        knn_k = options['knn_k']
        
        self.stdout.write(self.style.SUCCESS(f'Starting training of {model_type.upper()} model...'))
        
        try:
            model_record = RecommendationService.train_recommendation_model(
                model_type=model_type,
                min_ratings_per_user=min_ratings,
                n_factors=n_factors,
                knn_k=knn_k
            )
            
            if model_record:
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully trained {model_type.upper()} model with ID: {model_record.id}'
                ))
                if model_record.rmse is not None and model_record.mae is not None:
                    self.stdout.write(f'RMSE: {model_record.rmse:.4f}, MAE: {model_record.mae:.4f}')
            else:
                self.stdout.write(self.style.ERROR('Model training failed. Check logs for details.'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error training model: {str(e)}'))