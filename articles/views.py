from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from articles.models import Article
from .serializers import ArticleUploadSerializer, ArticleGetSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from rest_framework.decorators import api_view
User = get_user_model()

# Create your views here.
class ArticleView(APIView):
    @csrf_exempt
    def post(self, request):
        serializer = ArticleUploadSerializer(data=request.data)
        if serializer.is_valid():

            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        id = request.query_params.get('id')
        if id:
            article = Article.objects.get(id=id)
            serializer = ArticleGetSerializer(article)
            data = serializer.data
            author_id = data['author']
            author = User.objects.get(id=author_id)
            data['author'] = author.first_name + ' ' + author.last_name
            return Response(data)
        else:
            articles = Article.objects.all()
            serializer = ArticleGetSerializer(articles, many=True)
            data = serializer.data
            for article in data:
                author_id = article['author']
                author = User.objects.get(id=author_id)
                article['author'] = author.first_name + ' ' + author.last_name
            return Response(data)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return []


class ArticleListView(APIView):
    def get(self, request):
        articles = Article.objects.all()
        serializer = ArticleGetSerializer(articles, many=True)
        data = serializer.data
        for article in data:
            author_id = article['author']
            author = User.objects.get(id=author_id)
            article['author'] = author.first_name + ' ' + author.last_name
        return Response(data)
    
# @csrf_exempt
@api_view(['POST'])
def uploadArticle(request):
    if request.method == 'POST':
        serializer = ArticleUploadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)