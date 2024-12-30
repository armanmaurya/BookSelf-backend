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

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        isExist = Notebook.objects.filter(slug=self.slug, user=self.user).exists()
        
        if isExist:
            raise Notebook.AlreadyExist("Notebook with this name already exists")
        super(Notebook, self).save(*args, **kwargs)

    def __str__(self):
        return self.name
