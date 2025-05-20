from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class NotificationType(models.Model):
    """
    Model to define different types of notifications.
    This allows for easy extension of notification types.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Notification(models.Model):
    """
    Generic notification model that can be linked to any object.
    Uses the ContentType framework to enable generic relations.
    """
    # Who the notification is for
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    
    # Who triggered the notification (optional)
    actor_content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        related_name='actor_notifications',
        null=True, blank=True
    )
    actor_object_id = models.CharField(max_length=255, null=True, blank=True)
    actor = GenericForeignKey('actor_content_type', 'actor_object_id')
    
    # The verb describing the action (e.g., "commented on", "liked", "followed")
    verb = models.CharField(max_length=255)
    
    # The object the action was performed on (optional)
    target_content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        related_name='target_notifications',
        null=True, blank=True
    )
    target_object_id = models.CharField(max_length=255, null=True, blank=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')
    
    # The object that was created by the action (optional)
    action_object_content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        related_name='action_object_notifications',
        null=True, blank=True
    )
    action_object_id = models.CharField(max_length=255, null=True, blank=True)
    action_object = GenericForeignKey('action_object_content_type', 'action_object_id')
    
    # Type of notification for filtering
    notification_type = models.ForeignKey(
        NotificationType, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        null=True, blank=True
    )
    
    # Additional data stored as JSON
    data = models.JSONField(default=dict, blank=True)
    
    # Status fields
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['recipient']),
            models.Index(fields=['read']),
        ]
    
    def __str__(self):
        return f"{self.recipient.username} - {self.verb}"
    
    def mark_as_read(self):
        """
        Mark the notification as read.
        """
        if not self.read:
            self.read = True
            self.save(update_fields=['read'])
    
    def mark_as_unread(self):
        """
        Mark the notification as unread.
        """
        if self.read:
            self.read = False
            self.save(update_fields=['read'])

# Create default notification types
def create_default_notification_types():
    """
    Create default notification types if they don't exist.
    This can be called in a migration or when the app is ready.
    """
    default_types = [
        {'name': 'follow', 'description': 'When someone follows you'},
        {'name':'unfollow', 'description': 'When someone unfollows you'},
        {'name': 'book_review', 'description': 'When someone reviews a book you authored or are following'},
        {'name': 'book_rating', 'description': 'When someone rates a book you authored or are following'},
        {'name': 'mention', 'description': 'When someone mentions you in a comment or review'},
        {'name': 'system', 'description': 'System notifications'},
    ]
    
    for type_data in default_types:
        NotificationType.objects.get_or_create(
            name=type_data['name'],
            defaults={'description': type_data['description']}
        )