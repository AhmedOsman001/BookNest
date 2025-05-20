from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from follows.models import Follow
from follows.serializers import (
    FollowSerializer, 
    FollowCreateSerializer,
    FollowerListSerializer,
    FollowingListSerializer
)
from users.models.profile import Profile


class FollowListAPIView(generics.ListAPIView):
    """
    API endpoint for listing follow relationships for the current user.
    """
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Follow.objects.filter(
            Q(follower__user=self.request.user) | Q(followed__user=self.request.user)
        ).order_by('-created_at')


class FollowDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving a specific follow relationship.
    """
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Follow.objects.filter(
            Q(follower__user=self.request.user) | Q(followed__user=self.request.user)
        )


class FollowCreateAPIView(generics.CreateAPIView):
    """
    API endpoint for creating a follow relationship (current user follows another user).
    """
    serializer_class = FollowCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # Get the follower (current user) and followed profiles
        follower_profile = self.request.user.profile
        followed_id = serializer.validated_data['followed'].id
        followed_profile = get_object_or_404(Profile, id=followed_id)
        
        # Prevent users from following themselves
        if follower_profile == followed_profile:
            return Response(
                {'error': 'You cannot follow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already following
        if Follow.objects.filter(follower=follower_profile, followed=followed_profile).exists():
            return Response(
                {'error': 'You are already following this user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the follow relationship
        serializer.save(follower=follower_profile)


class FollowDeleteAPIView(generics.DestroyAPIView):
    """
    API endpoint for deleting a follow relationship (unfollowing a user).
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, *args, **kwargs):
        followed_id = kwargs.get('followed_id')
        if not followed_id:
            return Response(
                {'error': 'Followed user ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        follower_profile = request.user.profile
        followed_profile = get_object_or_404(Profile, id=followed_id)
        
        follow = get_object_or_404(
            Follow, 
            follower=follower_profile, 
            followed=followed_profile
        )
        
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowerListAPIView(generics.ListAPIView):
    """
    API endpoint for listing users who follow the current user.
    """
    serializer_class = FollowerListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Follow.objects.filter(followed__user=self.request.user).order_by('-created_at')


class FollowingListAPIView(generics.ListAPIView):
    """
    API endpoint for listing users that the current user follows.
    """
    serializer_class = FollowingListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Follow.objects.filter(follower__user=self.request.user).order_by('-created_at')


class UserFollowersAPIView(generics.ListAPIView):
    """
    API endpoint for listing followers of a specific user.
    """
    serializer_class = FollowerListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        profile = get_object_or_404(Profile, id=user_id)
        return Follow.objects.filter(followed=profile).order_by('-created_at')


class UserFollowingAPIView(generics.ListAPIView):
    """
    API endpoint for listing users that a specific user follows.
    """
    serializer_class = FollowingListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        profile = get_object_or_404(Profile, id=user_id)
        return Follow.objects.filter(follower=profile).order_by('-created_at')