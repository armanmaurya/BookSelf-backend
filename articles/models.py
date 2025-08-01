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
from pgvector.django import VectorField

# Create your models here.


class Article(models.Model):
    DRAFT = "DR"
    PUBLISHED = "PU"
    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (PUBLISHED, "Published"),
    ]
    embedding = VectorField(dimensions=768, null=True)
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
    image = models.ImageField(upload_to="article_images/", null=True, blank=True)

    def __str__(self):
        if self.title:
            return self.title
        return "Untitled"

    def related(self, min_similarity=0.6):
        """Returns a list of related articles based on embedding cosine similarity, limited to top 20."""
        if self.embedding is None:
            return Article.objects.none()
        
        from pgvector.django import CosineDistance
        
        # Calculate maximum distance for minimum similarity
        # Similarity = (1 - distance), so distance = 1 - similarity
        # max_distance = 1 - min_similarity
        
        related_articles = Article.objects.filter(
            embedding__isnull=False,
            status=self.PUBLISHED
        ).exclude(id=self.id).annotate(
            similarity_score=CosineDistance('embedding', self.embedding)
        # ).filter(
        #     similarity_score__lte=max_distance  # Only articles above similarity threshold
        ).order_by('similarity_score')[:20]
        
        # Print similarity scores for debugging
        print(f"\n=== Related articles for '{self.title}' (ID: {self.id}) ===")
        # print(f"Minimum similarity threshold: {min_similarity*100:.1f}%")
        
        if not related_articles.exists():
            print("No articles found above similarity threshold")
            return related_articles
            
        for article in related_articles:
            similarity_percentage = (1 - article.similarity_score) * 100
            print(f"- '{article.title}' (ID: {article.id}): {similarity_percentage:.2f}% similar (distance: {article.similarity_score:.4f})")
        
        return related_articles
    
    def get_embedding_text(self):
        """Get the text that should be used for embedding generation."""
        combined_text = ""
        if self.title:
            combined_text += f"Title: {self.title}\n\n"
        if self.content:
            combined_text += f"Content: {self.content}"
        
        # Include tags if available
        if hasattr(self, 'tags') and self.tags.exists():
            tags_text = ", ".join([tag.name for tag in self.tags.all()])
            combined_text += f"\n\nTags: {tags_text}"
        
        return combined_text.strip()

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


class ArticleDraft(models.Model):
    image = models.ImageField(upload_to="article_images/", null=True, blank=True)
    article = models.OneToOneField(
        Article, on_delete=models.CASCADE, related_name="draft"
    )
    title = models.CharField(max_length=100, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.title:
            return self.title
        return "Untitled"


class UserArticlesVisitHistory(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="reading_history"
    )
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="visitors"
    )

    last_visited = models.DateTimeField(auto_now=True)  # Updates on every visit
    visit_count = models.PositiveIntegerField(default=1)  # Tracks repeated visits

    class Meta:
        unique_together = ("user", "article")  # Ensures only one entry per user-article

    def __str__(self):
        return f"{self.user.username} visited {self.article.title} at {self.last_visited} {self.visit_count} times"


class ArticleComment(models.Model):
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="comments"
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    likes = models.ManyToManyField(CustomUser, related_name="comment_likes", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} commented on {self.article.title}"

    def is_root_comment(self):
        return self.parent is None

    def get_child_comments(self):
        return ArticleComment.objects.filter(parent=self)


class Collection(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="collections"
    )
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)  # Auto-set on creation
    updated_at = models.DateTimeField(auto_now=True)  # Auto-set on update

    def __str__(self):
        return self.name


class CollectionItem(models.Model):
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, related_name="items"
    )
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    date_added = models.DateTimeField(
        auto_now_add=True
    )  # Track when the item was added

    class Meta:
        unique_together = ("collection", "article")
        ordering = ["order"]  # Order by the order field

    def __str__(self):
        return f"{self.collection.name} - {self.article.title}"
