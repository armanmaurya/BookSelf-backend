import random
import string
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid
from taggit.managers import TaggableManager
from taggit.models import GenericUUIDTaggedItemBase, TaggedItemBase
from django.utils.text import slugify
from users.models import CustomUser

# Create your models here.


class Article(models.Model):
    DRAFT = "DR"
    PUBLISHED = "PU"
    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (PUBLISHED, "Published"),
    ]
    title = models.CharField(max_length=100, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    likes = models.ManyToManyField(CustomUser, related_name="likes", blank=True)
    tags = TaggableManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    thumbnail = models.ImageField(upload_to="thumbnails/", null=True, blank=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=DRAFT)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    views = models.PositiveIntegerField(default=0)

    def __str__(self):
        if self.title:
            return self.title
        return "Untitled"

    def save(self, *args, **kwargs):
        if not self.id:
            super().save(*args, **kwargs)
        self.slug = self.generate_unique_slug()
        super().save()

    def like(self, user):
        self.likes.add(user)

    def unlike(self, user):
        self.likes.remove(user)

    def get_likes_count(self):
        return self.likes.count()

    def generate_unique_slug(self):
        print(self.id)
        slug = ""
        if self.title:
            base_slug = slugify(self.title)
            slug = f"{base_slug}-{self.id}"
        else:
            slug = str(self.id)

        return slug


class UserArticlesVisitHistory(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} visited {self.article.title} at {self.timestamp}"
    

class ArticleComment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} commented on {self.article.title}"
    
    def is_root_comment(self):
        return self.parent is None
    
    def get_child_comments(self):
        return ArticleComment.objects.filter(parent=self)
    
    
