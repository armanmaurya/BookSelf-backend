from rest_framework import serializers
from .models import Article

class ArticleUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['title', 'content']

class ArticleGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'title', 'content',
                  'author', 'created_at', "thumbnail"]