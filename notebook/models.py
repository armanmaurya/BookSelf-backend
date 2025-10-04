from django.db import models
from django.utils.text import slugify
from users.models import CustomUser

# Create your models here.


class Notebook(models.Model):
    slug = models.SlugField(max_length=100, unique=True, null=True, blank=True)  # Unique identifier
    name = models.CharField(max_length=100)  # Notebook name
    overview = models.TextField(blank=True, null=True)  # Optional description
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    cover = models.ImageField(upload_to='notebook_covers/', blank=True, null=True)

    def get_index_page(self):
        root_page = self.pages.filter(parent=None).first()
        if root_page:
            return root_page
        return None

    def save(self, *args, **kwargs):
        # Only generate slug if this is an update to an existing object with ID
        if self.pk:
            self.slug = self.generate_unique_slug()
        
        # Call the parent save method
        super().save(*args, **kwargs)
        
        # Generate slug after first save if this was a new object
        if not self.slug:
            self.slug = self.generate_unique_slug()
            super().save(update_fields=['slug'])
    
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
        unique_together = [['notebook', 'parent', 'index']]  # Ensure unique index within same parent
    
    def get_next_index(self):
        """Get the next available index for this page's siblings"""
        siblings = Page.objects.filter(notebook=self.notebook, parent=self.parent)
        if self.pk:
            siblings = siblings.exclude(pk=self.pk)
        
        max_index = siblings.aggregate(models.Max('index'))['index__max']
        return (max_index or 0) + 1
    
    def reorder_after(self, target_page_id=None):
        """Reorder this page to come after the target page, or at the beginning if target_page_id is None"""
        if target_page_id:
            try:
                target_page = Page.objects.get(id=target_page_id, notebook=self.notebook, parent=self.parent)
                new_index = target_page.index + 1
            except Page.DoesNotExist:
                raise ValueError("Target page not found in the same parent")
        else:
            new_index = 1
        
        # Shift existing pages to make room
        Page.objects.filter(
            notebook=self.notebook,
            parent=self.parent,
            index__gte=new_index
        ).exclude(id=self.id).update(index=models.F('index') + 1)
        
        self.index = new_index
        self.save()
    
    def reorder_before(self, target_page_id):
        """Reorder this page to come before the target page"""
        try:
            target_page = Page.objects.get(id=target_page_id, notebook=self.notebook, parent=self.parent)
            new_index = target_page.index
        except Page.DoesNotExist:
            raise ValueError("Target page not found in the same parent")
        
        # Shift existing pages to make room
        Page.objects.filter(
            notebook=self.notebook,
            parent=self.parent,
            index__gte=new_index
        ).exclude(id=self.id).update(index=models.F('index') + 1)
        
        self.index = new_index
        self.save()
    
    def save(self, *args, **kwargs):
        if self.pk is None and self.parent is not None:
            self.parent.has_children = True
            self.parent.save()
        if self.pk is None and self.index == 0:  # Check if it's a new object
            self.index = self.get_next_index()
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
