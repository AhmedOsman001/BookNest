from django.urls import path
from notifications.views import (
    NotificationListAPIView,
    NotificationDetailAPIView,
    NotificationCreateAPIView,
    NotificationUpdateAPIView,
    NotificationDeleteAPIView,
    NotificationMarkAsReadAPIView,
    NotificationMarkAsUnreadAPIView,
    NotificationMarkAllAsReadAPIView,
    NotificationUnreadCountAPIView,
    NotificationTypeListAPIView,
    NotificationTypeDetailAPIView
)

urlpatterns = [
    # Notification endpoints
    path('', NotificationListAPIView.as_view(), name='notification-list'),
    path('create/', NotificationCreateAPIView.as_view(), name='notification-create'),
    path('<int:id>/', NotificationDetailAPIView.as_view(), name='notification-detail'),
    path('<int:id>/update/', NotificationUpdateAPIView.as_view(), name='notification-update'),
    path('<int:id>/delete/', NotificationDeleteAPIView.as_view(), name='notification-delete'),
    path('<int:id>/mark-read/', NotificationMarkAsReadAPIView.as_view(), name='notification-mark-read'),
    path('<int:id>/mark-unread/', NotificationMarkAsUnreadAPIView.as_view(), name='notification-mark-unread'),
    path('mark-all-read/', NotificationMarkAllAsReadAPIView.as_view(), name='notification-mark-all-read'),
    path('unread-count/', NotificationUnreadCountAPIView.as_view(), name='notification-unread-count'),
    
    # Notification type endpoints
    path('types/', NotificationTypeListAPIView.as_view(), name='notification-type-list'),
    path('types/<int:id>/', NotificationTypeDetailAPIView.as_view(), name='notification-type-detail'),
]