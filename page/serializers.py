from .models import Page
from rest_framework import serializers

class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["id", "title", "content", "created_at", "updated_at", "notebook", "parent"]


class PageCreateFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["title"]