import random
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

import uuid
from .managers import CustomUserManager


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
    
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