from rest_framework import serializers
from .models import Follow
from users.serializers.profile import ProfileSerializer

class FollowSerializer(serializers.ModelSerializer):
    """
    Serializer for the Follow model with detailed follower and followed information.
    """
    follower_detail = ProfileSerializer(source='follower', read_only=True)
    followed_detail = ProfileSerializer(source='followed', read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'followed', 'follower_detail', 'followed_detail', 'created_at']
        read_only_fields = ['follower', 'created_at']

class FollowCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a follow relationship.
    Only requires the followed user's ID.
    """
    class Meta:
        model = Follow
        fields = ['followed']

class FollowerListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing followers with profile details.
    """
    profile = ProfileSerializer(source='follower', read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'profile', 'created_at']

class FollowingListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users being followed with profile details.
    """
    profile = ProfileSerializer(source='followed', read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'profile', 'created_at']