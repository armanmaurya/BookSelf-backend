from django.db import models
from django.utils.text import slugify
from notebook.models import Notebook

# Create your models here.

class Page(models.Model):
    slug = models.SlugField(max_length=255)
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE, related_name="pages")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    
    def save(self, *args, **kwargs):
        if self.pk:
            original = Page.objects.get(pk=self.pk)
            if original.title != self.title:
                self.slug = slugify(self.title)
        else:
            self.slug = slugify(self.title)
        super(Page, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.title

