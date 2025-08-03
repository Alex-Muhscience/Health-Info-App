"""
Django models for the Health Management System frontend.
These models are for Django-specific functionality (users, sessions).
The main health data is managed by the Flask backend.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Custom user model for Django frontend.
    This extends Django's built-in User model.
    """
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.username


class UserSession(models.Model):
    """
    Track user sessions with the Flask backend.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    flask_token = models.TextField()  # JWT token from Flask backend
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at}"
