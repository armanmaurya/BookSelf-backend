from rest_framework import serializers
from .models import Notebook

class NotebookFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notebook
        fields = ["name"]

class NotebookGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notebook
        fields = "__all__"