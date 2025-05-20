from django.urls import path
from follows.views import (
    FollowListAPIView,
    FollowDetailAPIView,
    FollowCreateAPIView,
    FollowDeleteAPIView,
    FollowerListAPIView,
    FollowingListAPIView,
    UserFollowersAPIView,
    UserFollowingAPIView
)

urlpatterns = [
    # Follow relationship endpoints
    path('', FollowListAPIView.as_view(), name='follow-list'),
    path('create/', FollowCreateAPIView.as_view(), name='follow-create'),
    path('<int:id>/', FollowDetailAPIView.as_view(), name='follow-detail'),
    path('unfollow/<int:followed_id>/', FollowDeleteAPIView.as_view(), name='follow-delete'),
    
    # User follow relationships
    path('followers/', FollowerListAPIView.as_view(), name='follower-list'),
    path('following/', FollowingListAPIView.as_view(), name='following-list'),
    path('user/<int:user_id>/followers/', UserFollowersAPIView.as_view(), name='user-followers'),
    path('user/<int:user_id>/following/', UserFollowingAPIView.as_view(), name='user-following'),
]