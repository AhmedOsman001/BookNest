from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from notifications.models import Notification, NotificationType
from notifications.serializers import NotificationSerializer, NotificationCreateSerializer


class IsRecipientOrAdmin(IsAuthenticated):
    """
    Custom permission to only allow recipients to view their own notifications.
    """
    def has_object_permission(self, request, view, obj):
        # Admin can see all notifications
        if request.user.is_staff:
            return True
        # Recipients can only see their own notifications
        return obj.recipient == request.user


class NotificationListAPIView(generics.ListAPIView):
    """
    API endpoint for listing notifications for the current user.
    Can be filtered by read/unread status and notification type.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Return notifications for the current user.
        Can be filtered by read/unread status.
        """
        user = self.request.user
        queryset = Notification.objects.filter(recipient=user)
        
        # Filter by read status if provided
        read = self.request.query_params.get('read')
        if read is not None:
            read_bool = read.lower() == 'true'
            queryset = queryset.filter(read=read_bool)
        
        # Filter by notification type if provided
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type__name=notification_type)
        
        return queryset.order_by('-timestamp')


class NotificationDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving a specific notification.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsRecipientOrAdmin]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationCreateAPIView(generics.CreateAPIView):
    """
    API endpoint for creating a new notification.
    """
    serializer_class = NotificationCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        notification = serializer.save()
        return notification


class NotificationUpdateAPIView(generics.UpdateAPIView):
    """
    API endpoint for updating a notification.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsRecipientOrAdmin]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationDeleteAPIView(generics.DestroyAPIView):
    """
    API endpoint for deleting a notification.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsRecipientOrAdmin]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationMarkAsReadAPIView(APIView):
    """
    API endpoint for marking a notification as read.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, id=None):
        notification = get_object_or_404(Notification, id=id, recipient=request.user)
        notification.mark_as_read()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationMarkAsUnreadAPIView(APIView):
    """
    API endpoint for marking a notification as unread.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, id=None):
        notification = get_object_or_404(Notification, id=id, recipient=request.user)
        notification.mark_as_unread()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationMarkAllAsReadAPIView(APIView):
    """
    API endpoint for marking all notifications as read.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        Notification.objects.filter(recipient=request.user, read=False).update(read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationUnreadCountAPIView(APIView):
    """
    API endpoint for getting the count of unread notifications.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, read=False).count()
        return Response({'count': count})