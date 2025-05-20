# Import views to make them available when importing from the views package
from .notification_views import (
    NotificationListAPIView,
    NotificationDetailAPIView,
    NotificationCreateAPIView,
    NotificationUpdateAPIView,
    NotificationDeleteAPIView,
    NotificationMarkAsReadAPIView,
    NotificationMarkAsUnreadAPIView,
    NotificationMarkAllAsReadAPIView,
    NotificationUnreadCountAPIView
)

from .notification_type_views import (
    NotificationTypeListAPIView,
    NotificationTypeDetailAPIView
)