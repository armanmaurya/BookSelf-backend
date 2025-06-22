import random
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

import uuid
from .managers import CustomUserManager


class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(_("email address"), unique=True)
    
    REGISTRATION_CHOICES = [
        ("email", "Email"),
        ("google", "Google"),
    ]
    
    registration_method = models.CharField(
        max_length=10, choices=REGISTRATION_CHOICES, default="email"
    )
    profile_picture = models.ImageField(upload_to="profile_pictures/", null=True, blank=True)
    about = models.TextField(_(""), null=True, blank=True)
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "first_name", "last_name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    

class RegisterAccountTemp(models.Model):
    email = models.EmailField(_(""), max_length=254)
    first_name = models.CharField(_(""), max_length=150, null=True, blank=True)
    last_name = models.CharField(_(""), max_length=150, null=True, blank=True)


class EmailVerification(models.Model):
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    def is_valid(self):
        return (timezone.now() - self.created_at).total_seconds() < 3600  # valid for 1 hour
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = str(random.randint(1000, 9999))
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.email
    

class Follow(models.Model):
    user = models.ForeignKey(CustomUser, related_name='followers', on_delete=models.CASCADE)
    following = models.ForeignKey(CustomUser, related_name='following', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'following')

    def __str__(self):
        return f"{self.user.username} follows {self.following.username}"
    
