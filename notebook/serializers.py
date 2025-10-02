from rest_framework import serializers
from .models import Notebook, Page

class NotebookFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notebook
        fields = ["name", "overview"]

class NotebookGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notebook
        fields = ["id", "name", "slug","overview", "created_at"]


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["id", "title", "content", "created_at", "updated_at", "notebook", "parent", "index", "has_children", "slug"]


class PageCreateFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["title"]

class PageUpdateFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["title", "content"]