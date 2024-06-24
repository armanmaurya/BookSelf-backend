from django.db import models
from django.conf import settings
import uuid

# Create your models here.


class Article(models.Model):
    DRAFT = 'DR'
    PUBLISHED = 'PU'
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
    ]
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    thumbnail = models.ImageField(
        upload_to='thumbnails/', null=True, blank=True)
    status = models.CharField(
        max_length=2, choices=STATUS_CHOICES, default=DRAFT)

    def __str__(self):
        if self.title:
            return self.title
        return "Untitled"
