import logging
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from books.models import Book, BookRating

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Create test users and random book ratings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of test users to create'
        )
        parser.add_argument(
            '--ratings-per-user',
            type=int,
            default=10,
            help='Number of random ratings to generate per user'
        )
        parser.add_argument(
            '--rating-range',
            type=str,
            default='1-5',
            help='Range of ratings (min-max)'
        )
        parser.add_argument(
            '--username-prefix',
            type=str,
            default='testuser',
            help='Prefix for test usernames'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='password123',
            help='Password for test users'
        )

    def handle(self, *args, **options):
        num_users = options['users']
        ratings_per_user = options['ratings_per_user']
        username_prefix = options['username_prefix']
        password = options['password']
        
        try:
            rating_min, rating_max = map(int, options['rating_range'].split('-'))
        except ValueError:
            self.stdout.write(self.style.ERROR('Invalid rating range format. Use min-max (e.g., 1-5)'))
            return
            
        # Get available books
        books = list(Book.objects.all())
        if not books:
            self.stdout.write(self.style.ERROR('No books found in the database. Please add books first.'))
            return
            
        self.stdout.write(f'Found {len(books)} books in the database')
        
        users_created = 0
        ratings_created = 0
        
        try:
            with transaction.atomic():
                # Create test users
                created_users = []
                for i in range(1, num_users + 1):
                    username = f"{username_prefix}{i}"
                    
                    # Check if user already exists
                    if User.objects.filter(username=username).exists():
                        user = User.objects.get(username=username)
                        self.stdout.write(f'User {username} already exists (ID: {user.id})')
                    else:
                        user = User.objects.create_user(
                            username=username,
                            email=f"{username}@example.com",
                            password=password
                        )
                        self.stdout.write(f'Created user {username} (ID: {user.id})')
                        users_created += 1
                        
                    created_users.append(user)
                
                # Create random ratings
                for user in created_users:
                    # Select random books for this user to rate
                    if len(books) <= ratings_per_user:
                        books_to_rate = books
                    else:
                        books_to_rate = random.sample(books, ratings_per_user)
                    
                    for book in books_to_rate:
                        # Check if rating already exists
                        if BookRating.objects.filter(user=user, book=book).exists():
                            continue
                            
                        # Generate a random rating
                        rating_value = random.randint(rating_min, rating_max)
                        
                        BookRating.objects.create(
                            user=user,
                            book=book,
                            rate=rating_value
                        )
                        ratings_created += 1
                        
            self.stdout.write(self.style.SUCCESS(
                f'Successfully created {users_created} new users and {ratings_created} new ratings'
            ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating test data: {str(e)}'))