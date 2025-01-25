from rest_framework import serializers
from users.models.profile import Profile, ProfileInterest, ProfileSocialLink
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

class ProfileInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileInterest
        fields = ['interest']
        
class ProfileSocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileSocialLink
        fields = ['platform', 'url']




class ProfileSerializer(serializers.ModelSerializer):
    interests = ProfileInterestSerializer(many=True, required=False)
    social_links = ProfileSocialLinkSerializer(many=True, required=False)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    # Add a custom method to handle Cloudinary image field
    profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['id', 'username', 'email', 'profile_pic', 'bio', 'profile_type',
                  'settings', 'interests', 'social_links', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']

    def get_profile_pic(self, obj):
    
        if obj.profile_pic:
            # Convert Cloudinary field to string and remove any unwanted prefixes
            url = str(obj.profile_pic)
            
            # Remove 'image/upload/' prefix if present
            if url.startswith('image/upload/'):
                url = url.replace('image/upload/', '', 1)
            
            return url
        return None

    def create(self, validated_data):
        interests_data = validated_data.pop('interests', [])
        social_links_data = validated_data.pop('social_links', [])
        
        profile = Profile.objects.create(**validated_data)
        
        for interest_data in interests_data:
            ProfileInterest.objects.create(profile=profile, **interest_data)
            
        for link_data in social_links_data:
            ProfileSocialLink.objects.create(profile=profile, **link_data)
            
        return profile

    def update(self, instance, validated_data):
        # Handle nested interests
        interests_data = validated_data.pop('interests', [])
        if interests_data is not None:
            instance.interests.all().delete()
            for interest_data in interests_data:
                ProfileInterest.objects.create(profile=instance, **interest_data)

        # Handle nested social links
        social_links_data = validated_data.pop('social_links', [])
        if social_links_data is not None:
            instance.social_links.all().delete()
            for link_data in social_links_data:
                ProfileSocialLink.objects.create(profile=instance, **link_data)

        # Update the remaining fields
        return super().update(instance, validated_data)