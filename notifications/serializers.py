from rest_framework import serializers
from .models import Notification, NotificationType
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

class NotificationTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for notification types.
    """
    class Meta:
        model = NotificationType
        fields = ['id', 'name', 'description']

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for notifications with detailed information about related objects.
    """
    actor_name = serializers.SerializerMethodField()
    target_name = serializers.SerializerMethodField()
    action_object_name = serializers.SerializerMethodField()
    notification_type_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'actor_name', 'verb', 'target_name',
            'action_object_name', 'notification_type_name', 'data',
            'read', 'timestamp'
        ]
        read_only_fields = ['recipient', 'timestamp']
    
    def get_actor_name(self, obj):
        """
        Get a string representation of the actor.
        """
        if obj.actor:
            if hasattr(obj.actor, 'get_full_name'):
                return obj.actor.get_full_name() or obj.actor.username
            return str(obj.actor)
        return None
    
    def get_target_name(self, obj):
        """
        Get a string representation of the target.
        """
        if obj.target:
            return str(obj.target)
        return None
    
    def get_action_object_name(self, obj):
        """
        Get a string representation of the action object.
        """
        if obj.action_object:
            return str(obj.action_object)
        return None
    
    def get_notification_type_name(self, obj):
        """
        Get the name of the notification type.
        """
        if obj.notification_type:
            return obj.notification_type.name
        return None

class NotificationCreateSerializer(serializers.Serializer):
    """
    Serializer for creating notifications through the API.
    This provides a simplified interface for creating notifications.
    """
    recipient_id = serializers.IntegerField()
    actor_id = serializers.IntegerField(required=False)
    verb = serializers.CharField(max_length=255)
    target_content_type = serializers.CharField(required=False)
    target_object_id = serializers.CharField(required=False)
    action_object_content_type = serializers.CharField(required=False)
    action_object_id = serializers.CharField(required=False)
    notification_type = serializers.CharField(required=False)
    data = serializers.JSONField(required=False, default=dict)
    
    def validate_recipient_id(self, value):
        try:
            User.objects.get(id=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Recipient user does not exist")
    
    def validate_actor_id(self, value):
        if value:
            try:
                User.objects.get(id=value)
                return value
            except User.DoesNotExist:
                raise serializers.ValidationError("Actor user does not exist")
        return value
    
    def validate_notification_type(self, value):
        if value:
            try:
                NotificationType.objects.get(name=value)
                return value
            except NotificationType.DoesNotExist:
                raise serializers.ValidationError("Notification type does not exist")
        return value
    
    def create(self, validated_data):
        # Import here to avoid circular imports
        from .services import NotificationService
        
        recipient = User.objects.get(id=validated_data['recipient_id'])
        
        # Get actor if provided
        actor = None
        if 'actor_id' in validated_data and validated_data['actor_id']:
            actor = User.objects.get(id=validated_data['actor_id'])
        
        # Get target if provided
        target = None
        if 'target_content_type' in validated_data and 'target_object_id' in validated_data:
            try:
                content_type = ContentType.objects.get(model=validated_data['target_content_type'])
                target_model = content_type.model_class()
                target = target_model.objects.get(id=validated_data['target_object_id'])
            except (ContentType.DoesNotExist, AttributeError, target_model.DoesNotExist):
                pass
        
        # Get action_object if provided
        action_object = None
        if 'action_object_content_type' in validated_data and 'action_object_id' in validated_data:
            try:
                content_type = ContentType.objects.get(model=validated_data['action_object_content_type'])
                action_object_model = content_type.model_class()
                action_object = action_object_model.objects.get(id=validated_data['action_object_id'])
            except (ContentType.DoesNotExist, AttributeError, action_object_model.DoesNotExist):
                pass
        
        # Get notification_type if provided
        notification_type = None
        if 'notification_type' in validated_data and validated_data['notification_type']:
            notification_type = NotificationType.objects.get(name=validated_data['notification_type'])
        
        # Create notification using the service
        notification = NotificationService.create_notification(
            recipient=recipient,
            actor=actor,
            verb=validated_data['verb'],
            target=target,
            action_object=action_object,
            notification_type=notification_type,
            data=validated_data.get('data', {})
        )
        
        return notification