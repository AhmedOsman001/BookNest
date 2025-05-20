from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import signals
from django.contrib.auth import get_user_model
import re
from .models import Notification, NotificationType
from books.models import BookReview, BookRating
from follows.models import Follow

User = get_user_model()

# Create default notification types when the app is ready
@receiver(signals.post_migrate)
def create_default_types(sender, **kwargs):
    """
    Create default notification types after migrations.
    """
    if sender.name == 'notifications':
        from .models import create_default_notification_types
        create_default_notification_types()

# # Helper function to detect mentions in text
# def detect_mentions(text):
#     """
#     Detect @username mentions in text and return a list of mentioned users.
    
#     Args:
#         text: The text to search for mentions
        
#     Returns:
#         List of User objects that were mentioned
#     """
#     # Find all @username patterns in the text
#     mention_pattern = r'@(\w+)'
#     mentions = re.findall(mention_pattern, text)
    
#     # Get the corresponding users
#     mentioned_users = []
#     for username in mentions:
#         try:
#             user = User.objects.get(username=username)
#             mentioned_users.append(user)
#         except User.DoesNotExist:
#             # Username doesn't exist, skip it
#             pass
    
#     return mentioned_users

# Book Review Notifications
@receiver(post_save, sender=BookReview)
def book_review_created(sender, instance, created, **kwargs):
    """
    Signal handler to create notifications when a book review is created.
    Notifies book authors and users following the book.
    """
    if created:
        # Import here to avoid circular imports
        from .services import NotificationService
        from users.models import Profile
        
        # Get the book authors to notify them
        for book_author in instance.book.authors.all():
            # Find the user profile associated with this author if any
            try:
                # Check for profiles with AUTHOR type that might be associated with this author
                author_profiles = Profile.objects.filter(profile_type='AUTHOR')
                for profile in author_profiles:
                    if profile.user:
                        # Notify the author about the review
                        NotificationService.create_notification(
                            recipient=profile.user,
                            actor=instance.user,
                            verb='reviewed your book',
                            target=instance.book,
                            action_object=instance,
                            notification_type='book_review'
                        )
            except Exception as e:
                print(f"Error creating notification for author {book_author.name}: {e}")
        
        # Check for user mentions in the review text
        # mentioned_users = detect_mentions(instance.review_text)
        # for mentioned_user in mentioned_users:
        #     # Don't notify the author of the review
        #     if mentioned_user != instance.user:
        #         try:
        #             NotificationService.create_notification(
        #                 recipient=mentioned_user,
        #                 actor=instance.user,
        #                 verb='mentioned you in a review',
        #                 target=instance.book,
        #                 action_object=instance,
        #                 notification_type='mention'
        #             )
        #         except Exception as e:
        #             print(f"Error creating mention notification for user {mentioned_user.username}: {e}")
        
        # Notify users who follow this book (through reading lists or other mechanisms)
        # This would require a model that tracks book followers
        # For now, we'll leave this as a placeholder

# Book Rating Notifications
@receiver(post_save, sender=BookRating)
def book_rating_created(sender, instance, created, **kwargs):
    """
    Signal handler to create notifications when a book rating is created.
    Notifies book authors about new ratings.
    """
    if created:
        # Import here to avoid circular imports
        from .services import NotificationService
        from users.models import Profile
        
        # Get the book authors to notify them
        for book_author in instance.book.authors.all():
            # Find the user profile associated with this author if any
            try:
                # Check for profiles with AUTHOR type that might be associated with this author
                author_profiles = Profile.objects.filter(profile_type='AUTHOR')
                for profile in author_profiles:
                    if profile.user:
                        # Notify the author about the rating
                        NotificationService.create_notification(
                            recipient=profile.user,
                            actor=instance.user,
                            verb=f'rated your book {instance.rate} stars',
                            target=instance.book,
                            action_object=instance,
                            notification_type='book_rating'
                        )
            except Exception as e:
                print(f"Error creating notification for author {book_author.name}: {e}")

# Reading List Notifications
@receiver(post_save, sender='books.ReadingListBooks')
def reading_list_book_added(sender, instance, created, **kwargs):
    """
    Signal handler to create notifications when a book is added to a reading list.
    Notifies book authors when their books are added to reading lists.
    """
    if created:
        # Import here to avoid circular imports
        from .services import NotificationService
        from users.models import Profile
        
        # Get the book authors to notify them
        for book_author in instance.book.authors.all():
            try:
                # Check for profiles with AUTHOR type that might be associated with this author
                author_profiles = Profile.objects.filter(profile_type='AUTHOR')
                for profile in author_profiles:
                    if profile.user:
                        # Notify the author about the book being added to a reading list
                        NotificationService.create_notification(
                            recipient=profile.user,
                            actor=instance.readinglist.profile.user,
                            verb='added your book to their reading list',
                            target=instance.book,
                            action_object=instance.readinglist,
                            notification_type='system'
                        )
            except Exception as e:
                print(f"Error creating notification for author {book_author.name}: {e}")

# System Notifications
# This can be used for system-wide announcements or important updates
def create_system_notification(recipients, message, data=None):
    """
    Create a system notification for multiple recipients.
    
    Args:
        recipients: List of users to receive the notification
        message: The notification message
        data: Additional data for the notification
    """
    from .services import NotificationService
    
    for recipient in recipients:
        NotificationService.create_notification(
            recipient=recipient,
            verb=message,
            notification_type='system',
            data=data or {}
        )