from django.db import models
from django.conf import settings
from users.models.profile import Profile

class Follow(models.Model):
    """
    Model to represent a follow relationship between users.
    A user (follower) can follow another user (followed).
    """
    follower = models.ForeignKey(
        Profile, 
        on_delete=models.CASCADE, 
        related_name='following'
    )
    followed = models.ForeignKey(
        Profile, 
        on_delete=models.CASCADE, 
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'followed')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.follower.user.username} follows {self.followed.user.username}"
    
    def save(self, *args, **kwargs):
        # Prevent users from following themselves
        if self.follower == self.followed:
            return
        super().save(*args, **kwargs)