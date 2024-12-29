from django.db import models
from users.models import CustomUser

# Create your models here.

class Notebook(models.Model):
    slug = models.SlugField(max_length=100)  # Unique identifier
    name = models.CharField(max_length=100)  # Notebook name
    description = models.TextField(blank=True, null=True)  # Optional description
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)


    def __str__(self):
        return self.name
