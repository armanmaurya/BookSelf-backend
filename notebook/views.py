from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from .serializers import NotebookFormSerializer, NotebookGetSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Notebook

from users.models import CustomUser as User

# Create your views here.

class NoteBookView(APIView):
    authentication_classes = [SessionAuthentication]

    def get(self, request, slug=None, username=None):
        if slug and username:
            try:
                user = User.objects.get(username=username)
                notebook = Notebook.objects.get(slug=slug, user=user)
                serializer = NotebookGetSerializer(notebook)
                return Response(serializer.data)
            except Notebook.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        elif username and slug is None:
            try:
                user = User.objects.get(username=username)
                notebooks = Notebook.objects.filter(user=user)
                serializer = NotebookGetSerializer(notebooks, many=True)
                return Response(serializer.data)
            except User.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            notebooks = Notebook.objects.all()
            serializer = NotebookGetSerializer(notebooks, many=True)
            return Response(serializer.data)

    @permission_classes([IsAuthenticated])
    def post(self, request):
        serializer = NotebookFormSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user = request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)