from django.db import models
from django.conf import settings

# Create your models here.


class Article(models.Model):
    DRAFT = 'DR'
    PUBLISHED = 'PU'
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
    ]

    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    thumbnail = models.ImageField(
        upload_to='thumbnails/', null=True, blank=True)
    status = models.CharField(
        max_length=2, choices=STATUS_CHOICES, default=DRAFT)

    def __str__(self):
        return self.title
