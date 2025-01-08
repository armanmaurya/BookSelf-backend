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
    index = models.PositiveIntegerField(default=0)
    has_children = models.BooleanField(default=False)

    class Meta:
        ordering = ['index']
    
    def save(self, *args, **kwargs):
        if self.pk is None and self.parent is not None:
            self.parent.has_children = True
            self.parent.save()
        if self.pk is None and self.index == 0:  # Check if it's a new object
            sibling_pages = Page.objects.filter(
                notebook=self.notebook, parent=self.parent
            )
            self.index = sibling_pages.count() + 1  # Make it the last page
        if self.pk:
            original = Page.objects.get(pk=self.pk)
            if original.title != self.title:
                self.slug = slugify(self.title)
        else:
            self.slug = slugify(self.title)
            if Page.objects.filter(slug=self.slug, parent = self.parent).exists():
                raise ValueError("A page with this slug already exists.")
        super(Page, self).save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        parent = self.parent
        super(Page, self).delete(*args, **kwargs)
        if parent:
            parent.has_children = parent.children.exists()
            parent.save(update_fields=['has_children'])
    
    def __str__(self):
        return self.title

