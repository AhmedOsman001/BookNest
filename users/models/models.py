from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import uuid
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)

class CustomUser(AbstractUser):
    objects = CustomUserManager()
    def delete(self, *args, **kwargs):
        # Delete associated tokens
        OutstandingToken.objects.filter(user=self).delete()
        super().delete(*args, **kwargs)
    def __str__(self):
        return self.username