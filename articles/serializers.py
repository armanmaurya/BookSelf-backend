from rest_framework import serializers
from .models import Article

class ArticleUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['author']

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'title', 'content',
                  'author', 'created_at', "thumbnail"]
        