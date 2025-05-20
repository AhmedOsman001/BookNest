from django.contrib.contenttypes.models import ContentType
from .models import Notification, NotificationType

class NotificationService:
    """
    Service class for creating and managing notifications.
    Implements a publisher-subscriber pattern for notification handling.
    """
    
    @classmethod
    def create_notification(cls, recipient, verb, actor=None, target=None, action_object=None, 
                           notification_type=None, data=None):
        """
        Create a notification with the given parameters.
        
        Args:
            recipient: The user who will receive the notification
            verb: A string describing the action (e.g., "commented on", "liked")
            actor: The user who performed the action (optional)
            target: The object the action was performed on (optional)
            action_object: The object created by the action (optional)
            notification_type: The type of notification or its name (optional)
            data: Additional data to store with the notification (optional)
            
        Returns:
            The created notification object
        """
        if data is None:
            data = {}
            
        # Handle notification_type as string or object
        if isinstance(notification_type, str):
            notification_type, _ = NotificationType.objects.get_or_create(
                name=notification_type,
                defaults={'description': f'Notification for {notification_type}'}
            )
        
        # Create the notification
        notification = Notification(
            recipient=recipient,
            verb=verb,
            data=data
        )
        
        # Set actor if provided
        if actor:
            actor_content_type = ContentType.objects.get_for_model(actor)
            notification.actor_content_type = actor_content_type
            notification.actor_object_id = actor.pk
        
        # Set target if provided
        if target:
            target_content_type = ContentType.objects.get_for_model(target)
            notification.target_content_type = target_content_type
            notification.target_object_id = target.pk
        
        # Set action_object if provided
        if action_object:
            action_object_content_type = ContentType.objects.get_for_model(action_object)
            notification.action_object_content_type = action_object_content_type
            notification.action_object_id = action_object.pk
        
        # Set notification_type if provided
        if notification_type:
            notification.notification_type = notification_type
        
        notification.save()
        
        # Trigger any additional processing (e.g., sending emails, push notifications)
        cls._process_notification(notification)
        
        return notification
    
    @classmethod
    def _process_notification(cls, notification):
        """
        Process a notification after creation.
        This can be extended to send emails, push notifications, etc.
        
        Args:
            notification: The notification object to process
        """
        # This is a placeholder for additional notification processing
        # For example, sending emails or push notifications
        pass
    
    @classmethod
    def get_unread_count(cls, user):
        """
        Get the count of unread notifications for a user.
        
        Args:
            user: The user to get the count for
            
        Returns:
            The count of unread notifications
        """
        return Notification.objects.filter(recipient=user, read=False).count()
    
    @classmethod
    def mark_all_as_read(cls, user):
        """
        Mark all notifications for a user as read.
        
        Args:
            user: The user whose notifications to mark as read
            
        Returns:
            The number of notifications marked as read
        """
        return Notification.objects.filter(recipient=user, read=False).update(read=True)
    
    @classmethod
    def delete_read_notifications(cls, user, days=30):
        """
        Delete read notifications older than the specified number of days.
        
        Args:
            user: The user whose notifications to delete
            days: The number of days to keep read notifications
            
        Returns:
            The number of notifications deleted
        """
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return Notification.objects.filter(
            recipient=user,
            read=True,
            timestamp__lt=cutoff_date
        ).delete()[0]