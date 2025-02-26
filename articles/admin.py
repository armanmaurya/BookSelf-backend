from django.contrib import admin
from .models import Article, UserArticlesVisitHistory, Collection

# Register your models here.
admin.site.register(Article)
admin.site.register(UserArticlesVisitHistory)
admin.site.register(Collection)
