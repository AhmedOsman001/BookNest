from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField

def validate_image_size(value):
    """Validator to ensure uploaded files aren't too large"""
    filesize = value.size
    
    if filesize > 5 * 1024 * 1024:  # 5MB
        raise ValidationError("The maximum file size that can be uploaded is 5MB")


class Profile(models.Model):
    # Profile type choices for the Profile_Type field
    PROFILE_TYPES = [
        ('REGULAR', 'Regular User'),
        ('AUTHOR', 'Author'),
        ('PUBLISHER', 'Publisher'),
    ]

    # One-to-one relationship with User model
    user = models.OneToOneField('users.CustomUser', on_delete=models.CASCADE, related_name='profile')
    profile_pic = CloudinaryField(
        'image', 
        max_length=500,
        folder='profile_pics/',  # Organize in a specific folder
        transformation=[
            {'width': 400, 'height': 400, 'crop': 'fill'},  # Optional: resize
        ],
        blank=True, 
        null=True
    )
    bio = models.TextField(max_length=500, blank=True)
    profile_type = models.CharField(max_length=20, choices=PROFILE_TYPES, default='REGULAR')
    settings = models.JSONField(default=dict)  # Storing settings as JSON
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class ProfileInterest(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='interests')
    interest = models.CharField(max_length=100)
    
    class Meta:
        unique_together = ['profile', 'interest']  # Prevent duplicate interests for same profile

    def __str__(self):
        return f"{self.profile.user.username} - {self.interest}"

class ProfileSocialLink(models.Model):
    SOCIAL_PLATFORMS = [
        ('TWITTER', 'Twitter'),
        ('FACEBOOK', 'Facebook'),
        ('INSTAGRAM', 'Instagram'),
        ('LINKEDIN', 'LinkedIn'),
        ('GITHUB', 'GitHub'),
        ('WEBSITE', 'Personal Website'),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='social_links')
    platform = models.CharField(max_length=20, choices=SOCIAL_PLATFORMS)
    url = models.URLField()

    class Meta:
        unique_together = ['profile', 'platform']  # One link per platform per profile

    def __str__(self):
        return f"{self.profile.user.username} - {self.platform}"

# Signal to automatically create a profile when a user is created
# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)

# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
# def save_user_profile(sender, instance, **kwargs):
#     instance.profile.save()