from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from notifications.models import NotificationType
from notifications.serializers import NotificationTypeSerializer


class NotificationTypeListAPIView(generics.ListAPIView):
    """
    API endpoint for listing all notification types.
    """
    queryset = NotificationType.objects.all()
    serializer_class = NotificationTypeSerializer
    permission_classes = [IsAuthenticated]


class NotificationTypeDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving a specific notification type.
    """
    queryset = NotificationType.objects.all()
    serializer_class = NotificationTypeSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'