from django.db import models
from django.utils.text import slugify
from users.models import CustomUser

# Create your models here.


class Notebook(models.Model):
    class AlreadyExist(Exception):
        """Exception raised when a notebook already exists."""
        pass

    slug = models.SlugField(max_length=100)  # Unique identifier
    name = models.CharField(max_length=100)  # Notebook name
    overview = models.TextField(blank=True, null=True)  # Optional description
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    cover = models.ImageField(upload_to='notebook_covers/', blank=True, null=True)

    def get_index_page(self):
        from page.models import Page

        root_page: Page | any = self.pages.filter(parent=None).first()
        if root_page:
            return root_page
        return None

    def save(self, *args, **kwargs):
        if not self.id:
            super().save(*args, **kwargs)
        self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)
    
    def generate_unique_slug(self):
        slug = ""
        if self.name:
            base_slug = slugify(self.name)
            slug = f"{base_slug}-{self.id}"
        else:
            slug = str(self.id)
        return slug

    def __str__(self):
        return self.name
