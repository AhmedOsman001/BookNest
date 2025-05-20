import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Count
from recommendation.services import RecommendationService
from books.models import BookRating

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Generate book recommendations for users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID of the user to generate recommendations for (optional)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Generate recommendations for all eligible users'
        )
        parser.add_argument(
            '--model-id',
            type=int,
            help='ID of the recommendation model to use (optional, uses active model by default)'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of recommendations to generate per user'
        )
        parser.add_argument(
            '--min-ratings',
            type=int,
            default=3,
            help='Minimum number of ratings required for a user to get recommendations'
        )

    def handle(self, *args, **options):
        user_id = options['user_id']
        generate_all = options['all']
        model_id = options['model_id']
        count = options['count']
        min_ratings = options['min_ratings']
        
        if user_id and generate_all:
            self.stdout.write(self.style.ERROR('Cannot specify both --user-id and --all. Choose one.'))
            return
            
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                
                # Check if user has enough ratings
                rating_count = BookRating.objects.filter(user=user).count()
                if rating_count < min_ratings:
                    self.stdout.write(self.style.WARNING(
                        f'User {user.username} (ID: {user.id}) has only {rating_count} ratings. '
                        f'Minimum {min_ratings} ratings required.'
                    ))
                    return
                    
                self.stdout.write(f'Generating {count} recommendations for user {user.username} (ID: {user.id})...')
                
                recommendations = RecommendationService.generate_recommendations_for_user(
                    user_id=user.id,
                    n_recommendations=count,
                    model_id=model_id
                )
                
                if recommendations:
                    self.stdout.write(self.style.SUCCESS(
                        f'Successfully generated {len(recommendations)} recommendations for user {user.username}'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'No recommendations generated for user {user.username}. '
                        'User may not be in the training set or has no unrated items.'
                    ))
                    
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {user_id} does not exist'))
                
        elif generate_all:
            self.stdout.write(f'Generating recommendations for all users with at least {min_ratings} ratings...')
            
            count = RecommendationService.generate_recommendations_for_all_users(
                n_recommendations=count,
                model_id=model_id,
                min_ratings=min_ratings
            )
            
            self.stdout.write(self.style.SUCCESS(f'Generated recommendations for multiple users. Total count: {count}'))
            
        else:
            self.stdout.write(self.style.ERROR('Please specify either --user-id or --all'))