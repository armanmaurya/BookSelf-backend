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
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

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

        related_articles = (
            Article.objects.filter(embedding__isnull=False, status=self.PUBLISHED)
            .exclude(id=self.id)
            .annotate(
                similarity_score=CosineDistance("embedding", self.embedding)
                # ).filter(
                #     similarity_score__lte=max_distance  # Only articles above similarity threshold
            )
            .order_by("similarity_score")[:20]
        )

        # Print similarity scores for debugging
        print(f"\n=== Related articles for '{self.title}' (ID: {self.id}) ===")
        # print(f"Minimum similarity threshold: {min_similarity*100:.1f}%")

        if not related_articles.exists():
            print("No articles found above similarity threshold")
            return related_articles

        for article in related_articles:
            similarity_percentage = (1 - article.similarity_score) * 100
            print(
                f"- '{article.title}' (ID: {article.id}): {similarity_percentage:.2f}% similar (distance: {article.similarity_score:.4f})"
            )

        return related_articles

    def get_embedding_text(self):
        """Get the text that should be used for embedding generation."""
        combined_text = ""
        if self.title:
            combined_text += f"Title: {self.title}\n\n"
        if self.content:
            combined_text += f"Content: {self.content}"

        # Include tags if available
        if hasattr(self, "tags") and self.tags.exists():
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

    def get_save_count(self):
        return CollectionItem.objects.filter(article=self).count()

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

    def compress_image(self, image_field):
        """Compress image before saving while maintaining aspect ratio"""
        if not image_field:
            return None
            
        try:
            # Open and process the image
            image = Image.open(image_field)
            image = image.convert("RGB")  # Ensure JPEG compatibility
            
            # Calculate new dimensions (max width/height of 1200px) while maintaining aspect ratio
            max_size = (1200, 1200)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)  # Maintains aspect ratio
            
            # Create buffer and save compressed image
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=85, optimize=True)
            buffer.seek(0)
            
            # Create new InMemoryUploadedFile
            compressed_image = InMemoryUploadedFile(
                buffer,
                "ImageField",
                image_field.name.split(".")[0] + ".jpg",
                "image/jpeg",
                sys.getsizeof(buffer),
                None,
            )
            return compressed_image
        except Exception as e:
            print(f"Image compression failed: {str(e)}")
            return image_field  # Return original if compression fails

    def save(self, *args, **kwargs):
        # Compress image if it exists and is being uploaded
        if self.image:
            self.image = self.compress_image(self.image)
        super().save(*args, **kwargs)

    def publish(self):
        """Publish the draft article, copying content and image without duplication"""
        article = self.article
        
        # Check if title or content changed to determine if embedding generation is needed
        title_changed = article.title != self.title
        content_changed = article.content != self.content
        needs_embedding = title_changed or content_changed
        
        # Only update fields if they changed
        if title_changed:
            article.title = self.title
        if content_changed:
            article.content = self.content
        
        # Only copy image if it's different
        image_changed = False
        if self.image and not article.thumbnail:
            # If draft has image but article doesn't, copy it
            article.thumbnail = self.image
            image_changed = True
        elif self.image and article.thumbnail and str(self.image) != str(article.thumbnail):
            # If both have images but they're different, replace article's image with draft's image
            article.thumbnail = self.image
            image_changed = True
        # If draft has no image, keep article's existing image (don't change)
        
        # Set status to published
        article.status = Article.PUBLISHED
        article.save()
        
        # Return whether embedding generation is needed
        return needs_embedding

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
    is_pinned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} commented on {self.article.title}"

    def pin(self):
        # Pin only if parent is None
        if self.is_root_comment():
            self.is_pinned = True
            self.save()

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
