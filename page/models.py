from django.db import models
from notebook.models import Notebook

# Create your models here.

class Page(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE, related_name="pages")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="children")

    def __str__(self):
        return self.title
    
