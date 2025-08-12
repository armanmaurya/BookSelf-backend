from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from .models import Article, ArticleComment, ArticleDraft
from users.serializers import UserSerializer


class ArticleUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["author"]


class ArticleSerializer(serializers.ModelSerializer, TaggitSerializer):
    tags = TagListSerializerField()
    likes_count = serializers.SerializerMethodField()
    author = UserSerializer()
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "title",
            "content",
            "likes_count",
            "created_at",
            "author",
            "thumbnail",
            "status",
            "slug",
            "views",
        ]

    def get_likes_count(self, obj):
        return obj.get_likes_count()
    
    def get_comments(self, obj):
        comments = ArticleComment.objects.filter(article=obj, parent=None)
        return CommentSerializer(comments, many=True).data

class ArticleDraftThumbnailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleDraft
        fields = ["image"]

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleComment
        fields = "__all__"
