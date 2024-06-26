from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from .models import Article


class ArticleUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["author"]


class ArticleSerializer(serializers.ModelSerializer, TaggitSerializer):
    tags = TagListSerializerField()

    class Meta:
        model = Article
        fields = "__all__"
