from django.db import models

# Create your models here.

class Notebook(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Notebook name
    description = models.TextField(blank=True, null=True)  # Optional description
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
